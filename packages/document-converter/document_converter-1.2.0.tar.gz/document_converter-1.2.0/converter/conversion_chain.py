import logging
from typing import Dict, List, Optional, Tuple, Type, Set
from collections import deque
from converter.base.converter_base import BaseConverter

logger = logging.getLogger(__name__)

class ConversionChain:
    """
    Manages a graph of conversions to support indirect conversion paths (A -> B -> C).
    """

    def __init__(self):
        # Graph representation: source_fmt -> {target_fmt: converter_class}
        self._graph: Dict[str, Dict[str, Type[BaseConverter]]] = {}

    def add_converter(self, source_fmt: str, target_fmt: str, converter_class: Type[BaseConverter]):
        """
        Add a converter to the graph.
        
        Args:
            source_fmt: Source format identifier.
            target_fmt: Target format identifier.
            converter_class: The converter class.
        """
        if source_fmt not in self._graph:
            self._graph[source_fmt] = {}
        self._graph[source_fmt][target_fmt] = converter_class
        logger.debug(f"Added conversion path: {source_fmt} -> {target_fmt}")

    def get_conversion_path(self, source_fmt: str, target_fmt: str) -> Optional[List[Tuple[str, str, Type[BaseConverter]]]]:
        """
        Find the shortest conversion path from source to target format using BFS.
        
        Args:
            source_fmt: Source format identifier.
            target_fmt: Target format identifier.
            
        Returns:
            List of tuples (current_fmt, next_fmt, converter_class) representing the path,
            or None if no path is found.
        """
        if source_fmt == target_fmt:
            return []

        if source_fmt not in self._graph:
            return None

        # BFS initialization
        queue = deque([(source_fmt, [])]) # (current_node, path_so_far)
        visited: Set[str] = {source_fmt}

        while queue:
            current_fmt, path = queue.popleft()

            if current_fmt == target_fmt:
                return path

            if current_fmt in self._graph:
                for next_fmt, converter_cls in self._graph[current_fmt].items():
                    if next_fmt not in visited:
                        visited.add(next_fmt)
                        new_path = path + [(current_fmt, next_fmt, converter_cls)]
                        
                        # Optimization: If we reached the target, return immediately (BFS guarantees shortest path in unweighted graph)
                        if next_fmt == target_fmt:
                            return new_path
                        
                        queue.append((next_fmt, new_path))

        return None
