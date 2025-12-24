---
name: problem-framing
description: Translate business requirements into ML/AI problems, define success metrics, and scope ML projects effectively
---

# Problem Framing Skill

## Description

This skill helps translate vague business problems into well-defined ML/AI objectives. It guides you through understanding stakeholder needs, classifying problem types (classification, regression, ranking, generation, agents), defining measurable success criteria, assessing feasibility, and creating structured project scopes. Use this skill at the start of any ML/AI project to ensure alignment between business goals and technical implementation.

Problem framing prevents common failures like building the wrong solution, optimizing for incorrect metrics, or underestimating data requirements. It establishes clear acceptance criteria and realistic timelines before any coding begins.

## When to Use

- When user describes a new business problem or initiative that might need ML/AI
- When asked "how would you approach [business problem] with ML?"
- When user is unclear about what type of ML solution they need
- When defining success metrics or KPIs for an ML project
- When assessing whether ML is the right solution vs simpler approaches
- When scoping timelines, data requirements, or feasibility
- When translating domain language into technical specifications
- Before starting any data-engineering, modeling, or deployment work

## How to Use

### Step 1: Gather Context and Clarify Objectives

**Understand the business problem deeply:**
- What specific business problem are we solving? (increase revenue, reduce costs, improve UX)
- Who are the stakeholders and end users?
- What is the current process or baseline solution?
- What are the constraints? (time, budget, regulatory, latency, accuracy requirements)
- What does success look like from a business perspective?
- What are the consequences of errors? (false positives vs false negatives)

**Ask clarifying questions if information is missing. Don't assume.**

### Step 2: Classify the Problem Type

**Determine the appropriate ML paradigm:**
- **Classification:** Predict discrete categories (fraud detection, churn prediction, sentiment analysis)
- **Regression:** Predict continuous values (price forecasting, demand estimation, time series)
- **Clustering:** Group similar items (customer segmentation, anomaly detection)
- **Ranking:** Order items by relevance (search results, recommendations)
- **Generation:** Create new content (text summarization, image generation, code completion)
- **Agent-based:** Multi-step reasoning and tool use (task automation, research assistants)

**Consider whether simpler non-ML solutions could work (rules, heuristics, SQL queries).**

### Step 3: Define Success Metrics

**Establish measurable objectives:**
- **Business metric:** Primary KPI (e.g., "reduce customer churn by 15%", "increase conversion rate by 10%")
- **ML metric:** Technical performance measure aligned with business goal (F1 score, RMSE, NDCG, task success rate)
- **Baseline:** Current performance or naive approach (e.g., "currently 8% churn, random guess would be 50% accuracy")
- **Target:** Acceptable minimum performance for deployment (e.g., "F1 > 0.85", "latency < 100ms")
- **Guardrails:** Secondary metrics to monitor (fairness, latency, cost per prediction)

**Ensure metrics are measurable, achievable, and aligned with business value.**

### Step 4: Assess Feasibility

**Evaluate technical, economic, and organizational viability:**
- **Data availability:** Is training data available? Quality? Quantity? Labels?
- **Technical feasibility:** Can we build this with available tools/compute?
- **Latency requirements:** Real-time (<100ms), near-real-time (<1s), or batch (hours/days)?
- **Budget:** Development cost, infrastructure cost, ongoing maintenance
- **Timeline:** When is this needed? Is the timeline realistic?
- **Team capability:** Do we have the required expertise?
- **Risks:** What could go wrong? Data quality issues? Ethical concerns?

**Identify blockers early and plan mitigation strategies.**

### Step 5: Create Problem Brief

**Document the problem statement:**
- Business problem and objectives
- Problem type and technical approach
- Success metrics (business + ML + baseline + target)
- Data requirements and availability
- Constraints and risks
- Phased approach (MVP → Pilot → Production)
- Open questions requiring further investigation

**Use the Problem Brief Template in examples below.**

## Best Practices

- **Challenge requirements:** The stated problem may not be the real problem. Ask "why" multiple times
- **Start simple:** Prefer simple solutions (rules, SQL) over ML when appropriate. Use simple ML over complex deep learning
- **Define clear metrics:** "Make it better" is not a metric. Quantify success upfront
- **Consider baseline:** What's the current performance? What would a naive approach achieve?
- **Assess feasibility early:** Don't start building if data doesn't exist or budget is insufficient
- **Plan in phases:** MVP (prove feasibility) → Pilot (limited deployment) → Production (full scale)
- **Document assumptions:** Write down what you're assuming about data, users, constraints
- **Align stakeholders:** Get buy-in on metrics and approach before building
- **Think end-to-end:** Consider deployment, monitoring, and maintenance from day one

