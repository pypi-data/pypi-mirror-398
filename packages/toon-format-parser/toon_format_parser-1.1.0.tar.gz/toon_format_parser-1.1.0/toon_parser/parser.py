import re
from typing import Any, Dict, List, Optional, Union

class ToonParser:
    """
    Parser for TOON (Token-Oriented Object Notation) format
    """
    
    @staticmethod
    def encode(data: Any, indent: int = 2, delimiter: str = ',') -> str:
        options = {
            'indent': indent,
            'delimiter': delimiter
        }
        return encode_value(data, 0, options)

    @staticmethod
    def decode(toon: str, indent: int = 2, delimiter: str = ',', trim: bool = True, comments: bool = True) -> Any:
        options = {
            'indent': indent,
            'delimiter': delimiter,
            'trim': trim,
            'comments': comments
        }
        decoder = Decoder(toon, options)
        return decoder.decode()

def encode_value(value: Any, indent_level: int, options: Dict[str, Any]) -> str:
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return quote_string(value, options)
    if isinstance(value, list):
        return encode_array(value, indent_level, options)
    if isinstance(value, dict):
        return encode_object(value, indent_level, options)
    return 'null'

def quote_string(s: str, options: Dict[str, Any]) -> str:
    delimiter = options.get('delimiter', ',')
    needs_quote = (
        delimiter in s or
        ':' in s or
        s.startswith(' ') or
        s.endswith(' ') or
        s in ('true', 'false', 'null') or
        (len(s) > 0 and s[0].isdigit())
    )

    if not needs_quote:
        return s

    escaped = s.replace('\\', '\\\\')\
               .replace('"', '\\"')\
               .replace('\n', '\\n')\
               .replace('\r', '\\r')\
               .replace('\t', '\\t')
    return f'"{escaped}"'

def is_tabular_array(arr: List[Any]) -> bool:
    if not arr or not isinstance(arr, list):
        return False
    
    if not all(isinstance(item, dict) and item is not None for item in arr):
        return False
    
    keys = list(arr[0].keys())
    if not keys:
        return False
    
    for item in arr:
        if list(item.keys()) != keys:
            return False
        if any(isinstance(val, (dict, list)) and val is not None for val in item.values()):
            return False
            
    return True

def encode_object(obj: Dict[str, Any], indent_level: int, options: Dict[str, Any]) -> str:
    indent_size = options.get('indent', 2)
    indent = ' ' * indent_size
    lines = []

    for key, value in obj.items():
        key_label = quote_string(key, options)
        key_prefix = (indent * indent_level) + key_label + ':'

        if value is None:
            lines.append(f"{key_prefix} null")
        elif isinstance(value, list):
            if is_tabular_array(value):
                keys = list(value[0].keys())
                header = options.get('delimiter', ',').join(keys)
                lines.append(f"{key_prefix} items[{len(value)}]{{{header}}}:")
                lines.append(encode_tabular_rows(value, indent_level + 1, options))
            else:
                lines.append(f"{key_prefix} items[{len(value)}]:")
                lines.append(encode_array(value, indent_level + 1, options))
        elif isinstance(value, dict):
            lines.append(key_prefix)
            lines.append(encode_object(value, indent_level + 1, options))
        else:
            lines.append(f"{key_prefix} {encode_value(value, 0, options)}")

    return '\n'.join(lines)

def encode_array(arr: List[Any], indent_level: int, options: Dict[str, Any]) -> str:
    if is_tabular_array(arr):
        return encode_tabular_array(arr, indent_level, options)
    
    indent_size = options.get('indent', 2)
    indent = ' ' * indent_size
    lines = []

    for item in arr:
        val = encode_value(item, indent_level, options)
        if isinstance(item, dict) and item is not None:
            val_lines = val.split('\n')
            first_line = val_lines[0]
            base_indent = indent * indent_level
            content = first_line.strip()
            val_lines[0] = f"{base_indent}- {content}"
            lines.append('\n'.join(val_lines))
        else:
            lines.append(f"{indent * indent_level}- {val.strip()}")

    return '\n'.join(lines)

