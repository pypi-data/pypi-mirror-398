import os
import ctypes
from tree_sitter import Language, Parser, Query, QueryCursor
from . import _binding

class BSVProjectParser:
    def __init__(self, lib_path, search_paths):
        lib = ctypes.cdll.LoadLibrary(lib_path)
        language_function = getattr(lib, "tree_sitter_bsv")
        language_function.restype = ctypes.c_void_p
        self.language = Language(language_function())
        self.parser = Parser(self.language)
        self.search_paths = search_paths
        self.visited = set()
        self.results = {
            "variables": {}, "structs": {}, "enums": {}, 
            "functions": {}, "interfaces": {}
        }

    def _get_text(self, node):
        return node.text.decode('utf8') if node else None

    def parse_recursive(self, filename,top=False):
        self.top=top
        filepath = self._resolve(filename)
        print(filepath,filename)
        if not filepath or filepath in self.visited:
            return
        self.visited.add(filepath)

        with open(filepath, 'rb') as f:
            tree = self.parser.parse(f.read())
            root = tree.root_node
            
            # v0.24 API: Define the Query object
            import_query = Query(self.language, "(imports filename: (identifier) @fname)")
            cursor = QueryCursor(import_query)
            captures = cursor.captures(root)
            
            if "fname" in captures:
                for node in captures["fname"]:
                    self.parse_recursive(self._get_text(node))

            self._extract_definitions(root)
    def _extract_definitions(self, root):
        for node in root.children:
            # Structs and Enums are usually wrapped in a 'typedefs' node
            if node.type == 'typedefs':
                inner = node.named_children[0]

                if inner.type == 'typedefStruct':
                    name = self._get_text(inner.child_by_field_name('struct_name'))
                    fields = []
                    # Use named_children to ignore '{', '}', and ','
                    for c in inner.named_children:
                        if c.type == 'declr':
                            f_type = self._get_text(c.child_by_field_name('type'))
                            f_name = self._get_text(c.child_by_field_name('variable_name'))
                            if f_name:
                                fields.append({f_name: f_type})
                    self.results["structs"][name] = fields

                elif inner.type == 'typedefEnum':
                    name = self._get_text(inner.child_by_field_name('enum_name'))
                    items = []
                    for c in inner.named_children:
                        if c.type == 'enumItem':
                            k = self._get_text(c.child_by_field_name('key'))
                            v = self._get_text(c.child_by_field_name('value'))
                            items.append({k: v})
                    self.results["enums"][name] = items

            # To capture variables from your module:
            # We need to look inside moduleDef -> moduleStmt -> assignment
            elif node.type == 'moduleDef' and self.top:
                for stmt in node.named_children:
                    if stmt.type == 'moduleStmt':
                        actual_stmt = stmt.named_children[0]
                        if actual_stmt.type == 'assignment':
                            self._extract_assignment(actual_stmt)

            # Top-level assignments
            elif node.type == 'assignment':
                self._extract_assignment(node)

    def _extract_assignment(self, node):
        v_node = node.child_by_field_name('variable_name')
        t_node = node.child_by_field_name('type')
        #print("DBG",v_node,t_node,node)
        if v_node:
            name = self._get_text(v_node)
            # If 'let' is used, type node might be missing
            dtype = self._get_text(t_node) if t_node else "inferred (let)"
            self.results["variables"][name] = f"{dtype}"

    def _resolve(self, name):
        for p in self.search_paths:
            full = os.path.join(p, name if name.endswith('.bsv') else f"{name}.bsv")
            if os.path.exists(full): return full
        print(f"{name=},{self.search_paths}")
        return None

# Usage
if __name__ == "__main__":
    # Update search_paths to your actual project directory
    analyzer = BSVProjectParser('./libtree-sitter-bsv.so', ['./test/corpus','/prj/hdl/veevx/hyperbus2/bsv'])
    #analyzer.parse_recursive('example.bsv')
    analyzer.parse_recursive('hyperbus2.bsv',top=True)
    
    import json
    print(json.dumps(analyzer.results, indent=2))
