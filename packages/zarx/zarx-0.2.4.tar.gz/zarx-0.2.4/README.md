# ZARX - Zero-to-AGI Deep Learning Framework

ZARX provides a clean, production-ready interface for deep learning, focusing on advanced architectures like IGRIS.

## Features

- Explicit model selection (IGRIS_277M, IGRIS_7B, etc.)
- Efficient data pipeline with binary formats
- Comprehensive tokenizer system
- Resume/continue training support
- Production-grade error handling

## Installation

```bash
pip install zarx
```

## Quick Start

```python
import zarx

# 1. Load model
model = zarx.IGRIS_277M()

# 2. Load tokenizer
tokenizer = zarx.load_pretrained('zarx_32k')

# 3. Convert data
zarx.txt_to_bin('train.txt', 'train.bin', tokenizer, max_length=2048)

# 4. Load data
data = zarx.load_from_bin('train.bin', batch_size=32)

# 5. Train
trainer = zarx.train(model, data, epochs=10)
trainer.train()
```

## Documentation

For detailed documentation, visit the [GitHub repository](https://github.com/Akik-Forazi/zarx.git).

## License

This project is licensed under the MIT License.
