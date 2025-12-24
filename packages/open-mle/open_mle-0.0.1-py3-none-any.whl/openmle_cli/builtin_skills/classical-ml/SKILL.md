---
name: classical-ml
description: Exploratory data analysis, statistical modeling, traditional ML algorithms, and model selection for structured data problems
---

# Classical ML Skill

## Description

This skill handles traditional machine learning approaches for structured/tabular data. It covers the full workflow from exploratory data analysis (EDA) through model training, evaluation, and interpretation. Use this skill for classification, regression, and clustering problems where you have structured data (CSV, database tables, DataFrames) and want to apply proven ML algorithms like decision trees, random forests, gradient boosting, linear models, and SVMs.

Classical ML often outperforms deep learning on small-to-medium structured datasets (<100K rows) and provides better interpretability. This skill emphasizes statistical rigor, proper validation, and production-ready implementations.

## When to Use

- When user asks to analyze tabular/structured data (CSV, Excel, database tables)
- When building classification or regression models for structured features
- When user requests EDA, data profiling, or statistical analysis
- When implementing traditional ML algorithms (XGBoost, Random Forest, Logistic Regression, etc.)
- When user needs feature engineering for non-deep-learning approaches
- When interpretability is important (feature importance, SHAP values)
- When handling small-to-medium datasets where deep learning is overkill
- When user asks about handling imbalanced data, missing values, or outliers
- When building ensemble models or comparing multiple algorithms

## How to Use

### Step 1: Exploratory Data Analysis (EDA)

**Understand the data before modeling:**
- Load data and check basic info (shape, dtypes, missing values)
- Compute summary statistics (mean, median, std, percentiles)
- Visualize distributions (histograms, box plots, KDE)
- Check for outliers (IQR method, Z-score)
- Analyze correlations (heatmaps, pair plots)
- Identify data quality issues (duplicates, inconsistencies, missing patterns)

**Use pandas, NumPy for analysis and matplotlib/seaborn for visualization.**

### Step 2: Feature Engineering & Preprocessing

**Transform raw data into ML-ready features:**
- Handle missing values (imputation, dropping, or flagging)
- Encode categorical variables (one-hot, label, target encoding)
- Scale numerical features (StandardScaler, MinMaxScaler, RobustScaler)
- Create interaction features, polynomial features, or domain-specific features
- Select relevant features (correlation filtering, RFE, feature importance)
- Split data properly (train/val/test or cross-validation strategy)

**Critical: Fit transformers ONLY on training data, then transform val/test sets.**

### Step 3: Model Selection & Training

**Choose and train appropriate algorithms:**
- Start with simple baseline (majority class, mean prediction)
- Train multiple algorithms with default parameters (Logistic Regression, Random Forest, XGBoost)
- Select top 2-3 performers based on cross-validation
- Perform hyperparameter tuning (GridSearchCV, RandomizedSearchCV, or Optuna)
- Consider ensemble methods if performance gain justifies complexity
- Validate on holdout test set for final evaluation

**Use scikit-learn for most algorithms. For gradient boosting, prefer XGBoost, LightGBM, or CatBoost.**

### Step 4: Model Evaluation & Interpretation

**Assess model quality and understand predictions:**
- Calculate appropriate metrics (accuracy, precision, recall, F1, AUC-ROC for classification; MAE, RMSE, R² for regression)
- Analyze confusion matrix and per-class performance
- Perform error analysis (what types of examples does the model fail on?)
- Generate feature importance plots
- Use SHAP or LIME for detailed explanations
- Check calibration if outputting probabilities

### Step 5: Production Preparation

**Make model deployment-ready:**
- Serialize model and preprocessing pipeline (joblib, pickle, or ONNX)
- Create inference function that handles new data
- Document model performance, limitations, and usage
- Implement input validation and error handling
- Consider model size and inference latency requirements

## Best Practices

- **Start simple:** Always compare against a simple baseline before trying complex models
- **Proper validation:** Use stratified k-fold CV for classification, time-aware splits for time series, group-aware splits when needed
- **No data leakage:** Fit preprocessing only on training data; test set should never influence model training
- **Feature engineering > complex models:** Good features with simple models often beat bad features with complex models
- **Handle imbalanced data:** Use appropriate metrics (F1, PR-AUC), consider resampling or class weights
- **Reproducibility:** Set random seeds, version data and code, track experiments
- **Interpretability:** Especially important for high-stakes decisions (healthcare, finance, hiring)
- **Monitor in production:** Track feature drift, prediction drift, and performance degradation

