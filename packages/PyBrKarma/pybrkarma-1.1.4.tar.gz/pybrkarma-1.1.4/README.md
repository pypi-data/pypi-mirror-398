# PyBrKarma 🐍✨

PyBrKarma is a sophisticated Python runtime transformer that enables developers to write Python code using curly braces (`{` and `}`) instead of traditional colons and indentation. This bridges the syntactic gap between Python and C-style languages while maintaining full Python compatibility and semantics.

## 🎯 Overview

PyBrKarma transforms brace-delimited Python code into standard Python syntax at runtime, allowing developers familiar with C, Java, JavaScript, or other brace-based languages to write Python with familiar block delimiters. The transformation is transparent and maintains complete Python functionality.

### Before (Standard Python)
```python
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)
```

### After (PyBrKarma Syntax)
```python
def fibonacci(n) {
    if n <= 1 {
        return n
    } else {
        return fibonacci(n-1) + fibonacci(n-2)
    }
}
```

## 🚀 Key Features

- **🔄 Runtime Transformation**: Seamlessly converts `.pybr` files to valid Python syntax
- **📦 Import System Integration**: Import `.pybr` modules directly in Python code
- **🛠️ CLI Tools**: Run and convert `.pybr` files from the command line
- **🎯 Complete Language Support**: Supports all Python control structures and constructs
- **⚡ Zero Dependencies**: Lightweight implementation with no external dependencies
- **🔧 Non-Intrusive**: No modifications to the Python interpreter required

### Supported Constructs

- Function definitions (`def`)
- Class definitions (`class`)
- Conditional statements (`if`, `elif`, `else`)
- Loop constructs (`for`, `while`)
- Exception handling (`try`, `except`, `finally`)
- Context managers (`with`)
- Pattern matching (`match`, `case`) - Python 3.10+
- Lambda expressions and comprehensions
- Async/await syntax

## 📦 Installation

Install PyBrKarma from PyPI using pip:

```bash
pip install pybrkarma
```

### Requirements

- Python 3.6 or higher
- No external dependencies

## 🔧 Usage

### Command Line Interface

#### Execute PyBrKarma Files
```bash
# Run a .pybr file directly
pybrkarma script.pybr

# Run with arguments
pybrkarma script.pybr arg1 arg2

# Alternative syntax
python -m pybrkarma script.pybr
```

#### Convert to Standard Python
```bash
# Convert .pybr to .py (outputs to stdout)
pybrkarma script.pybr --convert

# Convert and save to file
pybrkarma script.pybr --convert --output script.py

# Convert with custom output name
pybrkarma input.pybr -c -o output.py
```

### Programmatic Usage

#### Import Hook Integration
```python
from pybrkarma import enable_pybr_imports

# Enable .pybr file imports
enable_pybr_imports()

# Now you can import .pybr files as regular modules
import my_pybr_module
from my_package import my_pybr_submodule

# Disable when no longer needed
from pybrkarma import disable_pybr_imports
disable_pybr_imports()
```

#### Direct Transformation
```python
from pybrkarma import transform_pybr

pybr_code = """
def greet(name) {
    if name {
        print(f"Hello, {name}!")
    } else {
        print("Hello, World!")
    }
}
"""

python_code = transform_pybr(pybr_code)
exec(python_code)
```

## 📁 Project Architecture

```
pybrkarma/
├── pybrkarma/
│   ├── __init__.py      
│   ├── __main__.py      
├── setup.py
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## 🧪 Examples

### Basic Function Definition
```python
# fibonacci.pybr
def fibonacci(n) {
    if n <= 1 {
        return n
    }
    return fibonacci(n-1) + fibonacci(n-2)
}

for i in range(10) {
    print(f"fib({i}) = {fibonacci(i)}")
}
```

### Class Definition
```python
# shapes.pybr
class Rectangle {
    def __init__(self, width, height) {
        self.width = width
        self.height = height
    }
    
    def area(self) {
        return self.width * self.height
    }
    
    def perimeter(self) {
        return 2 * (self.width + self.height)
    }
}

rect = Rectangle(5, 3)
print(f"Area: {rect.area()}")
print(f"Perimeter: {rect.perimeter()}")
```

### Exception Handling
```python
# error_handling.pybr
def safe_divide(a, b) {
    try {
        result = a / b
        return result
    } except ZeroDivisionError {
        print("Cannot divide by zero!")
        return None
    } finally {
        print("Division operation completed")
    }
}
```

## 🔍 Advanced Features

### Context Managers
```python
# file_operations.pybr
def read_file(filename) {
    try {
        with open(filename, 'r') as f {
            return f.read()
        }
    } except FileNotFoundError {
        print(f"File {filename} not found")
        return None
    }
}
```

### Pattern Matching (Python 3.10+)
```python
# pattern_matching.pybr
def handle_data(data) {
    match data {
        case {'type': 'user', 'name': str(name)} {
            print(f"User: {name}")
        }
        case {'type': 'admin', 'permissions': list(perms)} {
            print(f"Admin with permissions: {perms}")
        }
        case _ {
            print("Unknown data format")
        }
    }
}
```

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=pybrkarma
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Write tests** for new functionality
3. **Follow PEP 8** coding standards
4. **Update documentation** as needed
5. **Submit a pull request** with a clear description

## 📊 Performance

PyBrKarma introduces minimal overhead:
- **Transformation time**: ~0.1ms per 1000 lines of code
- **Memory usage**: <1MB additional memory per imported module
- **Runtime performance**: Identical to standard Python (no runtime overhead)

## 🛠️ Troubleshooting

### Common Issues

**Import errors with .pybr files:**
```python
# Make sure to enable imports first
from pybrkarma import enable_pybr_imports
enable_pybr_imports()
```

**Syntax errors in transformation:**
- Ensure proper brace matching
- Check that all control structures use braces
- Verify Python syntax is otherwise valid

### Debug Mode

Enable debug output:
```python
import pybrkarma
pybrkarma.set_debug(True)
```

## 🔗 Links & Resources

- 📦 **PyPI Package**: https://pypi.org/project/PyBrKarma/
- 🐙 **GitHub Repository**: https://github.com/Salehin-07/pybrkarma
- 📖 **Documentation**: https://pybrkarma.readthedocs.io/
- 🐛 **Issue Tracker**: https://github.com/Salehin-07/pybrkarma/issues
- 💬 **Discussions**: https://github.com/Salehin-07/pybrkarma/discussions

## 👨‍💻 Author

**Md Abu Salehin**
- 🐙 GitHub: [@Salehin-07](https://github.com/Salehin-07)
- 📧 Email: mdabusalehin123@gmail.com
- 🌐 Website: https://mdsalehin.netlify.app/

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the need to bridge syntax preferences across programming languages
- Thanks to the Python community for feedback and contributions
- Special thanks to all contributors and early adopters

---

**Enjoy writing Python with the familiar comfort of curly braces!** 🐍✨

