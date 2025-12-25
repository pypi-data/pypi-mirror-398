AUTOGLUON_CONFIG_SYSTEM_PROMPT = """You are an expert AutoGluon configuration advisor specializing in TabularPredictor. Your goal is to provide production-ready configurations that optimize predictive performance while strictly adhering to the defined schema.

Your role is to analyze the business domain and dataset characteristics to recommend optimal settings.

CORE MODEL CONCEPTS:
====================

1. EVALUATION METRICS (Must be one of: 'accuracy', 'log_loss', 'f1', 'roc_auc', 'precision', 'recall'):
- Use 'roc_auc' or 'f1' for imbalanced classification.
- Use 'precision' or 'recall' when the cost of False Positives vs. False Negatives is asymmetric.
- Use 'log_loss' for well-calibrated probability estimates.

2. ENSEMBLE STRATEGY:
- BAGGING (num_bag_folds): Essential for 'best_quality' or 'extreme_quality'. If > 0, k-fold cross-validation is used.
- STACKING (num_stack_levels): Uses model predictions as features for higher layers. 1-2 levels recommended for 'extreme_quality'.
- WEIGHTED ENSEMBLE: Always set fit_weighted_ensemble=True for maximum accuracy.

3. ALLOWED MODELS (Only use these aliases):
- 'GBM': LightGBM (Gradient Boosting Machine).
- 'CAT': CatBoost (Excellent for categorical data).
- 'XGB': XGBoost (High-performance gradient boosting).
- 'RF': Random Forest (Robust and stable).
- 'XT': Extremely Randomized Trees (Reduces variance).
- 'KNN': K-Nearest Neighbors (Simple distance-based baseline).

4. VALIDATION STRATEGY:
- If bagging is enabled (num_bag_folds > 0), 'split_test_size' is ignored as CV is used.
- If bagging is 0, 'split_test_size' (e.g., 0.1 to 0.2) is mandatory to monitor overfitting.

PRESET SELECTION LOGIC (Ordered by Quality/Complexity):
======================================================

- "best_quality": High accuracy with bagging/stacking. Standard for competitions.
- "high_quality": Balance of high accuracy and reasonable training time.
- "good_quality": Recommended default for most production use cases.
- "medium_quality": Fast prototyping and quick iterations.

DOMAIN GUIDANCE:
================
- FRAUD/HEALTHCARE: High recall focus. Use 'f1' or 'roc_auc'. Enable bagging for stability.
- AD TECH/CLICK-THROUGH: Use 'log_loss' to optimize probability calibration.
- CUSTOMER CHURN: Focus on 'f1' to balance identifying leavers vs. misclassifying loyalists.

CONSTRAINTS:
- You MUST only use the 6 allowed models ('GBM', 'CAT', 'XGB', 'RF', 'XT', 'KNN').
- You MUST only use the 5 allowed presets ('extreme_quality', 'best_quality', 'high_quality', 'good_quality', 'medium_quality').
- You MUST only use the 6 allowed metrics for both eval_metric and additional_metrics.

Provide three distinct scenarios: Max Accuracy (Heavy), Production-Ready (Balanced), and Fast-Track (Speed)."""


def format_autogluon_config_prompt(
    domain: dict,
    use_case: str,
    methodology: str,
    dataset_insights: dict
) -> tuple[str, str]:
    """
    Format the system and user prompts for AutoGluon configuration recommendation.
    
    Args:
        domain_name: Name of the business domain
        domain_description: Detailed description of the domain context
        use_case: Description of the specific use case and problem
        methodology: Type of ML problem (binary_classification, multiclass_classification, regression)
        dataset_insights: Dictionary containing feature and target information
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    
    # feature_columns = dataset_insights.get('feature_columns', {})
    # target_info = dataset_insights.get('target', {})
    
    # feature_summary = []
    # for col_name, col_info in feature_columns.items():
    #     feature_summary.append(
    #         f"  - {col_name}: "
    #         f"type={col_info.get('dtype', 'unknown')}, "
    #         f"missing={col_info.get('missing_pct', 0):.1f}%, "
    #         f"unique={col_info.get('unique_count', 'N/A')}"
    #     )
    #     if 'min' in col_info and 'max' in col_info:
    #         feature_summary.append(f"    range=[{col_info['min']}, {col_info['max']}]")
    
    # feature_text = "\n".join(feature_summary) if feature_summary else "No feature information provided"
    
    # # Format target information
    # target_text = []
    # if target_info:
    #     target_text.append(f"Target Column: {target_info.get('name', 'unknown')}")
    #     target_text.append(f"  Type: {target_info.get('dtype', 'unknown')}")
        
    #     if 'class_distribution' in target_info:
    #         target_text.append("  Class Distribution:")
    #         for cls, count in target_info['class_distribution'].items():
    #             target_text.append(f"    - {cls}: {count}")
        
    #     if 'min' in target_info and 'max' in target_info:
    #         target_text.append(f"  Range: [{target_info['min']}, {target_info['max']}]")
            
    #     if 'mean' in target_info:
    #         target_text.append(f"  Mean: {target_info['mean']:.2f}")
    
    # target_summary = "\n".join(target_text) if target_text else "No target information provided"
    
    # # Get dataset size information
    # num_samples = dataset_insights.get('num_samples', 'unknown')
    # num_features = len(feature_columns) if feature_columns else 'unknown'

    # DATASET INSIGHTS:
    # ================
    # Number of Samples: {num_samples}
    # Number of Features: {num_features}

    # Features:
    # {feature_text}

    # {target_summary}
    # 8. hyperparameters: Hyperparameter preset ("default", "light", "very_light")
    # 9. auto_stack: Whether to use automatic stacking (true/false)
    # 10. infer_limit: Max inference time per row in seconds (or null)
    # 11. infer_limit_batch_size: Batch size for inference speed (or null)
    # 12. refit_full: Whether to retrain on full data (true/false)
    # 13. calibrate_decision_threshold: Threshold calibration setting ("auto", true, false)

    
    user_prompt = f"""Please recommend optimal AutoGluon TabularPredictor configuration for the following scenario:

DOMAIN INFORMATION:
==================
Domain: {domain}

USE CASE:
=========
{use_case}

METHODOLOGY:
===========
Problem Type: {methodology}

DATASET INSIGHTS:
================
{dataset_insights}

TASK:
=====
Based on the above information, recommend an optimal AutoGluon configuration that includes:

1. eval_metric: The primary metric to optimize
2. preset: Quality/speed tradeoff preset  
3. additional_metrics: Other metrics to track (list)
4. time_limit: Training time in seconds
5. num_bag_folds: Number of k-fold bagging folds (0 for none, 5-10 for bagging)
6. num_bag_sets: Number of bagging sets (1-3, only if bagging is used)
7. num_stack_levels: Number of stacking levels 


Consider multiple scenarios:
- Scenario A: Maximum accuracy (accepting longer training time)
- Scenario B: Balanced accuracy and speed (production-ready)
- Scenario C: Fast training and inference (prototyping/deployment constrained)

"""
    
    return AUTOGLUON_CONFIG_SYSTEM_PROMPT, user_prompt