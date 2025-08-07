from tree_sitter_languages import get_parser
from typing import List, Dict
from .base import DocstringExtractor
from datamodels import Docstring


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