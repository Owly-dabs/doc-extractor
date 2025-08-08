from tree_sitter_languages import get_parser
from typing import List, Dict
from .base import DocstringExtractor
from datamodels import Docstring, Symbol


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
            """Recursively find the first identifier-like name in a node's subtree."""
            if node.type in ["identifier", "field_identifier", "type_identifier", "namespace_identifier"]:
                return get_node_text(node)

            for child in node.children:
                name = get_node_name(child)
                if name != "<anonymous>":
                    return name

            return "<anonymous>"

        def traverse(node, parent_stack=None):
            if parent_stack is None:
                parent_stack = []

            is_parent_scope = node.type in ["class_specifier", "struct_specifier", "namespace_definition"]
            
            # Handle namespace aliases (they have different structure)
            if node.type == "namespace_alias":
                doc = extract_leading_doc_comment(node)
                name = get_node_name(node)
                if doc:
                    docstrings.append(Docstring(
                        name=name,
                        type="namespace",
                        parent=parent_stack[-1] if parent_stack else None,
                        docstring=doc
                    ))
            
            # Handle namespace definitions
            elif node.type == "namespace_definition":
                doc = extract_leading_doc_comment(node)
                name = get_node_name(node)
                if doc:
                    docstrings.append(Docstring(
                        name=name,
                        type="namespace",
                        parent=parent_stack[-1] if parent_stack else None,
                        docstring=doc
                    ))
                
                # Add to parent stack before traversing children
                parent_stack.append(name)
                
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

    def extract_used_symbols(self, code: str) -> List[Symbol]:
        """
        Extracts used symbols (functions, methods, classes, namespaces) from C++ code.
        
        Identifies:
        - Function calls (including namespace-qualified)
        - Method calls (member functions)
        - Class instantiations (via new or constructor calls)
        - Template instantiations
        - Namespace usage
        
        Args:
            code (str): The C++ source code
            
        Returns:
            List[Symbol]: List of used symbols with name, parent, and type
        """
        tree = self.parser.parse(code.encode("utf8"))
        root = tree.root_node
        used: List[Symbol] = []

        def get_node_text(node):
            return code.encode("utf8")[node.start_byte:node.end_byte].decode("utf8").strip()

        def walk(node):
            # Function calls: foo(), std::cout()
            if node.type == "call_expression":
                fn_node = node.child_by_field_name("function")
                
                if fn_node is None:
                    return
                    
                # Handle namespace/class qualified calls (std::string, Foo::bar)
                if fn_node.type == "qualified_identifier":
                    parts = []
                    current = fn_node
                    while current.type == "qualified_identifier":
                        parts.insert(0, get_node_text(current.child_by_field_name("name")))
                        current = current.child_by_field_name("scope")
                    
                    if len(parts) > 1:
                        used.append(Symbol(
                            name=parts[-1],
                            parent="::".join(parts[:-1]),
                            type="function" if parts[-1][0].islower() else "method"
                        ))
                    else:
                        used.append(Symbol(
                            name=parts[0],
                            parent=None,
                            type="function"
                        ))
                
                # Regular function calls
                elif fn_node.type == "identifier":
                    name = get_node_text(fn_node)
                    used.append(Symbol(
                        name=name,
                        parent=None,
                        type="function"
                    ))
            
            # Method calls: obj.method(), ptr->method()
            elif node.type == "field_expression":
                object_node = node.child_by_field_name("argument")
                field_node = node.child_by_field_name("field")
                
                if object_node and field_node:
                    parent = get_node_text(object_node)
                    name = get_node_text(field_node)
                    used.append(Symbol(
                        name=name,
                        parent=parent,
                        type="function"
                    ))
            
            # Constructor calls: Foo(), new Foo()
            elif node.type in ["new_expression", "constructor_init"]:
                type_node = node.child_by_field_name("type")
                if type_node:
                    name = get_node_text(type_node)
                    used.append(Symbol(
                        name=name,
                        parent=None,
                        type="class"
                    ))
            
            # Template instantiations: std::vector<int>
            elif node.type == "template_type":
                type_node = node.child_by_field_name("name")
                if type_node:
                    name = get_node_text(type_node)
                    used.append(Symbol(
                        name=name,
                        parent=None,
                        type="template"
                    ))
            
            # Using declarations: using namespace std;
            elif node.type == "using_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = get_node_text(name_node)
                    used.append(Symbol(
                        name=name,
                        parent=None,
                        type="namespace"
                    ))
            
            # Recurse through children
            for child in node.children:
                walk(child)

        walk(root)
        return used