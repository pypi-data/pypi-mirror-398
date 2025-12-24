---
name: infra-cost
description: Optimize infrastructure costs, select cost-effective resources, and implement FinOps practices for ML systems
---

# Infrastructure & Cost Optimization Skill

## Description

This skill covers infrastructure selection, cost analysis, and optimization strategies for ML systems. It includes cloud provider comparison, instance sizing, cost estimation, monitoring, and FinOps best practices. Use this skill when planning ML infrastructure, optimizing existing deployments, analyzing costs, or implementing cost-saving measures. Understanding cost implications early prevents budget overruns and enables sustainable ML operations.

ML infrastructure can be expensive: GPU training, large-scale inference, data storage, and network transfer all add up quickly. This skill emphasizes cost-aware design, proactive monitoring, and continuous optimization to maximize value while minimizing waste.

## When to Use

- When estimating costs for a new ML project
- When selecting cloud providers and instance types
- When optimizing training costs (GPU utilization, spot instances)
- When reducing inference costs (model optimization, caching)
- When analyzing current spending and identifying waste
- When implementing cost monitoring and budgeting
- When choosing between cloud providers or regions
- When optimizing data storage and transfer costs
- When implementing FinOps practices for ML teams
- When negotiating cloud contracts or reserved instances

## How to Use

### Step 1: Estimate Costs Upfront

**Break down cost components:**

**Training Costs:**
- Compute: GPU/TPU hours × hourly rate
- Storage: Datasets, checkpoints, artifacts
- Network: Data transfer (ingress usually free, egress expensive)
- Development: Notebooks, experimentation environments

**Serving Costs:**
- Compute: API servers, inference instances (CPU/GPU)
- Storage: Model weights, feature cache, logs
- Network: Request/response data transfer
- Database: Feature lookups, prediction storage

**Data Costs:**
- Storage: Raw data, processed features, backups (S3, BigQuery)
- Compute: ETL pipelines, transformations (Spark, Glue)
- Query costs: Data warehouse queries
- Transfer: Moving data between regions/services

**Overhead:**
- Monitoring tools: DataDog, Prometheus, etc.
- Model registry: MLflow, W&B storage
- CI/CD infrastructure: Build runners
- Development environments: Notebooks, IDEs

**Create cost estimate template:**
```
Training (one-time):
- 8x A100 80GB @ $32.77/hr × 100 hrs = $26,216
- Storage: 1TB dataset @ $23/month = $23
Total training: ~$26,239

Serving (monthly):
- 4x T4 GPU @ $1.35/hr × 24 × 30 = $3,888
- Storage: 10GB models @ $2.30 = $2.30
- Network: 1TB egress @ $90 = $90
Total serving: ~$3,980/month

Annual: $26,239 + ($3,980 × 12) = $74,000
Cost per 1K predictions: ~$0.12
```

**Use problem-framing skill insights for traffic estimates and requirements.**

### Step 2: Select Cost-Effective Infrastructure

**Cloud provider comparison:**

**AWS:**
- EC2: p4d, p3, g4dn, g5 instances for GPU
- Spot: Up to 90% discount, interruptible
- Reserved: 30-60% discount, 1-3 year commitment
- S3: ~$0.023/GB/month, cheap for large datasets
- Lambda: Serverless, cold start penalty

**GCP:**
- Compute Engine: A2 (A100), T4, V100 instances
- Preemptible: Up to 80% discount
- Committed use: Automatic sustained use discounts
- Cloud Storage: Similar to S3
- TPUs: Best price/performance for large models

**Azure:**
- N-series VMs for GPU
- Spot instances: Similar discounts
- Blob Storage: Comparable to S3/GCS

**Cost comparison (example for GPU training):**
- AWS p3.2xlarge (V100): ~$3.06/hr on-demand, ~$0.92/hr spot
- GCP n1-highmem-8 + V100: ~$2.48/hr on-demand, ~$0.74/hr preemptible
- Always compare per region, prices vary

**Instance selection:**
- Small models (<1B params): T4, A10G ($1-2/hr)
- Medium models (1-10B): A100 40GB, V100 32GB ($3-10/hr)
- Large models (>10B): A100 80GB, H100, multi-GPU ($15-50/hr)
- Inference: CPU often sufficient for classical ML, GPU for DL
- Batch jobs: Spot/preemptible instances (70-90% discount)
- Production serving: Reserved or on-demand (reliability)

