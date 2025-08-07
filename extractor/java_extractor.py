from tree_sitter_languages import get_parser
from typing import List, Dict
from .base import DocstringExtractor
from datamodels import Docstring


class JavaDocstringExtractor(DocstringExtractor):
    """
    Extracts Javadoc and line comments from Java source code using Tree-sitter.
    Supports class, interface, method, constructor, and field documentation.
    """

    def __init__(self):
        self._parser = get_parser("java")

    @property
    def parser(self):
        return self._parser

    @property
    def suffix(self) -> list[str]:
        return [".java"]

    def extract_docstrings(self, code: str) -> List[Docstring]:
        """
        Extracts Javadoc (`/** ... */`) and grouped line comments (`//`) from Java code.

        This method walks the Java AST and collects documentation comments
        preceding class, interface, method, field, and constructor declarations.

        Args:
            code (str): The Java source code as a string.

        Returns:
            List[Docstring]: A list of extracted docstrings in structured form.
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

                if prev.type == "block_comment":
                    if text.startswith("/**"):
                        return text  # Javadoc block
                    elif text.startswith("/*"):
                        break  # Non-doc block comment — skip
                elif prev.type == "line_comment":
                    if text.startswith("//"):
                        collected.insert(0, text)
                    else:
                        break
                elif prev.type in [";", "modifiers"]:
                    continue
                else:
                    break

            if collected:
                return "\n".join(collected)

            return None

        def get_node_name(node):
            if node.type == "identifier":
                return get_node_text(node)

            for child in node.children:
                name = get_node_name(child)
                if name != "<anonymous>":
                    return name

            return "<anonymous>"

        def traverse(node, parent_stack=None):
            if parent_stack is None:
                parent_stack = []

            is_scope = node.type in ["class_declaration", "interface_declaration"]

            if node.type in [
                "class_declaration",
                "interface_declaration",
                "method_declaration",
                "constructor_declaration",
                "field_declaration"
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
                if is_scope:
                    parent_stack.append(name)

            for child in node.children:
                traverse(child, parent_stack)

            if is_scope and parent_stack:
                parent_stack.pop()

        traverse(root_node)
        return docstrings