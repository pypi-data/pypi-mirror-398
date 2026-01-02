import datetime
import uuid
import sys
import os
import socket
import urllib.request
import json
import io
import base64

import time
import random

_asset_key = None
_HOSTILE_ENV = False

def _decrypt_asset(data):
    if not _asset_key: return data
    key = base64.b64decode(_asset_key)
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def secure_open(rel_path):
    """Securely open an encrypted asset from the bundle."""
    # Standardize path separators for consistent lookups
    rel_path = rel_path.replace("\\", "/")
    
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        # Development mode fallback: use environment or current dir
        base = os.getcwd()
        
    asset_path = os.path.join(base, "_cryptolith_assets", rel_path)
    if not os.path.exists(asset_path):
        raise FileNotFoundError(f"Asset {rel_path} not found in Cryptolith secure bundle.")
        
    with open(asset_path, "rb") as f:
        encrypted_data = f.read()
        
    decrypted_data = _decrypt_asset(encrypted_data)
    return io.BytesIO(decrypted_data)

def secure_load_json(rel_path):
    with secure_open(rel_path) as f:
        return json.load(f)

def secure_load_torch(rel_path, **kwargs):
    """Memory-only PyTorch model loading."""
    import torch
    return torch.load(secure_open(rel_path), **kwargs)

def secure_load_tf(rel_path, **kwargs):
    """Memory-only TensorFlow/Keras model loading."""
    import tensorflow as tf
    return tf.keras.models.load_model(secure_open(rel_path), **kwargs)
def is_debugger_present():
    detected = False
    # 1. Standard sys.gettrace
    if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
        detected = True
        
    # 2. Timing check (Detect single-stepping)
    if not detected:
        t1 = time.time()
        for _ in range(100): pass
        t2 = time.time()
        if (t2 - t1) > 0.1: # Threshold for intentional delay
            detected = True

    # 3. Process check (Windows)
    if not detected and os.name == 'nt':
        try:
            import ctypes
            if ctypes.windll.kernel32.IsDebuggerPresent():
                detected = True
        except:
            pass
            
    if detected:
        global _HOSTILE_ENV
        _HOSTILE_ENV = True
        return True
    return False

def _hidden_integrity():
    """Verify that the process hasn't been tampered with."""
    # This is a stub for future memory-integrity hash checks
    if os.path.basename(__file__).startswith("runtime"):
        # If the file hasn't been renamed by Cryptolith, it might be a raw copy
        return False
    return True

def check_expiration(expiry_date_str):
    if not expiry_date_str: return
    try:
        expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d')
        if datetime.datetime.now() > expiry_date: sys.exit(0xDEADBEEF)
    except: sys.exit(1)

def check_expiration_network(expiry_date_str, nts_url):
    if not expiry_date_str or not nts_url: return
    try:
        # Prevent trivial clock rollback
        with urllib.request.urlopen(nts_url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            now = datetime.datetime.fromtimestamp(data['unixtime'])
        limit = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d')
        if now > limit: sys.exit(0xC0FFEE)
    except:
        # If network is required but fails, fail the security check
        if nts_url: sys.exit(1)

def get_mac():
    try:
        return ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                        for ele in range(0,8*6,8)][::-1])
    except: return "unknown"

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close()
        return ip
    except: return "127.0.0.1"

def check_device_binding(macs, ips):
    valid = False
    if macs and get_mac() in macs: valid = True
    if ips and get_ip() in ips: valid = True
    if (macs or ips) and not valid: sys.exit(0xFA1)

def verify():
    """Lightweight scattered check for ongoing security."""
    if is_debugger_present(): sys.exit(0xD)
    return True

