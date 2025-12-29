#!/usr/bin/env python3
"""
Template Rendering Example

Demonstrates generating documents from templates and data.
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from converter.template_engine import TemplateEngine


def example_basic_template():
    """Basic template with variables."""
    print("\n=== Example 1: Basic Template ===")
    
    engine = TemplateEngine()
    
    template = """Hello {{ name }}!

Welcome to {{ company }}.
Your account expires on: {{ expiry_date }}
"""
    
    context = {
        "name": "Alice",
        "company": "Document Converter Inc.",
        "expiry_date": "2025-12-31"
    }
    
    result = engine.render(template, context)
    print(result)


def example_with_loops():
    """Template with loops."""
    print("\n=== Example 2: Template with Loops ===")
    
    engine = TemplateEngine()
    
    template = """Sales Report - {{ month }}

Top Products:
{% for product in products %}
{{ product.rank }}. {{ product.name }} - ${{ product.sales }}
{% endfor %}

Total Revenue: ${{ total }}
"""
    
    context = {
        "month": "November 2024",
        "products": [
            {"rank": 1, "name": "Widget Pro", "sales": "15,000"},
            {"rank": 2, "name": "Gadget Plus", "sales": "12,500"},
            {"rank": 3, "name": "Tool Master", "sales": "10,200"}
        ],
        "total": "37,700"
    }
    
    result = engine.render(template, context)
    print(result)


def example_json_data():
    """Template with JSON data file."""
    print("\n=== Example 3: Template with JSON Data ===")
    
    # Create template file
    template_content = """
{{ title }}
{{ "=" * 60 }}

Generated: {{ generated_at }}

{% for section in sections %}
## {{ section.name }}
{{ section.description }}

{% for item in section.items %}
- {{ item }}
{% endfor %}

{% endfor %}

Summary: {{ summary }}
"""
    
    with open('report_template.txt', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    # Create data file
    data = {
        "title": "Monthly Report",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sections": [
            {
                "name": "Achievements",
                "description": "What we accomplished this month:",
                "items": [
                    "Launched new feature",
                    "Fixed 45 bugs",
                    "Improved performance by 30%"
                ]
            },
            {
                "name": "Metrics",
                "description": "Key performance indicators:",
                "items": [
                    "Users: 10,234 (+15%)",
                    "Revenue: $45,000 (+8%)",
                    "Satisfaction: 4.5/5 stars"
                ]
            }
        ],
        "summary": "Excellent progress across all metrics"
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    # Load and render
    engine = TemplateEngine()
    
    with open('report_template.txt', 'r', encoding='utf-8') as f:
        template = f.read()
    
    with open('data.json', 'r', encoding='utf-8') as f:
        context = json.load(f)
    
    result = engine.render(template, context)
    
    # Save output
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    
    print("✓ Report generated from template + JSON data")
    print(f"  Template: report_template.txt")
    print(f"  Data: data.json")
    print(f"  Output: report.txt")
    print("\nFirst 300 chars:")
    print("-" * 60)
    print(result[:300] + "...")


def example_streaming():
    """Streaming template for large datasets."""
    print("\n=== Example 4: Streaming Large Dataset ===")
    
    engine = TemplateEngine()
    
    template = """User Report
{{ "=" * 60 }}

{% for user in users %}
User {{ user.id }}: {{ user.name }} ({{ user.email }})
{% endfor %}

Total users: {{ total }}
"""
    
    # Large dataset
    context = {
        "users": [
            {"id": i, "name": f"User {i}", "email": f"user{i}@example.com"}
            for i in range(1000)  # 1000 users
        ],
        "total": 1000
    }
    
    # Stream to file
    print("Streaming 1000 users to file...")
    with open('users.txt', 'w', encoding='utf-8') as f:
        for chunk in engine.render_stream(template, context):
            f.write(chunk)
    
    file_size = os.path.getsize('users.txt')
    print(f"✓ Generated users.txt ({file_size:,} bytes)")


def cleanup():
    """Clean up generated files."""
    files = ['report_template.txt', 'data.json', 'report.txt', 'users.txt']
    for f in files:
        if os.path.exists(f):
            os.remove(f)
    print("\n✓ Cleaned up generated files")


if __name__ == '__main__':
    print("=" * 60)
    print("TEMPLATE RENDERING EXAMPLES")
    print("=" * 60)
    
    try:
        example_basic_template()
        example_with_loops()
        example_json_data()
        example_streaming()
    finally:
        cleanup()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
