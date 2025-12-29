import os
import sys
import shutil
import argparse
import subprocess
import datetime
import time
import threading
import json
from contextlib import contextmanager

PROJECT_ROOT = os.getcwd()

# --- 1. Global Setup ---
sys.setrecursionlimit(10000)
# Silence Kivy logs
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_NO_FILELOG"] = "1"
os.environ["KIVY_DUMMY_MODE"] = "1"

OUTPUT_FOLDER = "Completed_Build"
ARCHIVE_FOLDER = "Archived_Builds"
CONFIG_FILE = ".nvlibconfig"
SECRET_KEY = b"NVLIB_PROTECT_2025"
NVLIB_CONFIG = ".nvlibconfig"
APP_CONFIG = ".appconfig"

DEFAULT_APP_CONFIG = {
    "appname": "NVLib_App",
    "icon": "icon.ico",
    "version": "1.0",
    "auto_version": "true",
    "version_increment": "0.1"
}

# ------------------- Visual Helpers -------------------

class Spinner:
    """A threaded spinner to show progress while blocking operations run."""
    def __init__(self, message="Processing"):
        self.message = message
        self.stop_running = False
        self.thread = None

    def _spin(self):
        chars = "|/-\\"
        i = 0
        while not self.stop_running:
            sys.stdout.write(f"\r[NVLib] {self.message}... {chars[i]}")
            sys.stdout.flush()
            time.sleep(0.1)
            i = (i + 1) % len(chars)

    def start(self):
        self.stop_running = False
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def stop(self, success_message=None):
        self.stop_running = True
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * (len(self.message) + 20) + "\r")  # Clear line
        if success_message:
            print(f"[NVLib] {success_message}")
        sys.stdout.flush()

def clean_print(msg):
    print(f"[NVLib] {msg}")

