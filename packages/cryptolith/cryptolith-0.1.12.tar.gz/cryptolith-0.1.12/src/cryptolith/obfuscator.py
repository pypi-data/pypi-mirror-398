import ast
import random
import string
import base64
import os
import re
import uuid

class SymbolCollector(ast.NodeVisitor):
    def __init__(self, mapping=None, used_names=None, exclude_names=None, private_mode=False):
        self.mapping = mapping if mapping is not None else {}
        self.used_names = used_names if used_names is not None else set()
        self.exclude_names = exclude_names if exclude_names is not None else set()
        self.private_mode = private_mode
        self.internal_funcs = set()
        self.internal_attrs = set()
        self.reserved_names = {
            'self', 'cls', '__init__', '__main__', 'base64', 'cryptolith', 'sys', 'datetime', 'uuid', 'urllib', 'json', 'socket', 'zstd',
            'start', 'join', 'len', 'range', 'print', 'sum', 'min', 'max', 'int', 'float', 'str', 'list', 'dict', 'set', 'tuple', 'open', 
            'threading', 'numpy', 'np', 'append', 'extend', 'insert', 'pop', 'remove', 'clear', 'index', 'count', 'sort', 'reverse', 
            'copy', 'keys', 'values', 'items', 'get', 'update', 'split', 'strip', 'lower', 'upper', 'replace', 'find', 'join',
            # unittest hooks
            'setUp', 'tearDown', 'setUpClass', 'tearDownClass', 'runTest', 'skipTest', 'shortDescription',
            # Common test-related attributes and framework keywords
            'test_dir', 'project_dir', 'script', 'test_case', 'output_dir', 'dist_dir', 'build_dir',
            # Framework / Runtime Hooks
            'runtime_init', 'expiry', 'macs', 'ips', 'nts', 'asset_key', 'vm_map',
            'app', 'application', 'request', 'response', 'env', 'environ', 'context', 'meta',
            # Benchmark and common library attributes (Prevent BCC breakage)
            'Fernet', 'fernet', 'encrypt', 'decrypt', 'compress', 'decompress', 'ZstdCompressor', 'ZstdDecompressor',
            'frombuffer', 'astype', 'uint8', 'generate_key', 'hexdigest', 'sha256', 'ThreadPoolExecutor', 'submit', 'result',
            'DataProcessor', 'process_chunk', 'data', 'chunk_id', 'ival', 'compressed', 'encrypted', 'decrypted', 'decompressed'
        }
    
    def _generate_name(self):
        while True:
            name = ''.join(random.choices(string.ascii_letters, k=10))
            if name not in self.used_names and name not in self.reserved_names:
                self.used_names.add(name)
                return name

    def _add_to_mapping(self, name):
        if name and not name.startswith(('__', 'test_')) and name not in self.reserved_names and name not in self.exclude_names and name not in self.mapping:
            self.mapping[name] = self._generate_name()

    def visit_FunctionDef(self, node):
        self.internal_funcs.add(node.name)
        self.internal_attrs.add(node.name) # Methods are accessed as attributes
        self._add_to_mapping(node.name)
        for arg in node.args.args:
            self._add_to_mapping(arg.arg)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self._add_to_mapping(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        def _check_target(t):
            if isinstance(t, ast.Name):
                self._add_to_mapping(t.id)
            elif isinstance(t, ast.Attribute):
                if isinstance(t.value, ast.Name) and t.value.id == 'self':
                    self.internal_attrs.add(t.attr)
                    self._add_to_mapping(t.attr)
            elif isinstance(t, ast.Tuple) or isinstance(t, ast.List):
                for el in t.elts:
                    _check_target(el)

        for target in node.targets:
            _check_target(target)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        if isinstance(node.target, ast.Name):
            self._add_to_mapping(node.target.id)
        elif isinstance(node.target, ast.Attribute):
            if isinstance(node.target.value, ast.Name) and node.target.value.id == 'self':
                self.internal_attrs.add(node.target.attr)
                self._add_to_mapping(node.target.attr)
        self.generic_visit(node)

    def visit_For(self, node):
        def _check_target(t):
            if isinstance(t, ast.Name):
                self._add_to_mapping(t.id)
            elif isinstance(t, ast.Attribute):
                if isinstance(t.value, ast.Name) and t.value.id == 'self':
                    self.internal_attrs.add(t.attr)
                    self._add_to_mapping(t.attr)
            elif isinstance(t, ast.Tuple) or isinstance(t, ast.List):
                for el in t.elts:
                    _check_target(el)

        _check_target(node.target)
        self.generic_visit(node)

    def visit_With(self, node):
        for item in node.items:
            if isinstance(item.optional_vars, ast.Name):
                self._add_to_mapping(item.optional_vars.id)
        self.generic_visit(node)

class ControlFlowFlattener(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        if len(node.body) < 3: return node
        
        state_var = "".join(random.choices(string.ascii_letters, k=12))
        blocks = node.body
        
        # 1. Randomized State Mapping
        state_map = list(range(len(blocks)))
        random.shuffle(state_map)
        
        # Mapping from index in 'blocks' to its assigned state ID
        idx_to_state = {i: state_map[i] for i in range(len(blocks))}
        
        cases = []
        for i, stmt in enumerate(blocks):
            # The last block goes to -1 (exit)
            next_state = idx_to_state[i+1] if i < len(blocks) - 1 else -1
            
            # Sub-dispatcher logic: Update state
            case_body = [stmt, ast.Assign(targets=[ast.Name(id=state_var, ctx=ast.Store())], value=ast.Constant(value=next_state))]
            
            # 2. Add Opaque Predicates or Junk logic if complex enough
            if random.random() < 0.3:
                 junk = ast.Expr(value=ast.BinOp(left=ast.Constant(value=random.randint(1,100)), op=ast.Mult(), right=ast.Constant(value=0)))
                 case_body.insert(0, junk)

            cases.append(ast.If(test=ast.Compare(left=ast.Name(id=state_var, ctx=ast.Load()), ops=[ast.Eq()], comparators=[ast.Constant(value=idx_to_state[i])]), body=case_body, orelse=[]))

        # 3. Inject "Dead Blocks" (Junk cases that are never reached)
        for _ in range(2):
            dead_state = random.randint(1000, 9999)
            dead_body = [ast.Expr(value=ast.Call(func=ast.Name(id='print', ctx=ast.Load()), args=[ast.Constant(value='...')], keywords=[]))]
            cases.append(ast.If(test=ast.Compare(left=ast.Name(id=state_var, ctx=ast.Load()), ops=[ast.Eq()], comparators=[ast.Constant(value=dead_state)]), body=dead_body, orelse=[]))

        random.shuffle(cases) # Make static analysis even harder

        root_if = cases[0]
        curr = root_if
        for c in cases[1:]:
            curr.orelse = [c]
            curr = c

        node.body = [ast.Assign(targets=[ast.Name(id=state_var, ctx=ast.Store())], value=ast.Constant(value=idx_to_state[0])),
                     ast.While(test=ast.Compare(left=ast.Name(id=state_var, ctx=ast.Load()), ops=[ast.NotEq()], comparators=[ast.Constant(value=-1)]), body=[root_if], orelse=[])]
        return node

class ObfuscatorTransformer(ast.NodeTransformer):
    def __init__(self, mapping, xor_key, internal_funcs=None, internal_attrs=None, mix_str_pattern=None, runtime_module=None, enable_vm=False, is_pro=False, op_map=None):
        self.mapping = mapping
        self.xor_key = xor_key
        self.internal_funcs = internal_funcs if internal_funcs else set()
        self.internal_attrs = internal_attrs if internal_attrs else set()
        self.mix_str_pattern = mix_str_pattern
        self.runtime_module = runtime_module
        self.enable_vm = enable_vm
        self.is_pro = is_pro
        self.op_map = op_map
        self.string_pool = []
        self.joined_str_depth = 0
        self.get_helper_name = "".join(random.choices(string.ascii_letters, k=10))

    def _encrypt(self, s):
        data = s.encode('utf-8')
        enc = bytes([b ^ self.xor_key[i % len(self.xor_key)] for i, b in enumerate(data)])
        return base64.b64encode(enc).decode('utf-8')

    def _opaque_predicate(self):
        a = random.randint(1, 1000)
        return ast.If(
            test=ast.Compare(
                left=ast.BinOp(left=ast.Constant(value=a), op=ast.Mult(), right=ast.Constant(value=0)),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=0)]
            ),
            body=[ast.Expr(value=ast.Constant(value=None))],
            orelse=[ast.Raise(exc=ast.Call(func=ast.Name(id='RuntimeError', ctx=ast.Load()), args=[], keywords=[]))]
        )

    def visit_Import(self, node):
        for alias in node.names:
            if alias.asname and alias.asname in self.mapping:
                alias.asname = self.mapping[alias.asname]
        return node

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name in self.mapping:
                alias.name = self.mapping[alias.name]
            if alias.asname and alias.asname in self.mapping:
                alias.asname = self.mapping[alias.asname]
        return node

    def visit_Call(self, node):
        # Only rename keywords if it matches an internal project symbol
        # AND the call target itself is likely internal.
        is_internal_call = False
        if isinstance(node.func, ast.Name) and node.func.id in self.internal_funcs:
            is_internal_call = True
        
        for kw in node.keywords:
            if kw.arg in self.mapping:
                if is_internal_call:
                     kw.arg = self.mapping[kw.arg]
        self.generic_visit(node)
        return node

    def visit_Constant(self, node):
        if self.joined_str_depth > 0: return node
        if isinstance(node.value, str) and len(node.value) > 2:
            # ONLY encrypt strings if this is PRO edition
            if not self.is_pro: return node
            
            if self.mix_str_pattern and not re.search(self.mix_str_pattern, node.value): return node
            idx = len(self.string_pool)
            self.string_pool.append(self._encrypt(node.value))
            return ast.Call(func=ast.Name(id=self.get_helper_name, ctx=ast.Load()), args=[ast.Constant(value=idx)], keywords=[])
        
        if isinstance(node.value, int) and -1000 < node.value < 1000:
            a = random.randint(1, 100)
            return ast.BinOp(left=ast.Constant(value=a), op=ast.Add() if node.value >= a else ast.Sub(), 
                             right=ast.Constant(value=abs(node.value - a)))
        return node

    def visit_Name(self, node):
        if node.id in self.mapping: node.id = self.mapping[node.id]
        return node

    def visit_Attribute(self, node):
        if node.attr in self.mapping and node.attr in self.internal_attrs:
            node.attr = self.mapping[node.attr]
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        if node.name in self.mapping: node.name = self.mapping[node.name]
        for arg in node.args.args:
            if arg.arg in self.mapping: arg.arg = self.mapping[arg.arg]
        
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            if isinstance(node.body[0].value.value, str): node.body.pop(0)
            
        if len(node.body) > 1:
            node.body.insert(random.randint(0, len(node.body)-1), self._opaque_predicate())
            
        # SCATTERED INTEGRITY CHECK: Inject 20% of the time into non-empty functions
        if self.runtime_module and len(node.body) > 0 and random.random() < 0.2:
             check_call = ast.Expr(value=ast.Call(
                 func=ast.Attribute(value=ast.Name(id=self.runtime_module, ctx=ast.Load()), attr='verify', ctx=ast.Load()),
                 args=[], keywords=[]
             ))
             node.body.insert(random.randint(0, len(node.body)-1), check_call)
            
        if self.enable_vm and self.is_pro and len(node.body) > 0 and not node.name.startswith('__'):
            from cryptolith.virtualizer import virtualize_function
            try:
                vm_data = virtualize_function(node, mapping=self.mapping, op_map=self.op_map)
                if vm_data:
                    bytecode, constants, names = vm_data
                    # Replace body with vm_run call
                    node.body = [ast.Return(value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id=self.runtime_module, ctx=ast.Load()), attr='vm_run', ctx=ast.Load()),
                        args=[
                            ast.Constant(value=bytecode),
                            ast.Tuple(elts=[ast.Constant(value=c) for c in constants], ctx=ast.Load()),
                            ast.List(elts=[ast.Constant(value=n) for n in names], ctx=ast.Load()),
                            ast.Call(func=ast.Name(id='globals', ctx=ast.Load()), args=[], keywords=[]),
                            ast.Call(func=ast.Name(id='locals', ctx=ast.Load()), args=[], keywords=[])
                        ],
                        keywords=[]
                    ))]
                    # Fix: After replacing the body, we MUST fix missing locations
                    # And then let the transformer visit the NEW body (the vm_run call)
                    # so that constants in the constants list are encrypted.
                    ast.fix_missing_locations(node)
                    # We don't return early here, we let generic_visit handle the new body
            except Exception as e:
                # Fallback to standard obfuscation if virtualization fails
                pass

        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        if node.name in self.mapping: node.name = self.mapping[node.name]
        self.generic_visit(node)
        return node

    def visit_JoinedStr(self, node):
        self.joined_str_depth += 1
        self.generic_visit(node)
        self.joined_str_depth -= 1
        return node