**Right-sizing:**
- Start small, measure utilization, scale up as needed
- Monitor CPU, GPU, memory usage (aim for 70-85% utilization)
- Don't over-provision "just in case"

**Use ml-docs to fetch cloud provider pricing documentation.**

### Step 3: Optimize Training Costs

**Use spot/preemptible instances:**
- 70-90% cheaper than on-demand
- Can be interrupted (cloud needs capacity elsewhere)
- Best for: Training, experimentation, batch jobs
- Implementation: Frequent checkpointing (save every N minutes), automatic retry on interruption
- Tools: AWS Spot Fleet, GCP Preemptible VMs, Azure Spot

**Efficient training:**
- Mixed precision (FP16/BF16): 2x speedup, same cost per hour but finish faster
- Gradient accumulation: Simulate large batch on small GPU
- Efficient architectures: MobileNet, EfficientNet, DistilBERT (train faster)
- Transfer learning: Fine-tune instead of training from scratch (10-100x less compute)
- Early stopping: Don't overtrain, stop when validation loss plateaus
- Distributed training: Reduce wall-clock time (but more expensive per hour)

**Hyperparameter optimization:**
- Bayesian optimization (Optuna) > Grid search (more efficient)
- Successive halving: Stop bad runs early
- Parallel trials on spot instances

**Development efficiency:**
- Prototype on small datasets/models
- Use free tiers: Google Colab, Kaggle notebooks (limited GPU hours)
- Shut down idle notebooks/VMs (auto-shutdown scripts)

**Cost per experiment:**
- Track cost per training run (GPU hours × rate)
- Identify expensive experiments, optimize or eliminate

### Step 4: Optimize Inference Costs

**Model optimization:**
- Quantization: FP32 → INT8 (4x smaller, faster, no GPU needed)
- Pruning: Remove unimportant weights (smaller model)
- Distillation: Train small model from large model (faster inference)
- ONNX Runtime: Cross-platform optimization
- TensorRT (NVIDIA), OpenVINO (Intel): Hardware-specific acceleration

**Batching:**
- Accumulate requests, process together (higher throughput)
- Trade-off: Latency vs throughput
- Dynamic batching: Automatically batch requests

**Caching:**
- Result cache: Store (input_hash → prediction) in Redis
- Feature cache: Precompute expensive features
- Model cache: Keep hot models in memory
- Cache hit rate: Aim for >50% for cost savings

**Instance selection:**
- CPU: Sufficient for classical ML, small models, low QPS
- GPU (T4, A10G): For deep learning, real-time requirements
- Serverless (Lambda): For sporadic traffic (<10 req/min)
- Batch: For non-real-time predictions, use spot instances

**Auto-scaling:**
- Scale down during low traffic (nights, weekends)
- Scale up during peak hours
- Kubernetes HPA or cloud auto-scaling
- Save 40-60% on serving costs

**Multi-tenancy:**
- Serve multiple models on same instance (if resource utilization low)
- Model multiplexing to maximize GPU utilization

**Use deep-learning and mlops-production skills for model optimization techniques.**

### Step 5: Monitor and Optimize Continuously

**Cost monitoring:**
- Tag all resources: project, team, environment (dev/staging/prod)
- Cost allocation reports: Per project, per team
- Daily/weekly cost dashboards: Track trends
- Budget alerts: 50%, 80%, 100% thresholds
- Anomaly detection: Alert on unexpected cost spikes

**Key metrics:**
- Cost per training run
- Cost per 1K predictions
- Cost per user/transaction
- Infrastructure utilization (CPU, GPU, storage)
- Cost efficiency: performance / cost

**Regular reviews:**
- Weekly: Review top 10 cost items
- Monthly: Cost optimization opportunities
- Quarterly: Right-size instances, evaluate reserved capacity

**Identify waste:**
- Idle resources: VMs running 24/7 but used 8 hrs/day
- Over-provisioned instances: Low utilization
- Forgotten experiments: Old training jobs still running
- Unused storage: Old datasets, checkpoints
- Redundant backups: Excessive retention

