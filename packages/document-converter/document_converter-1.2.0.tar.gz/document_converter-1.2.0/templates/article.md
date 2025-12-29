# {{ title }}

*By {{ author }}*

{{ content }}

## References
{% for ref in references %}
1. {{ ref }}
{% endfor %}