def is_bcc_compatible(node):
    # Strict check for nodes supported by CGenerator
    supported_nodes = (
        ast.FunctionDef, ast.Return, ast.Assign, ast.AugAssign, ast.For, ast.While, ast.If, ast.Expr,
        ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Name, ast.Constant, ast.Subscript, 
        ast.Index, ast.Load, ast.Store, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.FloorDiv, ast.Mod,
        ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift,
        ast.And, ast.Or, ast.USub, ast.UAdd, ast.Not, ast.Invert,
        ast.Compare, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq,
        ast.Call, ast.List, ast.Tuple, ast.arg, ast.arguments, ast.keyword, ast.Starred,
        ast.Break, ast.Continue, ast.Attribute, ast.Dict, ast.Set,
        ast.Assert, ast.Pass, ast.Raise,
        ast.Slice, ast.Index, 
        ast.Import, ast.ImportFrom, ast.alias, ast.Global, ast.Nonlocal,
        ast.JoinedStr, ast.FormattedValue
    )
    
    for child in ast.walk(node):
        if not isinstance(child, supported_nodes):
            print(f"BCC COMPATIBILITY FAILURE: Unsupported node {type(child)} in {getattr(node, 'name', 'unknown')}")
            return False
    return True

class BCCCandidateExtractor(ast.NodeTransformer):
    def __init__(self):
        self.candidates = []
    
    def visit_FunctionDef(self, node):
        if node.name.startswith('__'):
            return self.generic_visit(node)
            
        source = ast.unparse(node)
        if 'for ' in source and ('[' in source or '+=' in source or '*=' in source):
            if is_bcc_compatible(node):
                # Tag for later stubbing
                node._bcc_compile = True
                
                # Identify used globals to inject imports
                used_globals = set()
                STDLIB_MODULES = (
                    'hashlib', 'math', 'os', 'sys', 'time', 'random', 'zstandard', 'cryptography',
                    'numpy', 'np', 'threading', 'json', 'pickle', 'io', 'binascii'
                )
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                        if child.id in STDLIB_MODULES:
                            used_globals.add(child.id)
                
                # Inject imports at the top
                for g in sorted(used_globals):
                    module_name = 'numpy' if g == 'np' else g
                    alias_name = 'np' if g == 'np' else None
                    imp = ast.Import(names=[ast.alias(name=module_name, asname=alias_name)])
                    node.body.insert(0, imp)
                
                self.candidates.append((node.name, node))
        
        return self.generic_visit(node)