**Optimization actions:**
- Auto-shutdown: Stop idle VMs after 2 hours
- Lifecycle policies: Move old data to cheaper storage tiers
- Cleanup: Delete unused artifacts, stopped instances
- Right-size: Downgrade over-provisioned instances
- Spot instances: Convert batch jobs to spot

**Tools:**
- AWS Cost Explorer, GCP Cost Management, Azure Cost Management
- CloudHealth, CloudCheckr (multi-cloud)
- Custom dashboards: Grafana, Tableau
- Infracost: Cost estimates for infrastructure-as-code

## Best Practices

- **Estimate upfront:** Understand cost implications before building
- **Tag everything:** Enforce tagging for cost allocation (project, owner, environment)
- **Use spot for training:** 70-90% savings for interruptible workloads
- **Right-size instances:** Match resources to actual needs, don't over-provision
- **Monitor continuously:** Track costs daily, alert on anomalies
- **Optimize models:** Quantization, pruning, distillation for inference
- **Cache aggressively:** Store frequent predictions, features
- **Auto-scale:** Scale down during low traffic periods
- **Clean up waste:** Delete unused resources, old experiments
- **Reserved instances:** For stable production workloads (30-60% discount)
- **Educate team:** Cost awareness is everyone's responsibility

## Examples

### Example 1: Training Cost Optimization

**User Request:** "Training our model costs $10K per run and takes 48 hours. How can we reduce costs?"

**Approach:**
1. **Current setup analysis:**
   - Using 8x A100 80GB on-demand @ $32.77/hr
   - Cost: $32.77 × 8 × 48 = $12,583
   - GPU utilization: Check nvidia-smi logs
   - Finding: GPU utilization only 60% (inefficient)
2. **Optimization strategies:**
   - **Switch to spot instances:** 8x A100 spot @ $9.83/hr
   - Savings: $9.83 × 8 × 48 = $3,774 (70% cheaper)
   - Implementation: Checkpointing every 15 mins, auto-retry on interruption
3. **Mixed precision training:**
   - Enable FP16: 2x speedup → 24 hours instead of 48
   - New cost: $9.83 × 8 × 24 = $1,887 (85% cheaper than original)
4. **Batch size tuning:**
   - Increase batch size to maximize GPU memory
   - Improved utilization: 60% → 85%
   - Further speedup: 24 → 20 hours
   - Final cost: $9.83 × 8 × 20 = $1,573 (87.5% cheaper)
5. **Additional optimizations:**
   - Gradient accumulation: Simulate large batch on fewer GPUs
   - Test with 4x A100 instead of 8x if loss convergence similar
   - Early stopping: Stop at 15 hours if validation loss plateaus

**Total savings: $12,583 → $1,573 (87.5% reduction)**

**Key implementation:**
```python
# Enable mixed precision
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()

# Checkpointing for spot instances
checkpoint_interval = 15 * 60  # 15 minutes in seconds
if time.time() - last_checkpoint > checkpoint_interval:
    torch.save(model.state_dict(), f"checkpoint_{epoch}.pt")
```

### Example 2: Inference Cost Optimization

**User Request:** "Our model serving costs $5K/month for 10M predictions. Can we reduce this?"

**Approach:**
1. **Current setup:**
   - 4x T4 GPU instances @ $1.35/hr × 24 × 30 = $3,888/month
   - Storage, network: ~$1,112/month
   - Cost per 1K predictions: $0.50
   - Traffic pattern: Peak 9am-6pm weekdays, low nights/weekends
2. **Implement caching:**
   - Analysis: 40% of queries are repeated
   - Add Redis cache for predictions (TTL: 1 hour)
   - Cache hits: 40% × 10M = 4M predictions cached
   - Reduced compute: 6M predictions need inference
   - Savings: 40% reduction in compute cost
3. **Auto-scaling:**
   - Peak hours (8 hrs/day, 5 days/week): 4 instances
   - Off-peak: 1 instance (sufficient for low traffic)
   - Average: (4 × 40 + 1 × 128) / 168 = 1.71 instances
   - New cost: $1.35 × 1.71 × 24 × 30 = $1,666 (57% cheaper)
4. **Model quantization:**
   - Convert FP32 → INT8 (4x smaller, faster)
   - Can serve on CPU instead of GPU
   - Switch to c5.2xlarge (CPU) @ $0.34/hr
   - New cost: $0.34 × 1.71 × 24 × 30 = $419 (89% cheaper)
