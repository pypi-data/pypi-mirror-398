import os
import shutil
import click
import sys
from cryptolith.core import process_script

@click.group()
def main():
    """
    Cryptolith: Professional Python Obfuscator & Compiler.
    
    Protects your Python intellectual property through advanced AST-based
    obfuscation, runtime security checks, and native C compilation.
    """
    pass

@main.command()
@click.argument('script', type=click.Path(exists=True))
@click.option('--output', '-o', default='dist', 
              help='Directory where the protected application will be saved. Default is "dist".')
@click.option('--expired', '-e', 
              help='Set an expiration date for the application. Format: YYYY-MM-DD or number of days from now (e.g., "30"). The app will refuse to start after this date.')
@click.option('--nts', 
              help='Network Time Server URL (e.g., pool.ntp.org). If provided, expiration checks will use this server to prevent users from bypassing security by changing their system clock.')
@click.option('--bind-mac', '-b', multiple=True, 
              help='Bind the application to specific hardware MAC addresses. The app will only run on these devices. Can be specified multiple times.')
@click.option('--bind-ip', multiple=True, 
              help='Bind the application to specific IP addresses. Useful for internal enterprise deployments. Can be specified multiple times.')
@click.option('--mix-str', '-m', 
              help='A regex pattern for sensitive string obfuscation. Strings matching this pattern (or all strings > 2 chars if omitted) will be encrypted and decrypted only at runtime.')
@click.option('--private', is_flag=True, 
              help='Enable Private Mode: Adds additional layers of anti-debugging and anti-tamper logic to the executable.')
@click.option('--recursive', '-r', is_flag=True, 
              help='Enable recursive mode for packages. Obfuscates all .py files within the same directory as the script.')
@click.option('--include', multiple=True,
              help='Glob pattern(s) for files to include in obfuscation (e.g., "src/**/*.py"). Can be used multiple times.')
@click.option('--exclude', multiple=True,
              help='Glob pattern(s) for files or directories to exclude from the build entirely. Can be used multiple times.')
@click.option('--protect-assets', multiple=True,
              help='Glob pattern(s) for data files or AI models to encrypt and bundle securely (e.g., "models/*.pth"). These files are decrypted only in memory at runtime.')
@click.option('--add-data', multiple=True, 
              help='Include additional data files in the bundle. Format: "source:dest". Use semicolon on Windows or colon on Linux.')
@click.option('--add-binary', multiple=True, 
              help='Include additional binaries or DLLs. Format: "source:dest". Needed for custom native dependencies.')
@click.option('--onefile', is_flag=True, default=True, 
              help='Bundle everything into a single standalone executable. This is the default mode.')
@click.option('--onedir', is_flag=True, 
              help='Produces a directory containing the executable and all its dependencies. Easier for debugging but less portable.')
@click.option('--debug', '-d', is_flag=True, 
              help='Enable verbose debug mode. Shows internal transformation steps, C compiler output, and full stack traces on failure.')
@click.option('--enable-bcc', is_flag=True, 
              help='Binary Code Compiler: Identifies performance-critical functions (loops/math) and compiles them into native C extensions (.pyd) for both speed and extreme security.')
@click.option('--enable-turbo', is_flag=True, 
              help='Turbo Mode: Extends BCC with GIL-less parallelism and NumPy buffer protocol. Use for multi-threaded numerical workloads where maximum speed is required.')
@click.option('--enable-vm', is_flag=True,
              help='Virtual Machine Mode: Translates critical logic into a custom, non-standard instruction set to defeat all known Python decompilers.')