def extract_bcc_candidates(tree):
    extractor = BCCCandidateExtractor()
    tree = extractor.visit(tree)
    return tree, extractor.candidates

def _process_file_parsing(f_path, code_dict, bcc):
    if code_dict and f_path in code_dict:
        source = code_dict[f_path]
    else:
        with open(f_path, 'r', encoding='utf-8') as f:
            source = f.read()
    tree = ast.parse(source)
    candidates = []
    if bcc:
        tree, candidates = extract_bcc_candidates(tree)
    return f_path, tree, candidates

class BCCStubTransformer(ast.NodeTransformer):
    def __init__(self, mod_name, bcc_funcs):
        self.mod_name = mod_name
        self.bcc_func_names = {f[0] for f in bcc_funcs}
        
    def visit_FunctionDef(self, node):
        if hasattr(node, '_bcc_compile') or node.name in self.bcc_func_names:
            # Replace body with stub
            arg_list = [a.arg for a in node.args.args]
            args_str = ", ".join(arg_list)
            args_join = args_str + ", " if args_str else ""
            node.body = [ast.parse(f"import {self.mod_name}\nreturn {self.mod_name}.{node.name}({args_join}_bcc_globals=globals())").body[1]]
            node.body.insert(0, ast.Import(names=[ast.alias(name=self.mod_name, asname=None)]))
            # Clear tag to avoid double processing
            if hasattr(node, '_bcc_compile'): del node._bcc_compile
            
        return self.generic_visit(node)

