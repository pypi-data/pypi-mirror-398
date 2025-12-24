---
name: evaluation
description: Evaluate ML models with appropriate metrics, design testing strategies, detect drift, and run A/B tests for production systems
---

# Evaluation Skill

## Description

This skill covers comprehensive evaluation of ML systems: selecting appropriate metrics, designing train/val/test splits, implementing offline and online evaluation, detecting model degradation and data drift, running A/B tests, and tracking experiments. Use this skill to assess model performance, compare different approaches, validate before deployment, and monitor production systems. Proper evaluation prevents deploying bad models and enables data-driven decisions.

Evaluation is critical at every stage: during development (compare models), before deployment (validate quality), and in production (monitor performance). This skill emphasizes statistical rigor, avoiding common pitfalls (data leakage, p-hacking), and aligning metrics with business objectives.

## When to Use

- When selecting metrics for a new ML project
- When designing train/validation/test splits or cross-validation strategy
- When comparing multiple models to select the best one
- When conducting hyperparameter tuning experiments
- When validating a model before production deployment
- When running A/B tests to compare model versions
- When monitoring model performance in production
- When detecting data drift or model degradation
- When performing error analysis or debugging model failures
- When evaluating fairness across demographic groups
- When setting up experiment tracking (MLflow, W&B)

## When to Use

- When selecting metrics for a new ML project
- When designing train/validation/test splits or cross-validation strategy
- When comparing multiple models to select the best one
- When conducting hyperparameter tuning experiments
- When validating a model before production deployment
- When running A/B tests to compare model versions
- When monitoring model performance in production
- When detecting data drift or model degradation
- When performing error analysis or debugging model failures
- When evaluating fairness across demographic groups
- When setting up experiment tracking (MLflow, W&B)

## How to Use

### Step 1: Select Appropriate Metrics

**Choose metrics aligned with business objectives and problem type:**

**Classification:**
- Binary: Accuracy, Precision, Recall, F1, F-beta, AUC-ROC, PR-AUC
- Multi-class: Macro/Micro/Weighted F1, per-class metrics, confusion matrix
- Imbalanced: PR-AUC > ROC-AUC, balanced accuracy, MCC
- Consider cost: False positives vs false negatives (e.g., fraud: FP = annoy user, FN = lose money)

**Regression:**
- MAE (robust to outliers), RMSE (penalizes large errors), MAPE (relative error), R² (explained variance)
- Choose based on error distribution and business impact

**Ranking:**
- NDCG, MRR, MAP, Precision@K, Recall@K
- Focus on top-k performance (users rarely scroll past top 5)

**Generation (Text/Images):**
- Text: BLEU, ROUGE, BERTScore (automatic), human evaluation (quality)
- Images: FID, IS, LPIPS, CLIP score
- Always include human evaluation for subjective quality

**Agents/LLMs:**
- Task success rate (completed correctly?)
- Efficiency (steps taken, tokens used)
- Correctness (factual accuracy, hallucination rate)
- Safety (no harmful outputs, proper tool use)

**Define primary metric + secondary metrics + guardrails (e.g., latency < 100ms, cost per prediction < $0.01).**

**Use problem-framing skill insights to align metrics with business goals.**

### Step 2: Design Data Splits and Validation Strategy

**Create proper train/validation/test splits:**

**Random Split (most common):**
- 70/15/15 or 80/10/10 for train/val/test
- Stratified: preserve class distribution (classification)
- Use for: i.i.d. data (independent and identically distributed)

**Time-Based Split (temporal data):**
- Train on past, validate on recent, test on future
- Use for: time series, production scenarios
- Never shuffle temporal data

**Group-Based Split:**
- Keep all samples from same group together (user, hospital, device)
- Prevents leakage when samples within group are correlated
- Use for: medical data (same patient), user behavior

**Cross-Validation:**
- K-Fold (k=5 or 10): standard approach, more stable estimates
- Stratified K-Fold: preserve class distribution
- Time Series Split: expanding or rolling window
- Leave-One-Group-Out: for grouped data
- Use for: small datasets, hyperparameter tuning (inner loop)

**Holdout test set:**
- NEVER touch until final evaluation
- Create multiple test sets for different scenarios (common cases, edge cases, adversarial)

**Critical: Fit all preprocessing (scaling, encoding) ONLY on training data, then transform val/test.**

### Step 3: Compare Models and Perform Error Analysis

**Model comparison:**
- Train multiple models with same data splits
- Compare on validation set using primary metric
- Statistical significance: paired t-test, Wilcoxon signed-rank
- Confidence intervals: bootstrap 1000+ samples
- Trade-off analysis: precision-recall curves, ROC curves

**Error analysis:**
- Confusion matrix: which classes are confused?
- Per-class performance: which categories underperform?
- Slice-based evaluation: performance by subgroup (age, location, time)
- Failure case analysis: manually inspect errors, find patterns
- Feature importance for errors: which features matter for mistakes?

**Calibration (if outputting probabilities):**
- Reliability diagram: predicted vs actual probability
- Expected Calibration Error (ECE)
- Calibration methods: Platt scaling, isotonic regression, temperature scaling

