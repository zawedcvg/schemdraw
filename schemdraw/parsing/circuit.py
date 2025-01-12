from itertools import combinations

BASE_OPERATIONS = {
    "not": lambda x: not x,
    "or": lambda x, y: x or y,
    "nor": lambda x, y: not (x or y),
    "xor": lambda x, y: x != y,
    "and": lambda x, y: x and y,
    "nand": lambda x, y: not (x and y),
    "implies": lambda x, y: not x or y,
    "equals": lambda x, y: x == y,
    "xnor": lambda x, y: not(x != y)
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

DOUBLE_OPERAND_OPS = ("and", "nand", "or", "nor", "xor", "xnor", "=>", "implies", "=", "!=")

def leaf_node(value):
    node = Node(left=None, right=None, gate=None, label=None, is_leaf_node=True, value=value)
    return node

def double_operand_gate_node(left, right, gate, label):
    node = Node(left=left, right=right, gate=gate, label=label, is_leaf_node=False)
    return node

def single_operand_gate_node(left, gate, label):
    node = Node(left=left, right=None, gate=gate, label=label, is_leaf_node=False)
    return node

class Node:
    def __init__(self, left, right, gate, label, is_leaf_node: bool, value=None) -> None:
        self.left = left
        self.right = right
        self.gate = gate
        self.label = label
        self.is_leaf_node = is_leaf_node
        self.value = value

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


class Circuit:
    def __init__(self):
        self.gates = {}
        self.values = []

    def add_nodes(self, node, is_head):
        self.gates[node.label] = node
        self.values.append(node.label)
        if is_head:
            self.head = node.label

    def evaluate_with_faults(self, inputs, faulty_set):
        return self.gates[self.head].evaluate_given_inputs(inputs, faulty_set)


def find_faulty_gates(circuit: Circuit, inputs, expected_output):
    gates = circuit.values
    all_faulty_sets = []
    for r in range(1, len(gates) + 1):
        for faulty_set in combinations(gates, r):
            result = circuit.evaluate_with_faults(inputs, faulty_set)
            if int(result) == expected_output:
                all_faulty_sets.append(list(faulty_set))
    return all_faulty_sets


# a_node = Node(None, None, None, None, True, "a")

if __name__ == "__main__":
    a_node = leaf_node("a")
    b_node = leaf_node("b")
    c_node = leaf_node("c")

    a_and_b_node = double_operand_gate_node(a_node, b_node, "and", "A")
    a_and_b_or_c_node = double_operand_gate_node(a_and_b_node, c_node, "or", "B")

    circuit = Circuit()

    circuit.add_nodes(a_and_b_node, False)
    circuit.add_nodes(a_and_b_or_c_node, True)

    inputs = {"a": 1, "b": 1, "c": 1}

    a = circuit.evaluate_with_faults(inputs, ["B"])
    print(a)

    faulty_set = find_faulty_gates(circuit, inputs, 0)
    print(faulty_set)