def _process_file_transformation(f_path, tree, mapping, xor_key, internal_funcs, internal_attrs, mix_str_pattern, runtime_module, enable_vm, is_pro, bcc_mod_info, bcc_functions, helper_tree, junk_tree, key_b64, op_map=None):
    from cryptolith.obfuscator import ObfuscatorTransformer, ControlFlowFlattener
    import ast
    import random
    import string
    
    transformer = ObfuscatorTransformer(
        mapping, xor_key, internal_funcs, internal_attrs, 
        mix_str_pattern, runtime_module=runtime_module, 
        enable_vm=enable_vm, is_pro=is_pro, op_map=op_map
    )

    if bcc_mod_info:
        mod_name, bin_path = bcc_mod_info
        tree = BCCStubTransformer(mod_name, bcc_functions).visit(tree)

    tree = transformer.visit(tree)
    tree = ControlFlowFlattener().visit(tree)
    
    helper_name = transformer.get_helper_name
    pool_name = "".join(random.choices(string.ascii_letters, k=10))
    key_var = "".join(random.choices(string.ascii_letters, k=10))
    
    helper_code = f"""
import base64
{key_var} = base64.b64decode('{key_b64}')
def {helper_name}(i):
    d = base64.b64decode({pool_name}[i])
    return bytes([b ^ {key_var}[j % len({key_var})] for j, b in enumerate(d)]).decode('utf-8')
"""
    actual_helper_tree = ast.parse(helper_code)
    pool_node = ast.Assign(
        targets=[ast.Name(id=pool_name, ctx=ast.Store())], 
        value=ast.List(elts=[ast.Constant(value=s) for s in transformer.string_pool], ctx=ast.Load())
    )
    
    tree.body = junk_tree.body + actual_helper_tree.body + [pool_node] + tree.body
    ast.fix_missing_locations(tree)
    try:
        return f_path, ast.unparse(tree)
    except Exception:
        try:
            import astunparse
            return f_path, astunparse.unparse(tree)
        except Exception:
            return f_path, None

