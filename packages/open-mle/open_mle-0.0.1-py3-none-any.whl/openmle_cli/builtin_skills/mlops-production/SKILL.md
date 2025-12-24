---
name: mlops-production
description: Deploy ML models to production with serving infrastructure, CI/CD pipelines, monitoring, and automated retraining
---

# MLOps Production Skill

## Description

This skill covers deploying and maintaining ML models in production environments. It includes model serving (REST APIs, batch, streaming), containerization, CI/CD pipelines, model registry, monitoring, automated retraining, and incident response. Use this skill when transitioning models from development to production, setting up deployment infrastructure, implementing monitoring systems, or maintaining production ML systems.

Production ML is fundamentally different from development. Models must be reliable, scalable, monitorable, and maintainable. This skill emphasizes operational excellence: zero-downtime deployments, comprehensive monitoring, automated pipelines, and incident response procedures.

## When to Use

- When deploying a trained model to production
- When building model serving APIs (REST, gRPC, batch)
- When containerizing ML applications with Docker
- When setting up CI/CD pipelines for ML
- When implementing model versioning and registry
- When monitoring model performance and infrastructure
- When setting up automated retraining pipelines
- When optimizing model inference (latency, throughput)
- When implementing deployment strategies (blue-green, canary, shadow)
- When debugging production issues or incidents
- When scaling ML systems to handle production traffic

## How to Use

### Step 1: Choose Deployment Pattern

**Select appropriate serving strategy:**

**Online Serving (Real-time):**
- REST API: FastAPI, Flask, Django (most common)
- gRPC: High performance, language-agnostic
- Latency: <100ms typical, <10ms critical applications
- Use for: User-facing predictions, fraud detection, recommendations
- Scaling: Horizontal (load balancer + multiple replicas)

**Batch Prediction:**
- Scheduled jobs: Airflow, cron
- Process large datasets offline
- Store predictions in database/cache
- Use for: Periodic scoring, analytics, non-time-sensitive tasks
- Latency: Minutes to hours acceptable

**Streaming:**
- Event-driven: Kafka, Kinesis, Pub/Sub
- Process messages as they arrive
- Maintain state for aggregations
- Use for: Real-time analytics, online features, IoT

**Edge Deployment:**
- Mobile: TensorFlow Lite, Core ML, ONNX
- IoT: TensorFlow Micro, optimized models
- Browser: TensorFlow.js, ONNX.js
- Use for: Low latency, privacy, offline capability

**Hybrid:**
- Precompute common predictions (batch)
- Fallback to online for new inputs
- Best of both worlds: speed + coverage

**Consider: latency requirements, traffic patterns, cost, infrastructure availability.**

**Use ml-docs to fetch FastAPI, Flask documentation for API implementation.**

### Step 2: Containerize and Set Up Infrastructure

**Create Docker container:**
- Base image: Python 3.9+ (or framework-specific like pytorch/pytorch)
- Install dependencies: requirements.txt with pinned versions
- Copy model artifacts and code
- Expose API endpoint
- Health check endpoint: `/health` returns 200 if ready
- Multi-stage build: smaller final image

**Orchestration with Kubernetes:**
- Deployment: Define replicas, resources (CPU/GPU, memory)
- Service: Load balancer, internal DNS
- HPA (Horizontal Pod Autoscaler): Auto-scale based on CPU/memory/custom metrics
- Health probes: Liveness (restart if dead), readiness (remove from load balancer if not ready)
- ConfigMap/Secrets: Environment variables, API keys

**Serverless (alternative):**
- AWS Lambda, Google Cloud Functions, Azure Functions
- Auto-scaling, pay-per-request
- Cold start latency (seconds) - not suitable for latency-critical
- Good for: Sporadic traffic, simple models, prototyping

**Infrastructure as Code:**
- Terraform, CloudFormation, Pulumi
- Version control infrastructure definitions
- Reproducible deployments

**Use ml-docs to fetch Docker, Kubernetes documentation.**

### Step 3: Implement CI/CD Pipeline

**Continuous Integration:**
- Trigger: Pull request, commit to main branch
- Steps:
  1. Linting: black, flake8, mypy (Python)
  2. Unit tests: pytest for code logic
  3. Data validation: Schema checks, quality tests
  4. Model tests: Load model, run inference on test samples
  5. Integration tests: API endpoint tests

**Continuous Deployment:**
- Stages: dev → staging → production
- Automated deployment to dev/staging
- Manual approval for production (or automated with sufficient testing)

**ML-specific pipeline:**
```
1. Code commit → Git push
2. Run tests (code, data, model)
3. Train model (if data/code changed)
4. Evaluate model (compare to baseline)
5. If passing threshold → Register model in registry
6. Deploy to staging environment
7. Run integration tests, load tests
8. If passing → Deploy to production (canary/blue-green)
9. Monitor for N hours
10. If stable → Full rollout
```

**Tools:**
- GitHub Actions, GitLab CI, Jenkins, CircleCI
- Argo Workflows, Kubeflow Pipelines (Kubernetes-native)
- DVC: Data/model versioning and pipeline tracking

