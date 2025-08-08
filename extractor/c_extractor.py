from tree_sitter_languages import get_parser
from typing import List, Dict
from .base import DocstringExtractor
from datamodels import Docstring, Symbol


class CDocstringExtractor(DocstringExtractor):
    """
    Extracts documentation comments from C source files using Tree-sitter.
    Handles function declarations, struct definitions, typedefs, and fields.
    """

    def __init__(self):
        self._parser = get_parser("c")

    @property
    def parser(self):
        return self._parser

    @property
    def suffix(self) -> list[str]:
        return [".c", ".h"]

    def extract_docstrings(self, code: str) -> List[Docstring]:
        """
        Extracts block (`/* ... */`) and grouped `//` comments from C code.

        Traverses the syntax tree to extract doc comments that appear before:
        - function definitions
        - declarations
        - struct and typedef definitions
        - field declarations

        Returns:
            List[Docstring]: A list of extracted documentation objects.
        """
        tree = self.parser.parse(code.encode("utf8"))
        root_node = tree.root_node
        docstrings: List[Docstring] = []

        def get_node_text(node):
            return code.encode("utf8")[node.start_byte:node.end_byte].decode("utf8").strip()

        def extract_leading_doc_comment(node):
            if not hasattr(node, "parent") or node.parent is None:
                return None

            siblings = node.parent.children
            idx = siblings.index(node)
            collected = []

            for i in reversed(range(0, idx)):
                prev = siblings[i]
                text = get_node_text(prev)

                if prev.type == "comment":
                    if text.startswith("/*"):
                        return text
                    elif text.startswith("//"):
                        collected.insert(0, text)
                    else:
                        break
                elif prev.type in [";", "}"]:
                    continue
                else:
                    break

            if collected:
                return "\n".join(collected)

            return None

        def get_node_name(node):
            """Recursively find the most likely symbol name from C declarations."""
            if node.type in ["identifier", "field_identifier"]:
                return get_node_text(node)

            if node.type == "type_definition":
                struct_node = next((c for c in node.children if c.type == "struct_specifier"), None)
                if struct_node:
                    return get_node_name(struct_node)

            if node.type == "struct_specifier":
                for child in node.children:
                    if child.type in ["type_identifier", "identifier"]:
                        return get_node_text(child)

            for child in node.children:
                if child.type == "function_declarator":
                    return get_node_name(child)

            for child in node.children:
                name = get_node_name(child)
                if name != "<anonymous>":
                    return name

            return "<anonymous>"

        def traverse(node, parent_stack=None):
            if parent_stack is None:
                parent_stack = []

            is_parent_scope = node.type in ["struct_specifier", "type_definition", "typedef_definition"]

            if node.type in [
                "function_definition",
                "declaration",
                "field_declaration",
                "struct_specifier",
                "type_definition",
                "typedef_definition",
            ]:
                doc = extract_leading_doc_comment(node)
                name = get_node_name(node)
                if doc:
                    docstrings.append(Docstring(
                        name=name,
                        type=node.type.replace("_", " "),
                        parent=parent_stack[-1] if parent_stack else None,
                        docstring=doc
                    ))

                if is_parent_scope:
                    parent_stack.append(name)

            for child in node.children:
                traverse(child, parent_stack)

            if is_parent_scope and parent_stack:
                parent_stack.pop()

        traverse(root_node)
        return docstrings

    def extract_used_symbols(self, code: str) -> List[Symbol]:
        """
        Extracts usage of symbols that would be documented by extract_docstrings.
        Focuses on functions, structs, typedefs, and their members.
        
        Args:
            code (str): The C source code
            
        Returns:
            List[Symbol]: List of used symbols with name, parent, and type
        """
        tree = self.parser.parse(code.encode("utf8"))
        root = tree.root_node
        used: List[Symbol] = []

        def get_node_text(node):
            return code.encode("utf8")[node.start_byte:node.end_byte].decode("utf8").strip()

        def walk(node):
            # Function calls - matches function_definition in docstrings
            if node.type == "call_expression":
                fn_node = node.child_by_field_name("function")
                if fn_node and fn_node.type == "identifier":
                    name = get_node_text(fn_node)
                    used.append(Symbol(
                        name=name,
                        parent=None,
                        type="function"
                    ))
            
            # Struct usage - matches struct_specifier in docstrings
            elif node.type == "struct_specifier":
                # Only count when used as type (not definitions)
                if node.parent and node.parent.type not in ["type_definition", "field_declaration"]:
                    name = get_node_text(node.child_by_field_name("name"))
                    if name:
                        used.append(Symbol(
                            name=name,
                            parent=None,
                            type="struct"
                        ))
            
            # Typedef usage - matches type_definition/typedef_definition in docstrings
            elif node.type == "type_identifier":
                # Skip if part of a declaration/definition
                if node.parent.type not in ["type_definition", "typedef_definition", "field_declaration"]:
                    name = get_node_text(node)
                    used.append(Symbol(
                        name=name,
                        parent=None,
                        type="typedef"
                    ))
            
            # Struct member access - matches field_declaration in docstrings
            elif node.type == "field_expression":
                field_node = node.child_by_field_name("field")
                parent_node = node.child_by_field_name("argument")
                if field_node and parent_node:
                    parent = get_node_text(parent_node)
                    name = get_node_text(field_node)
                    used.append(Symbol(
                        name=name,
                        parent=parent,
                        type="field"
                    ))
            
            # Function pointer calls
            elif node.type == "pointer_expression" and node.parent.type == "call_expression":
                ptr_node = node.child_by_field_name("argument")
                if ptr_node and ptr_node.type == "identifier":
                    name = get_node_text(ptr_node)
                    used.append(Symbol(
                        name=name,
                        parent=None,
                        type="function_pointer"
                    ))

            # Recurse through children
            for child in node.children:
                walk(child)

        walk(root)
        return used