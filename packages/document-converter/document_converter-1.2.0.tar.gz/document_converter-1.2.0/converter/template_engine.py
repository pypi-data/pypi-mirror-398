import re
import logging
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)

class TemplateEngine:
    """
    A basic template engine supporting variables, loops, and conditionals.
    Syntax:
        Variables: {{ variable_name }} or {{ dict.key }}
        Loops: {% for item in list %}Content: {{ item }}{% endfor %}
        Conditionals: {% if condition %}Content{% endif %}
    """

    def __init__(self):
        # Regex for splitting template into tokens (tags vs text)
        self.tokenizer = re.compile(r'({\%.*?\%}|{{.*?}})')
        # Regex for parsing specific tags
        self.var_tag = re.compile(r'^{{\s*(.*?)\s*}}$')
        self.block_tag = re.compile(r'^{\%\s*(.*?)\s*\%}$')

    def render(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a template string with the given context.
        """
        return "".join(self.render_stream(template, context))

    def render_stream(self, template: str, context: Dict[str, Any]):
        """
        Render a template streaming the output chunks.
        """
        tokens = self.tokenizer.split(template)
        try:
            parsed_nodes = self._parse(tokens)
            yield from self._evaluate_stream(parsed_nodes, context)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise

    def _parse(self, tokens: List[str]) -> List[Any]:
        """
        Parse tokens into a hierarchical structure of nodes.
        Returns a list of nodes. Nodes can be strings (text), or dicts (blocks).
        """
        nodes = []
        stack = [] # Stack for handling nested blocks. Each item: (block_type, children_list, params)

        # We will build 'nodes' as the root list.
        # If we enter a block, we push the current list to stack and start a new list.
        current_list = nodes

        for token in tokens:
            if not token:
                continue

            var_match = self.var_tag.match(token)
            block_match = self.block_tag.match(token)

            if var_match:
                # Variable tag
                current_list.append({'type': 'var', 'name': var_match.group(1)})
            elif block_match:
                # Block tag (for, if, endfor, endif)
                content = block_match.group(1).strip()
                parts = content.split()
                tag_name = parts[0]

                if tag_name == 'for':
                    # Parse 'for item in collection'
                    if len(parts) != 4 or parts[2] != 'in':
                        raise ValueError(f"Invalid for loop syntax: {content}")
                    
                    item_name = parts[1]
                    collection_name = parts[3]
                    
                    new_block = {'type': 'for', 'item_name': item_name, 'collection_name': collection_name, 'children': []}
                    current_list.append(new_block)
                    stack.append((current_list, new_block))
                    current_list = new_block['children']

                elif tag_name == 'if':
                    # Parse 'if condition'
                    if len(parts) < 2:
                         raise ValueError(f"Invalid if syntax: {content}")
                    
                    condition_var = parts[1]
                    
                    new_block = {'type': 'if', 'condition_var': condition_var, 'children': []}
                    current_list.append(new_block)
                    stack.append((current_list, new_block))
                    current_list = new_block['children']

                elif tag_name in ('endfor', 'endif'):
                    if not stack:
                        raise ValueError(f"Unexpected descriptor: {tag_name}")
                    
                    parent_list, block_node = stack.pop()
                    
                    # Validate nesting
                    expected_end = 'end' + block_node['type']
                    if tag_name != expected_end:
                        raise ValueError(f"Mismatched tags: expected {expected_end}, got {tag_name}")
                    
                    current_list = parent_list # Restore parent list
                
                else:
                    raise ValueError(f"Unknown block tag: {tag_name}")

            else:
                # Plain text
                current_list.append({'type': 'text', 'content': token})
        
        if stack:
            raise ValueError("Unclosed blocks in template")

        return nodes

    def _evaluate_stream(self, nodes: List[Any], context: Dict[str, Any]):
        """
        Recursively evaluate nodes against context yielding strings.
        """
        for node in nodes:
            if node['type'] == 'text':
                yield node['content']
            
            elif node['type'] == 'var':
                val = self._resolve_var(node['name'], context)
                yield str(val) if val is not None else ""
            
            elif node['type'] == 'for':
                collection = self._resolve_var(node['collection_name'], context)
                if not collection:
                    collection = [] # Handle None/Missing as empty
                
                if not hasattr(collection, '__iter__'):
                     raise ValueError(f"Variable '{node['collection_name']}' is not iterable")

                item_name = node['item_name']
                
                for item in collection:
                    # Create inner context
                    inner_context = context.copy()
                    inner_context[item_name] = item
                    yield from self._evaluate_stream(node['children'], inner_context)
            
            elif node['type'] == 'if':
                condition_val = self._resolve_var(node['condition_var'], context)
                if condition_val:
                    yield from self._evaluate_stream(node['children'], context)

    def _evaluate(self, nodes: List[Any], context: Dict[str, Any]) -> str:
        """Deprecated: use _evaluate_stream"""
        return "".join(self._evaluate_stream(nodes, context))

    def _resolve_var(self, path: str, context: Dict[str, Any]) -> Any:
        """Resolve dot-notated variable path in context."""
        parts = path.split('.')
        current = context
        
        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    # Try getattr for objects
                    current = getattr(current, part, None)
                
                if current is None:
                    return None
            return current
        except Exception:
            return None