**Automated testing:**
- Smoke tests: Basic functionality after deployment
- Load tests: Can handle expected traffic? (Locust, k6)
- Shadow tests: New model runs alongside old, compare outputs

**Use ml-docs to fetch CI/CD tool documentation (GitHub Actions, GitLab CI).**

### Step 4: Set Up Monitoring and Alerting

**Infrastructure Monitoring:**
- Metrics: CPU, memory, GPU utilization, disk I/O
- Latency: p50, p95, p99 (not just average)
- Throughput: Requests per second (QPS)
- Error rate: 4xx, 5xx errors
- Tools: Prometheus + Grafana, DataDog, New Relic

**Model Performance Monitoring:**
- Prediction metrics: If labels available, track accuracy/F1/etc.
- Prediction distribution: Should be stable over time
- Confidence scores: Track mean/std confidence
- Feature distribution: Detect drift (PSI, KL divergence)
- Data quality: Null rates, outliers, schema violations

**Business Metrics:**
- Downstream impact: Conversion, revenue, engagement
- User feedback: Explicit ratings, implicit (clicks, time spent)
- A/B test results: Treatment vs control performance

**Logging:**
- Structured logs: JSON format with timestamp, request_id, model_version
- Log: All predictions (input features, prediction, confidence, model version)
- Sampling: For high-traffic systems, sample logs (e.g., 10%)
- Retention: 30-90 days for debugging, longer for compliance

**Alerting:**
- Threshold-based: Latency >100ms, error rate >1%
- Anomaly detection: Sudden spikes/drops in metrics
- Data drift: PSI >0.1 on critical features
- Performance degradation: Accuracy drops >5%
- On-call rotation: PagerDuty, Opsgenie for critical alerts

**Dashboards:**
- Real-time: Latency, throughput, errors (5-min window)
- Daily: Performance metrics, data quality
- Weekly: Drift metrics, business impact
- Use: Grafana, Tableau, custom dashboards

**Tools for ML monitoring:** Evidently AI, Arize, Fiddler, Whylabs

**Use ml-docs to fetch Prometheus, Grafana, Evidently AI documentation.**

### Step 5: Implement Automated Retraining

**Retraining triggers:**
- Scheduled: Daily, weekly, monthly (most common)
- Performance-based: Accuracy drops below threshold
- Data-based: Accumulated N new samples
- Drift-based: Significant distribution shift detected

**Retraining pipeline:**
1. Fetch latest data from storage
2. Validate data quality (Great Expectations)
3. Preprocess and create features
4. Train new model with updated data
5. Evaluate on holdout set
6. Compare to production model (champion-challenger)
7. If better → Register new model, deploy to staging
8. If passing tests → Promote to production
9. Archive old model version (for rollback)

**Considerations:**
- Label availability: Delayed feedback (e.g., fraud labels arrive days later)
- Data volume: Incremental vs full retraining
- Compute cost: Training on large datasets expensive
- Model drift: Gradual vs sudden performance drops

**Automated vs manual:**
- Automated: Good for stable systems, clear metrics
- Manual approval: High-stakes decisions, new model architectures
- Hybrid: Auto-retrain, manual approval for deployment

**Model registry:**
- MLflow, Weights & Biases, AWS SageMaker Model Registry
- Store: Model artifacts, metadata, metrics, lineage
- Stages: Development, Staging, Production, Archived
- Version control: Semantic versioning (v1.0.0, v1.1.0)

**Use ml-docs to fetch MLflow, DVC documentation.**

## Best Practices

- **Version everything:** Code (git), data (DVC), models (registry), infrastructure (IaC)
- **Test thoroughly:** Unit tests, integration tests, load tests, shadow tests
- **Monitor continuously:** Infrastructure + model + business metrics
- **Automate pipelines:** CI/CD for code, automated retraining for models
- **Gradual rollouts:** Canary → A/B test → full rollout (not big bang)
- **Have rollback plan:** One-click rollback to previous version, test rollback procedure
- **Document everything:** Runbooks, architecture diagrams, incident reports
- **Security first:** Authentication (API keys, OAuth), authorization (RBAC), encryption (TLS, at rest)
- **Cost awareness:** Track cost per prediction, optimize compute usage (see infra-cost skill)
- **Incident response:** Clear procedures, on-call rotation, blameless postmortems

## Examples

### Example 1: REST API Deployment with FastAPI

**User Request:** "Deploy my trained scikit-learn model as a REST API that can handle 100 requests/second."

**Approach:**
1. **Create FastAPI application:**
   - Load model at startup (singleton pattern)
   - Define request/response schemas with Pydantic
   - Add health check endpoint
   - Add prediction endpoint with input validation
2. **Dockerize:**
   - Base image: python:3.9-slim
   - Install dependencies: fastapi, uvicorn, scikit-learn
   - Copy model file and app code
   - Expose port 8000
   - Multi-stage build for smaller image
3. **Deploy to Kubernetes:**
   - Create Deployment with 3 replicas (for 100 QPS, assume 30 QPS per pod)
   - Add Service for load balancing
   - Configure HPA to scale 2-10 replicas based on CPU
   - Add resource limits (1 CPU, 2GB RAM per pod)
