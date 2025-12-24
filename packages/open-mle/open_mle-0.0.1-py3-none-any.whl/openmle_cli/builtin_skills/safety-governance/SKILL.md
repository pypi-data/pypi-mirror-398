---
name: safety-governance
description: Ensure AI safety, fairness, privacy, security, and regulatory compliance for responsible ML deployment
---

# Safety & Governance Skill

## Description

This skill covers responsible AI practices: fairness and bias mitigation, privacy-preserving techniques, security and adversarial robustness, explainability, regulatory compliance (GDPR, CCPA, EU AI Act), and ethical frameworks. Use this skill when evaluating models for bias, implementing privacy protections, securing ML systems, ensuring compliance, or establishing AI governance processes. Safety and governance are critical for production ML systems, especially in high-stakes domains (healthcare, finance, hiring, criminal justice).

Responsible AI prevents harm, builds trust, and ensures compliance. This skill emphasizes proactive risk assessment, continuous monitoring, and systematic approaches to identifying and mitigating ethical and legal risks.

## When to Use

- When evaluating models for bias across demographic groups
- When implementing privacy protections (differential privacy, federated learning)
- When securing ML systems against adversarial attacks
- When building explainable/interpretable models
- When ensuring regulatory compliance (GDPR, CCPA, HIPAA, EU AI Act)
- When conducting fairness audits or impact assessments
- When establishing AI governance frameworks and review processes
- When responding to security incidents or model failures
- When documenting models (model cards, datasheets)
- When assessing ethical implications of ML deployments

## How to Use

### Step 1: Assess Fairness and Bias

**Identify potential sources of bias:**
- Historical bias: Training data reflects societal inequities
- Representation bias: Underrepresented groups in dataset
- Measurement bias: Noisy labels, proxy variables
- Aggregation bias: Single model for heterogeneous populations
- Deployment bias: Model used in unintended contexts

**Evaluate fairness:**
- Disaggregated evaluation: Performance by demographic group (gender, race, age)
- Fairness metrics:
  - Demographic parity: P(Ŷ=1|A=0) = P(Ŷ=1|A=1)
  - Equal opportunity: Equal TPR across groups
  - Equalized odds: Equal TPR and FPR across groups
  - Predictive parity: Equal precision across groups
- Disparate impact ratio: min/max of positive prediction rates (should be >0.8)
- Intersectional analysis: Check combinations of attributes (e.g., Black women)
- Worst-group performance: Identify most disadvantaged group

**Mitigation strategies:**
- Pre-processing: Resample, reweigh, remove biased features
- In-processing: Fairness constraints in loss function, adversarial debiasing
- Post-processing: Adjust thresholds per group, calibration
- Model selection: Choose architectures less prone to bias

**Tools:** Fairlearn, AI Fairness 360, What-If Tool, Aequitas

**Note:** Fairness definitions often conflict (impossibility theorems). Choose based on use case and stakeholder input.

**Use evaluation skill for fairness metrics implementation.**

### Step 2: Implement Privacy Protections

**Identify privacy threats:**
- Membership inference: Determine if individual in training data
- Model inversion: Reconstruct training data from model
- Attribute inference: Infer sensitive attributes
- Data extraction: Extract memorized examples (especially LLMs)

**Privacy-preserving techniques:**

**Differential Privacy:**
- Add calibrated noise to guarantee privacy (ε, δ parameters)
- DP-SGD: Clip gradients, add noise during training
- Trade-off: Privacy (lower ε) ↔ Utility (model accuracy)
- Typical values: ε=1-10 for reasonable utility

**Federated Learning:**
- Train on decentralized data without centralizing
- Share only model updates, not raw data
- Secure aggregation: Encrypt gradients
- Use for: Medical data, mobile devices

**Data Anonymization:**
- k-anonymity: Each record indistinguishable from k-1 others
- l-diversity: Diverse sensitive values within groups
- t-closeness: Distribution of sensitive values similar to overall
- Techniques: Generalization, suppression, perturbation

**PII Handling:**
- Detection: Regex, NER models for names, emails, SSNs
- Masking: Redaction, tokenization, pseudonymization
- Encryption: AES-256 at rest, TLS 1.3 in transit
- Deletion: Right to erasure (GDPR Article 17)

**Compliance:**
- GDPR: Data minimization, purpose limitation, right to explanation, erasure
- CCPA: Disclosure, access, deletion, opt-out of sale
- HIPAA: Healthcare data protection (US)
- Data residency: Store data in specific regions (EU, China)

**Tools:** Opacus (PyTorch DP), PySyft (federated learning), Presidio (PII detection)

**Use ml-docs to fetch privacy library documentation.**

### Step 3: Secure ML Systems

