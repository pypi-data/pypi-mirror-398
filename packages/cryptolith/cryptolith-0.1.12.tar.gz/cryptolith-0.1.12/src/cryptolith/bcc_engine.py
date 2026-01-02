import ast
import random
import string

class ConstantFolder(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
            try:
                op = node.op
                l = node.left.value
                r = node.right.value
                res = None
                if isinstance(op, ast.Add): res = l + r
                elif isinstance(op, ast.Sub): res = l - r
                elif isinstance(op, ast.Mult): res = l * r
                elif isinstance(op, ast.Div): res = l / r
                elif isinstance(op, ast.FloorDiv): res = l // r
                elif isinstance(op, ast.Mod): res = l % r
                elif isinstance(op, ast.Pow): res = l ** r
                elif isinstance(op, ast.LShift): res = l << r
                elif isinstance(op, ast.RShift): res = l >> r
                elif isinstance(op, ast.BitAnd): res = l & r
                elif isinstance(op, ast.BitOr): res = l | r
                elif isinstance(op, ast.BitXor): res = l ^ r
                # MatMult cannot be safely folded for constants usually (requires numpy arrays)

                if res is not None:
                    return ast.Constant(value=res)
            except:
                pass
        return node

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if isinstance(node.operand, ast.Constant):
            try:
                op = node.op
                v = node.operand.value
                res = None
                if isinstance(op, ast.UAdd): res = +v
                elif isinstance(op, ast.USub): res = -v
                elif isinstance(op, ast.Not): res = not v
                elif isinstance(op, ast.Invert): res = ~v

                if res is not None:
                    return ast.Constant(value=res)
            except:
                pass
        return node

class CGenerator(ast.NodeVisitor):
    def __init__(self, mod_name, turbo=False, mapping=None):
        self.mod_name = mod_name
        self.turbo = turbo
        self.mapping = mapping if mapping else {}
        self.functions = []
        self.c_code = []
        self.indent = 0
        self.temp_count = 0
        self.temp_types = {}
        self.raw_types = {}
        self.buffer_views = {}
        self.error_label = None # Label to jump to on error (if inside try)
        self.cleanup_stack = [] # Stack of cleanup code for returns/breaks inside with. Tuple: (code, loop_depth)
        self.loop_depth = 0

    def _add_line(self, text):
        self.c_code.append("    " * self.indent + text)

    def _add_check(self, var_name, error_msg="Python API Error"):
        if self.turbo:
            self._add_line(f"if (!{var_name}) {{ if (_save) {{ PyEval_RestoreThread(_save); _save = NULL; }} fprintf(stderr, \"BCC FATAL ERROR: %s\\n\", \"{error_msg}\"); return NULL; }}")
        else:
            self._add_line(f"if (!{var_name}) return NULL;")

    def _needs_gil(self, nodes):
        """Heuristic: does any of these nodes require the GIL?"""
        for node in nodes:
            if isinstance(node, (ast.Call, ast.Attribute, ast.Subscript, ast.List, ast.Tuple, ast.Dict, ast.Set, ast.BinOp, ast.UnaryOp)):
                # If it's a BinOp/UnaryOp, check if it can be raw
                # For simplicity, we check if it's in raw_types later, but here we are cautious
                # Actually, our _visit_expr already knows if it's raw.
                pass
            if isinstance(node, ast.Name):
                if node.id not in self.raw_types: return True
        # Safer approach: if it contains any "Py" function call, it needs GIL.
        # But we don't have the C code yet.
        # So we just check if it uses non-raw variables.
        return True # Default to True for now, will refine

    def _ensure_gil(self, locked=True):
        if not self.turbo: return
        if locked:
            self._add_line("if (_save) { PyEval_RestoreThread(_save); _save = NULL; }")
        else:
            self._add_line("if (!_save) _save = PyEval_SaveThread();")

    def _get_temp(self, is_obj=True):
        self.temp_count += 1
        name = f"tmp_{self.temp_count}"
        self.temp_types[name] = "PyObject*" if is_obj else "double"
        return name

    def _is_raw_val(self, v):
        if hasattr(self, 'raw_types') and v in self.raw_types: return True
        if isinstance(v, str):
            v = v.strip()
            # C-casts indicate raw values
            if v.startswith("(") and (")" in v) and ("int" in v or "long" in v or "double" in v): return True
            if v.startswith("pow(") or v.startswith("floor(") or v.startswith("fabs(") or v.startswith("log1p("): return True
            if v.isdigit(): return True
            try:
                float(v)
                return True
            except ValueError:
                pass
        return False


    def generate(self, func_node, original_name=None):
        # Apply constant folding first
        func_node = ConstantFolder().visit(func_node)

        func_name = original_name if original_name else func_node.name
        self.functions.append(func_name)
        
        # Rename self to bcc_self to avoid redefinition of the argument 'self' in class methods
        self._add_line(f"static PyObject* bcc_{func_name}(PyObject* bcc_self, PyObject* args, PyObject* kwargs) {{")
        self.indent += 1
        
        arg_names = [arg.arg for arg in func_node.args.args]
        format_str = "O" * len(arg_names) + "|O"
        keywords_init = ", ".join([f'"{name}"' for name in arg_names] + ["\"_bcc_globals\"", "NULL"])
        self._add_line(f"static char *kwlist[] = {{{keywords_init}}};")
        
        for name in arg_names:
            self._add_line(f"PyObject* py_{name} = NULL;")
            if self.turbo:
                # Never convert self/cls to double
                if name in ('self', 'cls'): continue
                if "arr" in name.lower() or "data" in name.lower():
                     self._add_line(f"double* {name} = NULL;")
                else:
                     self._add_line(f"double {name} = 0;")
        
        self.raw_types = {}
        if self.turbo:
            for name in arg_names:
                if name in ('self', 'cls'): continue
                if "arr" in name.lower() or "data" in name.lower():
                    self.raw_types[name] = "double* "
                else:
                    self.raw_types[name] = "double"

        class VarScanner(ast.NodeVisitor):
            def __init__(self, arg_names, turbo):
                self.found_double = set()
                self.found_long = set()
                self.found_obj = set()
                self.found_globals = set()
                self.assigned = set(arg_names)
                self.args = set(arg_names)
                self.turbo = turbo

            def _check_val(self, target, val):
                if not isinstance(target, ast.Name): return
                # Heuristic: if value is a Call (not math), List, Tuple, or Name known as obj
                is_obj = False
                is_int = False
                if isinstance(val, ast.Constant):
                     if isinstance(val.value, int): is_int = True
                     elif isinstance(val.value, float): pass
                     else: is_obj = True
                elif isinstance(val, (ast.List, ast.Tuple, ast.Dict, ast.Set, ast.JoinedStr)): is_obj = True
                elif isinstance(val, ast.Call):
                    f_name = None
                    if isinstance(val.func, ast.Name): f_name = val.func.id
                    elif isinstance(val.func, ast.Attribute) and isinstance(val.func.value, ast.Name) and val.func.value.id == "math":
                        f_name = val.func.attr
                    
                    if f_name in ('len', 'int', 'abs', 'min', 'max', 'sin', 'cos', 'tan', 'exp', 'log', 'log1p', 'sqrt'):
                        if f_name in ('len', 'int'): is_int = True
                    else: is_obj = True
                
                if self.turbo and not is_obj:
                    if is_int: self.found_long.add(target.id)
                    else: self.found_double.add(target.id)
                else: self.found_obj.add(target.id)

            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name): self.assigned.add(target.id)
                    self._check_val(target, node.value)
                self.generic_visit(node)

            def visit_AnnAssign(self, node):
                if isinstance(node.target, ast.Name): self.assigned.add(node.target.id)
                if node.value: self._check_val(node.target, node.value)
                self.generic_visit(node)

            def visit_BinOp(self, node):
                if isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift)):
                    if isinstance(node.left, ast.Name) and node.left.id in self.assigned: self.found_long.add(node.left.id)
                    if isinstance(node.right, ast.Name) and node.right.id in self.assigned: self.found_long.add(node.right.id)
                self.generic_visit(node)

            def visit_AugAssign(self, node):
                if isinstance(node.target, ast.Name):
                    self.assigned.add(node.target.id)
                    if isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift)):
                        self.found_long.add(node.target.id)
                self._check_val(node.target, node.value)
                self.generic_visit(node)

            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.assigned.add(name)
                    self.found_obj.add(name)

            def visit_ImportFrom(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.assigned.add(name)
                    self.found_obj.add(name)
                self.generic_visit(node)

            def visit_For(self, node):
                if isinstance(node.target, ast.Name):
                    self.assigned.add(node.target.id)
                    if node.target.id not in self.args:
                        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                             self.found_long.add(node.target.id)
                        else:
                             self.found_double.add(node.target.id)
                self.generic_visit(node)

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    if node.id not in self.assigned:
                        # Global or builtin
                        self.found_globals.add(node.id)
                self.generic_visit(node)

        scanner = VarScanner(arg_names, self.turbo)
        scanner.visit(func_node)
        
        all_local_vars = scanner.found_double | scanner.found_long | scanner.found_obj
        all_global_vars = scanner.found_globals
        
        for name in all_local_vars:
            self._add_line(f"PyObject* py_{name} = NULL;")
            if name in scanner.found_double:
                self._add_line(f"double {name} = 0;")
                self.raw_types[name] = "double"
            elif name in scanner.found_long:
                self._add_line(f"int64_t {name} = 0;")
                self.raw_types[name] = "int64_t"

        for name in all_global_vars:
            self._add_line(f"PyObject* py_{name} = NULL;")

        self._add_line("PyObject* _bcc_globals = NULL;")
        if arg_names:
            p_args = ", ".join([f"&py_{name}" for name in arg_names])
            self._add_line(f"if (!PyArg_ParseTupleAndKeywords(args, kwargs, \"{format_str}\", kwlist, {p_args}, &_bcc_globals)) return NULL;")
        else:
            self._add_line(f"if (!PyArg_ParseTupleAndKeywords(args, kwargs, \"{format_str}\", kwlist, &_bcc_globals)) return NULL;")

        # Initialize globals
        if all_global_vars:
            self._add_line("PyObject* _globals = _bcc_globals ? _bcc_globals : PyEval_GetGlobals();")
            self._add_line("PyObject* _builtins = PyEval_GetBuiltins();")
            for name in sorted(all_global_vars):
                mapped_name = self.mapping.get(name, name)
                self._add_line(f"py_{name} = _globals ? PyDict_GetItemString(_globals, \"{mapped_name}\") : NULL;")
                self._add_line(f"if (!py_{name}) py_{name} = PyDict_GetItemString(_builtins, \"{name}\");")
                self._add_line(f"if (!py_{name}) {{ py_{name} = Py_None; }}")

        self.locals = set(arg_names)
        self.buffer_views = {}
        self.returned = False
        self.error_label = None # Label to jump to on error (if inside try)
        self.cleanup_stack = [] # Stack of cleanup code for returns/breaks inside with. Tuple: (code, loop_depth)
        self.loop_depth = 0

        if self.turbo:
            self._add_line("PyThreadState* _save = NULL;")
            for n in arg_names:
                name = n.strip()
                if name in ('self', 'cls'): continue
                if "arr" in name.lower() or "data" in name.lower():
                    vn = f"view_{name}"
                    self._add_line(f"Py_buffer {vn};")
                    self._add_line(f"if (PyObject_GetBuffer(py_{name}, &{vn}, PyBUF_SIMPLE) < 0) return NULL;")
                    self.buffer_views[name] = vn
                else:
                    self._add_line(f"if (PyFloat_Check(py_{name})) {name} = PyFloat_AsDouble(py_{name}); else if (PyLong_Check(py_{name})) {name} = (double)PyLong_AsLong(py_{name});")
                    self.raw_types[name] = "double"
            # We start LOCKED to simplify initial setup. 
            # Sub-visits will decide when to unlock.

        for stmt in func_node.body:
            self.visit(stmt)

        if not self.returned:
            if self.turbo:
                self._ensure_gil(locked=True)
                for name, view in self.buffer_views.items():
                    self._add_line(f"PyBuffer_Release(&{view});")
            self._add_line("Py_RETURN_NONE;")
        self.indent -= 1
        self._add_line("}\n")


    def visit_Return(self, node):
        if self.turbo: self._ensure_gil(locked=True)
        if node.value:
            res = self._visit_expr(node.value)
            if self.turbo: self._ensure_gil(locked=True)
            ro = res if not self._is_raw_val(res) else f"PyFloat_FromDouble((double){res})"
            self._add_line(f"PyObject* final_ret = {ro};")
            for name, view in self.buffer_views.items():
                self._add_line(f"PyBuffer_Release(&{view});")
            self._add_line("return final_ret;")
        else:
            for name, view in self.buffer_views.items():
                self._add_line(f"PyBuffer_Release(&{view});")
            self._add_line("Py_RETURN_NONE;")
        self.returned = True

    def _expr_needs_gil(self, node):
        if isinstance(node, ast.Name):
            return node.id not in self.raw_types
        if isinstance(node, ast.Constant):
            return not isinstance(node.value, (int, float, type(None)))
        if isinstance(node, ast.BinOp):
            return self._expr_needs_gil(node.left) or self._expr_needs_gil(node.right)
        if isinstance(node, ast.UnaryOp):
            return self._expr_needs_gil(node.operand)
        if isinstance(node, ast.Compare):
            return self._expr_needs_gil(node.left) or any(self._expr_needs_gil(c) for c in node.comparators)
        if isinstance(node, ast.Subscript):
            # Safe raw read if owner is a buffer and index is raw
            if isinstance(node.value, ast.Name) and node.value.id in self.buffer_views:
                 return self._expr_needs_gil(node.slice)
            return True
        if isinstance(node, ast.Call):
            # len(raw_buffer) is raw
            if isinstance(node.func, ast.Name) and node.func.id == 'len':
                if len(node.args) == 1 and isinstance(node.args[0], ast.Name) and node.args[0].id in self.buffer_views:
                    return False
            # math functions on raw args are raw
            if isinstance(node.func, ast.Name) and node.func.id in ('int', 'float', 'abs', 'min', 'max', 'sin', 'cos', 'tan', 'sqrt'):
                return all(self._expr_needs_gil(a) == False for a in node.args)
        return True

    def visit_Assign(self, node):
        needs_gil = self._expr_needs_gil(node.value)
        # Also check targets
        for t in node.targets:
            if isinstance(t, ast.Name):
                if t.id not in self.raw_types: needs_gil = True
            else: needs_gil = True
        
        if self.turbo and needs_gil: self._ensure_gil(locked=True)
        val = self._visit_expr(node.value)
        def _check_target(t):
            if isinstance(t, ast.Name):
                is_raw = t.id in self.raw_types
                if is_raw:
                    rtype = self.raw_types[t.id]
                    v_raw = val
                    if not self._is_raw_val(val):
                        # Convert object to raw
                        if rtype == "double": v_raw = f"(PyFloat_Check({val}) ? PyFloat_AsDouble({val}) : (double)PyLong_AsLong({val}))"
                        else: v_raw = f"PyLong_AsLong({val})"
                    self._add_line(f"{t.id} = ({rtype}){v_raw};")
                else:
                    vo = val if not self._is_raw_val(val) else (f"PyFloat_FromDouble((double){val})" if "." in str(val) or "pow" in str(val) or "sin" in str(val) or "cos" in str(val) or "sqrt" in str(val) or "fabs" in str(val) else f"PyLong_FromLong((long){val})")
                    tmp_set = self._get_temp(is_obj=True)
                    self._add_line(f"PyObject* {tmp_set} = {vo};")
                    self._add_line(f"Py_XINCREF({tmp_set});")
                    self._add_line(f"Py_XDECREF(py_{t.id}); py_{t.id} = {tmp_set};")
            elif isinstance(t, ast.Subscript):
                # Check for raw buffer write
                owner = self._visit_expr(t.value)
                idx = self._visit_expr(t.slice)
                if owner in self.buffer_views and self._is_raw_val(idx) and not isinstance(t.slice, ast.Slice):
                    v = self.buffer_views[owner]
                    # Robust type-aware write
                    self._add_line(f"if ({v}.itemsize == 8) ((double*){v}.buf)[(long){idx}] = (double){val};")
                    self._add_line(f"else ((uint8_t*){v}.buf)[(long){idx}] = (uint8_t){val};")
                else:
                    obj = self._visit_expr(t.value, as_obj=True)
                    idx_obj = self._visit_expr(t.slice, as_obj=True)
                    vo = val if not self._is_raw_val(val) else (f"PyFloat_FromDouble((double){val})" if "." in str(val) or "pow" in str(val) or "sin" in str(val) or "cos" in str(val) or "sqrt" in str(val) or "fabs" in str(val) else f"PyLong_FromLong((long){val})")
                    self._add_line(f"PyObject_SetItem({obj}, {idx_obj}, {vo});")
                    if vo.startswith("tmp_") or "PyFloat_FromDouble" in vo or "PyLong_FromLong" in vo:
                         self._add_line(f"Py_DECREF({vo});")
            elif isinstance(t, ast.Attribute):
                obj = self._visit_expr(t.value, as_obj=True)
                vo = val if not self._is_raw_val(val) else f"PyFloat_FromDouble((double){val})"
                self._add_line(f"PyObject_SetAttrString({obj}, \"{t.attr}\", {vo});")
            elif isinstance(t, (ast.Tuple, ast.List)):
                # Unpacking
                vo = val if not self._is_raw_val(val) else f"PyLong_FromLong((long){val})"
                for i, el in enumerate(t.elts):
                    item = self._get_temp(is_obj=True)
                    self._add_line(f"PyObject* {item} = PySequence_GetItem({vo}, {i});")
                    if isinstance(el, ast.Name):
                        if el.id in self.raw_types:
                             rtype = self.raw_types[el.id]
                             if rtype == "double": self._add_line(f"{el.id} = ({rtype})PyFloat_AsDouble({item});")
                             else: self._add_line(f"{el.id} = ({rtype})PyLong_AsLong({item});")
                        else:
                             self._add_line(f"Py_XDECREF(py_{el.id}); py_{el.id} = {item}; Py_XINCREF(py_{el.id});")
                    self._add_line(f"Py_DECREF({item});")

        for target in node.targets:
            _check_target(target)
        if self.turbo and needs_gil: self._ensure_gil(locked=False)
        self.generic_visit(node)

    def visit_For(self, node):
        self.loop_depth += 1
        is_range = isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range'
        
        if is_range:
            # Determine if it's a raw range (all args are raw)
            is_raw_range = self.turbo and all(self._expr_needs_gil(arg) == False for arg in node.iter.args)
            
            start = 0
            stop = self._visit_expr(node.iter.args[0])
            if len(node.iter.args) > 1:
                start = stop
                stop = self._visit_expr(node.iter.args[1])

            if not self._is_raw_val(stop):
                if self.turbo: self._ensure_gil(locked=True)
                t = self._get_temp(is_obj=False)
                self._add_line(f"long {t} = PyLong_AsLong({stop});")
                stop = t

            if not self._is_raw_val(start):
                if self.turbo: self._ensure_gil(locked=True)
                t = self._get_temp(is_obj=False)
                self._add_line(f"long {t} = PyLong_AsLong({start});")
                start = t

            iv = node.target.id
            if self.turbo and is_raw_range:
                self.raw_types[iv] = "long"
                self._ensure_gil(locked=False) # Release GIL for the raw loop
                self._add_line(f"for (long {iv} = {start}; {iv} < (long){stop}; {iv}++) {{")
                self.indent += 1
                # NO sync of py_iv here - it requires GIL and is slow.
                # If py_iv is needed by some sub-expr, that expr will acquire GIL and convert it.
                for stmt in node.body:
                    self.visit(stmt)
                self.indent -= 1
                self._add_line("}")
                self._ensure_gil(locked=True) # Re-acquire GIL after
                del self.raw_types[iv]
            else:
                tx = self._get_temp(is_obj=False)
                self._add_line(f"for (long {tx} = {start}; {tx} < (long){stop}; {tx}++) {{")
                self.indent += 1
                # Always sync the py_ representation
                self._add_line(f"Py_XDECREF(py_{iv}); py_{iv} = PyLong_FromLong({tx});")
                # Also sync the raw representation if it exists
                if iv in self.raw_types:
                    rtype = self.raw_types[iv]
                    self._add_line(f"{iv} = ({rtype}){tx};")
                
                for s in node.body: self.visit(s)
                self.indent -= 1
                self._add_line("}")
        else:
            # Generic iterator
            iter_expr = self._visit_expr(node.iter, as_obj=True)
            if self.turbo: self._ensure_gil(locked=True)
            it = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {it} = PyObject_GetIter({iter_expr});")
            self._add_line("PyObject* item;")
            if self.turbo: self._ensure_gil(locked=True)
            
            self._add_line(f"while ((item = PyIter_Next({it}))) {{")
            self.indent += 1
            iv = node.target.id
            if iv in self.raw_types:
                rtype = self.raw_types[iv]
                if rtype == "double": self._add_line(f"{iv} = PyFloat_AsDouble(item);")
                else: self._add_line(f"{iv} = PyLong_AsLong(item);")
            else:
                self._add_line(f"PyObject* py_{iv} = item;")
            
            for s in node.body: self.visit(s)
            
            # Decref item if it's NOT captured in a py_var (wait, py_iv IS item)
            # Actually, standard logic: we handle py_vars as borrowed or we incref them.
            # Here it's cleaner to just let the loop manage it.
            self._add_line("Py_DECREF(item);")
            self.indent -= 1
            self._add_line("}")
            self._add_line(f"Py_DECREF({it});")

        self.loop_depth -= 1

    def visit_If(self, node):
        test = self._visit_expr(node.test)
        if self.turbo and not self._is_raw_val(test):
            self._add_line("")
            t = self._get_temp(is_obj=False)
            self._add_line(f"int {t} = PyObject_IsTrue({test});")
            self._add_line("")
            test = t
        self._add_line(f"if ({test}) {{")
        self.indent += 1
        for s in node.body: self.visit(s)
        self.indent -= 1
        if node.orelse:
            self._add_line("} else {")
            self.indent += 1
            for s in node.orelse: self.visit(s)
            self.indent -= 1
        self._add_line("}")

    def visit_While(self, node):
        self.loop_depth += 1
        self._add_line(f"while (1) {{")
        self.indent += 1
        test = self._visit_expr(node.test)
        if self.turbo and not self._is_raw_val(test):
            self._add_line("")
            t = self._get_temp(is_obj=False)
            self._add_line(f"int {t} = PyObject_IsTrue({test});")
            self._add_line("")
            test = t
        self._add_line(f"if (!({test})) break;")
        for s in node.body: self.visit(s)
        self.indent -= 1
        self._add_line("}")
        self.loop_depth -= 1

    def visit_Break(self, node):
        # Handle cleanups if inside with. Break exits the current loop.
        # Cleanup any 'with' blocks that were entered inside THIS loop (depth >= current)
        if self.cleanup_stack:
            for cleanup, depth in reversed(self.cleanup_stack):
                if depth >= self.loop_depth:
                    self._add_line(cleanup)
                else:
                    break
        self._add_line("break;")

    def visit_Assert(self, node):
        test = self._visit_expr(node.test)
        if self.turbo:
            if not self._is_raw_val(test):
                self._ensure_gil(locked=True)
                self._add_line(f"if (!PyObject_IsTrue({test})) {{ PyErr_SetString(PyExc_AssertionError, \"\"); return NULL; }}")
                self._ensure_gil(locked=True)
            else:
                 self._add_line(f"if (!({test})) {{ if (_save) PyEval_RestoreThread(_save); PyErr_SetString(PyExc_AssertionError, \"\"); return NULL; }}")
        else:
            self._add_line(f"if (!PyObject_IsTrue({test})) {{ PyErr_SetString(PyExc_AssertionError, \"\"); return NULL; }}")

    def visit_Pass(self, node):
        pass

    def visit_Global(self, node):
        pass

    def visit_Expr(self, node):
        if self.turbo: self._ensure_gil(locked=True)
        res = self._visit_expr(node.value)
        # If the expression returns a temporary object, we must decref it as it's not being used
        if isinstance(res, str) and res.startswith("tmp_"):
            if self.temp_types.get(res) == "PyObject*":
                self._add_line(f"Py_XDECREF({res});")
        if self.turbo: self._ensure_gil(locked=False)

    def visit_Nonlocal(self, node):
        pass

    def visit_Raise(self, node):
        if self.turbo: self._ensure_gil(locked=True)
        if node.exc:
            val = self._visit_expr(node.exc, as_obj=True)
            self._add_line(f"PyErr_SetObject((PyObject*)Py_TYPE({val}), {val});")
        else:
            self._add_line("PyErr_SetString(PyExc_RuntimeError, \"Exception raised in BCC\");")
        self._add_line("return NULL;")

    def visit_Continue(self, node):
        # Continue jumps to start of current loop.
        # Cleanup 'with' blocks entered inside THIS loop.
        if self.cleanup_stack:
             for cleanup, depth in reversed(self.cleanup_stack):
                 if depth >= self.loop_depth:
                     self._add_line(cleanup)
                 else:
                     break
        self._add_line("continue;")

    def visit_Try(self, node):
        # Improved Try/Except with goto labels and exception binding
        label_id = self.temp_count
        self.temp_count += 1
        except_label = f"except_{label_id}"
        end_label = f"end_try_{label_id}"

        prev_error_label = self.error_label
        self.error_label = except_label

        self._add_line(f"// try {label_id}")
        for stmt in node.body:
             self.visit(stmt)

        self.error_label = prev_error_label
        self._add_line(f"goto {end_label};")

        self._add_line(f"{except_label}:")
        self._add_line("if (PyErr_Occurred()) {")
        self.indent += 1

        # We assume handlers are checked in order
        for handler in node.handlers:
            if handler.type:
                # Check type
                type_node = self._visit_expr(handler.type)
                self._add_line(f"if (PyErr_ExceptionMatches({type_node})) {{")
                self.indent += 1

                # If name is present, we must bind it
                if handler.name:
                    # To bind, we must fetch the exception
                    # Note: PyErr_Fetch clears the exception state!
                    self._add_line("PyObject *etype, *evalue, *etrace;")
                    self._add_line("PyErr_Fetch(&etype, &evalue, &etrace);")
                    self._add_line("PyErr_NormalizeException(&etype, &evalue, &etrace);")
                    # Bind to python variable
                    # bcc usually uses py_varname for PyObject*
                    self._add_line(f"PyObject* py_{handler.name} = evalue;")
                    self._add_line(f"Py_INCREF(py_{handler.name});")
                    # Cleanup fetched refs
                    self._add_line("Py_XDECREF(etype); Py_XDECREF(evalue); Py_XDECREF(etrace);")
                else:
                    self._add_line("PyErr_Clear();") # Just consume it

                for stmt in handler.body:
                    self.visit(stmt)
                self.indent -= 1
                self._add_line("} else")
            else:
                # Catch all
                self._add_line("{")
                self.indent += 1
                self._add_line("PyErr_Clear();")
                for stmt in handler.body:
                    self.visit(stmt)
                self.indent -= 1
                self._add_line("}")

        # If no handler matched, we fall through here.
        # If we didn't clear the exception, it propagates naturally!
        # C-API: If PyErr_Occurred() is true and we return NULL, it propagates.
        # But wait, we emitted "if (PyErr_Occurred()) { ... }".
        # If no handler matched, we exit that block.
        # Then we hit `end_label`.
        # At `end_label`, if PyErr_Occurred() is still true, we should return NULL to propagate.
        self._add_line("{ /* If not handled, we fall through with exception set */ }")

        self.indent -= 1
        self._add_line("}")
        self._add_line(f"if (PyErr_Occurred()) return NULL;") # Propagate unhandled
        self._add_line(f"{end_label}: ;")

    def visit_With(self, node):
        for item in node.items:
            ctx_expr = self._visit_expr(item.context_expr)
            if self.turbo: self._ensure_gil(locked=True)

            mgr_name = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {mgr_name} = {ctx_expr};")

            # Error check
            if self.error_label: self._add_line(f"if (!{mgr_name}) goto {self.error_label};")
            else: self._add_line(f"if (!{mgr_name}) return NULL;")

            # __enter__
            enter_res = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {enter_res} = PyObject_CallMethod({mgr_name}, \"__enter__\", NULL);")
            if self.error_label: self._add_line(f"if (!{enter_res}) goto {self.error_label};")
            else: self._add_line(f"if (!{enter_res}) return NULL;")

            if item.optional_vars:
                 if isinstance(item.optional_vars, ast.Name):
                     target_id = item.optional_vars.id
                     if target_id in self.raw_types:
                          rtype = self.raw_types[target_id]
                          if rtype == "double":
                              self._add_line(f"{target_id} = PyFloat_AsDouble({enter_res});")
                          else:
                              self._add_line(f"{target_id} = PyLong_AsLong({enter_res});")
                     else:
                          self._add_line(f"py_{target_id} = {enter_res};")
                          self._add_line(f"Py_INCREF(py_{target_id});")

            if self.turbo: self._ensure_gil(locked=True)

            # Register cleanup
            cleanup_code = f"PyObject* exit_res_{mgr_name} = PyObject_CallMethod({mgr_name}, \"__exit__\", \"OOO\", Py_None, Py_None, Py_None); Py_XDECREF(exit_res_{mgr_name}); Py_DECREF({mgr_name}); Py_DECREF({enter_res});"
            self.cleanup_stack.append((cleanup_code, self.loop_depth))

            # Body
            for stmt in node.body:
                self.visit(stmt)

            # Pop cleanup and execute
            self.cleanup_stack.pop()
            if self.turbo: self._ensure_gil(locked=True)
            self._add_line(cleanup_code)
            if self.turbo: self._ensure_gil(locked=True)

    def visit_Import(self, node):
        if self.turbo: self._ensure_gil(locked=True)
        for alias in node.names:
            name = alias.name
            target = alias.asname if alias.asname else alias.name
            self._add_line(f"py_{target} = PyImport_ImportModule(\"{name}\");")
            self._add_check(f"py_{target}", f"Failed to import {name}")

    def visit_ImportFrom(self, node):
        if self.turbo: self._add_line("")
        module_name = node.module
        mod_temp = self._get_temp(is_obj=True)
        self._add_line(f"PyObject* {mod_temp} = PyImport_ImportModule(\"{module_name}\");")
        self._add_check(mod_temp, f"Failed to import from {module_name}")
        for alias in node.names:
            name = alias.name
            target = alias.asname if alias.asname else alias.name
            self._add_line(f"py_{target} = PyObject_GetAttrString({mod_temp}, \"{name}\");")
            self._add_check(f"py_{target}", f"Failed to get {name} from {module_name}")
        self._add_line(f"Py_DECREF({mod_temp});")
        if self.turbo: self._add_line("")

    def visit_AugAssign(self, node):
        needs_gil = self._expr_needs_gil(node.value)
        if hasattr(node.target, 'id') and node.target.id not in self.raw_types: needs_gil = True
        elif not hasattr(node.target, 'id'): needs_gil = True
        
        if self.turbo and needs_gil: self._ensure_gil(locked=True)
        if isinstance(node.target, ast.Name) and node.target.id in self.raw_types:
            r = self._visit_expr(node.value)
            rtype = self.raw_types[node.target.id]
            r_raw = r
            if not self._is_raw_val(r):
                if rtype == "double": r_raw = f"(PyFloat_Check({r}) ? PyFloat_AsDouble({r}) : (double)PyLong_AsLong({r}))"
                else: r_raw = f"PyLong_AsLong({r})"
            
            op_map = {'Add':'+', 'Sub':'-', 'Mult':'*', 'Div':'/', 'FloorDiv':'/', 'Mod':'%', 'BitAnd':'&', 'BitOr':'|', 'BitXor':'^', 'LShift':'<<', 'RShift':'>>'}
            op_name = node.op.__class__.__name__
            if op_name in op_map:
                op = op_map[op_name]
                if op_name == 'Pow': self._add_line(f"{node.target.id} = pow((double){node.target.id}, (double){r_raw});")
                elif op_name == 'FloorDiv': self._add_line(f"{node.target.id} = floor((double){node.target.id} / (double){r_raw});")
                elif op_name in ('BitAnd', 'BitOr', 'BitXor', 'LShift', 'RShift', 'Mod'):
                     # Use unsigned masking for bitwise ops if possible, but keep it simple
                     self._add_line(f"{node.target.id} = ({rtype})((unsigned long){node.target.id} {op} (unsigned long){r_raw});")
                else: self._add_line(f"{node.target.id} {op}= ({rtype}){r_raw};")
            if self.turbo and needs_gil: self._ensure_gil(locked=False)
            return

        # Object augmented assignment
        if self.turbo: self._ensure_gil(locked=True)
        target_obj = self._visit_expr(node.target, as_obj=True)
        val_obj = self._visit_expr(node.value, as_obj=True)
        ops = {
            'Add':'PyNumber_InPlaceAdd', 'Sub':'PyNumber_InPlaceSubtract', 'Mult':'PyNumber_InPlaceMultiply',
            'Div':'PyNumber_InPlaceTrueDivide', 'Pow':'PyNumber_InPlacePower', 'FloorDiv':'PyNumber_InPlaceFloorDivide',
            'Mod':'PyNumber_InPlaceRemainder', 'MatMult': 'PyNumber_InPlaceMatrixMultiply',
            'BitAnd': 'PyNumber_InPlaceAnd', 'BitOr': 'PyNumber_InPlaceOr', 'BitXor': 'PyNumber_InPlaceXor',
            'LShift': 'PyNumber_InPlaceLshift', 'RShift': 'PyNumber_InPlaceRshift'
        }
        api_func = ops.get(node.op.__class__.__name__, 'PyNumber_InPlaceAdd')
        
        # For targets, we need to handle name vs attribute vs subscript
        if isinstance(node.target, ast.Name):
             tmp_res = self._get_temp(is_obj=True)
             self._add_line(f"PyObject* {tmp_res} = {api_func}({target_obj}, {val_obj});")
             self._add_line(f"Py_XDECREF(py_{node.target.id}); py_{node.target.id} = {tmp_res};")
        elif isinstance(node.target, ast.Subscript):
             obj = self._visit_expr(node.target.value, as_obj=True)
             idx = self._visit_expr(node.target.slice)
             if self._is_raw_val(idx): idx = f"PyLong_FromLong((long){idx})"
             res = self._get_temp(is_obj=True)
             self._add_line(f"PyObject* {res} = {api_func}({target_obj}, {val_obj});")
             self._add_line(f"PyObject_SetItem({obj}, {idx}, {res});")
             self._add_line(f"Py_DECREF({res});")
        
        if self.turbo: self._ensure_gil(locked=False)

    def _is_raw_val(self, val):
        if isinstance(val, (int, float)): return True
        if not isinstance(val, str): return False
        if val in self.raw_types: return True
        if val in self.temp_types and self.temp_types[val] in ("double", "long", "int64_t"): return True
        if val.replace(".","").replace("-","").replace("f", "").isdigit(): return True
        # Track bitwise, comparison, math and logical ops as raw if they don't contain "Py"
        raw_markers = ['+', '-', '*', '/', '<', '>', '=', '&', '|', '^', '!', 'fabs', 'pow', '~', '%', '&&', '||',
                       'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh', 'exp', 'log', 'log1p', 'sqrt', 'ceil', 'floor']
        if ("(" in val and ")" in val and any(op in val for op in raw_markers)) and "Py" not in val: return True
        return False

    def _visit_expr(self, node, as_obj=False):
        if isinstance(node, ast.Constant):
            if as_obj:
                 if isinstance(node.value, bool): return "Py_True" if node.value else "Py_False"
                 if isinstance(node.value, int): return f"PyLong_FromLong({node.value})"
                 if isinstance(node.value, float): return f"PyFloat_FromDouble({node.value})"
                 return "Py_None" if node.value is None else f"PyUnicode_FromString(\"{node.value}\")"
            if isinstance(node.value, bool): return "Py_True" if node.value else "Py_False"
            if isinstance(node.value, int): return str(node.value) if self.turbo else f"PyLong_FromLong({node.value})"
            if isinstance(node.value, float): return str(node.value) if self.turbo else f"PyFloat_FromDouble({node.value})"
            return "Py_None" if node.value is None else f"PyUnicode_FromString(\"{node.value}\")"
        elif isinstance(node, ast.Name):
            if as_obj: 
                # If it's a raw pointer, we can't easily make an object out of it without more context
                # but we usually have a py_ version!
                # EXCEPT for loop variables like 'i' in range.
                if node.id in self.raw_types and self.raw_types[node.id] == "double* ":
                    return f"py_{node.id}"
                if node.id in self.raw_types:
                    rtype = self.raw_types[node.id]
                    if rtype == "double": return f"PyFloat_FromDouble((double){node.id})"
                    return f"PyLong_FromLong((long){node.id})"
                return f"py_{node.id}"
            return node.id if node.id in self.raw_types else f"py_{node.id}"
        elif isinstance(node, ast.BinOp):
            left = self._visit_expr(node.left); right = self._visit_expr(node.right)
            op_name = node.op.__class__.__name__
            if self.turbo and self._is_raw_val(left) and self._is_raw_val(right):
                op_map = {'Add':'+', 'Sub':'-', 'Mult':'*', 'Div':'/', 'FloorDiv':'/', 'Mod':'%', 'BitAnd':'&', 'BitOr':'|', 'BitXor':'^', 'LShift':'<<', 'RShift':'>>'}
                if op_name in op_map:
                    op = op_map[op_name]
                    if op_name == 'Pow':
                        return f"pow((double){left}, (double){right})"
                    if op_name == 'FloorDiv':
                        return f"floor((double){left} / (double){right})"
                    if op_name in ('BitAnd', 'BitOr', 'BitXor', 'LShift', 'RShift', 'Mod'):
                        if op_name == 'BitAnd' and str(right) == '4294967295':
                            return f"((int64_t)((uint32_t){left}))"
                        return f"((int64_t)((int64_t){left} {op} (int64_t){right}))"
                    return f"({left} {op} {right})"
                # Fallthrough if op not supported in raw mode (e.g. MatMult)

            ops = {
                'Add':'PyNumber_Add', 'Sub':'PyNumber_Subtract', 'Mult':'PyNumber_Multiply',
                'Div':'PyNumber_TrueDivide', 'Pow':'PyNumber_Power', 'FloorDiv':'PyNumber_FloorDivide',
                'Mod':'PyNumber_Remainder', 'MatMult': 'PyNumber_MatrixMultiply',
                'BitAnd': 'PyNumber_And', 'BitOr': 'PyNumber_Or', 'BitXor': 'PyNumber_Xor',
                'LShift': 'PyNumber_Lshift', 'RShift': 'PyNumber_Rshift'
            }
            api_func = ops.get(op_name, 'PyNumber_Add')
            lo = self._visit_expr(node.left, as_obj=True)
            ro = self._visit_expr(node.right, as_obj=True)
            t = self._get_temp(is_obj=True)
            if api_func == 'PyNumber_Power': self._add_line(f"PyObject* {t} = {api_func}({lo}, {ro}, Py_None);")
            else: self._add_line(f"PyObject* {t} = {api_func}({lo}, {ro});")
            return t
        elif isinstance(node, ast.UnaryOp):
            v = self._visit_expr(node.operand)
            if self.turbo and self._is_raw_val(v):
                op_map = {'USub':'-', 'UAdd':'+', 'Not':'!', 'Invert':'~'}
                op = op_map.get(node.op.__class__.__name__, '-')
                if op == '~': return f"(~((long){v}))"
                return f"({op}{v})"
            t = self._get_temp(is_obj=True)
            vo = v if not self._is_raw_val(v) else f"PyFloat_FromDouble((double){v})"
            ops = {'USub':'PyNumber_Negative', 'UAdd':'PyNumber_Positive', 'Not':'PyObject_Not', 'Invert':'PyNumber_Invert'}.get(node.op.__class__.__name__, 'PyNumber_Negative')
            if ops == 'PyObject_Not': self._add_line(f"PyObject* {t} = {ops}({vo}) ? Py_True : Py_False; Py_XINCREF({t});")
            else: self._add_line(f"PyObject* {t} = {ops}({vo});")
            return t
        elif isinstance(node, ast.BoolOp):
            # Short-circuiting is hard in C expressions, so we use temp vars
            t = self._get_temp(is_obj=self.turbo) # Use obj for bool op result if not handled as raw
            op = "&&" if isinstance(node.op, ast.And) else "||"
            vals = [self._visit_expr(v) for v in node.values]
            if self.turbo and all(self._is_raw_val(v) for v in vals):
                return "(" + f" {op} ".join([f"(int)({v})" for v in vals]) + ")"
            # Fallback to PyObject approach if any is complex
            rt = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {rt} = {vals[0] if not self._is_raw_val(vals[0]) else f'PyFloat_FromDouble((double){vals[0]})'};")
            for v in vals[1:]:
                cond = f"PyObject_IsTrue({rt})"
                if isinstance(node.op, ast.And): self._add_line(f"if ({cond}) {{ {rt} = {v if not self._is_raw_val(v) else f'PyFloat_FromDouble((double){v})'}; }}")
                else: self._add_line(f"if (!{cond}) {{ {rt} = {v if not self._is_raw_val(v) else f'PyFloat_FromDouble((double){v})'}; }}")
            return rt
        elif isinstance(node, ast.Compare):
            l = self._visit_expr(node.left); r = self._visit_expr(node.comparators[0])
            op_name = node.ops[0].__class__.__name__
            if self.turbo and self._is_raw_val(l) and self._is_raw_val(r):
                op_map = {'Lt':'<', 'LtE':'<=', 'Gt':'>', 'GtE':'>=', 'Eq':'==', 'NotEq':'!='}
                if op_name in op_map:
                    op = op_map[op_name]
                    return f"({l} {op} {r})"

            # Object comparison
            t = self._get_temp(is_obj=False)
            lo = self._visit_expr(node.left, as_obj=True)
            ro = self._visit_expr(node.comparators[0], as_obj=True)

            if op_name == 'In':
                self._add_line(f"int {t} = PySequence_Contains({ro}, {lo});") # Note: In(a, b) -> b contains a
            elif op_name == 'NotIn':
                self._add_line(f"int {t} = !PySequence_Contains({ro}, {lo});")
            elif op_name == 'Is':
                self._add_line(f"int {t} = ({lo} == {ro});")
            elif op_name == 'IsNot':
                self._add_line(f"int {t} = ({lo} != {ro});")
            else:
                op_map = {'Lt':'Py_LT', 'LtE':'Py_LE', 'Gt':'Py_GT', 'GtE':'Py_GE', 'Eq':'Py_EQ', 'NotEq':'Py_NE'}
                op = op_map.get(op_name, 'Py_EQ')
                self._add_line(f"int {t} = PyObject_RichCompareBool({lo}, {ro}, {op});")

            return t
        elif isinstance(node, ast.Subscript):
            owner = self._visit_expr(node.value)
            # If it's a raw buffer and we have a raw index, use raw access
            if owner in self.buffer_views and not isinstance(node.slice, ast.Slice):
                idx = self._visit_expr(node.slice)
                if self._is_raw_val(idx):
                    v = self.buffer_views[owner]
                    cast_type = "double*" if self.turbo else "uint8_t*" # simple fallback
                    # Use itemsize to decide
                    buf_access = f"((uint8_t*){v}.buf)[(long){idx}]"
                    if self.turbo: # In turbo mode we usually want numeric access
                        buf_access = f"({v}.itemsize == 8 ? ((double*){v}.buf)[(long){idx}] : (double)((uint8_t*){v}.buf)[(long){idx}])"
                    
                    if as_obj: return f"PyFloat_FromDouble((double){buf_access})"
                    return buf_access

            # Fallback to C-API
            if self.turbo: self._ensure_gil(locked=True)
            obj = self._visit_expr(node.value, as_obj=True)
            idx = self._visit_expr(node.slice, as_obj=True)
            t = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {t} = PyObject_GetItem({obj}, {idx});")
            self._add_check(t, "Subscript get item error")
            if not as_obj:
               # Try to convert to raw if appropriate, but usually we just return the object
               pass
            return t
        elif isinstance(node, ast.Attribute):
            val = self._visit_expr(node.value, as_obj=True)
            t = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {t} = PyObject_GetAttrString({val}, \"{node.attr}\");")
            self._add_check(t, f"Attribute error: {node.attr}")
            return t
        elif isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Name): func_name = node.func.id
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "math":
                func_name = node.func.attr

            if func_name == 'len':
                an = node.args[0].id
                if an in self.buffer_views:
                    vn = self.buffer_views[an]
                    # Python len() returns element count, so we divide by itemsize
                    return f"(int64_t)({vn}.len / {vn}.itemsize)"
                if self.turbo: self._ensure_gil(locked=True)
                tx = self._get_temp(is_obj=False)
                self._add_line(f"int64_t {tx} = PyObject_Length(py_{an});")
                if self.turbo: self._ensure_gil(locked=False)
                return tx if self.turbo else f"PyLong_FromLong({tx})"
            
            if func_name in ('sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh', 'exp', 'log', 'log1p', 'log10', 'sqrt', 'ceil', 'floor', 'fabs', 'abs'):
                arg = self._visit_expr(node.args[0])
                if self.turbo and self._is_raw_val(arg):
                    if func_name == 'abs': return f"fabs((double){arg})"
                    if func_name == 'log1p': return f"log1p((double){arg})"
                    return f"{func_name}((double){arg})"
                
                t = self._get_temp(is_obj=True)
                ao = arg if not self._is_raw_val(arg) else f"PyFloat_FromDouble((double){arg})"
                if func_name == 'abs': self._add_line(f"PyObject* {t} = PyNumber_Absolute({ao});")
                elif func_name == 'int': self._add_line(f"PyObject* {t} = PyNumber_Long({ao});")
                elif func_name == 'float': self._add_line(f"PyObject* {t} = PyNumber_Float({ao});")
                else:
                    self._add_line(f"double v_arg = PyFloat_AsDouble({ao});")
                    self._add_line(f"double v_res = {func_name}(v_arg);")
                    self._add_line(f"PyObject* {t} = PyFloat_FromDouble(v_res);")
                return t
            elif func_name in ('int', 'float'):
                arg = self._visit_expr(node.args[0])
                if self.turbo and self._is_raw_val(arg): return arg
                t = self._get_temp(is_obj=True)
                ao = arg if not self._is_raw_val(arg) else f"PyFloat_FromDouble((double){arg})"
                if func_name == 'int': self._add_line(f"PyObject* {t} = PyNumber_Long({ao});")
                else: self._add_line(f"PyObject* {t} = PyNumber_Float({ao});")
                return t
            elif func_name in ('min', 'max') and len(node.args) == 2:
                l = self._visit_expr(node.args[0]); r = self._visit_expr(node.args[1])
                if self.turbo and self._is_raw_val(l) and self._is_raw_val(r):
                    op = ">" if func_name == 'max' else "<"
                    return f"(({l} {op} {r}) ? {l} : {r})"
                t = self._get_temp(is_obj=True)
                lo = l if not self._is_raw_val(l) else f"PyFloat_FromDouble((double){l})"
                ro = r if not self._is_raw_val(r) else f"PyFloat_FromDouble((double){r})"
                cmp_op = 'Py_GT' if func_name == 'max' else 'Py_LT'
                self._add_line(f"PyObject* {t} = PyObject_RichCompareBool({lo}, {ro}, {cmp_op}) ? {lo} : {ro}; Py_XINCREF({t});")
                return t
            
            if self.turbo: self._ensure_gil(locked=True)
            t = self._get_temp(is_obj=True)
            func_obj = self._visit_expr(node.func, as_obj=True)
            
            # Build arguments tuple
            args_name = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {args_name} = PyTuple_New({len(node.args)});")
            for i, arg in enumerate(node.args):
                ao = self._visit_expr(arg, as_obj=True)
                # PyTuple_SetItem steals a reference. Ensure we own it!
                if not ao.startswith("tmp_") and "Py" not in ao:
                    self._add_line(f"Py_XINCREF({ao});")
                self._add_line(f"PyTuple_SetItem({args_name}, {i}, {ao});")
            
            # Build keywords dict
            kw_name = "NULL"
            if node.keywords:
                kw_name = self._get_temp(is_obj=True)
                self._add_line(f"PyObject* {kw_name} = PyDict_New();")
                for kw in node.keywords:
                    ko = self._visit_expr(kw.value, as_obj=True)
                    self._add_line(f"PyDict_SetItemString({kw_name}, \"{kw.arg}\", {ko});")
            
            self._add_line(f"PyObject* {t} = PyObject_Call({func_obj}, {args_name}, {kw_name});")
            self._add_line(f"Py_DECREF({args_name}); if ({kw_name}) Py_DECREF({kw_name});")
            return t
        elif isinstance(node, (ast.List, ast.Tuple)):
            is_list = isinstance(node, ast.List)
            t = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {t} = {'PyList_New' if is_list else 'PyTuple_New'}({len(node.elts)});")
            for i, e in enumerate(node.elts):
                v = self._visit_expr(e); vo = v if not self._is_raw_val(v) else f"PyFloat_FromDouble((double){v})"
                # Steals reference
                if not vo.startswith("tmp_") and "Py" not in vo:
                    self._add_line(f"Py_XINCREF({vo});")
                self._add_line(f"{'PyList_SetItem' if is_list else 'PyTuple_SetItem'}({t}, {i}, {vo});")
            return t
        elif isinstance(node, ast.Dict):
             t = self._get_temp(is_obj=True)
             self._add_line(f"PyObject* {t} = PyDict_New();")
             for k, v in zip(node.keys, node.values):
                 if k:
                     ko = self._visit_expr(k, as_obj=True); vo = self._visit_expr(v, as_obj=True)
                     self._add_line(f"PyDict_SetItem({t}, {ko}, {vo});")
                     if ko.startswith("tmp_"): self._add_line(f"Py_DECREF({ko});")
                     if vo.startswith("tmp_"): self._add_line(f"Py_DECREF({vo});")
             return t
        elif isinstance(node, ast.Set):
             t = self._get_temp(is_obj=True)
             self._add_line(f"PyObject* {t} = PySet_New(NULL);")
             for e in node.elts:
                 v = self._visit_expr(e, as_obj=True)
                 self._add_line(f"PySet_Add({t}, {v});")
                 if v.startswith("tmp_"): self._add_line(f"Py_DECREF({v});")
             return t
        elif isinstance(node, ast.Slice):
            lower = self._visit_expr(node.lower) if node.lower else "Py_None"
            upper = self._visit_expr(node.upper) if node.upper else "Py_None"
            step = self._visit_expr(node.step) if node.step else "Py_None"
            
            l_obj = lower if (not self._is_raw_val(lower) or lower == "Py_None") else f"PyLong_FromLong((long){lower})"
            u_obj = upper if (not self._is_raw_val(upper) or upper == "Py_None") else f"PyLong_FromLong((long){upper})"
            s_obj = step if (not self._is_raw_val(step) or step == "Py_None") else f"PyLong_FromLong((long){step})"
            
            t = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {t} = PySlice_New({l_obj}, {u_obj}, {s_obj});")
            return t
        elif isinstance(node, ast.JoinedStr):
            if self.turbo: self._ensure_gil(locked=True)
            t = self._get_temp(is_obj=True)
            parts_list = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {parts_list} = PyList_New(0);")
            for part in node.values:
                po = self._visit_expr(part, as_obj=True)
                self._add_line(f"PyList_Append({parts_list}, {po});")
                if po.startswith("tmp_"):
                    self._add_line(f"Py_DECREF({po});")
            empty_str = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {empty_str} = PyUnicode_FromString(\"\");")
            self._add_line(f"PyObject* {t} = PyUnicode_Join({empty_str}, {parts_list});")
            self._add_line(f"Py_DECREF({empty_str});")
            self._add_line(f"Py_DECREF({parts_list});")
            return t
        elif isinstance(node, ast.FormattedValue):
            vo = self._visit_expr(node.value, as_obj=True)
            t = self._get_temp(is_obj=True)
            self._add_line(f"PyObject* {t} = PyObject_Str({vo});")
            if vo.startswith("tmp_"):
                self._add_line(f"Py_DECREF({vo});")
            return t
        elif isinstance(node, (ast.ListComp, ast.GeneratorExp)):
            return "Py_None" # Fallback for now, just to allow it in functions
        return "Py_None"

def generate_c_source(module_name, functions, turbo=False, mapping=None):
    gen = CGenerator(module_name, turbo=turbo, mapping=mapping)
    gen.c_code.append("#define PY_SSIZE_T_CLEAN\n#include <Python.h>\n#include <math.h>\n#include <stdint.h>\n#include <inttypes.h>")
    for f in functions:
        if isinstance(f, tuple): gen.generate(f[1], original_name=f[0])
        else: gen.generate(f)
    ml = [f'{{"{fn}", (PyCFunction)bcc_{fn}, METH_VARARGS | METH_KEYWORDS, NULL}}' for fn in gen.functions]
    gen.c_code.append("static PyMethodDef BCCMethods[] = {\n    " + ",\n    ".join(ml) + ",\n    {NULL, NULL, 0, NULL}\n};\n")
    gen.c_code.append(f"static struct PyModuleDef bcc_m = {{PyModuleDef_HEAD_INIT, \"{module_name}\", NULL, -1, BCCMethods}};\nPyMODINIT_FUNC PyInit_{module_name}(void) {{return PyModule_Create(&bcc_m);}}")
    return "\n".join(gen.c_code)
