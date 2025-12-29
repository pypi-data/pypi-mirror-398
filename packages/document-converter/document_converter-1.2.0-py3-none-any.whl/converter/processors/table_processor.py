import logging
from typing import List, Optional, Any

logger = logging.getLogger(__name__)

class TableProcessor:
    """
    Processor for handling table operations and conversions.
    Provides utilities to convert between table data structures (List[List[str]])
    and format-specific representations (Markdown, HTML).
    """

    def __init__(self):
        pass

    def data_to_markdown(self, data: List[List[str]], headers: Optional[List[str]] = None) -> str:
        """
        Convert table data to Markdown table string.
        
        Args:
            data: List of rows, where each row is a list of cell strings.
            headers: Optional list of header strings. If None, first row of data might be used or no header.
        """
        if not data and not headers:
            return ""

        rows = []
        
        # Handle headers
        if headers:
            # | Header | Header |
            rows.append(f"| {' | '.join(headers)} |")
            # | --- | --- |
            rows.append(f"| {' | '.join(['---'] * len(headers))} |")
        
        # Determine columns count for consistent formatting if needed
        # But markdown usually handles it line by line.
        
        for row in data:
            clean_row = [str(cell).strip().replace("\n", "<br>") for cell in row]
            rows.append(f"| {' | '.join(clean_row)} |")
            
        return "\n".join(rows)

    def data_to_html(self, data: List[List[str]], headers: Optional[List[str]] = None) -> str:
        """
        Convert table data to HTML table string.
        """
        if not data and not headers:
            return ""

        html_parts = ["<table>"]
        
        if headers:
            html_parts.append("<thead><tr>")
            for h in headers:
                html_parts.append(f"<th>{str(h).strip()}</th>")
            html_parts.append("</tr></thead>")
            
        html_parts.append("<tbody>")
        for row in data:
            html_parts.append("<tr>")
            for cell in row:
                html_parts.append(f"<td>{str(cell).strip()}</td>")
            html_parts.append("</tr>")
        html_parts.append("</tbody>")
        html_parts.append("</table>")
        
        return "".join(html_parts)

    def html_to_data(self, table_soup) -> List[List[str]]:
        """
        Extract data from a BeautifulSoup table node.
        Returns list of rows (List[str]).
        Simple extraction: text only, implies no rowspan/colspan complexity handling for now.
        """
        data = []
        
        # Process rows
        rows = table_soup.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            if row_data:
                data.append(row_data)
                
        return data

    def standardize_table(self, data: List[List[Any]]) -> List[List[str]]:
        """
        Ensure all rows have the same number of columns by padding with empty strings.
        Converts all cells to strings.
        """
        if not data:
            return []
            
        max_cols = max(len(row) for row in data)
        standardized = []
        
        for row in data:
            new_row = [str(cell) if cell is not None else "" for cell in row]
            while len(new_row) < max_cols:
                new_row.append("")
            standardized.append(new_row)
            
        return standardized
