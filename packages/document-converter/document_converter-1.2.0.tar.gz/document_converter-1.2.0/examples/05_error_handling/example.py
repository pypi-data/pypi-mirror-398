#!/usr/bin/env python3
"""
Error Handling Example

Demonstrates robust error handling and recovery.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from converter.engine import ConversionEngine
from converter.formats.txt_converter import TXTConverter
from core.error_handler import ErrorHandler, ConversionError, FormatError
from core.transaction import TransactionManager


def example_basic_error_handling():
    """Basic try-catch error handling."""
    print("\n=== Example 1: Basic Error Handling ===")
    
    engine = ConversionEngine()
    engine.register_converter('txt', TXTConverter)
    
    # Try to convert non-existent file
    try:
        engine.convert('nonexistent.txt', 'output.html')
        print("✓ Conversion succeeded")
    except FileNotFoundError as e:
        print(f"✗ File not found: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")


def example_error_handler_suggestions():
    """Using ErrorHandler for actionable suggestions."""
    print("\n=== Example 2: Error Handler with Suggestions ===")
    
    handler = ErrorHandler()
    engine = ConversionEngine()
    
    try:
        # Try unsupported format
        raise FormatError("Unsupported format: .xyz")
    except Exception as e:
        report = handler.handle(e)
        
        print(f"Error Type: {report['type']}")
        print(f"Message: {report['message']}")
        print(f"Suggestion: {report['suggestion']}")


def example_transaction_rollback():
    """Automatic rollback on error."""
    print("\n=== Example 3: Transaction Rollback ===")
    
    # Create original file
    original_content = "Original important data"
    with open('important.txt', 'w') as f:
        f.write(original_content)
    
    print(f"Original content: '{original_content}'")
    
    try:
        with TransactionManager() as tm:
            tm.register_file('important.txt')
            
            # Modify file
            with open('important.txt', 'w') as f:
                f.write('Modified content')
            
            print("Modified content in transaction")
            
            # Simulate error
            raise ValueError("Something went wrong!")
            
    except ValueError as e:
        print(f"✓ Caught error: {e}")
    
    # Check file was rolled back
    with open('important.txt', 'r') as f:
        restored = f.read()
    
    if restored == original_content:
        print(f"✓ File rolled back: '{restored}'")
    else:
        print(f"✗ Rollback failed: '{restored}'")
    
    # Cleanup
    os.remove('important.txt')


def example_graceful_degradation():
    """Graceful error handling with fallbacks."""
    print("\n=== Example 4: Graceful Degradation ===")
    
    files_to_convert = [
        'file1.txt',  # exists
        'missing.txt',  # doesn't exist
        'file3.txt',  # exists
    ]
    
    # Create existing files
    for fname in ['file1.txt', 'file3.txt']:
        with open(fname, 'w') as f:
            f.write(f'Content of {fname}')
    
    engine = ConversionEngine()
    engine.register_converter('txt', TXTConverter)
    
    results = {'success': 0, 'failed': 0, 'errors': []}
    
    for fname in files_to_convert:
        try:
            output = fname.replace('.txt', '.html')
            success = engine.convert(fname, output)
            if success:
                results['success'] += 1
                print(f"✓ Converted: {fname}")
            else:
                results['failed'] += 1
                results['errors'].append(f"{fname}: conversion returned False")
                print(f"✗ Failed: {fname}")
        except FileNotFoundError:
            results['failed'] += 1
            results['errors'].append(f"{fname}: file not found")
            print(f"✗ Skipped: {fname} (not found)")
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"{fname}: {type(e).__name__}")
            print(f"✗ Error: {fname} - {e}")
    
    print("\n" + "-" * 40)
    print(f"Results: {results['success']} succeeded, {results['failed']} failed")
    
    # Cleanup
    for fname in ['file1.txt', 'file3.txt', 'file1.html', 'file3.html']:
        if os.path.exists(fname):
            os.remove(fname)


def example_validation():
    """Input validation before conversion."""
    print("\n=== Example 5: Input Validation ===")
    
    def validate_file(path):
        """Validate file before conversion."""
        if not os.path.exists(path):
            return False, "File does not exist"
        
        if not os.path.isfile(path):
            return False, "Path is not a file"
        
        if os.path.getsize(path) == 0:
            return False, "File is empty"
        
        if os.path.getsize(path) > 100 * 1024 * 1024:  # 100MB
            return False, "File too large (>100MB)"
        
        return True, "OK"
    
    # Test validation
    test_files = {
        'nonexistent.txt': None,
        'valid.txt': "Some content",
        'empty.txt': "",
    }
    
    # Create test files
    for fname, content in test_files.items():
        if content is not None:
            with open(fname, 'w') as f:
                f.write(content)
    
    # Validate each
    for fname in test_files.keys():
        valid, message = validate_file(fname)
        status = "✓ Valid" if valid else "✗ Invalid"
        print(f"{status}: {fname} - {message}")
    
    # Cleanup
    for fname in ['valid.txt', 'empty.txt']:
        if os.path.exists(fname):
            os.remove(fname)


if __name__ == '__main__':
    print("=" * 60)
    print("ERROR HANDLING EXAMPLES")
    print("=" * 60)
    
    example_basic_error_handling()
    example_error_handler_suggestions()
    example_transaction_rollback()
    example_graceful_degradation()
    example_validation()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
