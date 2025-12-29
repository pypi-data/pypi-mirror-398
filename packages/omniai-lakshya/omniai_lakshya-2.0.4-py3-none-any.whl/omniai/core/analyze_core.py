import os
import importlib.util
import sys

print("🔬 OMNI AI CORE MODULE ANALYSIS")
print("=" * 60)

# List all .py files (excluding backups)
py_files = [f for f in os.listdir('.') 
            if f.endswith('.py') and not f.endswith('.backup')]
            
print(f"Found {len(py_files)} Python modules:")
for py_file in sorted(py_files):
    size = os.path.getsize(py_file)
    print(f"  • {py_file} ({size} bytes)")

print("\n" + "=" * 60)

# Analyze main modules
modules_to_analyze = ['omni_ai_pipeline', 'advisor', 'cleaner']

for module_name in modules_to_analyze:
    if f"{module_name}.py" in py_files:
        print(f"\n📦 {module_name.upper()}:")
        try:
            spec = importlib.util.spec_from_file_location(
                module_name, 
                f"{module_name}.py"
            )
            module = importlib.util.module_from_spec(spec)
            
            # Get classes and functions
            import ast
            with open(f"{module_name}.py", 'r') as f:
                tree = ast.parse(f.read())
            
            classes = [node.name for node in ast.walk(tree) 
                      if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree) 
                        if isinstance(node, ast.FunctionDef)]
            
            if classes:
                print(f"  Classes: {', '.join(classes)}")
            if functions:
                print(f"  Functions: {', '.join(functions[:5])}" + 
                      ("..." if len(functions) > 5 else ""))
                      
        except Exception as e:
            print(f"  Error analyzing: {e}")

print("\n" + "=" * 60)
print("💡 RECOMMENDED NEXT STEPS:")
print("1. Run 'python omni_ai_pipeline.py' for demo")
print("2. Import modules in your own scripts")
print("3. Check advisor.py for algorithm recommendations")
print("4. Use cleaner.py for data preprocessing")
