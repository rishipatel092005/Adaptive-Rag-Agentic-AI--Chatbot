# Adaptive RAG - Code Style Guide

## Overview
This document provides guidelines for maintaining consistent code quality and style across the Adaptive RAG project.

## General Guidelines

### File Structure
Every Python file should follow this structure:
```python
"""Module docstring describing the file's purpose."""

# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
import requests
from pydantic import BaseModel

# Local imports
from src.config.settings import Config
```

### Docstring Format
All functions, classes, and modules should have docstrings in Google format:

```python
def process_document(content: str, format: str = "text") -> dict:
    """
    Process and validate document content.
    
    Supports multiple formats and performs validation on the content
    before processing.
    
    Args:
        content: The document content to process.
        format: Output format ('text', 'json', 'xml'). Defaults to 'text'.
    
    Returns:
        A dictionary containing processed content and metadata.
    
    Raises:
        ValueError: If content is empty or format is unsupported.
    
    Examples:
        >>> result = process_document("Hello World", "text")
        >>> result['status']
        'success'
    """
    pass
```

### Class Documentation
```python
class DocumentProcessor(BaseModel):
    """Process and validate documents for RAG system.
    
    This class handles document ingestion, chunking, and embedding
    generation for the vector store.
    """
    
    def __init__(self, config: Config):
        """Initialize the processor with configuration."""
        pass
```

## Naming Conventions

### Variables and Functions
- Use `snake_case` for variables and functions
- Use descriptive names (avoid single letters except for loop counters)
- Prefix private methods with underscore `_private_method()`

```python
# Good
user_session = ChatHistory.get_session(user_id)
def process_query(query: str) -> str:
    pass

# Avoid
s = ChatHistory.get_session(uid)
def process(q):
    pass
```

### Constants
- Use `UPPER_CASE` for constants
- Group related constants together

```python
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "adaptive_rag"
COLLECTION_NAME = "documents"
```

### Classes
- Use `PascalCase` for class names
- Use descriptive names that indicate the class purpose

```python
class ChatHistory:
    pass

class MongoDBChatMessageHistory:
    pass
```

## Code Organization

### Import Order
Follow this order:
1. Future imports
2. Standard library imports (alphabetical)
3. Third-party imports (alphabetical)
4. Local application imports (alphabetical)

### Spacing
- Two blank lines between top-level functions and classes
- One blank line between methods in a class
- Blank lines to separate logical groups within functions

```python
class Document:
    """Document model."""
    
    def __init__(self, content: str):
        self.content = content
    
    def process(self):
        """Process the document."""
        # Implementation
        pass
    
    def validate(self):
        """Validate the document."""
        # Implementation
        pass
```

## Type Hints
Use type hints for all function parameters and return types:

```python
from typing import Optional, List, Dict

def get_documents(
    session_id: str,
    limit: int = 10
) -> List[Dict[str, str]]:
    """Retrieve documents for a session."""
    pass

def find_user(user_id: str) -> Optional[dict]:
    """Find user by ID or return None."""
    pass
```

## Error Handling

### Custom Exceptions
Define exceptions at module level:

```python
class DocumentProcessingError(Exception):
    """Raised when document processing fails."""
    pass

class VectorStoreError(Exception):
    """Raised when vector store operations fail."""
    pass
```

### Exception Handling
Always catch specific exceptions:

```python
# Good
try:
    docs = loader.load()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    raise DocumentProcessingError(f"Could not load file: {e}")

# Avoid
try:
    docs = loader.load()
except Exception:
    pass
```

## Logging
Use the standard logging module:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Detailed debugging information")
logger.info("Confirmation that things are working")
logger.warning("Warning message")
logger.error("Serious error message")
logger.exception("Error with traceback")
```

## Async Code
When using async functions, follow these patterns:

```python
async def fetch_data(session_id: str) -> List[dict]:
    """Fetch data asynchronously."""
    # Implementation
    pass

async def process_and_save(data: dict) -> bool:
    """Process data and save to database."""
    # Implementation
    pass
```

## Testing Guidelines

### Function Testing
```python
def test_process_document():
    """Test document processing with valid content."""
    result = process_document("test content")
    assert result["status"] == "success"

def test_process_document_invalid():
    """Test document processing with invalid content."""
    with pytest.raises(ValueError):
        process_document("")
```

## Comment Guidelines

### Good Comments
- Explain WHY, not WHAT
- Provide context and reasoning
- Document non-obvious workarounds

```python
# Qdrant connection is established lazily to avoid connection
# timeouts in test environments
vectorstore = QdrantVectorStore.from_documents(...)
```

### Bad Comments
- Redundant comments
- Outdated comments
- Comments that restate code

```python
# Bad: This comment just restates the code
count = count + 1  # Increment count

# Good: Explains why it's done this way
count = count + 1  # Increment after validation to maintain 1-based indexing
```

## Code Complexity
- Keep functions focused and concise (< 30 lines when possible)
- Extract complex logic into helper functions
- Use meaningful variable names to reduce need for comments

```python
# Good
def validate_and_process(data: dict) -> dict:
    """Validate and process data."""
    if not is_valid_data(data):
        raise ValueError("Invalid data format")
    
    processed = process_data(data)
    return processed

# Avoid
def validate_and_process(data: dict) -> dict:
    """Validate and process data."""
    # 50 lines of validation logic here
    # 40 lines of processing logic here
    # Hard to understand and test
    pass
```

## Performance Considerations

### Async Operations
Use async for I/O operations:

```python
# Good: Async database operations
async def get_documents(session_id: str):
    """Fetch documents asynchronously."""
    docs = await db.collection.find({"session_id": session_id}).to_list()
    return docs
```

### Caching
Consider caching for expensive operations:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_embedding_model():
    """Get embedding model (cached)."""
    return OpenAIEmbeddings()
```

## Code Review Checklist
Before submitting code:
- ✓ All functions have docstrings
- ✓ Type hints present for parameters and returns
- ✓ Follows naming conventions
- ✓ No hardcoded values (use constants)
- ✓ Proper error handling
- ✓ No unused imports or variables
- ✓ PEP 8 compliant
- ✓ No commented-out code
- ✓ Proper logging in place
- ✓ Tests pass

## Tools and Automation

### Format Check
```bash
# Check PEP 8 compliance
flake8 src/

# Auto-format code
black src/

# Sort imports
isort src/
```

### Type Checking
```bash
# Check type hints
mypy src/
```

### Linting
```bash
# Run pylint
pylint src/

# Run flake8 with specific checks
flake8 src/ --select=E,W,F
```

## Project-Specific Guidelines

### RAG System
- Always document retriever tool instructions
- Include proper error handling for vector store operations
- Log intermediate steps for debugging

### Streamlit Applications
- Keep UI logic separate from business logic
- Use session state consistently
- Document page configuration

### API Routes
- Use proper HTTP status codes
- Document request/response schemas
- Add proper error messages

## Version Control
- Use descriptive commit messages
- One logical change per commit
- Format: `<type>: <description>`
  - `feat: add new feature`
  - `fix: resolve bug`
  - `refactor: reorganize code`
  - `docs: update documentation`
  - `style: formatting changes`