def print_dashboard(exe_name, version, exe_path, installer_path=None):
    print("\n" + "="*60)
    print(f"      NVLib BUILD DASHBOARD      ")
    print("="*60)
    print(f" [APP NAME]    : {exe_name}")
    print(f" [VERSION]     : {version}")
    print(f" [BUILD TIME]  : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    print(f" [EXE LOCATION]:")
    print(f" {exe_path}")
    print("-" * 60)
    if installer_path and os.path.exists(installer_path):
        print(f" [INSTALLER]   :")
        print(f" {installer_path}")
    elif installer_path:
        print(f" [SCRIPT ONLY] : {installer_path}")
    else:
        print(" [INSTALLER]   : Skipped (Inno Setup not found)")
    print("="*60 + "\n")

# ------------------- Config Helpers -------------------

def save_nvlib_config(executable_path):
    with open(NVLIB_CONFIG, "w") as f:
        f.write(os.path.abspath(executable_path))
    clean_print(f"Main executable set to: {os.path.basename(executable_path)}")

def load_nvlib_config():
    if os.path.exists(NVLIB_CONFIG):
        with open(NVLIB_CONFIG, "r") as f:
            return f.read().strip()
    return None

def save_app_config(config):
    with open(APP_CONFIG, "w") as f:
        json.dump(config, f, indent=4)

def load_app_config():
    config = {}
    if os.path.exists(APP_CONFIG):
        try:
            with open(APP_CONFIG, "r") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            config = {}
    for k, v in DEFAULT_APP_CONFIG.items():
        if k not in config:
            config[k] = v
    save_app_config(config)
    return config

def set_config(key, value):
    if key == "executable":
        save_nvlib_config(value)
    else:
        config = load_app_config()
        config[key] = value
        save_app_config(config)
        clean_print(f"Set {key} = {value}")

def ensure_config(required_fields=None):
    executable = load_nvlib_config()
    if not executable:
        executable = input("[CONFIG] Enter main executable path: ").strip()
        save_nvlib_config(executable)

    config = load_app_config()
    required_fields = required_fields or ["appname", "icon", "version"]
    missing = [f for f in required_fields if f not in config]
    for field in missing:
        value = input(f"[CONFIG] Enter {field}: ").strip()
        config[field] = value
    save_app_config(config)
    config["executable"] = executable
    return config

def handle_auto_version(config):
    if str(config.get("auto_version", "false")).lower() == "true":
        step = float(config.get("version_increment", 0.1))
        config["version"] = auto_increment_version(config["version"], step)
        save_app_config(config)
        print(f"[VERSION] New version: {config['version']}")
    return config

def auto_increment_version(version, step=0.1):
    version = str(version)
    parts = version.split('.')
    while len(parts) < 3:
        parts.append('0')
    major, minor, patch = map(int, parts)

    if step < 1:
        patch += int(step * 10)
    else:
        minor += int(step)

    while patch >= 10:
        patch -= 10
        minor += 1
    while minor >= 10:
        minor -= 10
        major += 1

    return f"{major}.{minor}.{patch}"

def find_iscc():
    iscc = shutil.which("iscc")
    if iscc: return iscc
    paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe"
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

# ------------------- Core Functions -------------------

def archive_and_clean(exe_name):
    """
    1. Moves any Setup.exe from Completed_Build/Installer to Archived_Builds/AppName/
    2. Deletes Completed_Build to ensure a fresh overwrite.
    """
    dist_root = os.path.join(PROJECT_ROOT, OUTPUT_FOLDER)
    installer_source_dir = os.path.join(dist_root, "Installer")
    
    # --- 1. Archive Installers ---
    if os.path.exists(installer_source_dir):
        # Create folder: Archived_Builds/AppName
        archive_dest_dir = os.path.join(PROJECT_ROOT, ARCHIVE_FOLDER, exe_name)
        os.makedirs(archive_dest_dir, exist_ok=True)
        
        files_moved = 0
        for f in os.listdir(installer_source_dir):
            # Only archive files that look like setup executables
            if f.endswith(".exe") and "setup" in f.lower():
                src = os.path.join(installer_source_dir, f)
                dst = os.path.join(archive_dest_dir, f)
                try:
                    # If same version exists in archive, overwrite it
                    if os.path.exists(dst):
                        os.remove(dst)
                    shutil.move(src, dst)
                    files_moved += 1
                except Exception as e:
                    print(f"[WARNING] Could not archive {f}: {e}")
        
        if files_moved > 0:
            clean_print(f"Archived {files_moved} installer(s) to {ARCHIVE_FOLDER}\\{exe_name}")

    # --- 2. Clean up Old Build ---
    # We remove the entire Completed_Build folder so PyInstaller starts fresh
    if os.path.exists(dist_root):
        try:
            shutil.rmtree(dist_root)
            clean_print("Cleaned up previous build folder.")
        except Exception as e:
            # If folder is open in Explorer, this might fail, but PyInstaller usually handles it.
            clean_print(f"Note: Could not fully delete old build folder ({e}). Proceeding...")


def protect_assets(project_root):
    # Disabled for now
    return

def generate_inno_script(project_name, version, compiled_folder_path, icon_path):
    installer_output_dir = os.path.join(os.path.dirname(compiled_folder_path), "Installer")
    os.makedirs(installer_output_dir, exist_ok=True)

    icon_line = f"SetupIconFile={icon_path}" if icon_path and os.path.exists(icon_path) else ""
    
    iss_content = f"""
[Setup]
AppName={project_name}
AppVersion={version}
DefaultDirName={{autopf}}\\{project_name}
DefaultGroupName={project_name}
UninstallDisplayIcon={{app}}\\{project_name}.exe
Compression=lzma2
SolidCompression=yes
OutputDir={installer_output_dir}
OutputBaseFilename={project_name}_v{version}_Setup
{icon_line}
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "{compiled_folder_path}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{project_name}"; Filename: "{{app}}\\{project_name}.exe"
Name: "{{autodesktop}}\\{project_name}"; Filename: "{{app}}\\{project_name}.exe"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{project_name}.exe"; Description: "Launch {project_name}"; Flags: nowait postinstall skipifsilent
"""
    iss_file_path = os.path.join(os.path.dirname(compiled_folder_path), f"{project_name}_installer.iss")
    with open(iss_file_path, "w", encoding="utf-8") as f:
        f.write(iss_content)
    
    return iss_file_path, installer_output_dir

def build_project(main_script_abs, exe_name, icon_path, version):
    project_root = PROJECT_ROOT
    dist_root = os.path.join(PROJECT_ROOT, OUTPUT_FOLDER)
    dist_path_specific = os.path.join(dist_root, exe_name)
    work_path = os.path.join(PROJECT_ROOT, "build") 
    
    # 1. Archive Old Installers & Clean Folder
    archive_and_clean(exe_name)

    clean_print(f"Building Application: '{exe_name}' (v{version})")

    # 2. Spec Generation
    data_list = []
    include_exts = (".json", ".ttf", ".jpg", ".jpeg", ".png", ".ico", ".kv", ".pyd")
    # Add OUTPUT_FOLDER and ARCHIVE_FOLDER to skip list to prevent recursion
    skip_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist', OUTPUT_FOLDER, ARCHIVE_FOLDER}

    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if file.lower().endswith(include_exts):
                full_path = os.path.abspath(os.path.join(root, file)).replace('\\', '/')
                rel_dir = os.path.relpath(os.path.dirname(full_path), project_root).replace('\\', '/')
                if rel_dir == ".": data_list.append((full_path, '.'))
                else: data_list.append((full_path, rel_dir))

    import kivymd
    data_list.append((os.path.dirname(kivymd.__file__).replace('\\', '/'), 'kivymd'))
    icon_option = f"icon='{icon_path.replace('\\', '/')}'" if icon_path else "icon=None"
    
    hidden_imports = [
        'kivymd', 'kivymd.uix', 'kivymd.uix.button', 'kivymd.uix.label',
        'kivymd.uix.screen', 'kivymd.theming', 'kivymd.icon_definitions',
        'kivymd.font_definitions', 'kivy.core.text', 'kivy.core.window', 'kivy.utils'
    ]

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
import sys
from kivy_deps import sdl2, glew, angle
sys.setrecursionlimit(10000)

a = Analysis(
    ['{main_script_abs.replace('\\', '/')}'], 
    pathex=[r'{project_root}'], 
    datas={repr(data_list)},
    hiddenimports={hidden_imports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter', 'sqlite3', 'numpy'], 
    noarchive=False
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, 
    a.scripts, 
    [], 
    exclude_binaries=True, 
    name='{exe_name}', 
    {icon_option},
    debug=False, 
    bootloader_ignore_signals=False, 
    strip=False, 
    upx=False, 
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None, 
)

coll = COLLECT(
    exe, 
    a.binaries, 
    a.datas, 
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)],
    strip=False, 
    upx=False, 
    upx_exclude=[], 
    name='{exe_name}'
)
"""
    spec_file = os.path.join(project_root, f"{exe_name}.spec")
    with open(spec_file, "w", encoding="utf-8") as f: f.write(spec_content)

    # 3. Execution with Spinner
    cmd = [
        sys.executable, "-m", "PyInstaller",
        spec_file, "--noconfirm", "--clean",
        "--distpath", dist_root,
        "--workpath", work_path,
        "--log-level=WARN"
    ]

    spinner = Spinner("Compiling Files using Pyinstaller")
    spinner.start()
    
    try:
        # Capture output to suppress noise
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            spinner.stop("Build Failed!")
            print("\n[ERROR LOGS]:")
            print(result.stderr)
            return
        else:
            spinner.stop("Compiled Files Successfully")

        final_exe_path = os.path.join(dist_path_specific, f"{exe_name}.exe")
        
        if os.path.exists(final_exe_path):
            # 4. Inno Setup
            iss_path, installer_dir = generate_inno_script(exe_name, version, dist_path_specific, icon_path)
            
            iscc_exe = find_iscc()
            if iscc_exe:
                spinner = Spinner("Building Installer with Inno Setup")
                spinner.start()
                
                result_iss = subprocess.run([iscc_exe, iss_path], capture_output=True, text=True)
                
                final_installer_path = os.path.join(installer_dir, f"{exe_name}_v{version}_Setup.exe")
                
                if result_iss.returncode == 0 and os.path.exists(final_installer_path):
                    spinner.stop("Installer Built Successfully")
                    print_dashboard(exe_name, version, final_exe_path, final_installer_path)
                else:
                    spinner.stop("Installer Building Failed")
                    print("\n[INNO SETUP ERROR]:")
                    print(result_iss.stderr or result_iss.stdout)
                    print_dashboard(exe_name, version, final_exe_path, iss_path)
            else:
                clean_print("Inno Setup not found. Skipping installer.")
                print_dashboard(exe_name, version, final_exe_path, iss_path)

            # Cleanup
            if os.path.exists(spec_file): os.remove(spec_file)
            shutil.rmtree(work_path, ignore_errors=True)
        else:
            clean_print("PyInstaller finished successfully but EXE is missing.")
            
    except Exception as e:
        spinner.stop("Error")
        print(f"\n[FATAL ERROR]: {e}")

def main():
    parser = argparse.ArgumentParser(description="NVLib Packaging Tool")
    subparsers = parser.add_subparsers(dest="command")
    set_p = subparsers.add_parser("set", help="Set config")
    set_p.add_argument("key"); set_p.add_argument("value")
    build_p = subparsers.add_parser("build", help="Package application"); build_p.add_argument("-exe", action="store_true")

    if len(sys.argv) == 1: parser.print_help(); sys.exit(0)
    args = parser.parse_args()

    if args.command == "set":
        if args.key and args.value: set_config(args.key, args.value)
    elif args.command == "build":
        config = ensure_config()
        config = handle_auto_version(config)
        
        if not os.path.exists(CONFIG_FILE):
            clean_print("Error: Config missing."); return
            
        with open(CONFIG_FILE, "r") as f: script_path = f.read().strip()
        
        p_name = config["appname"].strip() or "App"
        p_ver = config["version"].strip()
        i_path = config["icon"].strip()
        if i_path and not os.path.isabs(i_path):
            i_path = os.path.abspath(os.path.join(PROJECT_ROOT, i_path))
            
        build_project(script_path, p_name, i_path, p_ver)

if __name__ == "__main__":
    main()