5. **Batching:**
   - Batch size: 32 (accumulate for 50ms)
   - Throughput increase: 3x
   - Reduce instances: 1.71 → 0.57 (round up to 1 at all times)
   - Further savings possible

**Total savings: $3,888 → ~$500 (87% reduction)**
**New cost per 1K predictions: $0.05 (90% cheaper)**

**Key implementation:**
```python
# Caching layer
import redis
cache = redis.Redis()

def get_prediction(features):
    key = hash(tuple(features))
    cached = cache.get(key)
    if cached:
        return json.loads(cached)
    
    prediction = model.predict(features)
    cache.setex(key, 3600, json.dumps(prediction))  # 1 hour TTL
    return prediction

# Auto-scaling (Kubernetes HPA)
# Scale based on CPU: target 70% utilization
# Min replicas: 1, Max replicas: 4
```

### Example 3: Storage Cost Optimization

**User Request:** "We're spending $10K/month on S3 storage for ML data. Most of it is old experiment data we rarely access."

**Approach:**
1. **Analyze storage:**
   - Total: 400TB stored in S3
   - Standard storage: $0.023/GB/month
   - Cost: 400,000 GB × $0.023 = $9,200/month
   - Usage analysis: 80% of data is >90 days old, rarely accessed
2. **Implement lifecycle policies:**
   - Active data (<30 days): S3 Standard ($0.023/GB)
   - Warm data (30-90 days): S3 Infrequent Access ($0.0125/GB)
   - Cold data (>90 days): S3 Glacier ($0.004/GB)
   - Archive data (>1 year): S3 Glacier Deep Archive ($0.00099/GB)
3. **New cost calculation:**
   - Active (20% = 80TB): 80,000 × $0.023 = $1,840
   - Warm (10% = 40TB): 40,000 × $0.0125 = $500
   - Cold (60% = 240TB): 240,000 × $0.004 = $960
   - Archive (10% = 40TB): 40,000 × $0.00099 = $40
   - Total: $3,340/month (64% savings)
4. **Additional cleanup:**
   - Identify and delete failed experiments: 50TB
   - Deduplicate checkpoints: Keep only best model per experiment: 30TB
   - Compress Parquet files: 10-20% size reduction
   - New storage: 320TB → Cost: ~$2,500/month (73% savings)

**Total savings: $9,200 → $2,500 (73% reduction)**

**Implementation:**
```bash
# AWS S3 lifecycle policy
aws s3api put-bucket-lifecycle-configuration --bucket ml-data --lifecycle-configuration '{
  "Rules": [
    {
      "Id": "Move to IA after 30 days",
      "Filter": {"Prefix": "experiments/"},
      "Status": "Enabled",
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"},
        {"Days": 90, "StorageClass": "GLACIER"},
        {"Days": 365, "StorageClass": "DEEP_ARCHIVE"}
      ]
    },
    {
      "Id": "Delete old checkpoints",
      "Filter": {"Prefix": "checkpoints/"},
      "Status": "Enabled",
      "Expiration": {"Days": 30}
    }
  ]
}'
```

## Notes

- **Training vs inference costs:** Training is one-time, inference is ongoing. Optimize inference first for long-term impact
- **Spot instance risks:** Can be interrupted with 2-min warning. Always checkpoint frequently. Not suitable for critical serving
- **Reserved instances:** Only purchase for stable, predictable workloads. Commitment is 1-3 years
- **Data egress:** Most expensive network cost. Keep compute and data in same region. Use private networking (VPC peering)
- **GPU vs CPU:** GPUs expensive ($1-30/hr). Use CPU when possible (classical ML, small models, quantized inference)
- **Multi-cloud complexity:** Avoid unless necessary. Data transfer between clouds is very expensive
- **Cost vs performance trade-off:** Sometimes cheapest option is too slow. Find optimal balance
- **Hidden costs:** Monitoring, logging, data transfer add up. Factor into total cost
- **FinOps culture:** Cost optimization is ongoing, not one-time. Make cost visible to entire team
- **Use ml-docs skill:** Fetch cloud provider pricing and optimization documentation
- **Integration with other skills:** Coordinates with mlops-production for deployment, evaluation for cost-performance trade-offs, safety-governance for cost compliance