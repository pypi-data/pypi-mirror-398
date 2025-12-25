from pydantic import BaseModel, Field
from typing import List, Literal

class AutoGluonConfig(BaseModel):
    eval_metric: str = Field(
        ..., 
        description="Primary metric to optimize. Allowed: 'accuracy', 'log_loss', 'f1', 'roc_auc', 'precision', 'recall'."
    )
    
    preset: Literal[
        'best_quality', 'high_quality', 'good_quality', 'medium_quality'
    ] = Field(
        ..., 
         description="Preset configurations. 'extreme_quality' and 'best_quality' enable bagging/stacking for maximum accuracy."
    )
    
    additional_metrics: List[str] = Field(
        ..., 
        description="List of additional metrics to track. Allowed: 'accuracy', 'log_loss', 'f1', 'roc_auc', 'precision', 'recall'."
    )
    
    time_limit: int = Field(
        ..., 
        description="Total training time in seconds. AutoGluon will distribute this across models. Small datasets: 300, Medium: 3600, Large: 7200+."
    )
    
    num_bag_folds: int = Field(
        ..., 
        description="Number of folds for k-fold bagging. 0 = no bagging. 5-10 is standard for 'best_quality'. Bagging reduces variance and allows the model to be trained on all data (if refit_full=True)."
    )
    
    num_bag_sets: int = Field(
        ..., 
        description="Number of bagging sets. Each set repeats k-fold bagging to reduce variance further. Only used if num_bag_folds > 0. Usually 1-3."
    )
    
    num_stack_levels: int = Field(
        ..., 
        description="Levels of stacking. 0 = no stacking, 1 = one level (models trained on base model predictions). Higher values increase accuracy but exponentially increase training time."
    )

    models: list[str] = Field(
        ...,
        description="""Models to train. 
        'GBM', 
        'CAT', 
        'XGB', 
        'RF', 
        'XT', 
        'KNN'. """
    )

    fit_weighted_ensemble: bool = Field(
        ..., 
        description="Whether to fit an ensemble that weights predictions of base models to improve accuracy. Usually recommended to keep True."
    )

    split_test_size: float = Field(
        ..., 
        description="Fraction of data held out for validation. You MUST choose exactly one value from: [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]."
    )