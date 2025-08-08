from tree_sitter_languages import get_parser
from typing import List, Dict
from .base import DocstringExtractor
from datamodels import Docstring, Symbol


class JavaScriptDocstringExtractor(DocstringExtractor):
    """
    Extracts documentation comments from JavaScript source code using Tree-sitter.
    """

    def __init__(self):
        self._parser = get_parser("javascript")

    @property
    def parser(self):
        return self._parser

    @property
    def suffix(self) -> list[str]:
        return [".js", ".jsx"]

    def extract_docstrings(self, code: str) -> List[Docstring]:
        """
        Extracts JSDoc-style (`/** ... */`) and grouped `//` comments from JavaScript code.

        This method parses the source into an AST and extracts documentation for:
        - Function declarations
        - Method definitions
        - Class declarations
        - Exported arrow and function expressions
        - Variable declarations with functions

        Returns:
            List[Docstring]: A list of structured docstring records.
        """
        tree = self.parser.parse(code.encode("utf8"))
        root_node = tree.root_node
        docstrings: List[Docstring] = []
        exported_identifiers = set()

        def get_node_text(node):
            return code.encode("utf8")[node.start_byte:node.end_byte].decode("utf8").strip()

        def extract_leading_doc_comment(node):
            def find_leading_comment_among_siblings(target_node):
                if not hasattr(target_node, "parent") or target_node.parent is None:
                    return None

                siblings = target_node.parent.children
                idx = siblings.index(target_node)
                collected = []

                for i in reversed(range(0, idx)):
                    prev = siblings[i]
                    text = get_node_text(prev)
                    if prev.type == "comment":
                        if text.startswith("/**"):
                            return text
                        elif text.startswith("//"):
                            collected.insert(0, text)
                        else:
                            break
                    elif prev.type in [";", "}"]:
                        continue
                    else:
                        break

                return "\n".join(collected) if collected else None

            comment = find_leading_comment_among_siblings(node)
            if comment:
                return comment

            parent = node.parent
            while parent is not None and parent.type in ["export_statement", "lexical_declaration"]:
                comment = find_leading_comment_among_siblings(parent)
                if comment:
                    return comment
                parent = parent.parent

            return None

        def get_node_name(node):
            if node.type in ["identifier", "type_identifier", "property_identifier"]:
                return get_node_text(node)
            for child in node.children:
                name = get_node_name(child)
                if name != "<anonymous>":
                    return name
            return "<anonymous>"

        def collect_exported_identifiers(node):
            if node.type == "export_statement":
                for child in node.children:
                    if child.type == "export_clause":
                        for ident in child.children:
                            if ident.type == "identifier":
                                exported_identifiers.add(get_node_text(ident))

        def extract_variable_function_doc(node, parent_stack):
            results = []
            for declarator in node.children:
                if declarator.type != "variable_declarator":
                    continue

                identifier_node = next((c for c in declarator.children if c.type == "identifier"), None)
                value_node = next((c for c in declarator.children if c.type in ["arrow_function", "function"]), None)

                if identifier_node and value_node:
                    identifier_name = get_node_text(identifier_node)
                    if identifier_name not in exported_identifiers:
                        continue

                    doc = extract_leading_doc_comment(declarator)
                    if doc:
                        results.append(Docstring(
                            name=identifier_name,
                            type="arrow function" if value_node.type == "arrow_function" else "function expression",
                            parent=parent_stack[-1] if parent_stack else None,
                            docstring=doc
                        ))
            return results

        def traverse(node, parent_stack=None):
            if parent_stack is None:
                parent_stack = []

            is_scope = node.type == "class_declaration"

            if node.type in ["function_declaration", "method_definition", "class_declaration"]:
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

            elif node.type == "variable_declaration":
                docstrings.extend(extract_variable_function_doc(node, parent_stack))

            elif node.type == "export_statement":
                collect_exported_identifiers(node)
                for child in node.children:
                    traverse(child, parent_stack)
                return

            for child in node.children:
                traverse(child, parent_stack)

            if is_scope and parent_stack:
                parent_stack.pop()

        traverse(root_node)
        return docstrings


    def extract_used_symbols(self, code: str) -> List[Symbol]:
        """
        Extracts used symbols (functions, methods, classes) from a TypeScript code snippet.

        This method identifies identifiers and member expressions used in function calls,
        constructor calls, and method invocations, and returns them as `Symbol` objects.

        Args:
            code (str): The TypeScript source code.

        Returns:
            List[Symbol]: A list of used symbols with name, parent, and type.
        """
        tree = self.parser.parse(code.encode("utf8"))
        root = tree.root_node
        used: List[Symbol] = []

        def get_node_text(node):
            return code.encode("utf8")[node.start_byte:node.end_byte].decode("utf8").strip()

        def walk(node):
            # function or method call: foo(), obj.method()
            if node.type == "call_expression":
                fn_node = node.child_by_field_name("function")

                if fn_node is None:
                    return

                if fn_node.type == "member_expression":
                    object_node = fn_node.child_by_field_name("object")
                    property_node = fn_node.child_by_field_name("property")

                    if object_node and property_node:
                        parent = get_node_text(object_node)
                        name = get_node_text(property_node)
                        used.append(Symbol(
                            name=name,
                            parent=parent,
                            type="method"
                        ))

                elif fn_node.type == "identifier":
                    name = get_node_text(fn_node)
                    # Simple heuristic: Capitalized = class constructor
                    symbol_type = "class" if name and name[0].isupper() else "function"
                    used.append(Symbol(
                        name=name,
                        parent=None,
                        type=symbol_type
                    ))

            # constructor usage: new Foo()
            elif node.type == "new_expression":
                constructor_node = node.child_by_field_name("constructor")
                if constructor_node and constructor_node.type == "identifier":
                    name = get_node_text(constructor_node)
                    used.append(Symbol(
                        name=name,
                        parent=None,
                        type="class"
                    ))

            for child in node.children:
                walk(child)

        walk(root)
        return used