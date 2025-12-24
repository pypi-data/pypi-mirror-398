---
name: deep-learning
description: Design, train, and optimize neural networks for computer vision, NLP, time series, and multi-modal applications
---

# Deep Learning Skill

## Description

This skill covers deep learning with neural networks for unstructured data (images, text, audio, video) and complex patterns. It includes architecture selection, training strategies, optimization techniques, transfer learning, and production deployment. Use this skill when working with large datasets, complex patterns, or when classical ML approaches are insufficient. The skill emphasizes practical implementation, efficient training, and production-ready models.

Deep learning excels at feature learning from raw data (pixels, tokens, waveforms) and scales well with data. It's essential for computer vision, NLP, speech, and multi-modal tasks but requires more data, compute, and expertise than classical ML.

## When to Use

- When working with images, video, or computer vision tasks
- When processing natural language (classification, generation, embeddings)
- When handling sequential data (time series, audio, speech)
- When building multi-modal systems (vision + text, audio + text)
- When classical ML underperforms and you have sufficient data (>10K samples)
- When user requests CNNs, RNNs, Transformers, or specific architectures
- When fine-tuning pretrained models (BERT, ResNet, GPT)
- When implementing custom neural network architectures
- When optimizing model training (distributed, mixed precision, hyperparameters)
- When converting models for production inference (ONNX, TensorRT, quantization)

## How to Use

### Step 1: Select Appropriate Architecture

**Choose architecture based on data type and task:**

**Computer Vision:**
- Classification: ResNet, EfficientNet, Vision Transformer (ViT), ConvNeXt
- Object Detection: YOLO, Faster R-CNN, DETR
- Segmentation: U-Net, Mask R-CNN, DeepLab, Segment Anything
- Use pretrained models from timm library (PyTorch) or TensorFlow Hub

**NLP/Text:**
- Encoding: BERT, RoBERTa, DeBERTa (sentence/document classification)
- Generation: GPT, T5 (text generation, summarization)
- Embeddings: sentence-transformers for semantic search
- For simple tasks, start with lightweight models (DistilBERT, MobileBERT)

**Time Series:**
- LSTM, GRU for sequential patterns
- 1D CNNs for local patterns
- Transformer models for long-range dependencies
- Temporal Fusion Transformer for forecasting

**Multi-modal:**
- CLIP for vision-text alignment
- Flamingo, BLIP for image captioning
- Cross-attention for fusion

**Prefer transfer learning:** Start with pretrained weights whenever possible. Training from scratch requires massive data and compute.

**Use ml-docs skill to fetch PyTorch, TensorFlow, Hugging Face documentation for specific implementations.**

### Step 2: Prepare Data and Setup Training

**Data preparation:**
- Normalization: Use ImageNet stats for vision (if transfer learning), dataset-specific otherwise
- Augmentation: Geometric transforms (flip, rotate, crop), color jittering, mixup, cutout
- Batching: As large as GPU memory allows (use gradient accumulation if needed)
- Splits: Train/val/test with stratification, time-aware for temporal data

**Training setup:**
- Initialize model: Load pretrained weights or use proper initialization (He, Xavier)
- Loss function: CrossEntropy (classification), MSE/MAE (regression), custom for special tasks
- Optimizer: AdamW (default), SGD+momentum (sometimes better convergence)
- Learning rate: 1e-3 from scratch, 1e-4 to 1e-5 for fine-tuning
- Scheduler: Cosine annealing, OneCycleLR, ReduceLROnPlateau
- Mixed precision: Use fp16/bf16 for 2x speedup and memory savings

**Set random seeds for reproducibility.**

### Step 3: Train and Monitor

**Training loop:**
- Start with small experiment: Overfit single batch to verify model can learn
- Monitor: Train/val loss, metrics, learning rate, gradient norms
- Checkpoint: Save best model based on val metric, periodic backups
- Early stopping: Stop if val loss doesn't improve for N epochs
- Gradient clipping: Prevent exploding gradients (clip_grad_norm_)

