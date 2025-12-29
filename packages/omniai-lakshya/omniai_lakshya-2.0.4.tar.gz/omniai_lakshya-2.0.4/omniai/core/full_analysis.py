# Let's understand the full capability
import inspect
import omni_ai_pipeline

print("=== COMPLETE OMNI AI ANALYSIS ===")
print(f"Module location: {omni_ai_pipeline.__file__}")

# Get the main class
OMNI_AI_Pipeline = getattr(omni_ai_pipeline, 'OMNI_AI_Pipeline')
print(f"\nMain class: {OMNI_AI_Pipeline}")

# Get methods
methods = [m for m in dir(OMNI_AI_Pipeline) if not m.startswith('_')]
print(f"\nAvailable methods: {methods}")

# Try to create instance and see what methods do
try:
    pipeline = OMNI_AI_Pipeline()
    print(f"\nPipeline instance created")
    
    # Check if we can get help on methods
    print("\nMethod signatures:")
    for method in methods:
        try:
            func = getattr(pipeline, method)
            sig = inspect.signature(func)
            print(f"  - {method}{sig}")
        except:
            print(f"  - {method}()")
            
except Exception as e:
    print(f"\nError creating instance: {e}")
    
# Check for example functions
print("\n\nLooking for example functions...")
example_funcs = [name for name in dir(omni_ai_pipeline) 
                 if 'example' in name.lower() and callable(getattr(omni_ai_pipeline, name))]
print(f"Example functions: {example_funcs}")