**Adversarial Robustness:**

**Attack types:**
- White-box: Attacker has model access (FGSM, PGD, C&W attacks)
- Black-box: Query-based attacks, transfer attacks
- Physical: Adversarial patches, 3D objects
- Backdoor: Poisoned training data triggers misclassification

**Defenses:**
- Adversarial training: Include adversarial examples in training
- Input validation: Reject out-of-distribution inputs
- Certified defenses: Provable robustness guarantees
- Ensemble methods: Multiple models, majority vote
- Gradient masking: Obfuscate gradients (not recommended, false sense of security)

**API Security:**
- Prompt injection: Manipulate LLM via crafted inputs (jailbreaking)
- Defense: Input sanitization, output filtering, system prompt protection
- Model stealing: Reconstruct model via queries
- Defense: Rate limiting, query monitoring, watermarking
- Data poisoning: Inject malicious training data
- Defense: Data validation, outlier detection, robust training

**Infrastructure Security:**
- Authentication: OAuth, API keys, JWT tokens
- Authorization: RBAC (role-based access control), least privilege
- Encryption: TLS for transit, AES for rest
- Secrets management: Vault, AWS Secrets Manager (never hardcode)
- Network security: VPC, firewalls, WAF
- Container security: Scan images (Trivy, Snyk), runtime protection

**Supply Chain Security:**
- Dependency scanning: Detect vulnerabilities (Dependabot, Snyk)
- Model provenance: Verify source, integrity (checksums, signatures)
- Reproducibility: Pin versions, audit dependencies
- Code signing: Verify authenticity

**Use mlops-production skill for infrastructure security implementation.**

### Step 4: Ensure Explainability and Compliance

**Explainability:**

**Model-agnostic methods:**
- SHAP: Shapley values for feature importance (any model)
- LIME: Local linear approximation (any model)
- Partial Dependence Plots (PDP): Marginal effect of features
- Permutation importance: Shuffle feature, measure impact
- Counterfactuals: Minimal input changes to flip prediction

**Model-specific methods:**
- Linear models: Coefficients as feature importance
- Tree models: Feature importance (gain, split count)
- Neural networks: Attention weights, Grad-CAM, saliency maps

**LLM Explainability:**
- Chain-of-thought: Show reasoning steps
- Citations: Reference sources for claims
- Confidence scores: Uncertainty quantification
- Token attribution: Which inputs matter most

**Trade-offs:**
- Accuracy vs interpretability (simpler models more interpretable)
- Global vs local explanations
- Fidelity vs simplicity

**Regulatory Compliance:**

**GDPR (EU):**
- Right to explanation: Meaningful info about logic
- Right to erasure: Delete personal data upon request
- Data minimization: Collect only what's needed
- Purpose limitation: Use data only for stated purpose
- Privacy by design: Build privacy into systems from start

**CCPA (California):**
- Disclosure: Inform users about data collection
- Access: Users can request their data
- Deletion: Users can request data deletion
- Opt-out: From data sale/sharing

**EU AI Act:**
- Risk-based approach: Prohibited, high-risk, limited-risk, minimal-risk
- High-risk systems: Conformity assessment, documentation, monitoring
- Transparency: Users informed when interacting with AI
- Human oversight: Humans can intervene and override

**Documentation:**
- Model cards: Intended use, performance, limitations, fairness
- Datasheets: Dataset characteristics, collection, biases
- Impact assessments: Privacy (DPIA), fairness, societal risks
- Audit trails: Decisions, changes, incidents

**Tools:** SHAP, LIME, Fairlearn, model card templates

**Use ml-docs to fetch explainability tool documentation.**

### Step 5: Establish Governance and Monitoring

**AI Governance Framework:**

**Risk Assessment:**
1. Identify stakeholders affected
2. Map potential harms (direct, indirect, short-term, long-term)
3. Assess likelihood and severity
4. Prioritize mitigation strategies

**Ethical Review:**
- Internal review board: Cross-functional team (ethics, legal, technical, domain experts)
- External audit: Independent third-party assessment
- Stakeholder consultation: Engage affected communities
- Continuous monitoring: Detect emerging issues

**Red Teaming:**
- Adversarial testing: Try to break the system
- Bias hunting: Search for discriminatory behavior
- Misuse scenarios: Identify abuse potential
- Edge cases: Unusual inputs, contexts

**Model Governance:**

**Model Inventory:**
- Catalog all models in production
- Metadata: Purpose, owner, data sources, performance, risks
- Lifecycle stage: Development, staging, production, retired
- Dependencies: Upstream/downstream models and systems

**Change Management:**
- Approval workflows: Who can deploy models?
- Impact assessment: Evaluate risks before deployment
- Rollback plan: How to revert if issues arise
- Communication: Notify stakeholders of changes

