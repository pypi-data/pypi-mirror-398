import os
import sys
import subprocess
import shutil

def compile_extension(c_source, module_name, output_dir, debug=False):
    """
    Compiles the generated C source into a Python extension module (.pyd/.so).
    Uses caching if possible.
    """
    import tempfile
    import hashlib
    
    # Caching logic
    source_hash = hashlib.sha256(c_source.encode('utf-8')).hexdigest()
    hash_file = os.path.join(output_dir, f"{module_name}.hash")
    ext = ".pyd" if os.name == 'nt' else ".so"
    
    # Find existing compiled file (might have platform tags)
    existing_compiled = None
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            if f.startswith(module_name) and f.endswith(ext):
                existing_compiled = os.path.join(output_dir, f)
                break
    
    if existing_compiled and os.path.exists(hash_file):
        with open(hash_file, "r") as hf:
            if hf.read().strip() == source_hash:
                if debug: print(f"Using cached BCC module for {module_name}")
                return existing_compiled

    with tempfile.TemporaryDirectory() as shard_tmp:
        source_file = os.path.join(shard_tmp, f"{module_name}.c")
        with open(source_file, "w") as f:
            f.write(c_source)
            
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        # Also save to output_dir for debugging
        debug_c_file = os.path.join(output_dir, f"{module_name}.c")
        with open(debug_c_file, "w") as f:
            f.write(c_source)
        print(f"BCC_SOURCE_SAVED: {debug_c_file}")
            
        setup_py_content = f"""
from setuptools import setup, Extension
setup(
    name='{module_name}',
    ext_modules=[Extension('{module_name}', sources=['{module_name}.c'])],
    script_args=['build_ext', '--inplace']
)
"""
        setup_file = os.path.join(shard_tmp, f"setup_{module_name}.py")
        with open(setup_file, "w") as f:
            f.write(setup_py_content)
            
        if debug: print(f"Compiling native module {module_name} in isolated dir {shard_tmp}...")
        try:
            res = subprocess.run([sys.executable, f"setup_{module_name}.py"], 
                                 cwd=shard_tmp, 
                                 capture_output=True, 
                                 text=True)
            
            if res.returncode != 0:
                print(f"--- COMPILER ERROR FOR {module_name} ---")
                print("STDOUT:", res.stdout)
                print("STDERR:", res.stderr)
                raise RuntimeError(f"C compilation failed for {module_name}. Error: {res.stderr}")
                
            compiled_file_name = None
            for f in os.listdir(shard_tmp):
                if f.startswith(module_name) and f.endswith(ext):
                    compiled_file_name = f
                    break
            
            if not compiled_file_name:
                raise RuntimeError("Compilation succeeded but extension file not found.")
                
            # Move result to output_dir
            if not os.path.exists(output_dir): os.makedirs(output_dir)
            final_path = os.path.join(output_dir, compiled_file_name)
            shutil.copy2(os.path.join(shard_tmp, compiled_file_name), final_path)
            
            # Save hash
            with open(hash_file, "w") as hf:
                hf.write(source_hash)
                
            return final_path
            
        except Exception as e:
            raise e
