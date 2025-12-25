# Python Package and FastAPI Demo

This project demonstrates how to create a Python package and use it in a FastAPI application.

## 📚 Documentation

- **👋 New to this?** Start with [QUICK_START.md](QUICK_START.md) - Simple 3-step guide
- **📖 Need detailed steps?** See [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete step-by-step instructions
- **⚡ Want automation?** Use the setup scripts: `bash setup.sh` then `bash start_server.sh`

## 🎯 Important: Understanding the Structure

- **Package (`my_feature_package/`)**: This is just code that you **INSTALL**, not run. **NO SERVER NEEDED!**
- **FastAPI App (`fastapi_app/`)**: This is a web server that you **RUN**. This is the only server.

## Project Structure

```
creating-package-in-python/
├── my_feature_package/          # The Python package
│   ├── __init__.py
│   ├── text_formatter.py        # Text formatting utilities
│   └── validator.py             # Validation utilities
├── fastapi_app/                 # FastAPI application
│   └── main.py                  # FastAPI app using the package
├── setup.py                     # Package installation file
├── requirements.txt             # FastAPI dependencies
└── README.md                    # This file
```

## Installation Steps

### 1. Install the Package

First, install the package in development mode:

```bash
pip install -e .
```

This will install `my-feature-package` so it can be imported in your FastAPI app.

### 2. Install FastAPI Dependencies

```bash
pip install -r requirements.txt
```

## Running the FastAPI Application

Start the FastAPI server:

```bash
cd fastapi_app
uvicorn main:app --reload
```

Or from the root directory:

```bash
uvicorn fastapi_app.main:app --reload
```

The API will be available at: `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Text Formatter Endpoints

- `POST /format/title` - Convert text to title case
- `POST /format/snake` - Convert text to snake_case
- `POST /format/reverse` - Reverse the text
- `POST /format/capitalize` - Capitalize first letter of each word
- `POST /format/remove-whitespace` - Remove all whitespace

### Validator Endpoints

- `POST /validate/email` - Validate email address
- `POST /validate/phone` - Validate phone number
- `POST /validate/password` - Validate strong password

## Example Usage

### Using the Package Directly

```python
from my_feature_package import TextFormatter, Validator

formatter = TextFormatter()
validator = Validator()

# Format text
result = formatter.to_title_case("hello world")
print(result)  # "Hello World"

# Validate email
is_valid = validator.is_email("user@example.com")
print(is_valid)  # True
```

### Using the API

```bash
# Format text
curl -X POST "http://localhost:8000/format/title" \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world"}'

# Validate email
curl -X POST "http://localhost:8000/validate/email" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

## Package Features

### TextFormatter
- `to_title_case()` - Convert to title case
- `to_snake_case()` - Convert to snake_case
- `reverse_text()` - Reverse text
- `capitalize_words()` - Capitalize each word
- `remove_whitespace()` - Remove all whitespace

### Validator
- `is_email()` - Validate email format
- `is_phone()` - Validate phone number (10 digits)
- `is_strong_password()` - Validate strong password requirements