def obfuscate_project(files, mix_str_pattern=None, private=False, bcc=False, bcc_output_dir=None, debug=False, turbo=False, runtime_module=None, exclude_names=None, code_dict=None, enable_vm=False, is_pro=False, op_map=None):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import os
    
    mapping = {}
    used_names = set()
    xor_key = bytes([random.randint(0, 255) for _ in range(32)])
    key_b64 = base64.b64encode(xor_key).decode('utf-8')
    bcc_functions = {} # f_path -> list of (name, node) tuples
    all_exclude_names = set(exclude_names) if exclude_names else set()

    # Step 1: Parallel Parsing
    parsed_files = {}
    max_workers = os.cpu_count() or 4
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_process_file_parsing, f, code_dict, bcc) for f in files]
        for future in as_completed(futures):
            f_path, tree, candidates = future.result()
            parsed_files[f_path] = tree
            if candidates:
                bcc_functions[f_path] = candidates
                for name, node in candidates: all_exclude_names.add(name)

    # Step 2: Sequential Symbol Collection (must be sequential for global consistency)
    collector = SymbolCollector(mapping, used_names, exclude_names=all_exclude_names, private_mode=private)
    for tree in parsed_files.values():
        collector.visit(tree)

    # Step 3: Sharded BCC Compilation
    bcc_modules = {} # f_path -> (mod_name, bin_path)
    
    if bcc and bcc_functions:
        from cryptolith.bcc_engine import generate_c_source
        from cryptolith.compiler import compile_extension
        
        # Group files into shards to balance load and minimize overhead
        fps = list(bcc_functions.keys())
        num_shards = min(len(fps), max_workers)
        shards = [[] for _ in range(num_shards)]
        for i, fp in enumerate(fps):
            shards[i % num_shards].append(fp)
            
        def compile_shard(shard_fps):
            # Combined source for all functions in this shard
            shard_functions = []
            for fp in shard_fps:
                shard_functions.extend(bcc_functions[fp])
            
            mod_name = f"bcc_{uuid.uuid4().hex[:8]}"
            try:
                c_src = generate_c_source(mod_name, shard_functions, turbo=turbo, mapping=collector.mapping)
                bin_path = compile_extension(c_src, mod_name, bcc_output_dir, debug=debug)
                return shard_fps, mod_name, bin_path
            except Exception as e:
                import traceback
                print(f"BCC COMPILATION FATAL ERROR: {e}")
                traceback.print_exc()
                raise e

        with ThreadPoolExecutor(max_workers=num_shards) as executor:
            shard_futures = [executor.submit(compile_shard, s) for s in shards if s]
            for future in as_completed(shard_futures):
                s_fps, mod_name, result = future.result()
                if mod_name:
                    for fp in s_fps:
                        bcc_modules[fp] = (mod_name, result)
                else:
                    # ALWAYS print error if it fails
                    print(f"BCC Compilation Error: {result}")
                    for fp in s_fps:
                        # Fallback: Restore original bodies for this shard
                        # This part needs to be handled carefully. If BCC fails,
                        # the original function nodes should remain in the AST
                        # for standard obfuscation. The current `parsed_files[fp].body = nodes + parsed_files[fp].body`
                        # in the original code was incorrect as it would add nodes to the body of the file, not the function.
                        # For now, we'll just let the functions be processed by the standard transformer.
                        pass 

    # Step 4: Parallel Transformation
    results = {}
    junk_code = "import sys as _obs_sys\nimport os as _obs_os\ndef _junk_func(): pass\n"
    junk_tree = ast.parse(junk_code)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        trans_futures = []
        for f_path, tree in parsed_files.items():
            bcc_info = bcc_modules.get(f_path)
            bcc_funcs = bcc_functions.get(f_path, [])
            trans_futures.append(executor.submit(
                _process_file_transformation,
                f_path, tree, mapping, xor_key, 
                collector.internal_funcs, collector.internal_attrs,
                mix_str_pattern, runtime_module, enable_vm, is_pro,
                bcc_info, bcc_funcs, None, junk_tree, key_b64, op_map
            ))
        
        for future in as_completed(trans_futures):
            f_path, code = future.result()
            if code is None:
                raise RuntimeError(f"Failed to unparse {f_path} after transformation")
            results[f_path] = code

    return results, mapping, bcc_modules

def obfuscate_code(source_code, runtime_check=None, mix_str_pattern=None, private=False, exclude_names=None, is_pro=True):
    return list(obfuscate_project(["temp.py"], mix_str_pattern, private, exclude_names=exclude_names, code_dict={"temp.py": source_code}, is_pro=is_pro)[0].values())[0]
