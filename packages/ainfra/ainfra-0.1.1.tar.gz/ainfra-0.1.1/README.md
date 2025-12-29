# 🚀 AInfra

[中文文档](README_zh.md) | English

Simple and intelligent way to install PyTorch, vLLM, Flash Attention, SGLang, and other ML/AI libraries with automatic environment detection.

## 🌐 Web Visualization Tool

Don't want to use the command line? Try our **web-based visualization tool** at:

👉 **[https://linxueyuan.online/AInfra/](https://linxueyuan.online/AInfra/)**

The web interface provides an intuitive way to generate installation commands based on your configuration. Simply select your Python version, CUDA version, and the libraries you need, and get the complete installation script instantly!

## 🌟 Features

- 🔍 **Environment Detection**: Automatically detects your NVIDIA driver, CUDA version, OS, and Python version
- 📦 **Smart Installation**: Installs the right package versions based on your environment (e.g., CPU vs CUDA for PyTorch)
- ✅ **User Confirmation**: Shows installation plan and asks for confirmation before proceeding
- 🎨 **Beautiful CLI**: Rich terminal output with colored tables and clear formatting
- 📚 **Comprehensive Library Support**: Supports popular ML/AI libraries including torch, vllm, numpy, flash-attn, and sglang

## 📥 Installation

```bash
pip install ainfra
```

## 🎯 Quick Start

### 🔎 Check Your Environment

Display your system's environment information:

```bash
ainfra info
```

Example output:
```
System Information                 
┌───────────────────────┬─────────────────────────┐
│ Operating System      │ Ubuntu 22.04.3 LTS      │
│ OS Version            │ Linux 5.15.0            │
│ System Architecture   │ x86_64 / AMD64          │
│ Python Version        │ 3.10.12                 │
│ Nvidia Driver Version │ 550.54.15               │
│ CUDA Driver Version   │ 12.4                    │
└───────────────────────┴─────────────────────────┘
```

### 📋 List Supported Libraries

View all libraries that AInfra can install:

```bash
ainfra list
```

Example output:
```
Supported Libraries                                  
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Package    ┃ Description                                                       ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ torch      │ PyTorch - Deep learning framework with GPU acceleration support   │
│ vllm       │ vLLM - High-throughput and memory-efficient inference engine for  │
│            │ LLMs                                                              │
│ numpy      │ NumPy - Fundamental package for scientific computing with Python  │
│ flash-attn │ Flash Attention - Fast and memory-efficient exact attention       │
│ sglang     │ SGLang - Structured Generation Language for LLMs                  │
└────────────┴───────────────────────────────────────────────────────────────────┘

Total: 5 libraries
```

For detailed information about each library, see [SUPPORTED_LIBRARIES.md](.github/instructions/SUPPORTED_LIBRARIES.md).

### 🔧 Install Packages

Install packages based on your local environment with user confirmation:

**Install specific packages:**
```bash
ainfra install torch vllm numpy
```

**Install all supported packages:**
```bash
ainfra install all
```

**Get help:**
```bash
ainfra install --help
```

The install command will:
1. Detect your environment (Python version, CUDA version)
2. Show the list of packages to be installed
3. Ask for your confirmation before proceeding
4. Install the packages with appropriate versions based on your environment

## 💡 Usage Examples

```bash
# Check your system environment
ainfra info

# List all supported libraries
ainfra list

# Install PyTorch (automatically selects CUDA or CPU version)
ainfra install torch

# Install multiple libraries
ainfra install torch vllm numpy

# Install all supported libraries
ainfra install all
```

## 🛠️ Development

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### 📦 Setup

```bash
# Install dependencies
poetry install

# Run the CLI
poetry run ainfra info
poetry run ainfra list
poetry run ainfra install torch
```

### 🏗️ Build

```bash
# Build the package
poetry build

# The built package will be in the dist/ directory
```

## 📚 Supported Libraries

- **torch**: PyTorch - Deep learning framework with GPU acceleration support
- **vllm**: vLLM - High-throughput and memory-efficient inference engine for LLMs
- **numpy**: NumPy - Fundamental package for scientific computing with Python
- **flash-attn**: Flash Attention - Fast and memory-efficient exact attention
- **sglang**: SGLang - Structured Generation Language for LLMs

See [SUPPORTED_LIBRARIES.md](.github/instructions/SUPPORTED_LIBRARIES.md) for detailed information.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License. See [LICENSE](LICENSE) file for details.
