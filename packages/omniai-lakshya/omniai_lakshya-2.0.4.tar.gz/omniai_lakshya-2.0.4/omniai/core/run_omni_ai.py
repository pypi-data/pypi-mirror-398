print("OMNI AI - Complete System")
print("=" * 60)

# Try to run the pipeline
try:
    from omni_pipeline import OMNI_Final_Pipeline, test_pipeline
    
    print("✅ Pipeline loaded successfully")
    
    # Ask user what they want to do
    print("\nOptions:")
    print("1. Run test with sample data")
    print("2. Use with your own data (see instructions)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n" + "=" * 60)
        result = test_pipeline()
        
        print("\n📋 Summary:")
        if result.get('reaches_90_target'):
            print("✅ 90%+ accuracy is achievable!")
            print(f"Top algorithms: {result.get('top_algorithms', [])}")
        else:
            print("⚠️  Needs improvement for 90%+")
            print(f"Start with: {result.get('top_algorithms', [])}")
    
    else:
        print("\n" + "=" * 60)
        print("📚 HOW TO USE OMNI AI WITH YOUR DATA")
        print("=" * 60)
        print("""
        1. Prepare your data as a CSV file or pandas DataFrame
        2. Identify your target column (what you want to predict)
        3. Use this code:
        
           from omni_pipeline import OMNI_Final_Pipeline
           import pandas as pd
           
           # Load your data
           df = pd.read_csv('your_data.csv')
           
           # Create pipeline
           pipeline = OMNI_Final_Pipeline()
           
           # Run 90% accuracy analysis
           result = pipeline.run_90_percent_pipeline(df, 'your_target_column')
           
           # Check results
           if result['reaches_90_target']:
               print(f"🎉 90%+ accuracy achievable!")
               print(f"Use: {result['top_algorithms']}")
           else:
               print(f"Start with: {result['top_algorithms']}")
        
        4. Implement the recommended algorithms
        5. Tune hyperparameters for best results
        """)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Make sure you have:")
    print("  - advisor.py in the same directory")
    print("  - cleaner.py in the same directory")
    print("  - Required packages: pandas, numpy, scikit-learn")

print("\n" + "=" * 60)
print("OMNI AI - Created by Lakshya Gupta")
print("Christmas Edition 2025")
print("=" * 60)
