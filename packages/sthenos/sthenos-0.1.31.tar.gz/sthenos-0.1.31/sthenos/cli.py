import sys
import os
import subprocess
import platform

def main():
    # Detect Source Directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir = os.path.join(base_dir, "bin")
    
    # Detect OS
    system = platform.system().lower()
    
    binary_name = "sthenos"
    if system == "windows":
        binary_name = "sthenos.exe"
    elif system == "linux":
        binary_name = "sthenos-linux"
    elif system == "darwin":
        binary_name = "sthenos-mac"
    else:
        print(f"Warning: Unknown operating system '{system}'. Trying default 'sthenos' binary.")
    
    binary_path = os.path.join(bin_dir, binary_name)
    
    if not os.path.exists(binary_path):
        print(f"Error: Sthenos binary not found at {binary_path}")
        print("Please ensure the package was installed correctly.")
        sys.exit(1)
        
    # Forward arguments to the binary
    # We use subprocess to hand over control
    try:
        # Pass all args except the first one (which is the script name 'sthenos')
        cmd = [binary_path] + sys.argv[1:]
        subprocess.call(cmd)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error launching sthenos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
