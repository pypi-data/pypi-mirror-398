# Basic Conversion Example

This example demonstrates simple single-file conversions.

## What This Example Shows

- Setting up the ConversionEngine
- Registering converters for specific formats
- Converting files between formats
- Basic error handling

## Files

- `example.py` - Main script with 3 examples

## Examples Included

### Example 1: TXT to HTML
Converts a plain text file to HTML format.

### Example 2: Markdown to HTML  
Converts a Markdown file to HTML.

### Example 3: Error Handling
Shows proper exception handling for missing files.

## Running the Example

```bash
cd examples/01_basic_conversion
python example.py
```

## Expected Output

The script will:
1. Create sample input files
2. Convert them to different formats
3. Show output previews
4. Clean up generated files

## Key Concepts

### Registering Converters

```python
engine = ConversionEngine()
engine.register_converter('txt', TXTConverter)
```

You must register a converter for each format you want to work with.

### Converting Files

```python
success = engine.convert('input.txt', 'output.html')
```

The `convert()` method returns `True` on success, `False` on failure.

### Error Handling

```python
try:
    engine.convert('input.txt', 'output.html')
except FileNotFoundError:
    print("Input file not found!")
```

Always handle exceptions for production code.

## Next Steps

- Try modifying the sample content
- Add your own input files
- Experiment with different formats
- See `02_batch_processing/` for handling multiple files