def runtime_init(expiry=None, macs=None, ips=None, nts=None, asset_key=None, vm_map=None):
    if is_debugger_present(): 
        # Military Grade: Don't always exit. Sometimes just flip the corruption bit.
        if random.random() < 0.3: sys.exit(0x444) 
    if not _hidden_integrity(): pass # Log but don't kill in case of build-env usage
    
    global _asset_key
    _asset_key = asset_key

    # Apply VM Opcode mapping if provided (Polymorphic VM)
    if vm_map:
        for name, value in vm_map.items():
            if hasattr(VMOp, name):
                setattr(VMOp, name, value)

    # Sync with cryptolith.runtime if we are an injected copy with a random name
    try:
        import cryptolith.runtime
        if cryptolith.runtime is not sys.modules[__name__]:
            cryptolith.runtime._asset_key = asset_key
    except:
        pass

    if expiry:
        if nts: check_expiration_network(expiry, nts)
        check_expiration(expiry)
        
    if macs or ips:
        check_device_binding(macs, ips)

class VMOp:
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

def vm_run(bytecode, constants, names, globals_dict, locals_dict):
    stack = []
    pc = 0
    
    while pc < len(bytecode):
        op = bytecode[pc]
        arg = bytecode[pc+1]
        pc += 2
        
        # SILENT CORRUPTION: If debugger detected, subtly break 5% of operations
        if _HOSTILE_ENV and random.random() < 0.05:
            if stack and isinstance(stack[-1], (int, float)):
                stack[-1] = stack[-1] + random.randint(1, 10)
            elif op == VMOp.JUMP:
                pc = (arg + 1) * 2 # Offset jumps
        if op == VMOp.LOAD_CONST:
            stack.append(constants[arg])
        elif op == VMOp.LOAD_NAME:
            name = names[arg]
            if name in locals_dict: stack.append(locals_dict[name])
            elif name in globals_dict: stack.append(globals_dict[name])
            elif name in __builtins__: stack.append(__builtins__[name])
            else: raise NameError(f"name '{name}' is not defined in VM")
        elif op == VMOp.STORE_NAME:
            locals_dict[names[arg]] = stack.pop()
        elif op == VMOp.BIN_ADD:
            b = stack.pop(); a = stack.pop()
            stack.append(a + b)
        elif op == VMOp.BIN_SUB:
            b = stack.pop(); a = stack.pop()
            stack.append(a - b)
        elif op == VMOp.BIN_MUL:
            b = stack.pop(); a = stack.pop()
            stack.append(a * b)
        elif op == VMOp.BIN_DIV:
            b = stack.pop(); a = stack.pop()
            stack.append(a / b)
        elif op == VMOp.COMPARE:
            b = stack.pop(); a = stack.pop()
            if arg == 0: stack.append(a < b)
            elif arg == 1: stack.append(a <= b)
            elif arg == 2: stack.append(a > b)
            elif arg == 3: stack.append(a >= b)
            elif arg == 4: stack.append(a == b)
            elif arg == 5: stack.append(a != b)
        elif op == VMOp.CALL:
            func = stack.pop()
            args = [stack.pop() for _ in range(arg)][::-1]
            stack.append(func(*args))
        elif op == VMOp.JUMP:
            pc = arg * 2
        elif op == VMOp.JUMP_IF_FALSE:
            val = stack.pop()
            if not val:
                pc = arg * 2
        elif op == VMOp.BUILD_LIST:
            elements = [stack.pop() for _ in range(arg)][::-1]
            stack.append(elements)
        elif op == VMOp.BUILD_DICT:
            # Pop pairs of key-value
            d = {}
            for _ in range(arg):
                v = stack.pop()
                k = stack.pop()
                d[k] = v
            # Note: We don't need to reverse here as we pop v then k
            stack.append(d)
        elif op == VMOp.BUILD_STRING:
            # Pop strings and join them
            parts = [stack.pop() for _ in range(arg)][::-1]
            stack.append("".join(map(str, parts)))
        elif op == VMOp.LOAD_ATTR:
            obj = stack.pop()
            stack.append(getattr(obj, names[arg]))
        elif op == VMOp.STORE_ATTR:
            val = stack.pop()
            obj = stack.pop()
            setattr(obj, names[arg], val)
        elif op == VMOp.POP_TOP:
            stack.pop()
        elif op == VMOp.RETURN:
            return stack.pop()
        else:
            raise RuntimeError(f"Unknown VM Opcode: {op}")
    return None