4. **Set up monitoring:**
   - Prometheus scrapes /metrics endpoint
   - Grafana dashboard for latency, throughput, errors
   - Alerts for latency >100ms, error rate >1%
5. **CI/CD:**
   - GitHub Actions: test → build Docker image → push to registry
   - ArgoCD: Auto-deploy to staging, manual approval for production

**Key code pattern:**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI()

# Load model at startup
model = joblib.load("model.pkl")

class PredictionRequest(BaseModel):
    features: list[float]

class PredictionResponse(BaseModel):
    prediction: float
    confidence: float
    model_version: str

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    try:
        features = np.array(request.features).reshape(1, -1)
        prediction = model.predict(features)[0]
        confidence = model.predict_proba(features).max()
        return PredictionResponse(
            prediction=float(prediction),
            confidence=float(confidence),
            model_version="v1.2.0"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

**Use ml-docs to fetch FastAPI documentation.**

### Example 2: Blue-Green Deployment Strategy

**User Request:** "I need to deploy a new model version without any downtime. How do I do this safely?"

**Approach:**
1. **Setup:**
   - Blue environment: Current production model (v1.0)
   - Green environment: New model (v2.0)
   - Both environments running simultaneously
2. **Deployment steps:**
   - Deploy v2.0 to green environment
   - Run integration tests on green (synthetic traffic)
   - Smoke test: Send small % of real traffic to green (5%)
   - Monitor green metrics closely for 1 hour
   - If stable: Switch load balancer to route all traffic to green
   - Keep blue running for 24 hours (for quick rollback)
   - If no issues: Decommission blue
3. **Rollback procedure:**
   - If green has issues: Switch load balancer back to blue (instant)
   - No data loss, no user impact
4. **Infrastructure:**
   - Kubernetes Services for blue and green
   - Ingress controller routes traffic based on label
   - Switch by updating Ingress to point to different Service

**Benefits:**
- Zero downtime
- Instant rollback
- Full testing before switch

**Drawbacks:**
- 2x resources during deployment
- Need to manage two environments

**Alternative: Canary deployment** (gradual rollout 5% → 25% → 50% → 100%)

### Example 3: Production Monitoring and Incident Response

**User Request:** "Our model API is returning errors. Help me debug and fix it."

**Approach:**
1. **Detect issue:**
   - Alert triggered: Error rate 15% (threshold: 1%)
   - Dashboard shows spike starting 2 hours ago
2. **Triage:**
   - Check logs: Filter by error status (500)
   - Error message: "ValueError: Input shape mismatch"
   - Check recent changes: New app version deployed 2 hours ago
3. **Root cause:**
   - New version expects 10 features, production data has 9 features
   - Code change added new feature but preprocessing pipeline not updated
4. **Immediate mitigation:**
   - Rollback to previous version (blue-green deployment makes this instant)
   - Error rate drops to 0% immediately
   - Service restored
5. **Investigation:**
   - Review PR that introduced bug: Missing data pipeline update
   - Why did tests not catch this? Integration tests used old test data
6. **Fix:**
   - Update data pipeline to compute new feature
   - Update integration tests with production-like data
   - Re-deploy new version with proper testing
   - Monitor for 24 hours before full rollout
7. **Postmortem:**
   - Document incident: timeline, root cause, impact
   - Action items: Add schema validation test, update CI/CD to check feature consistency
   - Blameless culture: Focus on process improvement

**Incident response checklist:**
- Detect (monitoring alerts)
- Triage (assess severity, impact)
- Mitigate (rollback, reroute, fallback)
- Investigate (logs, metrics, recent changes)
- Fix (code change, retrain, config update)
- Deploy fix (with testing)
- Postmortem (document, improve process)

**Use ml-docs to fetch monitoring and logging tools documentation.**

## Notes

- **Training vs serving skew:** Most common production issue. Ensure features computed identically in training and serving
- **Model registry is critical:** Track which model version is in production, enable rollback, audit trail
- **Monitoring is not optional:** Silent failures are worse than loud failures. Monitor everything
- **Start simple:** Don't over-engineer. REST API + Docker + basic monitoring is often sufficient
- **Gradual rollouts:** Never deploy to 100% traffic immediately. Canary → A/B test → full rollout
- **Testing in production:** Shadow mode, canary analysis, feature flags for safe experimentation
- **Incident response:** Have runbooks, practice rollback, maintain on-call rotation
- **Security:** Never expose models without authentication, encrypt data in transit and at rest
- **Cost optimization:** See infra-cost skill for detailed strategies (right-sizing, spot instances, caching)
- **Compliance:** GDPR, CCPA require audit logs, data deletion, explainability (see safety-governance skill)
- **Use ml-docs skill:** Fetch Docker, Kubernetes, FastAPI, MLflow documentation for implementation details
- **Integration with other skills:** Receives models from classical-ml, deep-learning, llm-agent. Uses evaluation skill for validation. Coordinates with infra-cost for optimization and safety-governance for compliance