**Debugging checklist:**
- Loss not decreasing? → Check learning rate (too low/high), data loading, loss function
- Loss = NaN? → Exploding gradients (lower LR, gradient clipping)
- Overfitting? → Regularization (dropout, weight decay), data augmentation, early stopping
- Slow training? → Use mixed precision, larger batch size, profile bottlenecks

**Use TensorBoard or Weights & Biases for experiment tracking.**

### Step 4: Optimize and Evaluate

**Hyperparameter tuning:**
- Start with reasonable defaults, then tune systematically
- Key hyperparameters: learning rate, batch size, dropout, weight decay
- Use Bayesian optimization (Optuna) or random search (not grid search)
- Run for sufficient epochs to assess convergence

**Model optimization:**
- Ensemble: Combine multiple models if performance gain justifies complexity
- Quantization: Convert fp32 → int8 for 4x speedup in inference
- Pruning: Remove unimportant weights to reduce model size
- Distillation: Train smaller model to mimic larger model

**Evaluation:**
- Test on holdout set with appropriate metrics
- Error analysis: Which examples does model fail on? Why?
- Visualize: Attention maps, activation patterns, embeddings (t-SNE/UMAP)
- Interpretability: Grad-CAM, SHAP for feature attribution

### Step 5: Prepare for Production

**Model export:**
- Serialize: Save weights and architecture (PyTorch: .pt, TensorFlow: SavedModel)
- Convert to ONNX: Cross-platform format for deployment
- Optimize: TensorRT (NVIDIA), OpenVINO (Intel) for hardware-specific acceleration

**Inference optimization:**
- Batch predictions when possible (higher throughput)
- Use smaller models if latency critical (MobileNet, DistilBERT)
- Quantization and pruning for edge deployment
- Cache common predictions

**Integration with mlops-production skill for deployment pipelines.**

## Best Practices

- **Transfer learning first:** Pretrained models > training from scratch (10-100x less data needed)
- **Start simple:** Baseline model with default hyperparameters before complex architectures
- **Validate pipeline:** Overfit single batch before full training (catches bugs early)
- **Use mixed precision:** Free 2x speedup and memory savings with minimal code changes
- **Monitor everything:** Loss curves, gradient norms, learning rate, activation statistics
- **Save checkpoints:** Best model + periodic backups (resume training, rollback if needed)
- **Test incrementally:** Add complexity gradually, validate each change improves performance
- **Augment aggressively:** Data augmentation often more valuable than architecture tweaks
- **Profile bottlenecks:** Identify slow operations (data loading, forward pass, backward pass)
- **Version everything:** Code, data, model weights, hyperparameters for reproducibility

## Examples

### Example 1: Image Classification with Transfer Learning

**User Request:** "Build an image classifier to detect defects in manufactured parts. I have 5,000 labeled images across 10 defect categories."

**Approach:**
1. **Architecture selection:** Use pretrained ResNet50 or EfficientNet-B0 (good balance of accuracy and speed)
2. **Data preparation:**
   - Resize images to 224x224
   - Normalize with ImageNet stats (pretrained model expects this)
   - Augmentation: random flip, rotate, color jitter, cutout
   - Split: 70% train, 15% val, 15% test (stratified by class)
3. **Fine-tuning strategy:**
   - Freeze backbone layers, train only classification head first
   - Unfreeze backbone gradually and fine-tune with low learning rate
   - Use discriminative learning rates: 1e-5 for backbone, 1e-3 for head
4. **Training:**
   - Loss: CrossEntropyLoss with label smoothing (reduces overfitting)
   - Optimizer: AdamW with weight decay 0.01
   - Scheduler: Cosine annealing over 30 epochs
   - Mixed precision for faster training
5. **Evaluation:**
   - Confusion matrix to identify difficult pairs
   - Per-class precision/recall
   - Visualize misclassified examples

**Key code pattern:**
```python
import torch
import timm  # PyTorch Image Models

# Load pretrained model
model = timm.create_model('resnet50', pretrained=True, num_classes=10)

# Freeze backbone
for param in model.parameters():
    param.requires_grad = False
model.fc.requires_grad = True  # Only train classification head

# Later: unfreeze all and use low learning rate
# optimizer = torch.optim.AdamW([
#     {'params': model.conv1.parameters(), 'lr': 1e-5},
#     {'params': model.fc.parameters(), 'lr': 1e-3}
# ])
```