def encode_tabular_rows(arr: List[Dict[str, Any]], indent_level: int, options: Dict[str, Any]) -> str:
    if not arr: return ""
    keys = list(arr[0].keys())
    delimiter = options.get('delimiter', ',')
    indent_size = options.get('indent', 2)
    indent_str = ' ' * (indent_size * indent_level)

    rows = []
    for item in arr:
        values = [encode_value(item[key], 0, options) for key in keys]
        rows.append(indent_str + delimiter.join(values))

    return '\n'.join(rows)

def encode_tabular_array(arr: List[Dict[str, Any]], indent_level: int, options: Dict[str, Any]) -> str:
    if not arr: return ""
    keys = list(arr[0].keys())
    delimiter = options.get('delimiter', ',')
    header = delimiter.join(keys)
    indent_size = options.get('indent', 2)
    indent = ' ' * indent_size
    prefix = (indent * indent_level) + f"items[{len(arr)}]{{{header}}}:"
    return prefix + '\n' + encode_tabular_rows(arr, indent_level + 1, options)

class Decoder:
    def __init__(self, toon: str, options: Dict[str, Any]):
        self.lines = toon.split('\n')
        self.index = 0
        self.options = options

    def decode(self) -> Any:
        self.skip_empty_lines()
        return self.parse_value(0)

    def skip_empty_lines(self):
        while self.index < len(self.lines):
            line = self.lines[self.index]
            if self.options.get('trim', True):
                line = line.strip()
            
            if not line or (self.options.get('comments', True) and line.startswith('#')):
                self.index += 1
            else:
                break

    def get_current_line(self) -> Optional[str]:
        if self.index < len(self.lines):
            return self.lines[self.index]
        return None

    def get_indent(self, line: str) -> int:
        indent = 0
        for char in line:
            if char == ' ':
                indent += 1
            elif char == '\t':
                indent += 4
            else:
                break
        return indent

    def parse_value(self, expected_indent: int) -> Any:
        line = self.get_current_line()
        if line is None:
            return None

        indent = self.get_indent(line)
        if indent < expected_indent:
            return None

        content = line[indent:].strip()

        # Handle markers
        marker_match = re.match(r'^items\[\d+\](\{.*?\})?:$', content)
        if marker_match:
            headers_str = marker_match.group(1)
            self.index += 1
            delimiter = self.options.get('delimiter', ',')
            
            new_expected_indent = indent + self.options.get('indent', 2)
            if headers_str:
                headers = [h.strip() for h in headers_str[1:-1].split(delimiter)]
                return self.parse_tabular(new_expected_indent, headers)
            else:
                return self.parse_array(new_expected_indent)

        if content.startswith('[') or content.startswith('- '):
            return self.parse_array(expected_indent)
        elif self.is_tabular_start(content):
            return self.parse_tabular(expected_indent)
        elif self.has_key(content):
            return self.parse_object(expected_indent)
        else:
            value = parse_primitive(content)
            self.index += 1
            return value

    def has_key(self, content: str) -> bool:
        s = content
        if s.startswith('- '):
            s = s[2:].strip()
        colon_idx = s.find(':')
        if colon_idx <= 0:
            return False
        before = s[:colon_idx].strip()
        # Basic check for a key
        return ' ' not in before and not re.match(r'^[-+]?\d', before) and not before.startswith('"') and '\n' not in before

    def is_tabular_start(self, content: str) -> bool:
        delimiter = self.options.get('delimiter', ',')
        return (
            delimiter in content and
            not self.has_key(content) and
            not content.startswith('"') and
            content not in ('true', 'false', 'null', 'undefined')
        )

    def parse_object(self, expected_indent: int, is_array_item: bool = False) -> Any:
        obj = {}
        first_line = self.get_current_line()
        has_braces = first_line and first_line.strip().startswith('{')
        if has_braces:
            self.index += 1

        first = True
        while self.index < len(self.lines):
            self.skip_empty_lines()
            line = self.get_current_line()
            if line is None:
                break

            indent = self.get_indent(line)
            if indent < expected_indent:
                break

            trimmed = line[indent:].strip()
            if has_braces and trimmed == '}':
                self.index += 1
                break

            if trimmed.startswith('- '):
                if not first and is_array_item:
                    break
                trimmed = trimmed[2:].strip()
            first = False

            colon_idx = trimmed.find(':')
            if colon_idx >= 0:
                key = unquote_string(trimmed[:colon_idx].strip())
                value_str = trimmed[colon_idx + 1:].strip()
                self.index += 1

                if value_str:
                    marker_match = re.match(r'^items\[\d+\](\{.*?\})?:$', value_str)
                    if marker_match:
                        headers_str = marker_match.group(1)
                        delimiter = self.options.get('delimiter', ',')
                        new_expected_indent = indent + self.options.get('indent', 2)
                        if headers_str:
                            headers = [h.strip() for h in headers_str[1:-1].split(delimiter)]
                            obj[key] = self.parse_tabular(new_expected_indent, headers)
                        else:
                            obj[key] = self.parse_array(new_expected_indent)
                    else:
                        obj[key] = parse_primitive(value_str)
                else:
                    nested_value = self.parse_value(indent + self.options.get('indent', 2))
                    if nested_value is not None:
                        obj[key] = nested_value
            elif trimmed:
                if is_array_item and not obj:
                    self.index += 1
                    return parse_primitive(trimmed)
                self.index += 1
            else:
                self.index += 1
        return obj

    def parse_array(self, expected_indent: int) -> List[Any]:
        arr = []
        first_line = self.get_current_line()
        has_brackets = first_line and first_line.strip().startswith('[')
        if has_brackets:
            self.index += 1

        while self.index < len(self.lines):
            self.skip_empty_lines()
            line = self.get_current_line()
            if line is None:
                break

            indent = self.get_indent(line)
            trimmed = line.strip()

            if has_brackets and trimmed == ']':
                self.index += 1
                break

            if indent < expected_indent:
                break

            if trimmed.startswith('- '):
                item = self.parse_object(indent, True)
                if item is not None:
                    arr.append(item)
            else:
                value = self.parse_value(expected_indent)
                if value is not None:
                    arr.append(value)
        return arr

    def parse_tabular(self, expected_indent: int, provided_headers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        delimiter = self.options.get('delimiter', ',')
        headers = []

        if provided_headers:
            headers = provided_headers
        else:
            header_line = self.get_current_line()
            if not header_line:
                return []
            header_indent = self.get_indent(header_line)
            header_content = header_line[header_indent:].strip()
            headers = [unquote_string(h.strip()) for h in header_content.split(delimiter)]
            self.index += 1

        rows = []
        while self.index < len(self.lines):
            self.skip_empty_lines()
            line = self.get_current_line()
            if line is None:
                break

            line_indent = self.get_indent(line)
            if line_indent < expected_indent:
                break

            content = line[line_indent:].strip()
            values = []
            current = content
            for _ in range(len(headers) - 1):
                idx = current.find(delimiter)
                if idx == -1:
                    break
                values.append(current[:idx])
                current = current[idx + 1:]
            values.append(current)

            if len(values) >= len(headers):
                obj = {}
                for h, v in zip(headers, values):
                    obj[h] = parse_primitive(v.strip())
                rows.append(obj)
            
            self.index += 1
        return rows

def parse_primitive(content: str) -> Any:
    if content == 'null': return None
    if content == 'true': return True
    if content == 'false': return False
    if content == 'undefined': return None # Python doesn't have undefined, use None
    if re.match(r'^-?\d+(\.\d+)?$', content):
        return float(content) if '.' in content else int(content)
    return unquote_string(content)

def unquote_string(s: str) -> str:
    if not (s.startswith('"') and s.endswith('"')):
        return s
    s = s[1:-1]
    s = s.replace('\\n', '\n')\
         .replace('\\r', '\r')\
         .replace('\\t', '\t')\
         .replace('\\"', '"')\
         .replace('\\\\', '\\')
    return s
