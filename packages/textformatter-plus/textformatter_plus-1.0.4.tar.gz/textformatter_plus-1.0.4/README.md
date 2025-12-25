# TextFormatter Plus

A comprehensive Python package providing professional text formatting and validation utilities. Perfect for developers who need reliable text manipulation and data validation in their applications.

## 🎯 What is TextFormatter Plus?

TextFormatter Plus is a lightweight, easy-to-use Python package that offers:
- **Text Formatting**: Transform text in multiple ways (title case, snake case, reverse, capitalize, remove whitespace)
- **Data Validation**: Validate emails, phone numbers, and password strength
- **Zero Dependencies**: Works out of the box with no external dependencies
- **Python 3.8+**: Compatible with modern Python versions

## 🚀 Features

### Text Formatting
- **Title Case**: Convert text to proper title case (e.g., "hello world" → "Hello World")
- **Snake Case**: Convert to snake_case format (e.g., "Hello World" → "hello_world")
- **Reverse Text**: Reverse any text string
- **Capitalize Words**: Capitalize first letter of each word
- **Remove Whitespace**: Remove all spaces from text

### Validation
- **Email Validation**: Check if email addresses are in valid format
- **Phone Validation**: Validate 10-digit phone numbers
- **Password Strength**: Check if passwords meet strength requirements (8+ chars, uppercase, lowercase, digit)

## 📦 Installation

```bash
pip install textformatter-plus
```

## 💻 Quick Start

```python
from textformatter_plus import TextFormatter, Validator

# Text Formatting
formatter = TextFormatter()
result = formatter.to_title_case("hello world")
print(result)  # "Hello World"

result = formatter.to_snake_case("Hello World")
print(result)  # "hello_world"

# Validation
validator = Validator()
is_valid = validator.is_email("user@example.com")
print(is_valid)  # True

is_strong = validator.is_strong_password("MyPassword123")
print(is_strong)  # True
```

## 📚 Complete Usage Examples

### Text Formatting Examples

```python
from textformatter_plus import TextFormatter

formatter = TextFormatter()

# Title case
formatter.to_title_case("hello world")  # "Hello World"

# Snake case
formatter.to_snake_case("Hello World")  # "hello_world"

# Reverse text
formatter.reverse_text("hello")  # "olleh"

# Capitalize words
formatter.capitalize_words("hello world")  # "Hello World"

# Remove whitespace
formatter.remove_whitespace("hello world")  # "helloworld"
```

### Validation Examples

```python
from textformatter_plus import Validator

validator = Validator()

# Email validation
validator.is_email("user@example.com")  # True
validator.is_email("invalid-email")  # False

# Phone validation
validator.is_phone("1234567890")  # True
validator.is_phone("123")  # False

# Password strength
validator.is_strong_password("Password123")  # True
validator.is_strong_password("weak")  # False
```

## 🔧 Requirements

- Python 3.8 or higher
- No external dependencies required

## 📄 License

MIT License - Free to use in personal and commercial projects

## 👤 Author

Your Company Name

## 🔗 Links

- **PyPI**: https://pypi.org/project/textformatter-plus/
- **GitHub**: https://github.com/yourusername/textformatter-plus
- **Issues**: https://github.com/yourusername/textformatter-plus/issues

## 💡 Use Cases

- Form validation in web applications
- Data cleaning and preprocessing
- Text normalization in data pipelines
- User input validation
- API request validation
- Data transformation tasks

## 🎉 Why Choose TextFormatter Plus?

- ✅ **Simple API**: Easy to use, intuitive methods
- ✅ **No Dependencies**: Lightweight, no external packages needed
- ✅ **Well Tested**: Reliable and production-ready
- ✅ **Active Maintenance**: Regular updates and improvements
