# Quick Reference Guide - Code Formatting Standards

## 📌 At a Glance

### File Structure Template
```python
"""
Module description explaining the file's purpose.
"""

# Standard library
import os
from typing import Optional

# Third-party
from pydantic import BaseModel

# Local
from src.config import Config


class MyClass(BaseModel):
    """Class description."""
    
    def method(self) -> str:
        """Method description."""
        pass
```

## 🎯 Key Standards

### Docstring Format
```python
def function(arg1: str, arg2: int = 10) -> dict:
    """
    One-line summary.
    
    Longer description with more context about what 
    the function does and how to use it.
    
    Args:
        arg1: Description of arg1.
        arg2: Description of arg2. Defaults to 10.
    
    Returns:
        Dictionary containing results.
    
    Raises:
        ValueError: If arg1 is empty.
    """
    pass
```

### Class Documentation
```python
class MyClass:
    """Brief class description.
    
    Longer description of the class purpose,
    how it's used, and important implementation
    details.
    """
```

### Module Documentation
```python
"""
Short description of module purpose.

Longer description of what's in this module,
the main components, and how it's used in
the larger system.
"""
```

## 📋 Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Functions | snake_case | `get_user_data()` |
| Variables | snake_case | `user_session` |
| Classes | PascalCase | `ChatHistory` |
| Constants | UPPER_CASE | `MAX_RETRIES = 3` |
| Private | _snake_case | `_internal_method()` |

## 🔧 Import Order

1. **Standard library** (alphabetical)
   ```python
   import os
   import sys
   from datetime import datetime
   from typing import Optional
   ```

2. **Third-party** (alphabetical)
   ```python
   import requests
   from pydantic import BaseModel
   from fastapi import FastAPI
   ```

3. **Local** (alphabetical)
   ```python
   from src.config import Config
   from src.models import User
   ```

## ✨ Common Patterns

### Async Function
```python
async def fetch_data(session_id: str) -> List[dict]:
    """
    Fetch data asynchronously.
    
    Args:
        session_id: Session identifier.
    
    Returns:
        List of data dictionaries.
    """
    data = await db.get_data(session_id)
    return data
```

### Factory Class
```python
class Factory:
    """Factory for creating instances."""
    
    @classmethod
    def create(cls, config: dict):
        """
        Create instance with configuration.
        
        Args:
            config: Configuration dictionary.
        
        Returns:
            New instance.
        """
        return cls(**config)
```

### Error Handling
```python
def process(data: str) -> dict:
    """
    Process data with error handling.
    
    Args:
        data: Data to process.
    
    Returns:
        Processed result.
    
    Raises:
        ValueError: If data is empty.
        ProcessingError: If processing fails.
    """
    if not data:
        raise ValueError("Data cannot be empty")
    
    try:
        result = _process_internal(data)
    except Exception as e:
        raise ProcessingError(f"Failed to process: {e}")
    
    return result
```

## 🚫 What NOT to Do

### ❌ Bad
```python
# Missing docstring
def get_data(q):
    x=db.find(q)
    return x

# Commented code
# old_function()

# Mixed spacing
data={  "key":"value"  }

# Non-descriptive names
def f(x,y):
    return x+y
```

### ✅ Good
```python
def get_data(query: str) -> dict:
    """Retrieve data for the given query."""
    result = db.find(query)
    return result

# Data structure properly formatted
data = {"key": "value"}

# Descriptive function
def calculate_total(price: float, tax: float) -> float:
    """Calculate total price with tax."""
    return price + tax
```

## 🔍 Before Submitting

- [ ] Module has docstring
- [ ] All functions have docstrings
- [ ] All classes have docstrings
- [ ] Imports are organized
- [ ] No commented-out code
- [ ] No unused imports
- [ ] Type hints present
- [ ] PEP 8 compliant spacing
- [ ] Meaningful variable names

## 🛠️ Quick Commands

```bash
# Format with Black
black src/

# Sort imports
isort src/

# Check style
flake8 src/

# Type checking
mypy src/

# Lint check
pylint src/
```

## 📞 Common Issues

### Issue: Long function
**Solution**: Break into smaller functions
```python
# Instead of one 50-line function:
def process():
    # 50 lines...
    
# Do this:
def process():
    data = _load_data()
    result = _validate_data(data)
    return _format_result(result)
```

### Issue: Missing docstring
**Solution**: Add docstring immediately
```python
# Add this:
def function(param: str) -> str:
    """Brief description of function purpose."""
    pass
```

### Issue: Poor naming
**Solution**: Use descriptive names
```python
# Bad
def f(x):
    return x * 2

# Good
def calculate_doubled_value(value: int) -> int:
    """Calculate value multiplied by 2."""
    return value * 2
```

## 📚 Full Guides

For detailed information, see:
- **CODE_STYLE_GUIDE.md** - Complete style guide
- **FORMATTING_SUMMARY.md** - All changes made
- **README_FORMATTING.md** - Overview and statistics
- **VERIFICATION_CHECKLIST.md** - Complete checklist

## 🎯 Remember

> **Code is read much more often than it's written.**
> Make it easy for others (and your future self) to understand.

**Key Principles:**
1. **Clarity** - Code should be easy to understand
2. **Consistency** - Follow the same patterns
3. **Completeness** - Document thoroughly
4. **Correctness** - Handle errors properly

---

**Last Updated**: March 5, 2026
**Status**: Complete and production-ready ✓