**Fairness evaluation:**
- Per-group metrics: accuracy, FPR, FNR by demographics
- Disparate impact ratio (should be >0.8)
- Equal opportunity, equalized odds
- Tools: Fairlearn, AI Fairness 360

**Document findings: which model is best? Why? What are limitations?**

### Step 4: Track Experiments and Maintain Reproducibility

**Use experiment tracking tools:**
- MLflow, Weights & Biases, Neptune, TensorBoard
- Track: hyperparameters, metrics, code version, data version, artifacts

**What to log:**
- Code: git commit hash, dependencies (requirements.txt)
- Data: dataset version, preprocessing steps
- Model: architecture, hyperparameters, random seeds
- Metrics: train/val/test performance, training curves
- Artifacts: model weights, predictions, plots
- Environment: hardware, framework versions
- Notes: observations, ideas, decisions

**Reproducibility checklist:**
- Fix random seeds (Python, NumPy, PyTorch/TensorFlow)
- Pin dependencies (exact versions)
- Version datasets (DVC, dataset hash)
- Document data splits (which samples in train/val/test)
- Save preprocessing pipelines with models

**Organize experiments:**
- Hierarchical: project → experiment → run
- Naming convention: `model-name_dataset_date` (e.g., `xgboost_churn_2024-01-15`)
- Tags: baseline, ablation, production, failed
- Comparison views: parallel coordinates, scatter plots

**Use ml-docs to fetch MLflow, W&B documentation.**

### Step 5: Monitor Production Performance

**Online evaluation (production):**
- Track metrics on live traffic (if labels available)
- Compare to offline validation results (sanity check)
- Monitor business metrics: conversion, revenue, engagement
- Set up alerts: performance drops >5%, error rate spikes

**A/B Testing:**
- Random traffic split (50/50 or 90/10 for canary)
- Minimum sample size: power analysis (typically need 1000+ samples per variant)
- Statistical significance: z-test, chi-square, Mann-Whitney U
- Multiple testing correction: Bonferroni, FDR
- Run for sufficient time: account for weekly/daily patterns
- Compare primary metric + guardrail metrics (latency, errors)

**Data Drift Detection:**
- Feature distribution changes: PSI, KL divergence, Wasserstein distance
- Covariate shift: P(X) changes, P(Y|X) constant
- Concept drift: P(Y|X) changes (model needs retraining)
- Tools: Evidently AI, NannyML, Alibi Detect

**Model Degradation Monitoring:**
- Track prediction distribution (should be stable)
- Monitor confidence scores (dropping confidence = uncertainty)
- Collect delayed labels: compare predictions to actuals
- Retrain triggers: performance drops, drift detected, scheduled

**Dashboard recommendations:**
- Real-time: latency, throughput, error rate
- Daily: performance metrics, data quality
- Weekly: drift metrics, fairness metrics
- Monthly: business impact, cost analysis

**Use ml-docs to fetch monitoring tool documentation (Evidently AI, Prometheus).**

## Best Practices

- **Align with business:** Metrics must reflect true business value, not just ML performance
- **Multiple metrics:** Primary + secondary + guardrails. Never optimize single metric in isolation
- **Proper validation:** No data leakage, proper time splits, stratification when needed
- **Statistical rigor:** Report confidence intervals, not just point estimates. Test for significance
- **Error analysis:** Understand WHY model fails, not just THAT it fails
- **Fairness checks:** Evaluate across demographic groups, especially for high-stakes decisions
- **Reproducibility:** Version everything (code, data, models, environment)
- **Test set discipline:** NEVER tune on test set. Use only for final evaluation
- **Monitor continuously:** Offline performance ≠ online performance. Track both
- **Document decisions:** Why this metric? This threshold? This model? Future you will forget

## Examples

### Example 1: Binary Classification Model Selection

**User Request:** "I trained Logistic Regression, Random Forest, and XGBoost for fraud detection. Which should I deploy?"

**Approach:**
1. **Define metrics:** 
   - Primary: PR-AUC (imbalanced data, fraud is rare)
   - Secondary: Precision@90% recall (catch 90% fraud, minimize false alarms)
   - Guardrail: Inference time < 50ms
2. **Evaluate on validation set:**
   - Logistic Regression: PR-AUC=0.72, Precision@90%=0.15, 5ms
   - Random Forest: PR-AUC=0.81, Precision@90%=0.28, 30ms
   - XGBoost: PR-AUC=0.84, Precision@90%=0.32, 25ms
3. **Statistical significance:**
   - Bootstrap 1000 samples, XGBoost significantly better (p<0.05)
   - Confidence interval: XGBoost PR-AUC [0.82, 0.86]
4. **Error analysis:**
   - XGBoost fails on: new fraud patterns, low-amount transactions
   - Confusion matrix: FP mostly on legitimate international transactions
   - Recommendation: Add feature for international transaction history
5. **Final validation on test set:**
   - XGBoost: PR-AUC=0.83 (consistent with validation)
