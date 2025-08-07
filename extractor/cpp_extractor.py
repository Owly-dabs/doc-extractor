from tree_sitter_languages import get_parser
from typing import List, Dict
from .base import DocstringExtractor
from datamodels import Docstring


class CppDocstringExtractor(DocstringExtractor):
    """
    Extracts Doxygen-style documentation comments from C++ source code using Tree-sitter.
    Supports functions, fields, classes, structs, and declarations.
    """

    def __init__(self):
        self._parser = get_parser("cpp")

    @property
    def parser(self):
        return self._parser

    @property
    def suffix(self) -> list[str]:
        return [".cpp", ".hpp", ".cc", ".hh"]

    def extract_docstrings(self, code: str) -> List[Docstring]:
        """
        Extracts Doxygen-style (`/** ... */`, `/*! ... */`) or grouped `//`/`///` comments
        from C++ source code.

        Parses the syntax tree and extracts comments above:
        - function definitions
        - declarations
        - class/struct definitions
        - field declarations

        Returns:
            List[Docstring]: A list of structured docstring objects.
        """
        tree = self.parser.parse(code.encode("utf8"))
        root_node = tree.root_node
        docstrings: List[Docstring] = []

        def get_node_text(node):
            return code.encode("utf8")[node.start_byte:node.end_byte].decode("utf8").strip()

        def extract_leading_doc_comment(node):
            """Extract /** */, /*! */, ///, or grouped // comments directly above the node."""
            if not hasattr(node, "parent") or node.parent is None:
                return None

            siblings = node.parent.children
            idx = siblings.index(node)
            collected = []

            for i in reversed(range(0, idx)):
                prev = siblings[i]
                text = get_node_text(prev)

                if prev.type == "comment":
                    if text.startswith("/**") or text.startswith("/*!"):
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
            """Recursively find the first identifier-like name in a node's subtree."""
            if node.type in ["identifier", "field_identifier", "type_identifier"]:
                return get_node_text(node)

            for child in node.children:
                name = get_node_name(child)
                if name != "<anonymous>":
                    return name

            return "<anonymous>"

        def traverse(node, parent_stack=None):
            if parent_stack is None:
                parent_stack = []

            is_parent_scope = node.type in ["class_specifier", "struct_specifier"]

            if node.type in [
                "function_definition",
                "declaration",
                "field_declaration",
                "class_specifier",
                "struct_specifier",
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