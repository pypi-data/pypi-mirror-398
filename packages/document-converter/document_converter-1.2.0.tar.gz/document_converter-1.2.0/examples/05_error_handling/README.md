# Error Handling Example

This example demonstrates robust error handling strategies.

## What This Example Shows

- Basic try-catch patterns
- ErrorHandler for actionable suggestions
- Transaction rollback on errors
- Graceful degradation (continue despite errors)
- Input validation

## Files

- `example.py` - Error handling demonstrations

## Examples Included

### Example 1: Basic Error Handling
Standard try-catch exception handling.

### Example 2: Error Handler
Using ErrorHandler for helpful suggestions.

### Example 3: Transaction Rollback
Automatic file restoration on errors.

### Example 4: Graceful Degradation
Continue processing despite some failures.

### Example 5: Input Validation
Validate files before attempting conversion.

## Running the Example

```bash
cd examples/05_error_handling
python example.py
```

## Expected Output

The script will:
1. Handle missing file errors
2. Show error suggestions
3. Demonstrate automatic rollback
4. Process multiple files with some failures
5. Validate input files

## Key Concepts

### Basic Exception Handling

```python
try:
    engine.convert('input.txt', 'output.html')
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Error: {e}")
```

### Using ErrorHandler

```python
from core.error_handler import ErrorHandler

handler = ErrorHandler()
try:
    # Your code
    pass
except Exception as e:
    report = handler.handle(e)
    print(report['message'])
    print(report['suggestion'])
```

The ErrorHandler provides:
- Structured error reports
- Actionable recovery suggestions
- Context tracking

### Transaction Safety

```python
from core.transaction import TransactionManager

with TransactionManager() as tm:
    tm.register_file('critical.txt')
    
    # Modify file
    with open('critical.txt', 'w') as f:
        f.write('new content')
    
    # If error occurs, file is automatically restored
```

### Graceful Degradation

```python
results = {'success': 0, 'failed': 0}

for file in files:
    try:
        convert_file(file)
        results['success'] += 1
    except Exception as e:
        results['failed'] += 1
        log_error(file, e)

# Continue even if some files fail
print(f"Completed: {results['success']}/{len(files)}")
```

### Input Validation

```python
def validate_file(path):
    if not os.path.exists(path):
        return False, "File not found"
    if os.path.getsize(path) == 0:
        return False, "Empty file"
    return True, "OK"

valid, msg = validate_file('input.txt')
if valid:
    convert_file('input.txt')
```

## Error Types

The library defines custom exceptions:

- `DocumentConverterError` - Base exception
- `ConversionError` - Conversion failures
- `FormatError` - Unsupported formats
- `ConfigurationError` - Config issues
- `ResourceError` - Resource access problems

## Best Practices

1. **Validate Early**: Check inputs before processing
2. **Handle Specifically**: Catch specific exceptions, not just `Exception`
3. **Log Errors**: Record what went wrong for debugging
4. **Provide Context**: Include file names, options in error messages
5. **Fail Gracefully**: Continue processing other files when one fails
6. **Use Transactions**: Protect important files with TransactionManager
7. **Give Feedback**: Show users what went wrong and how to fix it

## Production Error Handling Template

```python
from core.error_handler import ErrorHandler
from core.transaction import TransactionManager
import logging

def safe_convert(input_path, output_path):
    """Production-ready conversion with error handling."""
    handler = ErrorHandler()
    
    # Validate input
    if not os.path.exists(input_path):
        logging.error(f"Input not found: {input_path}")
        return False
    
    try:
        with TransactionManager() as tm:
            if os.path.exists(output_path):
                tm.register_file(output_path)
            
            success = engine.convert(input_path, output_path)
            
            if not success:
                logging.warning(f"Conversion returned False: {input_path}")
                return False
            
            return True
            
    except Exception as e:
        report = handler.handle(e)
        logging.error(f"Conversion failed: {report['message']}")
        logging.info(f"Suggestion: {report['suggestion']}")
        return False
```

## Next Steps

- Implement retry logic for transient failures
- Add monitoring and alerting
- Create error recovery workflows
- Build user-friendly error messages for your application
