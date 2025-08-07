from tree_sitter_languages import get_parser
from pathlib import Path
from typing import List, Dict
from .base import DocstringExtractor
from datamodels import Docstring, Symbol


class PythonDocstringExtractor(DocstringExtractor):
    def __init__(self):
        self.parser = get_parser("python")

    @property
    def suffix(self) -> list[str]:
        return [".py"]

    def extract_docstrings(self, code: str) -> List[Docstring]:
        """
        Extracts docstrings from a Python source string.

        This method parses the source code using Tree-sitter and traverses the AST to extract
        docstrings from module, class, and function definitions. Each docstring is returned as
        a `Docstring` object with metadata about its symbol.

        Args:
            code (str): The Python source code to analyze.

        Returns:
            List[Docstring]: A list of extracted docstrings.
        """
        byte_code = code.encode("utf8")
        tree = self.parser.parse(byte_code)
        root_node = tree.root_node
        docstrings: List[Docstring] = []

        def is_docstring_node(node):
            return (
                node.type == "expression_statement"
                and node.child_count == 1
                and node.children[0].type == "string"
            )

        def extract_from_parent(node):
            for child in node.children:
                if child.type == "block":
                    for block_child in child.children:
                        if is_docstring_node(block_child):
                            string_node = block_child.children[0]
                            return byte_code[string_node.start_byte:string_node.end_byte].decode("utf8").strip()
                elif is_docstring_node(child):
                    string_node = child.children[0]
                    return byte_code[string_node.start_byte:string_node.end_byte].decode("utf8").strip()
            return None

        def get_identifier(node):
            name_node = node.child_by_field_name("name")
            if name_node:
                return byte_code[name_node.start_byte:name_node.end_byte].decode("utf8").strip()
            return "<unknown>"

        def traverse(node, parent_stack=None):
            if parent_stack is None:
                parent_stack = []

            if node.type in ["function_definition", "class_definition", "module"]:
                docstring = extract_from_parent(node)
                name = "<module>" if node.type == "module" else get_identifier(node)

                if docstring:
                    docstrings.append(Docstring(
                        name=name,
                        parent=parent_stack[-1] if parent_stack else None,
                        type=node.type.replace("_definition", ""),
                        docstring=docstring
                    ))

                if node.type != "module":
                    parent_stack.append(name)

            for child in node.children:
                traverse(child, parent_stack)

            if node.type in ["function_definition", "class_definition"] and parent_stack:
                parent_stack.pop()

        traverse(root_node)
        return docstrings

    def extract_used_symbols(self, code: str) -> List[Symbol]:
        """
        Extracts symbol usage from a Python source string.

        This method identifies function and class symbols that are *called* within the source code,
        returning them as `Symbol` objects with name, parent (if applicable), and type inferred
        from syntax or casing.

        Args:
            code (str): The Python source code to analyze.

        Returns:
            List[Symbol]: A list of function/class symbols used in the code.
        """
        tree = self.parser.parse(code.encode("utf8"))
        root = tree.root_node
        used: List[Symbol] = []

        def get_node_text(node):
            return code.encode("utf8")[node.start_byte:node.end_byte].decode("utf8").strip()

        def walk(node):
            if node.type == "call":
                fn_node = node.child_by_field_name("function")

                if fn_node is None:
                    return

                if fn_node.type == "attribute":
                    object_node = fn_node.child_by_field_name("object")
                    method_node = fn_node.child_by_field_name("attribute")

                    if object_node and method_node:
                        parent = get_node_text(object_node)
                        name = get_node_text(method_node)
                        used.append(Symbol(
                            name=name,
                            parent=parent,
                            type="function"
                        ))

                elif fn_node.type == "identifier":
                    name = get_node_text(fn_node)
                    symbol_type = "class" if name and name[0].isupper() else "function"
                    used.append(Symbol(
                        name=name,
                        parent=None,
                        type=symbol_type
                    ))

            for child in node.children:
                walk(child)

        walk(root)
        return used
