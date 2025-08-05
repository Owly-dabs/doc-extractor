from tree_sitter_languages import get_parser
from typing import List, Dict
from .base import DocstringExtractor


class JavaDocstringExtractor(DocstringExtractor):
    def __init__(self):
        self._parser = get_parser("java")

    @property
    def parser(self):
        return self._parser

    @property
    def suffix(self) -> list[str]:
        return [".java"]

    def extract_docstrings(self, code: str) -> List[Dict]:
        tree = self.parser.parse(code.encode("utf8"))
        root_node = tree.root_node
        docstrings = []

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
                        return text  # Prefer Javadoc-style block
                    elif text.startswith("/*"):
                        break  # Ignore non-doc block comment
                elif prev.type == "line_comment":
                    if text.startswith("//"):
                        collected.insert(0, text)
                    else:
                        break
                elif prev.type in [";", "modifiers"]:
                    continue  # skip syntactic clutter
                else:
                    break  # stop at unrelated nodes

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
                    docstrings.append({
                        "name": name,
                        "type": node.type.replace("_", " "),
                        "parent": parent_stack[-1] if parent_stack else None,
                        "docstring": doc
                    })
                if is_scope:
                    parent_stack.append(name)

            for child in node.children:
                traverse(child, parent_stack)

            if is_scope and parent_stack:
                parent_stack.pop()

        traverse(root_node)
        return docstrings