## Examples

### Example 1: E-commerce Churn Prediction

**User Request:** "Our customers are leaving. Can you build something with AI to stop that?"

**Approach:**
1. **Gather context:** "How do you define churn? (no purchase in 90 days?) What's current churn rate? What actions can you take if we predict churn? (email campaign, discount offer?)"
2. **Classify problem:** Binary classification (churned vs active customer)
3. **Define metrics:** 
   - Business: "Reduce churn rate from 20% to 15% (save $2M annually)"
   - ML: "F1 score > 0.75 (balance precision and recall)"
   - Baseline: "Majority class (predict all active) = 80% accuracy but useless"
4. **Assess feasibility:**
   - Data: "Do we have historical data? Customer demographics, purchase history, engagement metrics?"
   - Labels: "Can we label past churned vs retained customers?"
   - Action: "What will we do with predictions? Targeted retention campaigns?"
   - Timeline: "Need 3 months for MVP (data prep, modeling, evaluation)"
5. **Document:** Create problem brief with acceptance criteria

**Problem Brief:**
```
Business Problem: High customer churn (20%) costing $10M/year
ML Problem: Binary classification (churn risk prediction)
Success: Reduce churn to 15% via targeted retention campaigns
ML Metric: F1 > 0.75, AUC-ROC > 0.85
Data: 2 years customer data (100K customers, 20K churned)
Approach: Logistic Regression baseline → XGBoost → Deployment
Timeline: 3 months (1 month data prep, 1 month modeling, 1 month pilot)
Risks: Data quality issues, low feature predictiveness, campaign effectiveness
```

### Example 2: Document Search System

**User Request:** "We need an AI to help employees find information in our 10,000 internal documents."

**Approach:**
1. **Gather context:** "What types of documents? What are typical search queries? Current solution (keyword search)? Success = employees find answers faster?"
2. **Classify problem:** Ranking problem (retrieve most relevant documents) + possible generation (summarize answers) = RAG system
3. **Define metrics:**
   - Business: "Reduce time-to-answer from 15 minutes to 5 minutes"
   - ML: "NDCG@5 > 0.8 (top 5 results contain answer)"
   - User satisfaction: "80% of searches rated helpful"
   - Baseline: "Current keyword search = 60% success rate"
4. **Assess feasibility:**
   - Data: "10K documents, can we access/process them? Need to chunk and embed"
   - Tech: "Use vector DB (ChromaDB) + embeddings (sentence-transformers) + LLM (Claude/GPT)"
   - Latency: "Can search take 2-3 seconds? Or need <500ms?"
   - Cost: "Embedding storage + LLM API costs = ~$500/month"
5. **Document:** RAG architecture with clear success criteria

**Problem Brief:**
```
Business Problem: Employees waste time searching internal documents
ML Problem: Semantic search + retrieval augmented generation (RAG)
Success: 80% user satisfaction, <5 min to find answers
ML Metric: NDCG@5 > 0.8, answer relevance > 85%
Architecture: Documents → chunks → embeddings → vector DB → retrieve → LLM generate
Data: 10K internal docs (PDFs, Word, Wiki pages)
Timeline: 6 weeks (2 weeks data prep, 2 weeks RAG implementation, 2 weeks evaluation)
Risks: Document quality varies, outdated info, hallucination
```

### Example 3: Wrong Problem - No ML Needed

**User Request:** "Build an ML model to predict if a transaction amount is over $1000."

**Approach:**
1. **Gather context:** "Why do you need a prediction? Can't you just check if amount > 1000?"
2. **Challenge requirement:** "This is a deterministic rule, not a prediction problem. ML adds unnecessary complexity."
3. **Propose alternative:** "Use simple SQL: `SELECT * FROM transactions WHERE amount > 1000`. No ML needed."
4. **Real problem?** "Are you actually trying to detect fraud? Predict future transaction amounts? Those would need ML."

**Key insight: Not every problem needs ML. Use the simplest solution that works.**

## Notes

- **Integration with other skills:** Problem framing feeds into all other skills. After framing, proceed to data-engineering for pipeline design, then classical-ml/deep-learning/llm-agent for implementation
- **Iterative process:** Problem framing isn't one-and-done. Revisit as you learn more during development
- **Beware scope creep:** Stakeholders will ask for more features. Stick to MVP first, then iterate
- **Red flags:** Unclear success criteria, insufficient data, misaligned metrics, unrealistic timelines, ethical concerns
- **Use ml-docs skill:** When uncertain about what's technically possible, fetch relevant documentation to inform feasibility assessment
- **Document everything:** Decisions, assumptions, trade-offs. Future you (and teammates) will thank you