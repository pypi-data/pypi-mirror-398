import ast
import struct

class Op:
    LOAD_CONST = 0x01
    LOAD_NAME = 0x02
    STORE_NAME = 0x03
    CALL = 0x04
    BIN_ADD = 0x05
    BIN_SUB = 0x06
    BIN_MUL = 0x07
    BIN_DIV = 0x08
    COMPARE = 0x09
    JUMP = 0x0A
    JUMP_IF_FALSE = 0x0B
    RETURN = 0x0C
    POP_TOP = 0x0D
    BUILD_LIST = 0x0E
    BUILD_DICT = 0x0F
    BUILD_STRING = 0x10
    LOAD_ATTR = 0x11
    STORE_ATTR = 0x12

CMP_OPS = {
    ast.Lt: 0,
    ast.LtE: 1,
    ast.Gt: 2,
    ast.GtE: 3,
    ast.Eq: 4,
    ast.NotEq: 5
}

class PythonToVM(ast.NodeVisitor):
    def __init__(self, mapping=None, op_map=None):
        self.bytecode = []
        self.constants = []
        self.names = []
        self.mapping = mapping if mapping is not None else {}
        self.op_map = op_map if op_map is not None else {
            getattr(Op, attr): getattr(Op, attr) for attr in dir(Op) if not attr.startswith("__")
        }
        self.labels = {} # name -> index in bytecode
        self.fixups = [] # (index, label_name)

    def _add_const(self, val):
        if val not in self.constants:
            self.constants.append(val)
        return self.constants.index(val)

    def _add_name(self, name):
        # Use mapping if available
        mapped_name = self.mapping.get(name, name)
        if mapped_name not in self.names:
            self.names.append(mapped_name)
        return self.names.index(mapped_name)

    def emit(self, opcode, arg=0):
        # Translate opcode using op_map
        real_opcode = self.op_map.get(opcode, opcode)
        self.bytecode.extend([real_opcode, arg])
        return len(self.bytecode) - 1 # Return index of the argument

    def visit_If(self, node):
        self.visit(node.test)
        # Emit JUMP_IF_FALSE with placeholder
        jump_arg_idx = self.emit(Op.JUMP_IF_FALSE, 0)
        
        for stmt in node.body:
            self.visit(stmt)
        
        if node.orelse:
            # If we have an else, we need to jump over it after the 'if' body
            else_jump_idx = self.emit(Op.JUMP, 0)
            # The JUMP_IF_FALSE lands at the start of 'orelse'
            self.bytecode[jump_arg_idx] = len(self.bytecode) // 2
            
            for stmt in node.orelse:
                self.visit(stmt)
            # The JUMP lands after 'orelse'
            self.bytecode[else_jump_idx] = len(self.bytecode) // 2
        else:
            # No else, JUMP_IF_FALSE lands here
            self.bytecode[jump_arg_idx] = len(self.bytecode) // 2

    def visit_Constant(self, node):
        idx = self._add_const(node.value)
        self.emit(Op.LOAD_CONST, idx)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            idx = self._add_name(node.id)
            self.emit(Op.LOAD_NAME, idx)
        elif isinstance(node.ctx, ast.Store):
            idx = self._add_name(node.id)
            self.emit(Op.STORE_NAME, idx)

    def visit_Attribute(self, node):
        self.visit(node.value)
        idx = self._add_name(node.attr)
        if isinstance(node.ctx, ast.Load):
            self.emit(Op.LOAD_ATTR, idx)
        elif isinstance(node.ctx, ast.Store):
            self.emit(Op.STORE_ATTR, idx)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        if isinstance(node.op, ast.Add): self.emit(Op.BIN_ADD)
        elif isinstance(node.op, ast.Sub): self.emit(Op.BIN_SUB)
        elif isinstance(node.op, ast.Mult): self.emit(Op.BIN_MUL)
        elif isinstance(node.op, ast.Div): self.emit(Op.BIN_DIV)

    def visit_Compare(self, node):
        self.visit(node.left)
        # Only support single comparator for now
        self.visit(node.comparators[0])
        op_idx = CMP_OPS.get(type(node.ops[0]), 4)
        self.emit(Op.COMPARE, op_idx)

    def visit_Call(self, node):
        # Push args in order
        for arg in node.args:
            self.visit(arg)
        # Load the function name
        # Load the function name/attribute
        self.visit(node.func)
        self.emit(Op.CALL, len(node.args))

    def visit_Assign(self, node):
        self.visit(node.value)
        # Only support single Name targets
        for target in node.targets:
            self.visit(target)

    def visit_While(self, node):
        start_pc = len(self.bytecode) // 2
        self.visit(node.test)
        jump_arg_idx = self.emit(Op.JUMP_IF_FALSE, 0)
        
        for stmt in node.body:
            self.visit(stmt)
        
        self.emit(Op.JUMP, start_pc)
        self.bytecode[jump_arg_idx] = len(self.bytecode) // 2

    def visit_Return(self, node):
        if node.value:
            self.visit(node.value)
        else:
            self.emit(Op.LOAD_CONST, self._add_const(None))
        self.emit(Op.RETURN)

    def visit_Expr(self, node):
        self.visit(node.value)
        self.emit(Op.POP_TOP)

    def visit_List(self, node):
        for el in node.elts:
            self.visit(el)
        self.emit(Op.BUILD_LIST, len(node.elts))

    def visit_Dict(self, node):
        for k, v in zip(node.keys, node.values):
            self.visit(k)
            self.visit(v)
        self.emit(Op.BUILD_DICT, len(node.keys))

    def visit_JoinedStr(self, node):
        for val in node.values:
            self.visit(val)
        self.emit(Op.BUILD_STRING, len(node.values))

    def visit_FormattedValue(self, node):
        self.visit(node.value)
        # We ignore conversion/format_spec for now, just convert to str
        self.emit(Op.LOAD_NAME, self._add_name('str'))
        self.emit(Op.CALL, 1)

    def finalize(self):
        return bytes(self.bytecode), tuple(self.constants), tuple(self.names)

def virtualize_function(node, mapping=None, op_map=None):
    """
    Translates a FunctionDef node into VM bytecode.
    """
    if not isinstance(node, ast.FunctionDef):
        return None
    
    v = PythonToVM(mapping=mapping, op_map=op_map)
    for stmt in node.body:
        v.visit(stmt)
    
    # Ensure a return at the end if none exists
    if not v.bytecode or v.bytecode[-2] != (op_map.get(Op.RETURN, Op.RETURN) if op_map else Op.RETURN):
        v.emit(Op.LOAD_CONST, v._add_const(None))
        v.emit(Op.RETURN)
        
    return v.finalize()
