# Template Rendering Example

This example demonstrates document generation from templates.

## What This Example Shows

- Basic variable interpolation
- Loops and iterations
- Loading data from JSON files
- Streaming for large datasets

## Files

- `example.py` - Template rendering demonstrations

## Examples Included

### Example 1: Basic Template
Simple variable substitution in templates.

### Example 2: Loops
Iterating over lists to generate repeated content.

### Example 3: JSON Data
Loading template and data from separate files.

### Example 4: Streaming
Efficiently rendering large datasets.

## Running the Example

```bash
cd examples/03_template_rendering
python example.py
```

## Expected Output

The script will:
1. Render a greeting template
2. Generate a sales report with loops
3. Create a report from JSON data
4. Stream 1000 user records to file
5. Clean up generated files

## Key Concepts

### Basic Rendering

```python
from converter.template_engine import TemplateEngine

engine = TemplateEngine()
result = engine.render(template, context)
```

### Template Syntax

**Variables:**
```
Hello {{ name }}!
```

**Loops:**
```
{% for item in items %}
- {{ item }}
{% endfor %}
```

**Conditionals:**
```
{% if condition %}
Text if true
{% endif %}
```

### Loading from Files

```python
# Load template
with open('template.txt', 'r') as f:
    template = f.read()

# Load data
with open('data.json', 'r') as f:
    context = json.load(f)

# Render
result = engine.render(template, context)
```

### Streaming Large Output

```python
with open('output.txt', 'w') as f:
    for chunk in engine.render_stream(template, large_context):
        f.write(chunk)
```

Streaming avoids loading entire output into memory.

## Use Cases

1. **Report Generation**: Monthly/weekly reports from database data
2. **Email Templates**: Personalized emails with user data
3. **Documentation**: Auto-generated docs from code metadata
4. **Invoices**: Dynamic invoice generation
5. **Bulk Communications**: Letters, certificates, etc.

## Template Best Practices

1. **Separate data from templates**: Keep templates and data in separate files
2. **Use meaningful variable names**: `{{ customer_name }}` not `{{ cn }}`
3. **Stream large outputs**: Use `render_stream()` for >10MB output
4. **Validate data**: Check required fields exist before rendering
5. **Test with sample data**: Create sample JSON for testing

## Next Steps

- Create your own templates
- Load data from databases
- Combine with batch processing for bulk generation
- Add error handling for missing variables
