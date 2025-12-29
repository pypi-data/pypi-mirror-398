# Dreamstack

**A lightweight Python core library for the Dreamstack ecosystem.**

[![PyPI version](https://img.shields.io/pypi/v/dreamstack.svg)](https://pypi.org/project/dreamstack/)
[![Python versions](https://img.shields.io/pypi/pyversions/dreamstack.svg)](https://pypi.org/project/dreamstack/)
[![License](https://img.shields.io/pypi/l/dreamstack.svg)](https://pypi.org/project/dreamstack/)

---

## Installation

Install Dreamstack using pip:

```bash
pip install dreamstack
```

---

## Quick Start

### Basic Usage

```python
from dreamstack import hello

# Simple greeting
print(hello("World"))
# Output: Hello, World! Welcome to the dreamstack library.

print(hello("Alice"))
# Output: Hello, Alice! Welcome to the dreamstack library.
```

### Custom Greetings

```python
from dreamstack import greet

# Customizable greeting
print(greet("Alice"))
# Output: Hello, Alice!

print(greet("Bob", "Hi"))
# Output: Hi, Bob!

print(greet("Charlie", greeting="Hey"))
# Output: Hey, Charlie!
```

### Message Formatting

```python
from dreamstack import format_message

# Basic message
print(format_message("Alice", "Welcome aboard"))
# Output: Alice: Welcome aboard

# With prefix
print(format_message("Bob", "Great work", prefix="[INFO]"))
# Output: [INFO] Bob: Great work

# With suffix
print(format_message("Charlie", "Task completed", suffix="✓"))
# Output: Charlie: Task completed ✓

# With both
print(format_message("Diana", "Login successful", prefix="[SUCCESS]", suffix="🎉"))
# Output: [SUCCESS] Diana: Login successful 🎉
```

---

## Command-Line Interface

Dreamstack also provides a simple CLI:

```bash
# Basic greeting
python -m dreamstack Alice
# Output: Hello, Alice! Welcome to the dreamstack library.

# Show version
python -m dreamstack --version

# Verbose output
python -m dreamstack Bob --verbose
# Output:
# Hello, Bob! Welcome to the dreamstack library.
# [Dreamstack v0.1.2]

# Help
python -m dreamstack --help
```

---

## Features

- **Simple API**: Easy-to-use functions for common greeting tasks
- **Type-safe**: Full type hints for better IDE support
- **Validated**: Input validation with helpful error messages
- **CLI Support**: Use as a command-line tool
- **Namespace Package**: Designed to support ecosystem extensions
- **Well-documented**: Comprehensive docstrings and examples

---

## API Reference

### `hello(name: str) -> str`

Returns a welcoming greeting message.

**Parameters:**
- `name` (str): The name to greet (non-empty string)

**Returns:**
- str: A formatted greeting message

**Raises:**
- `TypeError`: If name is not a string
- `ValueError`: If name is empty or whitespace-only

---

### `greet(name: str, greeting: str = "Hello") -> str`

Returns a customizable greeting message.

**Parameters:**
- `name` (str): The name to greet (non-empty string)
- `greeting` (str): The greeting word (default: "Hello")

**Returns:**
- str: A formatted greeting with custom greeting

**Raises:**
- `TypeError`: If name or greeting is not a string
- `ValueError`: If name or greeting is empty or whitespace-only

---

### `format_message(name: str, message: str, prefix: str | None = None, suffix: str | None = None) -> str`

Formats a message with optional prefix and suffix.

**Parameters:**
- `name` (str): The name to include in the message
- `message` (str): The main message content
- `prefix` (str | None): Optional prefix before the message
- `suffix` (str | None): Optional suffix after the message

**Returns:**
- str: A formatted message string

**Raises:**
- `TypeError`: If arguments are not strings (where required)
- `ValueError`: If name or message is empty or whitespace-only

---

## Requirements

- Python >= 3.12, < 3.13

---

## License

Proprietary License. Copyright © 2025 [Scape Agency](https://www.scape.agency).

---

## Links

- **Homepage**: [https://www.scape.agency](https://www.scape.agency)
- **PyPI**: [https://pypi.org/project/dreamstack/](https://pypi.org/project/dreamstack/)
- **Issues**: Report bugs and request features on our issue tracker

---

## Support

For questions and support, please contact [info@scape.agency](mailto:info@scape.agency).

---

**Made with 💙 by Scape Agency**