@click.option('--license', help='Path to professional license.dat file. If omitted, Cryptolith will look for license.dat in the current directory.')
def build(script, output, expired, nts, bind_mac, bind_ip, mix_str, private, recursive, include, exclude, protect_assets, add_data, add_binary, onefile, onedir, debug, enable_bcc, enable_turbo, enable_vm, license):
    """
    Obfuscate and Compile your Python script or package into a secure standalone binary.
    """
    

    final_onefile = onefile
    if onedir:
        final_onefile = False

    if expired and expired.isdigit():
        import datetime
        days = int(expired)
        expired = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')

    license_path = license or "license.dat"
    is_pro = False
    from cryptolith.license_manager import LicenseManager
    lm = LicenseManager()
    license_data = lm.verify_license(license_path)
    if license_data:
        is_pro = True
        click.echo(f"  --- [PRO EDITION ACTIVE] Licensed to: {license_data.get('user', 'Valued Customer')} ---")

    try:
        process_script(
            script, output, 
            expired=expired, 
            nts=nts,
            macs=bind_mac, 
            ips=bind_ip,
            mix_str=mix_str, 
            private=private, 
            recursive=recursive,
            include=include,
            exclude=exclude,
            protect_assets=protect_assets,
            add_data=add_data,
            add_binary=add_binary,
            onefile=final_onefile,
            debug=debug,
            bcc=enable_bcc,
            turbo=enable_turbo,
            enable_vm=enable_vm,
            license_path=license_path if is_pro else None
        )
        click.echo(f"Success! Output is in {os.path.abspath(output)}")
    except Exception as e:
        if debug:
            import traceback
            traceback.print_exc()
        
        click.echo(f"\n[!] Cryptolith Build Error: {e}", err=True)
        sys.exit(1)

@main.command()
@click.option('--name', required=True, 
              help='The original name of the application entry point (e.g., "myapp").')
@click.option('--build-dir', default='dist', 
              help='The directory containing the output of a previous "build" command. Default is "dist".')
@click.option('--release-dir', required=True, 
              help='Target directory for the final release package.')
@click.option('--update-only', is_flag=True, 
              help='A fast "patch" mode: Only copy the main executable binary, skipping the redistribution of shared libraries and assets.')
def release(name, build_dir, release_dir, update_only):
    """
    Manage application releases. Packages built binaries into portable distribution formats.
    """
    build_path = os.path.abspath(build_dir)
    release_path = os.path.abspath(release_dir)
    exe_filename = f"{name}.exe" if sys.platform == 'win32' else name
    
    exe_src = os.path.join(build_path, exe_filename)
    if not os.path.exists(exe_src):
        exe_src = os.path.join(build_path, name, exe_filename)
    
    if not os.path.exists(exe_src):
        click.echo(f"Error: Could not find {exe_filename} in {build_path}. Make sure the build succeeded.", err=True)
        sys.exit(1)

    if not os.path.exists(release_path):
        os.makedirs(release_path)

    if update_only:
        click.echo(f"[*] Quick-update: Copying '{exe_filename}' to {release_path}...")
        shutil.copy2(exe_src, os.path.join(release_path, exe_filename))
    else:
        click.echo(f"[*] Full-release: Packaging application in {release_path}...")
        src_dir = os.path.dirname(exe_src)
        if src_dir == build_path:
            shutil.copy2(exe_src, os.path.join(release_path, exe_filename))
        else:
            for item in os.listdir(src_dir):
                s = os.path.join(src_dir, item)
                d = os.path.join(release_path, item)
                if os.path.isdir(s):
                    if os.path.exists(d): shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
    click.echo("[V] Release operation successful.")

@main.command()
def test():
    """
    Run the internal Cryptolith Verification Suite.
    
    Executes a comprehensive battery of tests covering:
    - Basic Obfuscation & String Security
    - Class Inheritance & Symbol Mapping
    - BCC Native Compilation
    - Turbo-BCC Parallelism (GIL-less)
    - Library Interoperability (NumPy/Requests)
    - Metaprogramming & Advanced Logic
    """
    # Import and run the test runner script
    # We use a subprocess to ensure clean environment
    import subprocess
    click.echo("[*] Initiating 15-Tier Verification Suite...")
    test_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "run_tests.py")
    if not os.path.exists(test_script):
        click.echo("[!] Error: Test script not found in the expected location.")
        sys.exit(1)
        
    try:
        subprocess.check_call([sys.executable, test_script])
        click.echo("\n[V] ALL TESTS PASSED.")
    except subprocess.CalledProcessError:
        click.echo("\n[X] TEST SUITE FAILED.")
        sys.exit(1)

if __name__ == '__main__':
    main()
