# Simple test to understand Omni AI API
import pandas as pd
import numpy as np

print("=== SIMPLE OMNI AI API TEST ===")

# Create sample data
data = {
    'feature1': [1, 2, 3, 4, 5],
    'feature2': [2, 3, 4, 5, 6],
    'feature3': [3, 4, 5, 6, 7],
    'target': [0, 1, 0, 1, 0]
}
df = pd.DataFrame(data)
print(f"Sample data created: {df.shape}")

try:
    # Try to import and use Omni AI
    from omni_ai_pipeline import OMNI_AI_Pipeline
    
    print("✓ OMNI_AI_Pipeline imported successfully")
    
    # Create pipeline
    pipeline = OMNI_AI_Pipeline()
    print(f"Pipeline created: {pipeline}")
    
    # Try to run pipeline
    print("\nTrying to run pipeline...")
    result = pipeline.run_90_percent_pipeline(df, 'target')
    
    print("\n=== RESULTS ===")
    for key, value in result.items():
        if isinstance(value, list):
            print(f"{key}: {value[:3]}" + ("..." if len(value) > 3 else ""))
        else:
            print(f"{key}: {value}")
            
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
