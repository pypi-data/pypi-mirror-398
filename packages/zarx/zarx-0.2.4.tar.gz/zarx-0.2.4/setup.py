from setuptools import setup, find_packages

setup(
    name='zarx',
    version='0.2.4',  # This should match the __version__ in zarx/__init__.py
    packages=find_packages(),
    author='Akik Faraji',
    author_email='akikfaraji@gmail.com',
    description='Zero-to-AGI Deep Learning Framework',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Akik-Forazi/zarx.git',
    install_requires=[
        'torch>=1.10.0',
        'numpy>=1.20.0',
        'tokenizers>=0.11.0',
        'tqdm>=4.0.0',
        'pyarrow>=6.0.0',
        'pandas>=1.0.0',
        'psutil>=5.0.0',
        'pyyaml>=5.0.0',
        'scipy>=1.0.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.8',
    include_package_data=True,
    zip_safe=False,
)
