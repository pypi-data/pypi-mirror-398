import os
print("=== OMNI AI PROJECT STRUCTURE ===")
print(f"Current directory: {os.getcwd()}")

# List top-level
print("\n=== TOP LEVEL ===")
for item in os.listdir('.'):
    print(f"  - {item}")

# Check for omniai folder
print("\n=== omniai FOLDER ===")
omniai_path = os.path.join('.', 'omniai')
if os.path.exists(omniai_path):
    for item in os.listdir(omniai_path):
        print(f"  - {item}")
else:
    print("  omniai folder not found!")

# Check for core folder
print("\n=== CORE FOLDER ===")
core_path = os.path.join('.', 'omniai', 'core')
if os.path.exists(core_path):
    for item in os.listdir(core_path):
        print(f"  - {item}")
else:
    print("  core folder not found!")
