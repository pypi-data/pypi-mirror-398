import os
import shutil
import base64
import random
import string
import glob
import subprocess
import sys
import fnmatch
from cryptolith.obfuscator import obfuscate_project, obfuscate_code

def process_script(script_path, output_dir, expired=None, nts=None, macs=None, ips=None, mix_str=None, 
                   private=False, recursive=False, include=None, exclude=None, protect_assets=None, enable_vm=False, 
                   add_data=None, add_binary=None, onefile=True, debug=False, bcc=False, turbo=False, license_path=None):
    """
    Core build orchestration with advanced security options and Tier Gating.
    """
    is_pro = license_path is not None
    
    if not is_pro:
        # Enforce Community Edition limitations (Useful Free Tier)
        enable_vm = False
        bcc = False # Only Pro gets Turbo/BCC for now
        turbo = False
        # mix_str = None # We allow basic mix_str if possible, or gate it. 
        # Actually, let's keep mix_str for Pro only to gate string encryption.
        mix_str = None
        protect_assets = None
    
    # Pro features: Turbo requires BCC to be active
    if is_pro and turbo:
        bcc = True
    
    watermark = '' # KILL THE WATERMARK

    script_abs = os.path.abspath(script_path)
    base_dir = os.path.dirname(script_abs)
    script_name = os.path.basename(script_abs)
    root_dir = base_dir # Default to script's dir for project root

    # 1. Setup Build Environment
    project_build_path = os.path.join(base_dir, f"build_{os.path.splitext(script_name)[0]}")
    if os.path.exists(project_build_path):
        shutil.rmtree(project_build_path)
    os.makedirs(project_build_path)

    def ignore_build(path, names):
        # Ignore our own build directory, common envs, and metadata
        ignore_common = {'.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules', 'dist', 'results'}
        ignored = [n for n in names if n.startswith(('.', 'build_')) or n in ignore_common]
        
        # Explicitly check if we are in the build directory itself (redundant but safe)
        if os.path.basename(path) == os.path.basename(project_build_path):
            return names
            
        # Apply exclude patterns if provided
        if exclude:
            rel_path = os.path.relpath(path, base_dir)
            for name in names:
                if name in ignored: continue
                rel_f = os.path.join(rel_path, name) if rel_path != "." else name
                for pat in exclude:
                    if fnmatch.fnmatch(rel_f, pat):
                        ignored.append(name)
                        break
        return ignored

    # 2. Collect Project Files
    shutil.copytree(base_dir, os.path.join(project_build_path, "project"), ignore=ignore_build)
    
    # Update script_abs to point to the copy
    dest_script_path = os.path.join(project_build_path, "project", script_name)
    
    # Collect all Python files for obfuscation
    all_py_files = []
    for root, _, files in os.walk(os.path.join(project_build_path, "project")):
        for f in files:
            if f.endswith('.py'):
                all_py_files.append(os.path.join(root, f))

    # 3. Handle Script Scoping
    if include or exclude:
        filtered_files = []
        for f in all_py_files:
            rel_f = os.path.relpath(f, os.path.join(project_build_path, "project"))
            
            # Entry script is ALWAYS included
            if os.path.samefile(f, dest_script_path):
                filtered_files.append(f)
                continue
                
            if exclude:
                is_excluded = False
                for pat in exclude:
                    if fnmatch.fnmatch(rel_f, pat):
                        is_excluded = True
                        break
                if is_excluded: continue
            
            if include:
                is_included = False
                for pat in include:
                    if fnmatch.fnmatch(rel_f, pat):
                        is_included = True
                        break
                if not is_included: continue
            
            filtered_files.append(f)
        all_py_files = filtered_files
    elif not recursive:
        # If not recursive, only protect the entry script
        all_py_files = [dest_script_path]

    # 4. Obfuscation Logic & VM Polymorphism
    from cryptolith.virtualizer import Op
    vm_op_map = {}
    virtualizer_op_map = None
    if enable_vm and is_pro:
        op_names = [attr for attr in dir(Op) if not attr.startswith("__")]
        shuffled_codes = random.sample(range(1, 255), len(op_names))
        vm_op_map = {name: code for name, code in zip(op_names, shuffled_codes)}
        virtualizer_op_map = {getattr(Op, name): code for name, code in vm_op_map.items()}

    runtime_module_name = "".join(random.choices(string.ascii_letters, k=8))
    runtime_dest = os.path.join(project_build_path, "project", f"{runtime_module_name}.py")
    runtime_src = os.path.join(os.path.dirname(__file__), "runtime.py")

    # Obfuscated runtime call
    asset_key = base64.b64encode(os.urandom(32)).decode('utf-8') if protect_assets else None
    runtime_check = f"""
{watermark}
import {runtime_module_name}
{runtime_module_name}.runtime_init(expiry={repr(expired)}, nts={repr(nts)}, macs={repr(list(macs)) if macs else None}, ips={repr(list(ips)) if ips else None}, asset_key={repr(asset_key)}, vm_map={repr(vm_op_map) if vm_op_map else None})
"""

    if bcc:
        msg = "Turbo-BCC Mode Enabled (GIL Release + Parallelism)." if turbo else "BCC Mode Enabled: Some functions will be compiled to native C extensions."
        print(msg)

    import sys
    sys.stderr.write(f"DEBUG: Calling obfuscate_project with {len(all_py_files)} files...\n")
    sys.stderr.flush()
    
    obfuscated_results, mapping, bcc_modules = obfuscate_project(
        all_py_files, 
        mix_str_pattern=mix_str, 
        private=private,
        bcc=bcc,
        bcc_output_dir=project_build_path,
        debug=debug,
        turbo=turbo,
        runtime_module=runtime_module_name,
        enable_vm=enable_vm,
        is_pro=is_pro,
        op_map=virtualizer_op_map
    )
    
    # RECURSIVE RUNTIME PROTECTION
    with open(runtime_src, 'r', encoding='utf-8') as f:
        runtime_code = f.read()

    vm_ops = ['VMOp', 'LOAD_CONST', 'LOAD_NAME', 'STORE_NAME', 'LOAD_ATTR', 'STORE_ATTR', 'CALL', 'BIN_ADD', 'BIN_SUB', 'BIN_MUL', 'BIN_DIV', 'COMPARE', 'JUMP', 'JUMP_IF_FALSE', 'RETURN', 'POP_TOP', 'BUILD_LIST', 'BUILD_DICT', 'BUILD_STRING']
    protected_runtime = obfuscate_code(runtime_code, exclude_names=['runtime_init', 'verify', 'expiry', 'macs', 'ips', 'nts', 'asset_key', 'vm_run'] + vm_ops)
    
    with open(runtime_dest, 'w', encoding='utf-8') as f:
        f.write(protected_runtime)

    # Write back project files
    for f_path, content in obfuscated_results.items():
        if os.path.samefile(f_path, dest_script_path):
            lines = content.splitlines()
            insert_idx = 0
            for i, line in enumerate(lines):
                if not line.startswith(('import ', 'from ', '#')):
                    insert_idx = i
                    break
            lines.insert(insert_idx, runtime_check)
            content = "\n".join(lines)
            
        with open(f_path, 'w', encoding='utf-8') as f:
            f.write(content)

    # Handle Asset Protection (VFS)
    if protect_assets:
        assets_dest_dir = os.path.join(project_build_path, "project", "_cryptolith_assets")
        os.makedirs(assets_dest_dir, exist_ok=True)
        key_bytes = base64.b64decode(asset_key)
        
        asset_count = 0
        for pat in protect_assets:
            for f_path in glob.glob(os.path.join(base_dir, pat), recursive=True):
                if os.path.isdir(f_path): continue
                rel_f = os.path.relpath(f_path, base_dir)
                dest_f = os.path.join(assets_dest_dir, rel_f)
                os.makedirs(os.path.dirname(dest_f), exist_ok=True)
                
                with open(f_path, "rb") as f:
                    data = f.read()
                
                enc_data = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])
                with open(dest_f, "wb") as f:
                    f.write(enc_data)
                asset_count += 1
                
                # Remove from project build source so it doesn't get bundled by PyInstaller
                # Correctly target the file in the build path, not base_dir
                rel_f = os.path.relpath(f_path, base_dir)
                build_f_path = os.path.join(project_build_path, "project", rel_f)
                if os.path.exists(build_f_path) and not os.path.samefile(build_f_path, dest_script_path):
                    os.remove(build_f_path)
        
        if asset_count > 0:
            print(f"Encrypted and bundled {asset_count} assets securely.")
            sep = os.pathsep
            add_data = list(add_data) if add_data else []
            # Use relative path from project_build_path
            add_data.append(f"project{os.sep}_cryptolith_assets{sep}_cryptolith_assets")

    # 5. Compilation
    print("--- Starting Packaged Compilation (PyInstaller) ---")
    output_abs = os.path.abspath(output_dir)
    cmd = [
        sys.executable, "-m", "PyInstaller", "--clean", "--distpath", output_abs
    ]
    # Modules used by BCC should be included as hidden imports
    cmd += [
        '--hidden-import', 'cryptography',
        '--hidden-import', 'cryptography.hazmat.primitives.asymmetric.ed25519',
        '--hidden-import', 'cryptography.hazmat.primitives.serialization',
        '--hidden-import', 'cryptography.hazmat.backends',
        '--hidden-import', 'math',
        '--hidden-import', 'time',
        '--hidden-import', 'threading',
        '--hidden-import', 'concurrent',
        '--hidden-import', 'concurrent.futures',
        '--hidden-import', 'zstd',
        '--hidden-import', 'zstandard'
    ]
    
    if not debug:
        cmd.append("--noconfirm")
    
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
        
    ext = ".pyd" if os.name == 'nt' else ".so"
    for f in os.listdir(project_build_path):
        if f.startswith("bcc_") and f.endswith(ext):
            sep = os.pathsep
            cmd.extend(["--add-binary", f"{f}{sep}."])

    if add_data:
        for item in add_data: cmd.extend(["--add-data", item])
    if add_binary:
        for item in add_binary: cmd.extend(["--add-binary", item])
            
    cmd.append(dest_script_path)
    
    if debug: print(f"Running command: {' '.join(cmd)}")
    
    try:
        res = subprocess.run(cmd, cwd=project_build_path, capture_output=True, text=True)
        if res.returncode != 0:
            print("\n[!] PyInstaller Compilation Failed!", file=sys.stderr)
            print(res.stdout)
            print(res.stderr)
            raise RuntimeError("PyInstaller execution failed.")
    except Exception as e:
        raise RuntimeError(f"Compilation failed: {e}")
        
    print("--- Build Complete ---")
    
    # 6. Cleanup Staging Area
    if not debug:
        try:
            shutil.rmtree(project_build_path)
        except:
            pass
