from itertools import combinations

from schemdraw.parsing import logic_parser

BASE_OPERATIONS = {
    "not": lambda x: not x,
    "or": lambda x, y: x or y,
    "nor": lambda x, y: not (x or y),
    "xor": lambda x, y: x != y,
    "and": lambda x, y: x and y,
    "nand": lambda x, y: not (x and y),
    "implies": lambda x, y: not x or y,
    "equals": lambda x, y: x == y,
    "xnor": lambda x, y: not (x != y),
}

OPERATION_ALIASES = {
    "not": ["not", "-", "~"],
    "or": ["or"],
    "nor": ["nor"],
    "xor": ["xor", "!="],
    "xnor": ["xnor"],
    "and": ["and"],
    "nand": ["nand"],
    "implies": ["=>", "implies"],
    "equals": ["="],
}

SINGLE_OPERAND_OPS = ("not", "~", "-")

DOUBLE_OPERAND_OPS = (
    "and",
    "nand",
    "or",
    "nor",
    "xor",
    "xnor",
    "=>",
    "implies",
    "=",
    "!=",
)


class Node:
    def __init__(
        self, left, right, gate, label, is_leaf_node: bool, value=None
    ) -> None:
        self.left = left
        self.right = right
        self.gate = gate
        self.label = label
        self.is_leaf_node = is_leaf_node
        self.value = value

    def representation(self):
        left_notation = self.left.get_value_or_label() if self.left else ""
        right_notation = self.right.get_value_or_label() if self.right else ""
        gate = self.gate if self.gate else ""
        label = self.label
        value = self.value if self.value else ""
        is_leaf_node = self.is_leaf_node
        return (left_notation, right_notation, gate, label, is_leaf_node, value)

    def get_value_or_label(self):
        if self.is_leaf_node:
            return self.value
        else:
            return self.label

    def evaluate_given_inputs(self, inputs, faulty_set):

        if self.is_leaf_node:
            return inputs[self.value]

        left_value = self.left.evaluate_given_inputs(inputs, faulty_set)

        if self.gate in DOUBLE_OPERAND_OPS:
            right_value = self.right.evaluate_given_inputs(inputs, faulty_set)
            output = BASE_OPERATIONS[self.gate](left_value, right_value)
        else:
            output = BASE_OPERATIONS[self.gate](left_value)

        if self.label in faulty_set:
            return not output
        else:
            return output


def pretty_print_tree(node: Node, indent=0):
    """
    Recursively pretty prints a tree-like structure rooted at `node`.
    Args:
        node (Node): The root node of the tree to print.
        indent (int): The current level of indentation.
    """
    if node is None:
        return

    # Print the current node
    prefix = "  " * indent  # Create indentation
    if node.is_leaf_node:
        print(f"{prefix}Leaf Node: {node.label}, Value: {node.value}")
    else:
        print(f"{prefix}Gate Node: {node.label}, Gate: {node.gate}")

    # Recursively print left and right children
    if node.left:
        print(f"{prefix}  Left:")
        pretty_print_tree(node.left, indent + 2)

    if node.right:
        print(f"{prefix}  Right:")
        pretty_print_tree(node.right, indent + 2)


def create_circuit_with_head_node(node: Node):
    """Given a completed head node, create the circuit

    Args:
        node (Node): the head node

    Returns:
        the circuit object
    """
    circuit = Circuit()

    def traverse_and_add(node, is_head):
        """recursively creates the circuit.

        Args:
            node (Node): Current node in the circuit.
            is_head (bool): if current node is the head
        """
        # if node.is_leaf_node:
        #     circuit.nodes[node.label] = node
        #     return
        is_leaf_node = circuit.add_node(node, is_head)
        is_head = False
        if is_leaf_node:
            return
        if node.left:
            traverse_and_add(node.left, is_head)
        if node.right:
            traverse_and_add(node.right, is_head)

    traverse_and_add(node, True)
    return circuit


def leaf_node(value):
    node = Node(
        left=None, right=None, gate=None, label=None, is_leaf_node=True, value=value
    )
    return node


def double_operand_gate_node(left, right, gate, label):
    node = Node(left=left, right=right, gate=gate, label=label, is_leaf_node=False)
    return node


def single_operand_gate_node(left, gate, label):
    node = Node(left=left, right=None, gate=gate, label=label, is_leaf_node=False)
    return node


class Circuit:
    def __init__(self):
        self.gates = {}
        self.gate_labels = []
        self.nodes = {}

    def add_node(self, node, is_head):
        self.nodes[node.label] = node
        if not node.is_leaf_node:
            self.gates[node.label] = node
            self.gate_labels.append(node.label)

        if is_head:
            # WARNING: Bad way of doing it since only this function adds the self.head value
            self.head = node.label
        return node.is_leaf_node

    def evaluate_with_faults(self, inputs, faulty_set):
        return self.gates[self.head].evaluate_given_inputs(inputs, faulty_set)

    def save_circuit(self):
        circuit_representation = []
        print(f"self.nodes are {self.nodes}")
        input()
        for i in self.gates.values():
            # if self.
            if i.label == self.head:
                circuit_representation.insert(0, i.representation())
            else:
                circuit_representation.append(i.representation())
        print(circuit_representation)


def find_minimal_faulty_gates(circuit: Circuit, inputs, expected_output):
    gates = circuit.gate_labels
    all_faulty_sets = []
    for r in range(1, len(gates) + 1):
        for faulty_set in combinations(gates, r):
            result = circuit.evaluate_with_faults(inputs, faulty_set)
            if int(result) == expected_output:
                all_faulty_sets.append(list(faulty_set))
    return minimal_list_of_lists(all_faulty_sets)


def minimal_list_of_lists(lists):
    # Remove duplicates by converting each list to a tuple and creating a set
    unique_lists = [
        list(item) for item in set(tuple(sorted(sublist)) for sublist in lists)
    ]

    # Sort lists by length for subset comparison
    unique_lists.sort(key=len)

    # Remove lists that are subsets of others
    minimal_set = []
    for sublist in unique_lists:
        if not any(set(existing).issubset(set(sublist)) for existing in minimal_set):
            minimal_set.append(sublist)

    return minimal_set


# a_node = Node(None, None, None, None, True, "a")

if __name__ == "__main__":
    # TODO: add more sanity tests
    a_node = leaf_node("a")
    b_node = leaf_node("b")
    c_node = leaf_node("c")

    a_and_b_node = double_operand_gate_node(a_node, b_node, "and", "A")
    a_and_b_or_c_node = double_operand_gate_node(a_and_b_node, c_node, "or", "B")

    circuit = Circuit()

    circuit.add_node(a_and_b_node, False)
    circuit.add_node(a_and_b_or_c_node, True)

    inputs = {"a": 1, "b": 1, "c": 1}

    a = circuit.evaluate_with_faults(inputs, ["B"])
    print(a)

    faulty_set = find_minimal_faulty_gates(circuit, inputs, 0)
    print(faulty_set)

    checker_circuit = (
        "(not((z xor (not x))) nand (not((z xnor (not y))) nand (x and (not y))))"
    )

    # faulty_gates are B, C and A
    k, node = logic_parser.logicparse(checker_circuit)
    circuit = create_circuit_with_head_node(node)
    circuit.save_circuit()
    k.draw()
