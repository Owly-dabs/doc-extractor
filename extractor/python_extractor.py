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
        tree = self.parser.parse(code.encode("utf8"))
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
                            return code.encode("utf8")[string_node.start_byte:string_node.end_byte].decode("utf8").strip()
                elif is_docstring_node(child):
                    string_node = child.children[0]
                    return code.encode("utf8")[string_node.start_byte:string_node.end_byte].decode("utf8").strip()
            return None

        def get_identifier(node):
            for child in node.children:
                if child.type == "identifier":
                    return code[child.start_byte:child.end_byte]
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