**Use ml-docs to fetch timm, PyTorch documentation for details.**

### Example 2: Text Classification with BERT

**User Request:** "Classify customer support tickets into 5 categories. We have 20,000 labeled tickets."

**Approach:**
1. **Architecture selection:** Use pretrained BERT-base (good balance) or DistilBERT (faster, slightly lower accuracy)
2. **Data preparation:**
   - Tokenize text with BERT tokenizer (handles subwords, special tokens)
   - Max length 512 tokens, pad/truncate as needed
   - Create DataLoader with batching
3. **Fine-tuning:**
   - Add classification head on top of [CLS] token
   - Use HuggingFace Transformers library
   - Learning rate: 2e-5 (common for BERT fine-tuning)
   - Epochs: 3-5 (BERT fine-tunes quickly)
4. **Training:**
   - Monitor val accuracy per epoch
   - Use class weights if imbalanced
   - Gradient accumulation if GPU memory limited
5. **Evaluation:**
   - F1 score per category
   - Confusion matrix for category overlap patterns
   - Analyze failure cases: ambiguous tickets, rare categories

**Key code pattern:**
```python
from transformers import BertForSequenceClassification, BertTokenizer, Trainer

# Load pretrained BERT
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=5)
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

# Tokenize
def tokenize_function(examples):
    return tokenizer(examples['text'], padding='max_length', truncation=True, max_length=512)

# Use Trainer API for training
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset
)
trainer.train()
```

**Use ml-docs to fetch Hugging Face Transformers documentation.**

### Example 3: Time Series Forecasting with LSTM

**User Request:** "Predict next 7 days of sales based on past 30 days. We have 2 years of daily sales data."

**Approach:**
1. **Architecture selection:** LSTM or GRU (handle sequential dependencies), or try Temporal Fusion Transformer
2. **Data preparation:**
   - Create sliding windows: [day 1-30] → [day 31-37]
   - Normalize features (MinMaxScaler or StandardScaler)
   - Include additional features: day of week, holidays, promotions
   - Time-series split: train on first 70%, validate on next 15%, test on last 15%
3. **Model design:**
   - Input: 30 time steps, N features
   - LSTM layers: 2 layers with 64-128 hidden units
   - Output: 7 time steps (multi-step forecasting)
   - Dropout between layers for regularization
4. **Training:**
   - Loss: MSE or MAE (more robust to outliers)
   - Optimizer: Adam with learning rate 0.001
   - Early stopping on validation loss
5. **Evaluation:**
   - RMSE, MAE, MAPE on test set
   - Plot predictions vs actuals
   - Check residuals for patterns (should be random)

**Key code pattern:**
```python
import torch.nn as nn

class SalesLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2, output_steps=7):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, output_steps)
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        # Use last time step output
        predictions = self.fc(lstm_out[:, -1, :])
        return predictions

# Input shape: (batch_size, 30, num_features)
# Output shape: (batch_size, 7)
```

## Notes

- **When to use deep learning vs classical ML:** Deep learning wins for images, text, audio, video, and large datasets (>100K samples). Classical ML often better for small structured data (<10K rows)
- **GPU requirements:** Training deep models requires GPU (NVIDIA preferred). Use Google Colab, AWS/GCP for cloud GPUs
- **Transfer learning is critical:** Pretrained models reduce training time 10-100x and require far less data
- **Debugging is iterative:** Start simple (overfit single batch), add complexity gradually, test each change
- **Distributed training:** For very large models, use PyTorch DDP, DeepSpeed, or PyTorch Lightning for multi-GPU training
- **Common pitfalls:** Forgetting to set model.eval() at test time, data leakage in normalization, improper augmentation
- **Framework choice:** PyTorch (research-friendly, dynamic), TensorFlow/Keras (production focus, static graphs), JAX (functional, research)
- **Use ml-docs skill:** Fetch PyTorch, TensorFlow, Hugging Face documentation for specific implementations
- **Integration with other skills:** Receives data from data-engineering, uses evaluation skill for metrics, feeds to mlops-production for deployment