**Access Control:**
- Model access: Who can view, use, modify
- Data access: Who can access training/production data
- Audit logs: Track all access and changes
- Separation of duties: Prevent conflicts of interest

**Incident Management:**
- Detection: Monitoring alerts, user reports, audits
- Response: Triage severity, investigate, mitigate
- Communication: Internal and external stakeholders
- Postmortem: Root cause analysis, lessons learned, prevention

**Continuous Monitoring:**
- Performance: Accuracy, fairness, robustness
- Data quality: Distribution shifts, schema violations
- Prediction drift: Output distribution changes
- User feedback: Complaints, satisfaction scores
- Security: Attack attempts, anomalous behavior

**Regular Audits:**
- Fairness audit: Quarterly disaggregated performance review
- Privacy audit: PII handling, compliance verification
- Security audit: Vulnerability scanning, penetration testing
- Documentation review: Ensure model cards, datasheets up-to-date

**Use evaluation skill for continuous monitoring implementation.**

## Best Practices

- **Privacy by default:** Minimize data collection, anonymize when possible
- **Fairness from start:** Consider fairness in problem framing, not just post-hoc evaluation
- **Security in depth:** Multiple layers of defense (defense in depth principle)
- **Explainability built-in:** Don't bolt on after deployment, design for interpretability
- **Document everything:** Model cards, datasheets, decisions, trade-offs
- **Regular audits:** Quarterly fairness reviews, annual security assessments
- **Diverse teams:** Include varied perspectives in development and review
- **Stakeholder engagement:** Involve affected communities early and often
- **Continuous monitoring:** Don't deploy and forget, track metrics continuously
- **Fail gracefully:** Plan for failures, have fallbacks and human oversight
- **Transparency:** Be honest about limitations, risks, and uncertainty
- **Human oversight:** Keep humans in loop for high-stakes decisions

## Examples

### Example 1: Fairness Audit for Hiring Model

**User Request:** "Our resume screening model might be biased. How do I check and fix this?"

**Approach:**
1. **Define protected attributes:** Gender, race, age
2. **Disaggregated evaluation:**
   - Overall accuracy: 85%
   - By gender: Male 87%, Female 80% (7% gap)
   - By race: White 86%, Black 78%, Hispanic 81% (8% gap)
   - Intersectional: Black women 74% (worst group)
3. **Check fairness metrics:**
   - Demographic parity: Male 40% selected, Female 32% (violation)
   - Disparate impact ratio: 32/40 = 0.8 (borderline)
   - Equal opportunity: Different TPR across groups (violation)
4. **Root cause analysis:**
   - Feature importance: "Years of experience" highly weighted
   - Bias source: Women have career gaps (maternity leave) → lower experience → lower score
   - Historical bias: Training data reflects past hiring patterns
5. **Mitigation:**
   - Remove/reduce weight on "years of experience"
   - Add fairness constraints: Equalized odds constraint in training
   - Reweigh training data: Oversample underrepresented groups
   - Post-processing: Adjust thresholds per group to achieve fairness
6. **Re-evaluate:**
   - New accuracy: Male 84%, Female 83% (1% gap)
   - Demographic parity: Male 38%, Female 36% (improved)
   - Disparate impact ratio: 36/38 = 0.95 (compliant)
7. **Document:**
   - Model card: Known limitations, fairness trade-offs
   - Monitor: Quarterly audits, alert if fairness degrades

**Key code pattern:**
```python
from fairlearn.metrics import MetricFrame, demographic_parity_ratio
from fairlearn.reductions import ExponentiatedGradient, EqualizedOdds

# Evaluate fairness
metric_frame = MetricFrame(
    metrics={'accuracy': accuracy_score, 'selection_rate': selection_rate},
    y_true=y_test,
    y_pred=y_pred,
    sensitive_features=sensitive_features
)
print(metric_frame.by_group)

# Mitigate with fairness constraints
constraint = EqualizedOdds()
mitigator = ExponentiatedGradient(estimator, constraint)
mitigator.fit(X_train, y_train, sensitive_features=sensitive_train)
```

**Use ml-docs to fetch Fairlearn documentation.**

### Example 2: Privacy-Preserving Medical Model

**User Request:** "Train a model on patient data from 5 hospitals without centralizing sensitive medical records."

**Approach:**
1. **Choose federated learning:** Data stays at hospitals, only share model updates
2. **Architecture:**
   - Central server: Coordinates training, aggregates updates
   - Hospital clients: Train locally on their data
   - Secure aggregation: Encrypt gradients before sending
