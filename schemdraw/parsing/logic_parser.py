''' Module for converting a logic string expression into a schemdraw.Drawing.

Example:

>>> logicparse("a and (b or c)")

'''
from typing import Optional
import pyparsing  # type: ignore
from circuit import Circuit, leaf_node, gate_node

from .. import schemdraw
from .. import logic
from ..elements import RightLines
from .buchheim import buchheim


class LogicTree():
    ''' Organize the logic gates into tree structure '''
    def __init__(self, node, *children):
        self.node = node
        self.children = children if children else []

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.children[key]

    def __iter__(self):
        return self.children.__iter__()

    def __len__(self):
        return len(self.children)


def parse_string(logicstr):
    ''' Parse the logic string using pyparsing '''
    and_ = pyparsing.Keyword('and')
    or_ = pyparsing.Keyword('or')
    nor_ = pyparsing.Keyword('nor')
    nand_ = pyparsing.Keyword('nand')
    xor_ = pyparsing.Keyword('xor')
    xnor_ = pyparsing.Keyword('xnor')
    not_ = pyparsing.Keyword('not')
    true_ = pyparsing.Keyword('true')
    false_ = pyparsing.Keyword('false')

    not_op = not_ | '~' | '¬'
    and_op = and_ | nand_ | '&' | '∧'
    xor_op = xor_ | xnor_ | '⊕' | '⊻'
    or_op = or_ | nor_ | '|' | '∨' | '+'

    expr = pyparsing.Forward()

    identifier = ~(and_ | or_ | nand_ | nor_ | not_ | true_ | false_) + \
        pyparsing.Word('$' + pyparsing.alphas + '_', pyparsing.alphanums + '_' + '$')

    expr = pyparsing.infixNotation(true_ | false_ | identifier,
                                   [(not_op, 1, pyparsing.opAssoc.RIGHT),
                                    (and_op, 2, pyparsing.opAssoc.LEFT),
                                    (or_op, 2, pyparsing.opAssoc.LEFT),
                                    (xor_op, 2, pyparsing.opAssoc.LEFT)])

    return expr.parseString(logicstr)[0]


def to_tree(pres):
    ''' Convert the parsed logic expression into a LogicTree '''
    invertfunc = False

    if pres[0] in ['not', '~', '¬']:
        if isinstance(pres[1], str):
            return LogicTree('not', to_tree(pres[1]))
        else:
            pres = pres[1]
            invertfunc = True

    if isinstance(pres, str):
        return LogicTree(pres)

    func = pres[1]
    inputs = pres[::2]

    # print(f"func is {func}")
    # print(f"inputs are {inputs}")
    # input()

    func = {'&': 'and', '∧': 'and',
            '|': 'or', '∨': 'or',  '+': 'or',
            '⊕': 'xor', '⊻': 'xor'}.get(func, func)

    if invertfunc:
        func = {'and': 'nand', 'or': 'nor', 'not': 'buf',
                'nand': 'and', 'nor': 'or', 'buf': 'not',
                'xor': 'xnor', 'xnor': 'xor'}.get(func)

    return LogicTree(func, *[to_tree(i) for i in inputs])


def drawlogic(tree, gateH=.7, gateW=2, outlabel=None):
    ''' Draw the LogicTree to a schemdraw Drawing

        Parameters
        ----------
        tree: LogicTree
            The tree structure to draw
        gateH: float
            Height of one gate
        gateW: float
            Width of one gate
        outlabel: string
            Label for logic output

        Returns
        -------
        schemdraw.Drawing
    '''
    drawing = schemdraw.Drawing()
    drawing.unit = gateW  # NOTs still use d.unit

    dtree = buchheim(tree)

    label_count = 0

    def drawit(root, depth=0, outlabel=None, curr_index=0):
        ''' Recursive drawing function '''
        elmdefs = {'and': logic.And,
                   'or': logic.Or,
                   'xor': logic.Xor,
                   'nand': logic.Nand,
                   'xnor': logic.Xnor,
                   'nor': logic.Nor,
                   'not': logic.Not}
        elm = elmdefs.get(root.node, logic.And) #if gate not in defintions, use logic.And

        x = root.y * -gateW   # buchheim draws vertical trees, so flip x-y.
        y = -root.x * gateH

        #WARNING: going to assume that there are only two children

        to_use_label = chr(ord("A") + curr_index)
        curr_index += 1

        # The code basically always draws a gate, and if the next things are inputs draws that too and quits. else it goes to the recursive function.

        left_node = None
        right_node = None

        g = elm(d='r', at=(x, y), anchor='end',
                l=gateW, inputs=len(root.children))
        if outlabel:
            g.label(outlabel, loc='end')

        # NOTE: This part is slightly weird? Why not just one loop

        for i, child in enumerate(root.children):
            anchorname = 'start' if elm in [logic.Not, logic.Buf] else f'in{i+1}'
            # in probably stands for input number
            # so basically if child.node is an input put it as a input number thing. else something else idc
            if child.node not in elmdefs:
                g.label(child.node, loc=anchorname)
                if i == 0:
                    left_node = leaf_node(child.node)
                else:
                    right_node = leaf_node(child.node)

        g.label(to_use_label, loc="top")

        drawing.add(g)

        for i, child in enumerate(root.children):
            anchorname = 'start' if elm in [logic.Not, logic.Buf] else f'in{i+1}'
            if child.node in elmdefs:
                childelm, curr_index, output_node = drawit(child, depth+1, curr_index=curr_index)  # recursive
                drawing.add(RightLines(at=(g, anchorname), to=childelm.end))
                if i == 0:
                    left_node = output_node
                else:
                    right_node = output_node

        node = gate_node(left_node, right_node, root.node, to_use_label)
        return g, curr_index, node

    _, _, node = drawit(dtree, outlabel=outlabel, curr_index=label_count)
    return drawing, node


def logicparse(expr: str, gateW: float = 2, gateH: float = .75,
               outlabel: Optional[str] = None) -> schemdraw.Drawing:
    ''' Parse a logic string expression and draw the gates in a schemdraw Drawing

        Logic expression is defined by string using 'and', 'or', 'not', etc.
        for example, "a or (b and c)". Parser recognizes several symbols and
        names for logic functions:
        [and, '&', '∧']
        [or, '|', '∨', '+']
        [xor, '⊕', '⊻']
        [not, '~', '¬']

        Args:
            expr: Logic expression
            gateH: Height of one gate
            gateW: Width of one gate
            outlabel: Label for logic output

        Returns:
            schemdraw.Drawing with logic tree
    '''
    parsed = parse_string(expr)
    # print(parsed)
    # print("here")
    tree = to_tree(parsed)
    print(tree)
    drawing, node = drawlogic(tree, gateH=gateH, gateW=gateW, outlabel=outlabel)
    return drawing, node
