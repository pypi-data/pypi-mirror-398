"""
███████╗███╗   ███╗███╗   ██╗ ██╗ █████╗ 
██╔════╝████╗ ████║████╗  ██║███║██╔══██╗
█████╗  ██╔████╔██║██╔██╗ ██║╚██║╚█████╔╝
██╔══╝  ██║╚██╔╝██║██║╚██╗██║ ██║██╔══██╗
███████╗██║ ╚═╝ ██║██║ ╚████║ ██║╚█████╔╝
╚══════╝╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═╝ ╚════╝ 

O M N I   A I
Christmas Edition 2025
Created by: Lakshya Gupta
Date: 25 December 2025

FREE for everyone to use forever.
But this is MY work - please don't remove my name.
"""

# Your existing code continues here...
# omniai/core/advisor.py - CORRECT VERSION
"""
Enhanced Algorithm Advisor with 50+ algorithms
Class name: AlgorithmAdvisor
"""

class AlgorithmAdvisor:
    """Enhanced algorithm recommender with 50+ algorithms"""
    
    def __init__(self):
        self.algorithm_database = self._build_algorithm_database()
        print("   • Enhanced Algorithm Advisor initialized (50+ algorithms)")
    
    def _build_algorithm_database(self):
        """Build comprehensive algorithm database"""
        return {
            "LightGBM": {
                "category": "tree_based",
                "accuracy": "0.85-0.96",
                "best_for": ["large_data", "tabular", "fast_training"],
                "code": "from lightgbm import LGBMClassifier",
                "install": "pip install lightgbm"
            },
            "XGBoost": {
                "category": "tree_based", 
                "accuracy": "0.88-0.97",
                "best_for": ["accuracy", "missing_values"],
                "code": "from xgboost import XGBClassifier",
                "install": "pip install xgboost"
            },
            "Random Forest": {
                "category": "tree_based",
                "accuracy": "0.80-0.92",
                "best_for": ["interpretability", "medium_data"],
                "code": "from sklearn.ensemble import RandomForestClassifier",
                "install": "pip install scikit-learn"
            },
            "CatBoost": {
                "category": "tree_based",
                "accuracy": "0.86-0.95",
                "best_for": ["categorical_data", "no_preprocessing"],
                "code": "from catboost import CatBoostClassifier",
                "install": "pip install catboost"
            },
            "MLP (Neural Network)": {
                "category": "neural_network",
                "accuracy": "0.82-0.94",
                "best_for": ["complex_patterns", "non_linear"],
                "code": "from sklearn.neural_network import MLPClassifier",
                "install": "pip install scikit-learn"
            },
            "TabNet": {
                "category": "neural_network",
                "accuracy": "0.85-0.95",
                "best_for": ["tabular_data", "interpretability"],
                "code": "from pytorch_tabnet.tab_model import TabNetClassifier",
                "install": "pip install pytorch-tabnet"
            },
            "SVM (Linear)": {
                "category": "svm",
                "accuracy": "0.75-0.88",
                "best_for": ["high_dimension", "clear_margin"],
                "code": "from sklearn.svm import SVC",
                "install": "pip install scikit-learn"
            },
            "SVM (RBF)": {
                "category": "svm",
                "accuracy": "0.80-0.92",
                "best_for": ["non_linear", "complex_boundaries"],
                "code": "from sklearn.svm import SVC",
                "install": "pip install scikit-learn"
            },
            "Logistic Regression": {
                "category": "linear",
                "accuracy": "0.70-0.85",
                "best_for": ["interpretability", "baseline"],
                "code": "from sklearn.linear_model import LogisticRegression",
                "install": "pip install scikit-learn"
            },
            "K-Nearest Neighbors": {
                "category": "neighbors",
                "accuracy": "0.72-0.88",
                "best_for": ["small_data", "no_training"],
                "code": "from sklearn.neighbors import KNeighborsClassifier",
                "install": "pip install scikit-learn"
            },
            "Gaussian Naive Bayes": {
                "category": "bayesian",
                "accuracy": "0.65-0.80",
                "best_for": ["text_data", "fast"],
                "code": "from sklearn.naive_bayes import GaussianNB",
                "install": "pip install scikit-learn"
            },
            "AdaBoost": {
                "category": "ensemble",
                "accuracy": "0.78-0.90",
                "best_for": ["weak_learners", "improving_accuracy"],
                "code": "from sklearn.ensemble import AdaBoostClassifier",
                "install": "pip install scikit-learn"
            },
            "Gradient Boosting": {
                "category": "ensemble",
                "accuracy": "0.84-0.94",
                "best_for": ["medium_data", "robust"],
                "code": "from sklearn.ensemble import GradientBoostingClassifier",
                "install": "pip install scikit-learn"
            },
            "Medical Random Forest": {
                "category": "medical",
                "accuracy": "0.82-0.92",
                "best_for": ["medical_data", "interpretability"],
                "code": "from sklearn.ensemble import RandomForestClassifier",
                "install": "pip install scikit-learn",
                "medical_note": "Can show which medical features are most important"
            },
        "Medical XGBoost": {
            "category": "medical",
            "accuracy": "0.87-0.96",
            "best_for": ["medical_tabular", "clinical_trials"],
            "code": "from xgboost import XGBClassifier",
            "install": "pip install xgboost",
            "medical_note": "FDA-acceptable for some clinical applications"
        },
        
        # ========== NEW ALGORITHMS (30+) ==========
        "Extra Trees": {
            "category": "tree_based",
            "accuracy": "0.82-0.93",
            "best_for": ["reduced_overfitting", "fast_training"],
            "code": "from sklearn.ensemble import ExtraTreesClassifier",
            "install": "pip install scikit-learn"
        },
        "Decision Tree": {
            "category": "tree_based",
            "accuracy": "0.70-0.85",
            "best_for": ["interpretability", "small_data", "rules"],
            "code": "from sklearn.tree import DecisionTreeClassifier",
            "install": "pip install scikit-learn"
        },
        "Histogram-Based Gradient Boosting": {
            "category": "tree_based",
            "accuracy": "0.83-0.94",
            "best_for": ["large_data", "memory_efficient", "categorical_data"],
            "code": "from sklearn.ensemble import HistGradientBoostingClassifier",
            "install": "pip install scikit-learn"
        },
        "Transformer (Tabular)": {
            "category": "neural_network",
            "accuracy": "0.88-0.97",
            "best_for": ["very_large_data", "attention_patterns", "sequential_features"],
            "code": "from transformers import TabTransformer",
            "install": "pip install pytorch-tabular"
        },
        "NODE (Neural Oblivious Decision Trees)": {
            "category": "neural_network",
            "accuracy": "0.87-0.96",
            "best_for": ["tabular_data", "interpretable_neural", "high_accuracy"],
            "code": "from pytorch_tabular.models import NODE",
            "install": "pip install pytorch-tabular"
        },
        "AutoML Neural Network": {
            "category": "neural_network",
            "accuracy": "0.86-0.95",
            "best_for": ["automl", "no_tuning_needed", "beginner_friendly"],
            "code": "from auto-sklearn import AutoSklearnClassifier",
            "install": "pip install auto-sklearn"
        },
        "ResNet (Tabular)": {
            "category": "neural_network",
            "accuracy": "0.85-0.94",
            "best_for": ["very_deep_networks", "complex_patterns"],
            "code": "from pytorch_tabular.models import TabNet",
            "install": "pip install pytorch-tabular"
        },
        "Simple Neural Network (Keras)": {
            "category": "neural_network",
            "accuracy": "0.80-0.92",
            "best_for": ["custom_architectures", "deep_learning"],
            "code": "from tensorflow import keras",
            "install": "pip install tensorflow"
        },
        "Ridge Classifier": {
            "category": "linear",
            "accuracy": "0.72-0.87",
            "best_for": ["multicollinearity", "regularization_needed"],
            "code": "from sklearn.linear_model import RidgeClassifier",
            "install": "pip install scikit-learn"
        },
        "Lasso Classifier": {
            "category": "linear",
            "accuracy": "0.73-0.88",
            "best_for": ["feature_selection", "sparse_solutions"],
            "code": "from sklearn.linear_model import SGDClassifier(loss='log', penalty='l1')",
            "install": "pip install scikit-learn"
        },
        "ElasticNet Classifier": {
            "category": "linear",
            "accuracy": "0.74-0.89",
            "best_for": ["mixed_regularization", "correlated_features"],
            "code": "from sklearn.linear_model import SGDClassifier(loss='log', penalty='elasticnet')",
            "install": "pip install scikit-learn"
        },
        "SGD Classifier": {
            "category": "linear",
            "accuracy": "0.71-0.86",
            "best_for": ["incremental_learning", "large_data_streaming"],
            "code": "from sklearn.linear_model import SGDClassifier",
            "install": "pip install scikit-learn"
        },
        "Perceptron": {
            "category": "linear",
            "accuracy": "0.65-0.80",
            "best_for": ["very_fast", "linearly_separable"],
            "code": "from sklearn.linear_model import Perceptron",
            "install": "pip install scikit-learn"
        },
        "SVM (Polynomial)": {
            "category": "svm",
            "accuracy": "0.78-0.90",
            "best_for": ["polynomial_patterns", "moderate_nonlinear"],
            "code": "from sklearn.svm import SVC(kernel='poly')",
            "install": "pip install scikit-learn"
        },
        "SVM (Sigmoid)": {
            "category": "svm",
            "accuracy": "0.70-0.85",
            "best_for": ["neural_like", "specific_kernels"],
            "code": "from sklearn.svm import SVC(kernel='sigmoid')",
            "install": "pip install scikit-learn"
        },
        "Radius Neighbors": {
            "category": "neighbors",
            "accuracy": "0.68-0.83",
            "best_for": ["density_based", "variable_density"],
            "code": "from sklearn.neighbors import RadiusNeighborsClassifier",
            "install": "pip install scikit-learn"
        },
        "Nearest Centroid": {
            "category": "neighbors",
            "accuracy": "0.65-0.80",
            "best_for": ["very_fast", "prototype_based"],
            "code": "from sklearn.neighbors import NearestCentroid",
            "install": "pip install scikit-learn"
        },
        "K-Means Clustering (for pseudo-labeling)": {
            "category": "neighbors",
            "accuracy": "0.60-0.75",
            "best_for": ["unsupervised_preprocessing", "clustering_first"],
            "code": "from sklearn.cluster import KMeans",
            "install": "pip install scikit-learn"
        },
        "Multinomial Naive Bayes": {
            "category": "bayesian",
            "accuracy": "0.70-0.85",
            "best_for": ["text_classification", "discrete_data"],
            "code": "from sklearn.naive_bayes import MultinomialNB",
            "install": "pip install scikit-learn"
        },
        "Bernoulli Naive Bayes": {
            "category": "bayesian",
            "accuracy": "0.68-0.83",
            "best_for": ["binary_features", "document_classification"],
            "code": "from sklearn.naive_bayes import BernoulliNB",
            "install": "pip install scikit-learn"
        },
        "Gaussian Process": {
            "category": "bayesian",
            "accuracy": "0.80-0.92",
            "best_for": ["small_data", "uncertainty_quantification"],
            "code": "from sklearn.gaussian_process import GaussianProcessClassifier",
            "install": "pip install scikit-learn"
        },
        "Bagging Classifier": {
            "category": "ensemble",
            "accuracy": "0.81-0.92",
            "best_for": ["reducing_variance", "parallel_training"],
            "code": "from sklearn.ensemble import BaggingClassifier",
            "install": "pip install scikit-learn"
        },
        "Stacking Classifier": {
            "category": "ensemble",
            "accuracy": "0.86-0.96",
            "best_for": ["max_accuracy", "competitions"],
            "code": "from sklearn.ensemble import StackingClassifier",
            "install": "pip install scikit-learn"
        },
        "Voting Classifier": {
            "category": "ensemble",
            "accuracy": "0.84-0.95",
            "best_for": ["diversity", "robust_predictions"],
            "code": "from sklearn.ensemble import VotingClassifier",
            "install": "pip install scikit-learn"
        },
        "Isolation Forest (Anomaly Detection)": {
            "category": "ensemble",
            "accuracy": "0.85-0.95",
            "best_for": ["anomaly_detection", "outlier_detection"],
            "code": "from sklearn.ensemble import IsolationForest",
            "install": "pip install scikit-learn"
        },
        "Medical Logistic Regression": {
            "category": "medical",
            "accuracy": "0.75-0.88",
            "best_for": ["clinical_decisions", "interpretable_coefficients"],
            "code": "from sklearn.linear_model import LogisticRegression",
            "install": "pip install scikit-learn",
            "medical_note": "Common in clinical risk scores"
        },
        "Medical SVM": {
            "category": "medical",
            "accuracy": "0.80-0.91",
            "best_for": ["medical_imaging", "high_dimension_medical"],
            "code": "from sklearn.svm import SVC",
            "install": "pip install scikit-learn",
            "medical_note": "Used in medical image classification"
        },
        "Medical Neural Network": {
            "category": "medical",
            "accuracy": "0.84-0.94",
            "best_for": ["ecg_analysis", "medical_time_series"],
            "code": "from tensorflow import keras",
            "install": "pip install tensorflow",
            "medical_note": "Deep learning for complex medical patterns"
        },
        "Financial XGBoost": {
            "category": "financial",
            "accuracy": "0.89-0.97",
            "best_for": ["credit_scoring", "fraud_detection"],
            "code": "from xgboost import XGBClassifier",
            "install": "pip install xgboost"
        },
        "Financial Logistic Regression": {
            "category": "financial",
            "accuracy": "0.76-0.90",
            "best_for": ["credit_risk", "regulatory_compliance"],
            "code": "from sklearn.linear_model import LogisticRegression",
            "install": "pip install scikit-learn"
        },
        "Financial Isolation Forest": {
            "category": "financial",
            "accuracy": "0.88-0.96",
            "best_for": ["fraud_detection", "anomaly_detection"],
            "code": "from sklearn.ensemble import IsolationForest",
            "install": "pip install scikit-learn"
        },
        "Time Series Forest": {
            "category": "time_series",
            "accuracy": "0.83-0.93",
            "best_for": ["time_series_classification", "sequential_data"],
            "code": "from sktime.classification.interval_based import TimeSeriesForestClassifier",
            "install": "pip install sktime"
        },
        "LSTM (Time Series)": {
            "category": "time_series",
            "accuracy": "0.85-0.95",
            "best_for": ["sequential_patterns", "long_dependencies"],
            "code": "from tensorflow.keras.layers import LSTM",
            "install": "pip install tensorflow"
        },
        "Prophet (Forecasting)": {
            "category": "time_series",
            "accuracy": "0.80-0.92",
            "best_for": ["forecasting", "seasonality"],
            "code": "from prophet import Prophet",
            "install": "pip install prophet"
        },
        "BERT (Text Classification)": {
            "category": "text",
            "accuracy": "0.90-0.98",
            "best_for": ["nlp", "text_classification", "sentiment_analysis"],
            "code": "from transformers import BertForSequenceClassification",
            "install": "pip install transformers"
        },
        "FastText": {
            "category": "text",
            "accuracy": "0.85-0.94",
            "best_for": ["text_classification", "fast_training"],
            "code": "import fasttext",
            "install": "pip install fasttext"
        },
        "TF-IDF + Classifier": {
            "category": "text",
            "accuracy": "0.75-0.90",
            "best_for": ["simple_text", "baseline_nlp"],
            "code": "from sklearn.feature_extraction.text import TfidfVectorizer",
            "install": "pip install scikit-learn"
        }
        }
    
    def recommend(self, analysis, domain="generic", task="classification"):
        """
        Recommend algorithms based on data analysis
        """
        n_rows = analysis.get("rows", 0)
        n_features = analysis.get("n_features", 0)
        
        recommendations = []
        
        print(f"   • Data: {n_rows:,} rows, {n_features} features, {domain} domain")
        print(f"   • Task: {task}, Database: {len(self.algorithm_database)} algorithms available")
        
        # Base recommendations for all
        base_recs = ["LightGBM", "XGBoost", "Random Forest"]
        
        # Add based on data size
        if n_rows > 100000:
            # Large data - fast algorithms
            recs = ["LightGBM", "CatBoost", "Logistic Regression"]
        elif n_rows > 5000:
            # Medium data - balanced
            recs = ["XGBoost", "Random Forest", "Gradient Boosting", "MLP (Neural Network)"]
        else:
            # Small data - simple algorithms
            recs = ["Logistic Regression", "K-Nearest Neighbors", "Gaussian Naive Bayes", "SVM (Linear)"]
        
        # Add neural networks for complex data
        if n_features > 30 or analysis.get("complexity") == "high":
            if "MLP (Neural Network)" not in recs:
                recs.append("MLP (Neural Network)")
            recs.append("TabNet")
        
        # Add SVM for medium data
        if 1000 < n_rows < 100000:
            recs.append("SVM (RBF)")
                
        # Add domain-specific
        if domain == "medical":
            recs.extend(["Medical Random Forest", "Medical XGBoost"])
        if domain == "financial":
            recs.extend(["XGBoost", "LightGBM"])
        if domain == "retail":
            recs.extend(["LightGBM", "Random Forest"])
                # ========== ENHANCED RECOMMENDATIONS FOR 52 ALGORITHMS ==========
        
        # Enhanced medical domain
        if domain == "medical":
            recs.extend(["Medical Logistic Regression", "Medical SVM", "Medical Neural Network"])
        
        # Enhanced financial domain  
        if domain == "financial":
            recs.extend(["Financial XGBoost", "Financial Logistic Regression", "Financial Isolation Forest"])
        
        # Text/NLP data
        if analysis.get("data_type") == "text" or domain == "text":
            recs.extend(["BERT (Text Classification)", "FastText", "TF-IDF + Classifier"])
        
        # Time series data
        if analysis.get("data_type") == "time_series" or domain == "time_series":
            recs.extend(["Time Series Forest", "LSTM (Time Series)", "Prophet (Forecasting)"])
        
        # Anomaly detection
        if task == "anomaly_detection" or analysis.get("task") == "anomaly_detection":
            recs.append("Isolation Forest (Anomaly Detection)")
        
        # Small datasets
        if n_rows < 1000:
            recs.extend(["Decision Tree", "Gaussian Process", "Nearest Centroid"])
        
        # Large datasets
        if n_rows > 100000:
            recs.extend(["Transformer (Tabular)", "Histogram-Based Gradient Boosting"])
        
        # High-dimensional data
        if n_features > 50:
            recs.extend(["NODE (Neural Oblivious Decision Trees)", "AutoML Neural Network"])
        
        # Ensemble methods for medium data
        if 5000 < n_rows < 50000:
            recs.extend(["Extra Trees", "Bagging Classifier", "Stacking Classifier"])
        
        # ========== END OF ENHANCED RECOMMENDATIONS ==========
        
        # Remove duplicates and create recommendation objects
        seen = set()
        rank = 1
        for algo_name in recs:
            if algo_name not in seen and algo_name in self.algorithm_database:
                seen.add(algo_name)
                
                algo_info = self.algorithm_database[algo_name]
                
                # Create reason based on characteristics
                reason = self._generate_reason(algo_name, algo_info, n_rows, domain)
                
                recommendations.append({
                    "rank": rank,
                    "algorithm": algo_name,
                    "category": algo_info["category"],
                    "reason": reason,
                    "accuracy": algo_info.get("accuracy", "N/A"),
                    "code": algo_info.get("code", ""),
                    "install": algo_info.get("install", "")
                })
                rank += 1
        
        return recommendations[:10]  # Return top 10
    
    def _generate_reason(self, algo_name, algo_info, n_rows, domain):
        """Generate a reason for recommending this algorithm"""
        category = algo_info["category"]
        
        if algo_name == "LightGBM":
            return "Fastest for large datasets (>100K rows)"
        elif algo_name == "XGBoost":
            return "Best accuracy for medium to large datasets"
        elif algo_name == "Random Forest":
            return "Most interpretable tree-based method"
        elif algo_name == "MLP (Neural Network)":
            return "Captures complex non-linear patterns"
        elif algo_name == "TabNet":
            return "Neural network designed for tabular data with interpretability"
        elif algo_name == "Medical Random Forest":
            return "Interpretable for clinical decisions, shows feature importance"
        elif algo_name == "Medical XGBoost":
            return "High accuracy for medical data, handles missing values well"
        elif "SVM" in algo_name:
            return "Good for complex decision boundaries"
        elif algo_name == "Logistic Regression":
            return "Simple, interpretable baseline model"
        elif algo_name == "CatBoost":
            return "Handles categorical data without preprocessing"
        elif algo_name == "Extra Trees":
            return "Faster than Random Forest with similar accuracy"
        elif algo_name == "Decision Tree":
            return "Fully interpretable white-box model"
        elif algo_name == "Gradient Boosting":
            return "Sequential tree building for high accuracy"
        elif algo_name == "Histogram-Based Gradient Boosting":
            return "Memory-efficient for large datasets with categorical data"
        elif algo_name == "Transformer (Tabular)":
            return "State-of-the-art for tabular data with attention mechanisms"
        elif algo_name == "NODE (Neural Oblivious Decision Trees)":
            return "Neural network that behaves like interpretable decision trees"
        elif algo_name == "AutoML Neural Network":
            return "Automatically tuned neural network for beginners"
        elif algo_name == "ResNet (Tabular)":
            return "Deep residual networks for complex tabular patterns"
        elif algo_name == "Simple Neural Network (Keras)":
            return "Customizable deep learning architecture"
        elif algo_name == "Ridge Classifier":
            return "Regularized linear model for multicollinear features"
        elif algo_name == "Lasso Classifier":
            return "Linear model with automatic feature selection"
        elif algo_name == "ElasticNet Classifier":
            return "Balanced L1/L2 regularization for correlated features"
        elif algo_name == "SGD Classifier":
            return "Stochastic gradient descent for streaming/large data"
        elif algo_name == "Perceptron":
            return "Fast linear classifier for separable data"
        elif algo_name == "SVM (Polynomial)":
            return "SVM with polynomial kernel for moderate nonlinearity"
        elif algo_name == "SVM (Sigmoid)":
            return "SVM with neural network-like sigmoid kernel"
        elif algo_name == "Radius Neighbors":
            return "Density-based nearest neighbors with fixed radius"
        elif algo_name == "Nearest Centroid":
            return "Very fast prototype-based classification"
        elif algo_name == "K-Means Clustering (for pseudo-labeling)":
            return "Unsupervised clustering for preprocessing"
        elif algo_name == "Multinomial Naive Bayes":
            return "Best for text classification with discrete counts"
        elif algo_name == "Bernoulli Naive Bayes":
            return "For binary/boolean feature data"
        elif algo_name == "Gaussian Process":
            return "Provides uncertainty estimates with predictions"
        elif algo_name == "Bagging Classifier":
            return "Reduces variance through bootstrap aggregation"
        elif algo_name == "Stacking Classifier":
            return "Meta-ensemble for maximum accuracy (competition winner)"
        elif algo_name == "Voting Classifier":
            return "Combines multiple models for robust predictions"
        elif algo_name == "Isolation Forest (Anomaly Detection)":
            return "Specialized for anomaly and outlier detection"
        elif algo_name == "Medical Logistic Regression":
            return "Interpretable clinical risk model with coefficients"
        elif algo_name == "Medical SVM":
            return "Used in medical image classification tasks"
        elif algo_name == "Medical Neural Network":
            return "Deep learning for complex medical patterns (ECG, MRI)"
        elif algo_name == "Financial XGBoost":
            return "Optimized for credit scoring and fraud detection"
        elif algo_name == "Financial Logistic Regression":
            return "Regulatory-compliant risk modeling"
        elif algo_name == "Financial Isolation Forest":
            return "Specialized for financial fraud detection"
        elif algo_name == "Time Series Forest":
            return "Specialized for time series classification"
        elif algo_name == "LSTM (Time Series)":
            return "Long Short-Term Memory for sequential dependencies"
        elif algo_name == "Prophet (Forecasting)":
            return "Facebook's forecasting model with seasonality handling"
        elif algo_name == "BERT (Text Classification)":
            return "State-of-the-art transformer for NLP tasks"
        elif algo_name == "FastText":
            return "Fast and efficient text classification by Facebook"
        elif algo_name == "TF-IDF + Classifier":
            return "Traditional but effective text processing pipeline"
        else:
            return f"Good {category} algorithm for {domain} data"
    
    def get_algorithm_details(self, algorithm_name):
        """Get detailed information about a specific algorithm"""
        return self.algorithm_database.get(algorithm_name)
    
    def compare_algorithms(self, algorithm_names):
        """Compare multiple algorithms"""
        comparison = []
        for name in algorithm_names:
            details = self.get_algorithm_details(name)
            if details:
                comparison.append({
                    "algorithm": name,
                    "category": details.get("category"),
                    "accuracy": details.get("accuracy"),
                    "best_for": details.get("best_for", [])
                })
        return comparison

# Test the class
if __name__ == "__main__":
    print("Testing AlgorithmAdvisor class...")
    advisor = AlgorithmAdvisor()
    
    # Test recommendation
    test_analysis = {"rows": 10000, "n_features": 25}
    recs = advisor.recommend(test_analysis, domain="medical")
    
    print(f"\nGenerated {len(recs)} recommendations:")
    for rec in recs[:5]:
        print(f"{rec['rank']}. {rec['algorithm']} - {rec['reason']}")
    
    print("\n✅ AlgorithmAdvisor class is working!")