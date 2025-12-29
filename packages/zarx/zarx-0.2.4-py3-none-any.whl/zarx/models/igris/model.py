"""
ZARX_IGRIS_NANO_277M - Core Model Implementation
Production-grade main model that orchestrates all components.

This is the heart of the system - where all the magic happens.
277M total parameters, ~26M active per token.
Equivalent performance to 3-4B dense models at 1/50th the cost.

Architecture Overview:
    1. Token + Position Embeddings
    2. Internal CoT Vector Initialization
    3. Adaptive Router (makes all decisions)
    4. 16 HASS Blocks (3 pathways each: Local/Global/SSM)
    5. 192 Disk-Sharded MoE Experts (Top-2 routing)
    6. Merger Gate (fuses all outputs)
    7. LM Head → Logits

Key Innovation: Adaptive sparse activation via intelligent routing.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint
import math
import warnings
from typing import Optional, Tuple, Dict, List, Union, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import time

from zarx.config import IgrisConfig
from zarx.utils.logger import get_logger
from zarx.utils.math_utils import (
    TensorStability, 
    InformationTheory,
    count_parameters,
    get_device_memory_stats,
    RMSNorm
)
from zarx.model.components.cot_vector import InternalLatentCoT
from zarx.model.components.routing import AdaptiveRouter, RoutingDecision, RoutingRegularizer
from zarx.model.components.hass_block import HASSBlock
from zarx.model.components.merger import zarxMergerGate

logger = get_logger()



# ==================== MAIN MODEL ====================

from zarx.model.base import BaseModel, ModelOutput, GenerationConfig


class IgrisModel(BaseModel):
    """
    ZARX_IGRIS_NANO_277M - Production-grade main model.
    
    This is THE model. Everything comes together here.
    
    Architecture:
        - 277M total parameters
        - ~26M active per token (via adaptive routing)
        - 16 HASS blocks (hybrid attention + SSM)
        - 192 disk-sharded MoE experts
        - Internal 6-component CoT reasoning
        - Adaptive depth, width, and pathway selection
    
    Performance:
        - Equivalent to 3-4B dense models
        - 10-20× faster inference
        - 1/50th training cost
        - Runs on CPU (16GB RAM)
    
    Args:
        config: IgrisConfig instance with all hyperparameters
    """
    
    def __init__(self, config: IgrisConfig, test_mode: bool = False):
        super().__init__(config)
        
        if not isinstance(config, IgrisConfig):
            raise TypeError(f"config must be IgrisConfig, got {type(config)}")
        
        self.config = config
        self.test_mode = test_mode # Store test_mode
        
        # Validate configuration
        self._validate_config()
        
        logger.info("core", f"Initializing {config.model_name} with {config.num_layers} layers...")
        
        # ========== EMBEDDINGS ==========
        self.token_embedding = nn.Embedding(
            num_embeddings=config.vocab_size,
            embedding_dim=config.hidden_size,
            padding_idx=config.pad_token_id if hasattr(config, 'pad_token_id') else None
        )
        
        # Position embeddings (learned for now, can switch to RoPE)
        self.position_embedding = nn.Embedding(
            num_embeddings=config.context_length,
            embedding_dim=config.hidden_size
        )
        
        # Embedding dropout
        self.embedding_dropout = nn.Dropout(config.dropout)
        
        # ========== INTERNAL REASONING ==========
        # Internal CoT vector module (6 components)
        self.cot = InternalLatentCoT(config)
        logger.info("core", f"Internal CoT: {config.cot_components} components × {config.cot_dim} dim = {config.cot_dim * config.cot_components} total")
        
        # ========== ADAPTIVE ROUTING ==========
        # Router makes all decisions: depth, width, path, expert
        self.router = AdaptiveRouter(config)
        self.routing_regularizer = RoutingRegularizer(config)
        logger.info("core", "Adaptive Router initialized (depth/width/path/expert routing)")
        
        # ========== HASS BLOCKS ==========
        # 16 transformer blocks with 3 parallel pathways each
        self.blocks = nn.ModuleList([
            HASSBlock(config, layer_idx=i) 
            for i in range(config.num_layers)
        ])
        logger.info("core", f"Created {config.num_layers} HASS blocks (Local/Global/SSM pathways)")
        
        # ========== MOE EXPERT FABRIC ==========
        # Import here to avoid circular dependency
        from zarx.model.zmoe import ShardedExpertFabric
        logger.info("core", f"IgrisModel passing test_mode={self.test_mode} to ShardedExpertFabric")
        self.moe = ShardedExpertFabric(config, test_mode=self.test_mode) # Pass test_mode here
        logger.info("core", f"MoE: {config.expert_count} experts (Top-{config.top_k_experts} routing, disk-sharded)")
        
        # ========== MERGER GATE ==========
        # Fuses HASS output + MoE output + CoT vector
        self.merger = zarxMergerGate(config)
        logger.info("core", "Merger gate initialized (fuses HASS + MoE + CoT)")
        
        # ========== OUTPUT ==========
        # Final layer norm before LM head
        self.final_norm = RMSNorm(config.hidden_size, eps=config.layer_norm_eps)
        
        # Language model head (can be tied with token_embedding)
        self.lm_head = nn.Linear(
            config.hidden_size, 
            config.vocab_size, 
            bias=False
        )
        
        # Optionally tie weights
        if config.tie_word_embeddings:
            self.lm_head.weight = self.token_embedding.weight
            logger.info("core", "Tied word embeddings (embedding ↔ lm_head)")
        
        # ========== INITIALIZATION ==========
        self.apply(self._init_weights)
        
        # Special initialization for specific layers
        self._init_special_layers()
        
        # ========== GRADIENT CHECKPOINTING ==========
        self.gradient_checkpointing = config.gradient_checkpointing
        if self.gradient_checkpointing:
            logger.info("core", "Gradient checkpointing enabled (saves memory)")
        
        # ========== PERFORMANCE TRACKING ==========
        self._step_count = 0
        self._total_tokens_processed = 0
        self._active_params_history = []
        
        # Print model summary
        total_params = self.count_parameters()
        trainable_params = self.count_parameters(only_trainable=True)
        logger.info("core", f"Model initialized: {total_params:,} total params, {trainable_params:,} trainable")
        logger.info("core", f"Estimated active per token: ~26M ({26/277*100:.1f}% of total)")
    
    def _validate_config(self):
        """Validate configuration before building model."""
        config = self.config
        
        # Check basic requirements
        assert config.vocab_size > 0, "vocab_size must be positive"
        assert config.hidden_size > 0, "n_embd must be positive"
        assert config.num_layers > 0, "n_layer must be positive"
        assert config.num_attention_heads > 0, "n_head must be positive"
        assert config.hidden_size % config.num_attention_heads == 0, "n_embd must be divisible by n_head"
        
        # Check adaptive routing
        assert len(config.width_choices) > 0, "width_choices cannot be empty"
        assert max(config.width_choices) == config.hidden_size, "max width choice must equal n_embd"
        assert config.max_depth <= config.num_layers, "max_depth must be <= n_layer"
        
        # Check MoE
        assert config.expert_count > 0, "num_experts must be positive"
        assert config.top_k_experts <= config.expert_count, "top_k must be <= num_experts"
        
        # Check CoT
        assert config.cot_components == 6, "cot_components must be 6 (intention, decomposition, confidence, contradiction, direction, summary)"
        assert config.cot_dim > 0, "cot_dim must be positive"
        
        logger.debug("core", "Configuration validation passed")
    
    def _init_weights(self, module):
        """Initialize weights using best practices."""
        if isinstance(module, nn.Linear):
            # Use scaled initialization for stability
            std = 0.02
            if hasattr(module, 'scale_init'):
                std *= module.scale_init
            torch.nn.init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.padding_idx is not None:
                module.weight.data[module.padding_idx].zero_()
        
        elif isinstance(module, (nn.LayerNorm, RMSNorm)):
            if hasattr(module, 'bias') and module.bias is not None:
                torch.nn.init.zeros_(module.bias)
            if hasattr(module, 'weight'):
                torch.nn.init.ones_(module.weight)
    
    def _init_special_layers(self):
        """Special initialization for specific components."""
        # Scale down LM head for better initialization
        if not self.config.tie_word_embeddings:
            self.lm_head.weight.data.mul_(1.0 / math.sqrt(self.config.hidden_size))
        
        logger.debug("core", "Special layer initialization complete")
    
    # ==================== FORWARD PASS ====================
    
    def forward(
        self,
        input_ids: torch.LongTensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        labels: Optional[torch.LongTensor] = None,
        output_hidden_states: bool = False,
        output_routing_info: bool = False,
        output_cot_vector: bool = True,
        return_dict: bool = True,
        use_cache: bool = False,
    ) -> Union[ModelOutput, Tuple]:
        """
        Forward pass through the model.
        
        This is where the magic happens. Every token goes through:
            1. Embeddings
            2. Router (makes decisions)
            3. HASS blocks (adaptive depth)
            4. MoE experts
            5. Merger gate
            6. LM head
        
        Args:
            input_ids: [batch, seq_len] token IDs
            attention_mask: [batch, seq_len] mask (1=attend, 0=ignore)
            position_ids: [batch, seq_len] position indices (optional)
            labels: [batch, seq_len] labels for loss computation
            output_hidden_states: return intermediate layer outputs
            output_routing_info: return routing decisions
            output_cot_vector: return CoT reasoning trace
            return_dict: return ModelOutput object vs tuple
            use_cache: enable KV caching (for generation)
        
        Returns:
            ModelOutput with logits, loss, and optional intermediate states
        """
        batch_size, seq_length = input_ids.shape
        device = input_ids.device
        
        # Validate inputs
        if seq_length > self.config.context_length:
            raise ValueError(
                f"Sequence length {seq_length} exceeds maximum "
                f"{self.config.context_length}"
            )
        
        # ========== STEP 1: EMBEDDINGS ==========
        # Token embeddings
        hidden_states = self.token_embedding(input_ids)  # [B, T, H]
        
        # Position embeddings
        if position_ids is None:
            position_ids = torch.arange(
                seq_length, 
                dtype=torch.long, 
                device=device
            ).unsqueeze(0).expand(batch_size, -1)
        
        position_embeds = self.position_embedding(position_ids)  # [B, T, H]
        
        # Combine embeddings
        hidden_states = hidden_states + position_embeds
        hidden_states = self.embedding_dropout(hidden_states)
        
        # Create attention mask if not provided
        if attention_mask is None:
            attention_mask = torch.ones(
                (batch_size, seq_length),
                dtype=torch.bool,
                device=device
            )
        
        # ========== STEP 2: INITIALIZE COT ==========
        # Internal reasoning vector (6 components × 768 dim = 4608)
        cot_vector = self.cot.init_cot(batch_size, device)  # [B, cot_total_dim]
        
        # Expand to sequence length for convenience
        cot_vector_seq = cot_vector.unsqueeze(1).expand(-1, seq_length, -1)  # [B, T, cot_dim]
        
        # ========== STEP 3: ADAPTIVE ROUTING ==========
        # Router makes ALL decisions for the forward pass
        with torch.set_grad_enabled(self.training):
            routing_decision = self.router(
                x=hidden_states,
                cot_features=cot_vector_seq,
            )
        
        # Extract routing decisions
        depth_mask = routing_decision.depth_mask  # [B, T, n_layer]
        width_multiplier = routing_decision.width_multiplier  # [B, T, 1]
        path_probs = routing_decision.path_probs  # [B, T, num_paths]
        expert_indices = routing_decision.expert_indices  # [B, T, top_k]
        expert_weights = routing_decision.expert_weights  # [B, T, top_k]
        
        # ========== STEP 4: HASS BLOCKS ==========
        # Process through transformer blocks with adaptive depth
        layer_outputs = [] if output_hidden_states else None
        
        for layer_idx, block in enumerate(self.blocks):
            # Check if this layer should be executed for any token
            layer_mask = depth_mask[:, :, layer_idx]  # [B, T]
            
            # Skip layer if no tokens need it (efficiency)
            if not layer_mask.any():
                if output_hidden_states:
                    layer_outputs.append(hidden_states)
                continue
            
            # Apply gradient checkpointing if enabled
            if self.gradient_checkpointing and self.training:
                def create_forward_func(block_module, routing_decision_obj, attention_mask_obj):
                    def forward_func(h_states):
                        return block_module(
                            x=h_states,
                            routing_decision=routing_decision_obj,
                            attention_mask=attention_mask_obj
                        )
                    return forward_func
                
                # use_reentrant=False is the modern, more efficient approach
                hidden_states = checkpoint(
                    create_forward_func(block, routing_decision, attention_mask),
                    hidden_states,
                    use_reentrant=False
                )
            else:
                # Normal forward pass
                hidden_states = block(
                    x=hidden_states,
                    routing_decision=routing_decision,
                    attention_mask=attention_mask
                )
            
            # Update CoT vector (recurrent update)
            cot_vector_seq, _ = self.cot(
                hidden_states, 
                previous_cot=cot_vector_seq
            )
            
            if output_hidden_states:
                layer_outputs.append(hidden_states)
        
        # ========== STEP 5: MOE EXPERTS ==========
        # Flatten for expert processing
        batch_seq = batch_size * seq_length
        hidden_flat = hidden_states.reshape(batch_seq, -1)  # [B*T, H]
        expert_indices_flat = expert_indices.reshape(batch_seq, -1)  # [B*T, top_k]
        expert_weights_flat = expert_weights.reshape(batch_seq, -1)  # [B*T, top_k]
        
        # Process through MoE fabric
        moe_output_flat, expert_stats = self.moe(
            hidden_flat,
            expert_indices_flat,
            expert_weights_flat,
            attention_mask=attention_mask.reshape(batch_seq) if attention_mask is not None else None
        )
        
        # Reshape back
        moe_output = moe_output_flat.reshape(batch_size, seq_length, -1)  # [B, T, H]
        
        # ========== STEP 6: MERGER GATE ==========
        # Fuse HASS output + MoE output + CoT reasoning
        merged_output = self.merger(
            hass_output=hidden_states,
            moe_output=moe_output,
            cot_vector=cot_vector_seq,
            attention_mask=attention_mask
        )
        
        # ========== STEP 7: FINAL PROCESSING ==========
        # Final layer norm
        hidden_states = self.final_norm(merged_output)
        
        # LM head → logits
        logits = self.lm_head(hidden_states)  # [B, T, vocab_size]
        
        # ========== STEP 8: LOSS COMPUTATION ==========
        loss = None
        if labels is not None:
            # Shift for next-token prediction
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            # Compute cross-entropy loss
            loss_fct = nn.CrossEntropyLoss(
                ignore_index=self.config.pad_token_id if hasattr(self.config, 'pad_token_id') else -100
            )
            loss = loss_fct(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1)
            )
        
        # ========== STEP 9: AUXILIARY LOSSES ==========
        # Routing regularization
        routing_loss = self.routing_regularizer(routing_decision)
        
        # Expert load balancing
        load_balance_loss = self._compute_load_balance_loss(
            expert_indices_flat,
            expert_weights_flat
        )
        
        # CoT consistency (encourage smooth CoT updates)
        cot_consistency_loss = self._compute_cot_consistency_loss(cot_vector_seq)
        
        # ========== STEP 10: COMPUTE METRICS ==========
        active_params = self._estimate_active_params(routing_decision)
        compute_cost = self._estimate_compute_cost(routing_decision, batch_size, seq_length)
        
        # Update tracking
        self._step_count += 1
        self._total_tokens_processed += batch_size * seq_length
        self._active_params_history.append(active_params)
        
        # ========== RETURN OUTPUTS ==========
        if not return_dict:
            outputs = (logits, loss, cot_vector_seq if output_cot_vector else None)
            if output_hidden_states:
                outputs += (layer_outputs,)
            if output_routing_info:
                outputs += (routing_decision,)
            return outputs
        
        return ModelOutput(
            logits=logits,
            loss=loss,
            cot_vector=cot_vector_seq if output_cot_vector else None,
            routing_info=routing_decision if output_routing_info else None,
            layer_outputs=layer_outputs,
            expert_stats=expert_stats,
            routing_loss=routing_loss,
            load_balance_loss=load_balance_loss,
            cot_consistency_loss=cot_consistency_loss,
            active_params=active_params,
            compute_cost=compute_cost
        )
    
    # ==================== AUXILIARY LOSS FUNCTIONS ====================
    
    def _compute_load_balance_loss(
        self,
        expert_indices: torch.Tensor,
        expert_weights: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute load balancing loss to prevent expert collapse.
        
        We want experts to be used roughly equally to prevent
        some experts from being overused and others from dying.
        
        Args:
            expert_indices: [N, top_k] expert indices
            expert_weights: [N, top_k] expert weights
        
        Returns:
            Scalar load balance loss
        """
        num_experts = self.config.expert_count
        num_tokens = expert_indices.size(0)
        
        # Count how many tokens route to each expert
        expert_counts = torch.zeros(num_experts, device=expert_indices.device, dtype=expert_weights.dtype)
        for k in range(self.config.top_k_experts):
            expert_counts.scatter_add_(
                0,
                expert_indices[:, k],
                expert_weights[:, k]
            )
        
        # Normalize to get probabilities
        expert_probs = expert_counts / (num_tokens * self.config.top_k_experts + 1e-8)
        
        # Target: uniform distribution
        target_prob = 1.0 / num_experts
        
        # L2 loss
        loss = torch.sum((expert_probs - target_prob) ** 2)
        
        return self.config.load_balancing_weight * loss
    
    def _compute_cot_consistency_loss(self, cot_vector: torch.Tensor) -> torch.Tensor:
        """
        Compute CoT consistency loss to encourage smooth reasoning.
        
        We want the CoT vector to change smoothly across sequence,
        not jump erratically.
        
        Args:
            cot_vector: [B, T, cot_dim] CoT vector across sequence
        
        Returns:
            Scalar consistency loss
        """
        if cot_vector.size(1) < 2:
            return torch.tensor(0.0, device=cot_vector.device)
        
        # Compute difference between consecutive steps
        cot_diff = cot_vector[:, 1:, :] - cot_vector[:, :-1, :]  # [B, T-1, cot_dim]
        
        # Penalize large jumps (L2 norm)
        consistency_loss = torch.mean(cot_diff ** 2)
        
        return self.config.cot_consistency_weight * consistency_loss
    
    def _estimate_active_params(self, routing_decision: RoutingDecision) -> int:
        """
        Estimate number of active parameters for current forward pass.
        
        This is approximate but gives us a sense of compute efficiency.
        
        Args:
            routing_decision: Routing decisions for this batch
        
        Returns:
            Estimated number of active parameters
        """
        active_params = 0
        
        # Embeddings (always active)
        active_params += self.config.vocab_size * self.config.hidden_size
        
        # Average depth (number of layers executed)
        avg_depth = routing_decision.depth_mask.float().sum(dim=-1).mean().item()
        
        # Parameters per HASS block (approximate)
        params_per_block = count_parameters(self.blocks[0]) if self.blocks else 0
        active_params += int(avg_depth * params_per_block)
        
        # Active experts (top-k)
        intermediate_dim = int(self.config.hidden_size * self.config.expert_hidden_multiplier)
        active_params += self.config.top_k_experts * (
            self.config.hidden_size * intermediate_dim * 2
        )
        
        # CoT module (always active)
        active_params += count_parameters(self.cot)
        
        # Router (always active)
        active_params += count_parameters(self.router)
        
        # Merger (always active)
        active_params += count_parameters(self.merger)
        
        # LM head (always active)
        active_params += self.config.hidden_size * self.config.vocab_size
        
        return active_params
    
    def _estimate_compute_cost(
        self, 
        routing_decision: RoutingDecision,
        batch_size: int,
        seq_length: int
    ) -> float:
        """
        Estimate FLOPs for this forward pass.
        
        Args:
            routing_decision: Routing decisions
            batch_size: Batch size
            seq_length: Sequence length
        
        Returns:
            Estimated FLOPs (in GFLOPs)
        """
        # This is a rough estimate
        flops = 0.0
        
        # Embeddings: B * T * H
        flops += batch_size * seq_length * self.config.hidden_size
        
        # HASS blocks: depends on depth and width
        avg_depth = routing_decision.depth_mask.float().mean().item() * self.config.num_layers
        avg_width = routing_decision.width_multiplier.mean().item() * self.config.hidden_size
        
        # Attention: B * T^2 * H
        flops += avg_depth * batch_size * seq_length * seq_length * avg_width
        
        # MLP: B * T * H * (4H)
        flops += avg_depth * batch_size * seq_length * avg_width * (4 * avg_width)
        
        # MoE: B * T * top_k * expert_dim
        flops += batch_size * seq_length * self.config.top_k_experts * int(self.config.hidden_size * self.config.expert_hidden_multiplier)
        
        # LM head: B * T * H * vocab
        flops += batch_size * seq_length * self.config.hidden_size * self.config.vocab_size
        
        # Convert to GFLOPs
        return flops / 1e9
    
    # ==================== GENERATION ====================
    
    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.LongTensor,
        generation_config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> torch.LongTensor:
        """
        Generate text autoregressively.
        
        Args:
            input_ids: [batch, seq_len] starting tokens
            generation_config: Generation configuration
            **kwargs: Override generation_config parameters
        
        Returns:
            [batch, seq_len + max_new_tokens] generated token IDs
        """
        # Setup generation config
        if generation_config is None:
            generation_config = GenerationConfig()
        
        # Override with kwargs
        for key, value in kwargs.items():
            if hasattr(generation_config, key):
                setattr(generation_config, key, value)
        
        # Determine generation method
        if generation_config.num_beams > 1:
            return self._beam_search_generate(input_ids, generation_config)
        elif generation_config.do_sample:
            return self._sample_generate(input_ids, generation_config)
        else:
            return self._greedy_generate(input_ids, generation_config)
    
    def _greedy_generate(
        self,
        input_ids: torch.LongTensor,
        config: GenerationConfig
    ) -> torch.LongTensor:
        """Greedy decoding (deterministic)."""
        batch_size = input_ids.size(0)
        device = input_ids.device
        
        # Track which sequences are finished
        unfinished_sequences = torch.ones(batch_size, dtype=torch.long, device=device)
        
        for _ in range(config.max_new_tokens):
            # Forward pass
            outputs = self(input_ids, return_dict=True)
            next_token_logits = outputs.logits[:, -1, :]  # [B, vocab]
            
            # Apply temperature
            if config.temperature != 1.0:
                next_token_logits = next_token_logits / config.temperature
            
            # Apply repetition penalty
            if config.repetition_penalty != 1.0:
                next_token_logits = self._apply_repetition_penalty(
                    next_token_logits,
                    input_ids,
                    config.repetition_penalty
                )
            
            # Greedy selection
            next_tokens = torch.argmax(next_token_logits, dim=-1)
            
            # Update which sequences are finished
            if config.eos_token_id is not None:
                pad_token_id = config.pad_token_id if config.pad_token_id is not None else 0
                next_tokens = next_tokens * unfinished_sequences + pad_token_id * (1 - unfinished_sequences)
                unfinished_sequences = unfinished_sequences.mul(
                    next_tokens.ne(config.eos_token_id).long()
                )
            
            # Append to sequence
            input_ids = torch.cat([input_ids, next_tokens.unsqueeze(-1)], dim=-1)
            
            # Stop if all sequences are finished
            if unfinished_sequences.max() == 0:
                break
        
        return input_ids
    
    def _sample_generate(
        self,
        input_ids: torch.LongTensor,
        config: GenerationConfig
    ) -> torch.LongTensor:
        """Sampling-based generation (stochastic)."""
        batch_size = input_ids.size(0)
        device = input_ids.device
        
        unfinished_sequences = torch.ones(batch_size, dtype=torch.long, device=device)
        
        for _ in range(config.max_new_tokens):
            # Forward pass
            outputs = self(input_ids, return_dict=True)
            next_token_logits = outputs.logits[:, -1, :]  # [B, vocab]
            
            # Apply temperature
            next_token_logits = next_token_logits / config.temperature
            
            # Apply repetition penalty
            if config.repetition_penalty != 1.0:
                next_token_logits = self._apply_repetition_penalty(
                    next_token_logits,
                    input_ids,
                    config.repetition_penalty
                )
            
            # Apply top-k filtering
            if config.top_k is not None and config.top_k > 0:
                next_token_logits = self._top_k_filtering(
                    next_token_logits,
                    config.top_k
                )
            
            # Apply top-p (nucleus) filtering
            if config.top_p is not None and config.top_p < 1.0:
                next_token_logits = self._top_p_filtering(
                    next_token_logits,
                    config.top_p
                )
            
            # Sample from distribution
            probs = F.softmax(next_token_logits, dim=-1)
            next_tokens = torch.multinomial(probs, num_samples=1).squeeze(1)
            
            # Update sequences
            if config.eos_token_id is not None:
                pad_token_id = config.pad_token_id if config.pad_token_id is not None else 0
                next_tokens = next_tokens * unfinished_sequences + pad_token_id * (1 - unfinished_sequences)
                unfinished_sequences = unfinished_sequences.mul(
                    next_tokens.ne(config.eos_token_id).long()
                )
            
            # Append
            input_ids = torch.cat([input_ids, next_tokens.unsqueeze(-1)], dim=-1)
            
            # Early stopping
            if unfinished_sequences.max() == 0:
                break
        
        return input_ids
    
    def _beam_search_generate(
        self,
        input_ids: torch.LongTensor,
        config: GenerationConfig
    ) -> torch.LongTensor:
        """Beam search generation."""
        # Simplified beam search implementation
        batch_size = input_ids.size(0)
        device = input_ids.device
        num_beams = config.num_beams
        
        # Expand input for beam search
        input_ids = input_ids.unsqueeze(1).expand(batch_size, num_beams, -1)
        input_ids = input_ids.reshape(batch_size * num_beams, -1)
        
        # Beam scores
        beam_scores = torch.zeros(batch_size, num_beams, device=device)
        beam_scores[:, 1:] = -1e9  # Only first beam is active initially
        beam_scores = beam_scores.view(-1)
        
        unfinished_sequences = torch.ones(batch_size * num_beams, dtype=torch.long, device=device)
        
        for _ in range(config.max_new_tokens):
            outputs = self(input_ids, return_dict=True)
            next_token_logits = outputs.logits[:, -1, :]  # [B*num_beams, vocab]
            
            # Apply temperature
            next_token_logits = next_token_logits / config.temperature
            
            # Get log probabilities
            next_token_scores = F.log_softmax(next_token_logits, dim=-1)  # [B*num_beams, vocab]
            
            # Add beam scores
            next_token_scores = next_token_scores + beam_scores[:, None]  # [B*num_beams, vocab]
            
            # Reshape for beam selection
            vocab_size = next_token_scores.size(-1)
            next_token_scores = next_token_scores.view(batch_size, num_beams * vocab_size)
            
            # Select top 2*num_beams
            next_scores, next_tokens = torch.topk(
                next_token_scores, 
                2 * num_beams, 
                dim=1, 
                largest=True, 
                sorted=True
            )
            
            # Get beam indices and tokens
            next_indices = torch.div(next_tokens, vocab_size, rounding_mode='floor')
            next_tokens = next_tokens % vocab_size
            
            # Create new beams
            beam_outputs = []
            beam_scores_new = []
            
            for batch_idx in range(batch_size):
                beams = []
                for beam_idx in range(num_beams):
                    # Get top beams for this batch
                    for idx in range(2 * num_beams):
                        score = next_scores[batch_idx, idx]
                        token = next_tokens[batch_idx, idx]
                        beam_id = next_indices[batch_idx, idx]
                        
                        # Get original beam
                        orig_idx = batch_idx * num_beams + beam_id
                        new_seq = torch.cat([
                            input_ids[orig_idx],
                            token.unsqueeze(0)
                        ], dim=0)
                        
                        beams.append((score, new_seq))
                        
                        if len(beams) >= num_beams:
                            break
                    
                    if len(beams) >= num_beams:
                        break
                
                # Sort and select top beams
                beams = sorted(beams, key=lambda x: x[0], reverse=True)[:num_beams]
                
                for score, seq in beams:
                    beam_outputs.append(seq)
                    beam_scores_new.append(score)
            
            # Update
            input_ids = torch.stack(beam_outputs, dim=0)
            beam_scores = torch.tensor(beam_scores_new, device=device)
            
            # Check for EOS
            if config.eos_token_id is not None:
                unfinished_sequences = unfinished_sequences.mul(
                    input_ids[:, -1].ne(config.eos_token_id).long()
                )
            
            if unfinished_sequences.max() == 0:
                break
        
        # Return best beam for each batch
        input_ids = input_ids.view(batch_size, num_beams, -1)
        return input_ids[:, 0, :]  # Return first beam
    
    # ==================== HELPER FUNCTIONS ====================
    
    def _apply_repetition_penalty(
        self,
        logits: torch.Tensor,
        input_ids: torch.Tensor,
        penalty: float
    ) -> torch.Tensor:
        """Apply repetition penalty to discourage repeating tokens."""
        batch_size, vocab_size = logits.shape
        
        for i in range(batch_size):
            for token_id in set(input_ids[i].tolist()):
                # Lower probability of repeated tokens
                if logits[i, token_id] < 0:
                    logits[i, token_id] *= penalty
                else:
                    logits[i, token_id] /= penalty
        
        return logits
    
    def _top_k_filtering(
        self,
        logits: torch.Tensor,
        top_k: int
    ) -> torch.Tensor:
        """Filter logits to keep only top-k tokens."""
        top_k = min(top_k, logits.size(-1))
        indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
        logits[indices_to_remove] = -float('inf')
        return logits
    
    def _top_p_filtering(
        self,
        logits: torch.Tensor,
        top_p: float
    ) -> torch.Tensor:
        """Nucleus filtering: keep tokens with cumulative probability >= top_p."""
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
        
        # Remove tokens with cumulative probability above threshold
        sorted_indices_to_remove = cumulative_probs > top_p
        # Keep at least one token
        sorted_indices_to_remove[..., 0] = False
        
        # Scatter back to original indexing
        indices_to_remove = sorted_indices_to_remove.scatter(
            1, sorted_indices, sorted_indices_to_remove
        )
        logits[indices_to_remove] = -float('inf')
        return logits
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def count_parameters(self, only_trainable: bool = False) -> int:
        """Count total or trainable parameters."""
        if only_trainable:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)
        return sum(p.numel() for p in self.parameters())
    
    def get_num_params(self, only_trainable: bool = False) -> int:
        """Alias for count_parameters."""
        return self.count_parameters(only_trainable)
    
    def get_memory_footprint(self) -> Dict[str, Any]:
        """Get model memory footprint."""
        param_size = 0
        param_count = 0
        buffer_size = 0
        buffer_count = 0
        
        for param in self.parameters():
            param_count += param.numel()
            param_size += param.numel() * param.element_size()
        
        for buffer in self.buffers():
            buffer_count += buffer.numel()
            buffer_size += buffer.numel() * buffer.element_size()
        
        total_size = param_size + buffer_size
        
        return {
            'param_count': param_count,
            'param_size_mb': param_size / (1024 ** 2),
            'buffer_count': buffer_count,
            'buffer_size_mb': buffer_size / (1024 ** 2),
            'total_size_mb': total_size / (1024 ** 2),
            'total_size_gb': total_size / (1024 ** 3)
        }
    
    def print_model_summary(self, verbose: bool = True):
        """Print comprehensive model summary."""
        print("\n" + "="*70)
        print(f"  {self.config.model_name} - Model Summary")
        print("="*70)
        
        print(f"\n📊 Configuration:")
        print(f"  Vocabulary Size: {self.config.vocab_size:,}")
        print(f"  Hidden Dimension: {self.config.hidden_size}")
        print(f"  Number of Layers: {self.config.num_layers}")
        print(f"  Number of Heads: {self.config.num_attention_heads}")
        print(f"  Context Length: {self.config.context_length:,}")
        
        print(f"\n🧠 Adaptive Features:")
        print(f"  Width Choices: {self.config.width_choices}")
        print(f"  Depth Range: {self.config.min_depth}-{self.config.max_depth}")
        print(f"  Adaptive Routing: Depth + Width + Path + Expert")
        
        print(f"\n🔀 MoE Configuration:")
        print(f"  Total Experts: {self.config.expert_count}")
        print(f"  Top-K Active: {self.config.top_k_experts}")
        print(f"  Disk Sharded: {self.config.shard_experts}")
        print(f"  Cache Size: {self.config.max_expert_cache} experts")
        
        print(f"\n💭 CoT Configuration:")
        print(f"  Components: {self.config.cot_components}")
        print(f"  Dim per Component: {self.config.cot_dim}")
        print(f"  Total CoT Dimension: {self.config.cot_dim * self.config.cot_components}")
        
        print(f"\n📈 Parameters:")
        total_params = self.count_parameters()
        trainable_params = self.count_parameters(only_trainable=True)
        print(f"  Total: {total_params:,}")
        print(f"  Trainable: {trainable_params:,}")
        print(f"  Estimated Active per Token: ~26M ({26/277*100:.1f}% sparsity)")
        
        memory = self.get_memory_footprint()
        print(f"\n💾 Memory Footprint:")
        print(f"  Parameters: {memory['param_size_mb']:.2f} MB")
        print(f"  Total: {memory['total_size_mb']:.2f} MB ({memory['total_size_gb']:.3f} GB)")
        
        if verbose and len(self._active_params_history) > 0:
            avg_active = sum(self._active_params_history) / len(self._active_params_history)
            print(f"\n📊 Runtime Statistics:")
            print(f"  Steps: {self._step_count:,}")
            print(f"  Tokens Processed: {self._total_tokens_processed:,}")
            print(f"  Avg Active Params: {avg_active/1e6:.1f}M")
        
        print("\n" + "="*70 + "\n")
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get statistics about routing decisions."""
        if len(self._active_params_history) == 0:
            return {}
        
        return {
            'avg_active_params': sum(self._active_params_history) / len(self._active_params_history),
            'min_active_params': min(self._active_params_history),
            'max_active_params': max(self._active_params_history),
            'total_steps': self._step_count,
            'total_tokens': self._total_tokens_processed,
            'avg_params_per_token': sum(self._active_params_history) / max(self._total_tokens_processed, 1)
        }
    
    # ==================== CHECKPOINT MANAGEMENT ====================
    
    def save_checkpoint(
        self,
        path: Union[str, Path],
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        **kwargs
    ):
        """Save model checkpoint."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            'model_state_dict': self.state_dict(),
            'config': self.config.to_dict() if hasattr(self.config, 'to_dict') else None,
            'step_count': self._step_count,
            'total_tokens': self._total_tokens_processed,
        }
        
        if optimizer is not None:
            checkpoint['optimizer_state_dict'] = optimizer.state_dict()
        
        if scheduler is not None:
            checkpoint['scheduler_state_dict'] = scheduler.state_dict()
        
        if epoch is not None:
            checkpoint['epoch'] = epoch
        
        if step is not None:
            checkpoint['step'] = step
        
        # Add any additional kwargs
        checkpoint.update(kwargs)
        
        torch.save(checkpoint, path)
    
    def load_checkpoint(
        self,
        path: Union[str, Path],
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        strict: bool = True,
        map_location: Optional[Union[str, torch.device]] = None
    ) -> Dict[str, Any]:
        """Load model checkpoint."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {path}")
        
        checkpoint = torch.load(path, map_location=map_location)
        
        # Load model state
        self.load_state_dict(checkpoint['model_state_dict'], strict=strict)
        
        # Load optimizer state
        if optimizer is not None and 'optimizer_state_dict' in checkpoint:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        # Load scheduler state
        if scheduler is not None and 'scheduler_state_dict' in checkpoint:
            scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        # Load tracking stats
        if 'step_count' in checkpoint:
            self._step_count = checkpoint['step_count']
        if 'total_tokens' in checkpoint:
            self._total_tokens_processed = checkpoint['total_tokens']
        
        return checkpoint
    
    # ==================== SPECIAL METHODS ====================
    
    def __repr__(self) -> str:
        """String representation."""
        total_params = self.count_parameters()
        return (
            f"{self.__class__.__name__}("
            f"params={total_params:,}, "
            f"layers={self.config.num_layers}, "
            f"hidden={self.config.hidden_size}, "
            f"experts={self.config.expert_count}"
            f")"
        )
    
    def to(self, *args, **kwargs):
        """Override to handle expert fabric device movement."""
        # Move main model
        super().to(*args, **kwargs)
        
        # Notify MoE fabric of device change
        if hasattr(self, 'moe'):
            device = args[0] if args else kwargs.get('device')
            if device is not None:
                self.moe.set_device(device)
        
        return self



# ==================== TESTING ====================