## Examples

### Example 1: Binary Classification with Imbalanced Data

**User Request:** "Build a fraud detection model for credit card transactions. The dataset has 99% legitimate and 1% fraud cases."

**Approach:**
1. **EDA:** Check class distribution, analyze feature distributions for fraud vs legitimate, look for missing values
2. **Preprocessing:** Handle missing values, scale numerical features, encode categorical features
3. **Handle imbalance:** Use stratified split, compute class weights, consider SMOTE or undersampling
4. **Modeling:** Train Logistic Regression, Random Forest, XGBoost with class weights
5. **Evaluation:** Use PR-AUC instead of accuracy, analyze confusion matrix, tune threshold for desired precision/recall trade-off
6. **Interpretation:** Generate SHAP values to explain which features indicate fraud

**Key commands:**
```python
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE
from sklearn.metrics import classification_report, roc_auc_score

# Stratified split preserves class distribution
# SMOTE for oversampling minority class
# Use PR-AUC metric for imbalanced data
```

### Example 2: Regression with Feature Selection

**User Request:** "Predict house prices using a dataset with 80 features. Some features might be irrelevant."

**Approach:**
1. **EDA:** Analyze target distribution, check correlations between features and target, identify multicollinearity
2. **Feature selection:** Remove low-variance features, drop highly correlated pairs, use RFE or feature importance
3. **Preprocessing:** Handle outliers in price, log-transform skewed features, scale features
4. **Modeling:** Compare Linear Regression, Ridge, Lasso, Random Forest, XGBoost
5. **Hyperparameter tuning:** Use RandomizedSearchCV for efficient search
6. **Evaluation:** Use MAE and RMSE, analyze residual plots, check for heteroscedasticity
7. **Interpretation:** Show feature importance and partial dependence plots

**Key commands:**
```python
from sklearn.feature_selection import RFE, SelectKBest
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import RandomizedSearchCV

# Use Lasso for automatic feature selection via L1 regularization
# Ridge for handling multicollinearity
# GradientBoosting often performs best on tabular data
```

### Example 3: Multi-class Classification with Hyperparameter Tuning

**User Request:** "Classify customer segments into 5 categories based on their behavior. I want the best possible accuracy."

**Approach:**
1. **EDA:** Check class distribution (balanced or imbalanced?), analyze feature importance for each class
2. **Preprocessing:** Standard scaling, encode categorical features, handle missing values
3. **Baseline:** Train simple Logistic Regression to establish baseline performance
4. **Model comparison:** Train Random Forest, XGBoost, LightGBM with default parameters, select top 2
5. **Hyperparameter tuning:** Use Optuna or GridSearchCV to optimize hyperparameters for top models
6. **Ensemble:** If helpful, create voting classifier combining best models
7. **Evaluation:** Confusion matrix, per-class precision/recall, macro/micro F1 scores

**Key commands:**
```python
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import optuna

# Use Optuna for efficient Bayesian hyperparameter optimization
# LightGBM often fastest for large datasets
# VotingClassifier for ensemble if models are diverse
```

## Notes

- **When to use classical ML vs deep learning:** For structured data with <100K rows, classical ML often wins. For larger datasets, images, text, or sequences, consider deep learning.
- **XGBoost/LightGBM/CatBoost comparison:** XGBoost is most mature, LightGBM is fastest, CatBoost handles categorical features best
- **Interpretability vs performance trade-off:** Linear models and decision trees are most interpretable; boosted trees and ensembles perform better but are harder to interpret
- **Cross-validation strategy matters:** Use stratified for classification, time-series split for temporal data, group k-fold when samples are grouped
- **Feature engineering is iterative:** Start simple, add complexity based on error analysis and domain knowledge
- **Always check for data leakage:** Common sources include using future information, target leakage, or train/test contamination
- **Use ml-docs skill to fetch scikit-learn, XGBoost, pandas documentation when needed for specific implementations**