6. **Decision:** Deploy XGBoost. Meets latency requirement, best performance, statistically significant improvement

**Key code pattern:**
```python
from sklearn.metrics import precision_recall_curve, auc
from scipy import stats

# Compute PR-AUC
precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
pr_auc = auc(recall, precision)

# Bootstrap for confidence interval
from sklearn.utils import resample
aucs = []
for i in range(1000):
    y_true_boot, y_pred_boot = resample(y_true, y_pred_proba)
    p, r, _ = precision_recall_curve(y_true_boot, y_pred_boot)
    aucs.append(auc(r, p))
print(f"95% CI: [{np.percentile(aucs, 2.5)}, {np.percentile(aucs, 97.5)}]")

# Paired t-test for model comparison
_, p_value = stats.ttest_rel(xgboost_scores, random_forest_scores)
```

### Example 2: A/B Test for Model Version

**User Request:** "We deployed a new recommendation model. How do I know if it's better than the old one?"

**Approach:**
1. **Setup A/B test:**
   - Traffic split: 50% old model (control), 50% new model (treatment)
   - Primary metric: Click-through rate (CTR)
   - Secondary: Conversion rate, session length
   - Guardrails: Latency < 100ms, error rate < 0.1%
2. **Sample size calculation:**
   - Current CTR: 5%
   - Minimum detectable effect: 0.5% absolute increase (10% relative)
   - Power: 80%, significance: 5%
   - Required: 31,000 users per variant (use power calculator)
3. **Run test for 2 weeks:**
   - Collect sufficient samples
   - Account for day-of-week effects
4. **Analyze results:**
   - Control CTR: 5.0% (95% CI: [4.8%, 5.2%])
   - Treatment CTR: 5.4% (95% CI: [5.2%, 5.6%])
   - Z-test: p=0.002 (statistically significant)
   - Relative improvement: 8%
5. **Check guardrails:**
   - Latency: 85ms (both variants)
   - Error rate: 0.05% (both variants)
   - Conversion rate: no significant difference
6. **Decision:** New model is significantly better. Full rollout approved.

**Key considerations:**
- Don't stop test early (peeking problem)
- Use multiple testing correction if testing multiple metrics
- Check for novelty effects (users like new things temporarily)
- Segment analysis: improvement consistent across user groups?

### Example 3: Production Drift Detection

**User Request:** "Our model accuracy dropped from 85% to 78% in production. What happened?"

**Approach:**
1. **Identify issue type:**
   - Collect recent predictions and features
   - Check if we have ground truth labels (yes, delayed by 7 days)
2. **Data drift analysis:**
   - Compare feature distributions: training vs last 30 days production
   - PSI (Population Stability Index) for each feature
   - Finding: Feature "income" shifted significantly (PSI=0.35, threshold=0.1)
   - Root cause: Economic changes, user demographics shifted
3. **Concept drift check:**
   - Compare predictions vs actuals for last 7 days (labels available)
   - Finding: Model underperforms for low-income segment
   - Hypothesis: Relationship between features and target changed
4. **Prediction drift:**
   - Compare prediction distribution: training vs production
   - Finding: Model predicting more positive class than expected
5. **Action items:**
   - Short-term: Retrain model with recent data (last 3 months)
   - Long-term: Set up automated retraining (monthly)
   - Monitoring: Add alerts for PSI > 0.1 on critical features

**Key code pattern:**
```python
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report

# Create drift report
report = Report(metrics=[DataDriftPreset()])
report.run(reference_data=train_df, current_data=prod_df)
report.save_html("drift_report.html")

# Check drift for specific feature
from scipy.stats import ks_2samp
statistic, p_value = ks_2samp(train_df['income'], prod_df['income'])
if p_value < 0.05:
    print("Significant drift detected in 'income' feature")
```

**Use ml-docs to fetch Evidently AI documentation for drift detection.**

## Notes

- **Test set contamination:** Most common mistake. Never tune hyperparameters on test set. Use validation set
- **Data leakage:** Fitting preprocessing on full data, using future information, target leakage. Always split FIRST
- **P-hacking:** Testing many metrics/models, reporting only significant results. Use multiple testing correction
- **Overfitting to validation set:** Excessive tuning leads to overfitting val set. Use nested CV or holdout test set
- **Ignoring variance:** Single run with one random seed is unreliable. Use CV or multiple seeds
- **Wrong baseline:** Compare to meaningful baseline (not random), document how baseline was chosen
- **Metric gaming:** Optimizing metric that doesn't reflect business value (classic example: accuracy on imbalanced data)
- **Fairness blindness:** Not checking per-group performance can hide serious bias issues
- **Offline-online gap:** Models that perform well offline may fail online due to different distributions, serving latency, user behavior
- **Use ml-docs skill:** Fetch scikit-learn, MLflow, W&B, Evidently AI documentation for specific implementations
- **Integration with other skills:** Receives models from classical-ml, deep-learning, llm-agent. Feeds results to mlops-production for deployment decisions. Coordinates with safety-governance for fairness checks