3. **Implementation:**
   - Initialize global model at server
   - Server sends model to hospitals
   - Each hospital trains on local data for N epochs
   - Hospitals send encrypted gradients to server
   - Server aggregates (averaging), updates global model
   - Repeat for M rounds
4. **Add differential privacy:**
   - Clip gradients: Limit contribution of any single patient
   - Add noise: Gaussian noise to aggregated updates
   - Privacy budget: ε=3 (reasonable trade-off)
5. **Evaluate:**
   - Centralized baseline (theoretical): 92% accuracy
   - Federated learning: 89% accuracy (3% drop acceptable)
   - Privacy guarantee: (ε=3, δ=10^-5)-differential privacy
6. **Compliance:**
   - HIPAA: Data never leaves hospitals
   - GDPR: Minimal data sharing, privacy by design
   - Document: Privacy guarantees, limitations

**Key considerations:**
- Non-IID data: Hospitals have different patient populations
- Communication cost: Sending updates expensive
- Stragglers: Some hospitals slower than others
- Trust: Verify server doesn't log sensitive info

**Tools:** PySyft, TensorFlow Federated, Flower

**Use ml-docs to fetch federated learning library documentation.**

### Example 3: Adversarial Robustness for Autonomous Vehicle

**User Request:** "Our object detection model for self-driving cars needs to be robust against adversarial attacks. How do I ensure safety?"

**Approach:**
1. **Threat model:**
   - Physical attacks: Adversarial stickers on stop signs
   - Digital attacks: Perturbed sensor inputs
   - Consequences: Misclassification could cause accidents (high stakes)
2. **Evaluate current robustness:**
   - Test on adversarial examples (FGSM, PGD)
   - Clean accuracy: 95%
   - Adversarial accuracy (PGD): 62% (vulnerable!)
3. **Implement defenses:**
   - Adversarial training: Include adversarial examples in training
     - Generate adversarial examples with PGD
     - Mix 50% clean, 50% adversarial in each batch
     - Train for more epochs (3x longer)
   - Input preprocessing: Denoising, JPEG compression
   - Ensemble: Multiple models, vote on prediction
   - Certified defense: Randomized smoothing for provable guarantees
4. **Re-evaluate:**
   - Clean accuracy: 93% (slight drop)
   - Adversarial accuracy (PGD): 85% (23% improvement)
   - Physical attacks: Test with printed adversarial patches
5. **Safety measures:**
   - Multiple sensors: Camera, LiDAR, radar (sensor fusion)
   - Confidence thresholds: Reject low-confidence predictions
   - Human oversight: Driver can intervene
   - Continuous monitoring: Flag anomalous inputs
6. **Testing:**
   - Extensive simulation: Millions of scenarios
   - Real-world testing: Controlled environments
   - Red team: Security researchers try to break system
7. **Documentation:**
   - Safety case: Risk analysis, mitigation strategies
   - Limitations: Known failure modes, when to disengage
   - Regulatory compliance: ISO 26262, UN R155/R156

**Key code pattern:**
```python
import torch
from torchattacks import PGD

# Generate adversarial examples
attack = PGD(model, eps=8/255, alpha=2/255, steps=10)
adv_images = attack(images, labels)

# Adversarial training
for epoch in range(epochs):
    for images, labels in dataloader:
        # Clean examples
        loss_clean = criterion(model(images), labels)
        
        # Adversarial examples
        adv_images = attack(images, labels)
        loss_adv = criterion(model(adv_images), labels)
        
        # Combined loss
        loss = 0.5 * loss_clean + 0.5 * loss_adv
        loss.backward()
        optimizer.step()
```

## Notes

- **Fairness-accuracy trade-off:** Often need to sacrifice some accuracy for fairness. Justify with stakeholder input
- **Privacy-utility trade-off:** Stronger privacy (lower ε) reduces model accuracy. Find acceptable balance
- **Adversarial robustness is hard:** Perfect robustness is impossible. Aim for acceptable risk reduction
- **Explainability limitations:** Complex models (deep learning) harder to explain than simple models (linear, trees)
- **Compliance is ongoing:** Regulations change, models drift, new risks emerge. Continuous effort required
- **Documentation prevents issues:** Model cards, datasheets catch problems before deployment
- **Diverse teams matter:** Homogeneous teams miss blind spots. Include varied perspectives
- **Red teaming is essential:** Adversarial testing finds issues before attackers do
- **Human oversight required:** Don't fully automate high-stakes decisions (hiring, healthcare, criminal justice)
- **Use ml-docs skill:** Fetch Fairlearn, SHAP, privacy library documentation for implementations
- **Integration with other skills:** Coordinates with evaluation for fairness metrics, mlops-production for security, infra-cost for compliance costs. Oversees all ML lifecycle stages