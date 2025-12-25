import json
from typing import List, Optional


class TreeNode:
    def __init__(self, name, value, node_type, selected_models=None, left=None, right=None):
        # if node_type not in ["root", "imp", "automl", "hbd", "rsp", "clf"]:
        #     raise ValueError("Node type {} not supported in TreeNode".format(node_type))
        self.node_name = name
        self.node_type = node_type
        self.left = left
        self.right = right
        self.max_leaf_value = value  # Initialize max_leaf_value with node value
        self.max_value_pipe = []
        self.index = {}
        self.available_models = selected_models if selected_models else []

class BinaryTree:
    def __init__(self, schema_paths: Optional[List[List[str]]] = None):
        self.schema_paths = schema_paths or []
        self.leaf_node_types = {path[-1] for path in self.schema_paths} if self.schema_paths else set()
        self.root = TreeNode("root", -1, "root")

    def _assert_schema_configured(self):
        if not self.schema_paths:
            raise ValueError("BinaryTree schema_paths are not configured for schema-aware operations.")

    def insert(self, name, value, node_type, parent_type, selected_models=None):
        node = TreeNode(name, value, node_type, selected_models)

        self._search_insert(parent_type, node, self.root)

    def _search_insert(self, parent_type, child, parent):
        if parent is None:
            return
        if parent.node_type != parent_type:
            self._search_insert(parent_type, child, parent.left)
            self._search_insert(parent_type, child, parent.right)
        else:
            self._insert(parent, child)

    def _insert(self, parent: TreeNode, child: TreeNode):
        if parent.left is None:
            parent.left = child
        elif parent.right is None:
            if parent.left.max_leaf_value >= child.max_leaf_value:
                parent.right = child
            else:
                parent.right = parent.left
                parent.left = child
        else:
            self.print_tree()
            raise ValueError("Tree node is full, no more insert")

    @staticmethod
    def _find_child_by_type(parent: TreeNode, node_type: str) -> Optional[TreeNode]:
        """Return the child of parent with the given node_type, if present."""
        for child in (parent.left, parent.right):
            if child and child.node_type == node_type:
                return child
        return None

    def insert_path(self, components: List[str], node_types: List[str]):
        """
        Insert a path of components following the provided node_types sequence.
        Reuses existing nodes with the same node_type under the current parent.
        """
        if len(components) != len(node_types):
            raise ValueError("Components and node_types must have the same length.")
        if self.schema_paths and node_types not in self.schema_paths:
            raise ValueError(f"Path {node_types} is not allowed by the configured schema.")

        parent = self.root
        for name, node_type in zip(components, node_types):
            existing = self._find_child_by_type(parent, node_type)
            if existing:
                parent = existing
                continue
            child = TreeNode(name, -1, node_type)
            self._insert(parent, child)
            parent = child

    def _search_recursive(self, node, node_type, max_value=None, node_name=None):
        """ Search for node_type in BinaryTree
            if max_value is not None, replace the max_leaf_value for all the element of the path

        Return
        ----------
        The path found
        """
        if node is None:
            return None

        if node.node_type == node_type:
            if max_value is not None:
                node.max_leaf_value = max_value
                node.node_name = node_name
            return [node.node_name]

        for child in [node.left, node.right]:
            if child:
                path = self._search_recursive(child, node_type, max_value, node_name)
                if path:
                    if max_value is not None:
                        node.max_leaf_value = max(node.left.max_leaf_value if node.left else -1,
                                                  node.right.max_leaf_value if node.right else -1)
                        self._ensure_order(node)
                    return [node.node_name] + path
        return None

    @staticmethod
    def _ensure_order(node):
        """Ensure that left child always has the largest max_leaf_value."""
        if node.left and node.right and node.left.max_leaf_value < node.right.max_leaf_value:
            node.left, node.right = node.right, node.left

    def replace(self, node_type, max_value, node_name):
        """ Replace the max_leaf_value for all the element of the path """
        # node = self._search(node_type, max_value)
        node = self._search_recursive(self.root, node_type, max_value, node_name=node_name)
        if node is None:
            return None
        self.root.max_leaf_value = max_value

    def _search_node(self, node: TreeNode, target_type) -> TreeNode:
        """Search for a given node type downward from a node in a tree"""
        if node is None:
            return None
        if node.node_type == target_type:
            return node
        else:
            left = self._search_node(node.left, target_type)
            if left:
                return left

            right = self._search_node(node.right, target_type)
            if right:
                return right
        return None


    def update_pipe(self, pipe, value):
        """ check if sub-branch of the  BinaryTree need to be updated or not

        Return
        ----------
        Ture : if it updated the BinaryTree
        False : if it didn't update the BinaryTree
        """
        schema_path = self._match_schema_path(len(pipe))
        target_node_type = schema_path[-1]
        target_node = self._search_node(self.root, target_node_type)
        if target_node is None:
            raise ValueError(f"Tree node type {target_node_type} not found for update.")
        if target_node.max_leaf_value < value:
            for component, node_type in zip(pipe, schema_path):
                self.replace(node_type, value, component)
            return True
        return False

    def best_pipe(self):
        node = self.root.left
        pipe = []
        while node is not None:
            pipe.append(node.node_name)
            node = node.left

        return pipe

    def best_node_types(self):
        node = self.root.left
        node_types = []
        while node is not None:
            node_types.append(node.node_type)
            node = node.left

        return node_types

    def sub_best_pipe(self, node_type="automl"):
        """ Search for the best pipe built with node_type """
        node = self._search_node(self.root, target_type=node_type)
        pipe = []
        while node is not None:
            pipe.append(node.node_name)
            node = node.left
        return pipe

    def build_pipe(self, node_type):
        """Build the pipeline with the last element of the pipeline as node_type"""
        self._assert_schema_configured()
        if node_type not in self.leaf_node_types:
            raise ValueError(f"{node_type} is not a valid leaf node_type for the configured schema.")

        result = self._search_recursive(self.root, node_type=node_type)
        if not result:
            raise ValueError(f"Unable to build pipe for node_type {node_type}")
        return result[1:]

    def print_tree(self):
        print("----------------")
        self._print_tree_recursive(self.root, 0)
        print("----------------")

    def _print_tree_recursive(self, node, level):
        if node is not None:
            self._print_tree_recursive(node.right, level + 1)
            print("     " * level + str(node.node_name) + " " + str(node.node_type) + " (" + str(node.max_leaf_value) + ")" + str(node.available_models))
            self._print_tree_recursive(node.left, level + 1)

    def serialize(self):
        """Serialize the tree to a JSON string"""
        def serialize_node(node):
            if node is None:
                return None
            return {
                'name': node.node_name,
                'value': node.max_leaf_value,
                'type': node.node_type,
                'selected_models': node.available_models,
                'left': serialize_node(node.left),
                'right': serialize_node(node.right)
            }

        return json.dumps(serialize_node(self.root), indent=4)

    def save_to_file(self, filename):
        """Save the serialized tree to a JSON file."""
        serialized_tree = self.serialize()
        with open(filename, 'w') as file:
            file.write(serialized_tree)

    def _match_schema_path(self, path_length: int) -> List[str]:
        """Return the schema path matching a given length."""
        self._assert_schema_configured()
        candidates = [path for path in self.schema_paths if len(path) == path_length]
        if not candidates:
            raise ValueError(f"No schema paths match pipeline length {path_length}")
        if len(candidates) > 1:
            raise ValueError(f"Ambiguous schema paths for pipeline length {path_length}")
        return candidates[0]

    @classmethod
    def load_from_file(cls, filename, schema_paths: Optional[List[List[str]]] = None):
        """Load a tree from a JSON file and deserialize it."""
        with open(filename, 'r') as file:
            serialized_tree = file.read()
        return cls.deserialize(serialized_tree, schema_paths=schema_paths)

    @classmethod
    def deserialize(cls, data, schema_paths: Optional[List[List[str]]] = None):
        """Deserialize the JSON string to reconstruct the tree."""
        def deserialize_node(node_data):
            if node_data is None:
                return None
            node = TreeNode(node_data['name'], node_data['value'], node_data['type'], node_data['selected_models'])
            node.left = deserialize_node(node_data['left'])
            node.right = deserialize_node(node_data['right'])
            return node

        data = json.loads(data)
        root = deserialize_node(data)
        tree = cls(schema_paths=schema_paths)
        tree.root = root
        return tree


if __name__ == "__main__":
    schema = [["imp", "rsp", "clf"], ["imp", "hbd"], ["automl"]]
    tree = BinaryTree(schema_paths=schema)
    tree.insert_path(["mean", "smote", "svm"], ["imp", "rsp", "clf"])
    tree.insert_path(["median", "autosmote"], ["imp", "hbd"])
    tree.insert_path(["autosklearn"], ["automl"])
    tree.print_tree()
    tree.save_to_file("test.json")

    load_tree = BinaryTree.load_from_file("test.json", schema_paths=schema)
    load_tree.print_tree()
