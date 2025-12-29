# Check what imports are in each module
import ast
import os

def get_imports(filename):
    """Get all imports from a Python file"""
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    imports = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
    except:
        pass
    
    return imports

print("=== OMNI AI DEPENDENCIES ===")

modules = ['omni_ai_pipeline.py', 'advisor.py', 'cleaner.py']
for module in modules:
    if os.path.exists(module):
        print(f"\n📦 {module}:")
        imports = get_imports(module)
        if imports:
            for imp in imports[:10]:  # Show first 10 imports
                print(f"  - {imp}")
            if len(imports) > 10:
                print(f"  ... and {len(imports)-10} more")
        else:
            print("  No imports found or could not parse")
