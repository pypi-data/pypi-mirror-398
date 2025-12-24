---
name: ml-docs
description: Use this skill for requests related to machine learning frameworks (scikit-learn, TensorFlow, PyTorch, LangGraph), data science libraries (pandas, NumPy), and visualization tools (Matplotlib) to fetch relevant documentation and provide accurate, up-to-date guidance.
---

# ml-docs

## Overview

This skill explains how to access documentation for popular machine learning frameworks and data science libraries to help answer questions and guide implementation. Supported frameworks and libraries include:
- **pandas**: Data manipulation and analysis library
- **NumPy**: Fundamental package for numerical computing
- **Matplotlib**: Comprehensive library for creating visualizations
- **scikit-learn**: Traditional ML algorithms and tools
- **TensorFlow**: Deep learning framework by Google
- **PyTorch**: Deep learning framework by Meta
- **LangGraph**: Framework for building stateful, multi-actor applications with LLMs

## Instructions

### 1. Identify the Relevant Framework or Library

Based on the user's question, determine which framework(s) or library(ies) are most relevant:
- **scikit-learn**: classical ML (classification, regression, clustering, preprocessing)
- **TensorFlow**: deep learning, neural networks, Keras API
- **PyTorch**: deep learning, neural networks, custom architectures
- **LangGraph**: LLM agents, workflows, state management
- **pandas**: data loading, cleaning, transformation, analysis (DataFrames, Series)
- **NumPy**: arrays, mathematical operations, linear algebra, statistics
- **Matplotlib**: plotting, charts, graphs, data visualization

### 2. Fetch the Documentation Index

Use the fetch_url tool to read the appropriate documentation index:

- **scikit-learn**: https://ml-docs.pages.dev/sklearn_llms.txt
- **TensorFlow**: https://ml-docs.pages.dev/tensorflow_llms.txt
- **PyTorch**: https://ml-docs.pages.dev/pytorch_llms.txt
- **LangGraph**: https://docs.langchain.com/llms.txt
- **pandas**: https://ml-docs.pages.dev/pandas_llms.txt
- **NumPy**: https://ml-docs.pages.dev/numpy_llms.txt
- **Matplotlib**: https://ml-docs.pages.dev/matplotlib_llms.txt

Each index provides a structured list of all available documentation with descriptions.

### 3. Select Relevant Documentation

Based on the question, identify 2-4 most relevant documentation URLs from the index. Prioritize:
- Specific how-to guides for implementation questions
- Core concept pages for understanding questions
- Tutorials for end-to-end examples
- API reference docs for detailed function/class information
- Best practices and common patterns

### 4. Fetch Selected Documentation

Use the fetch_url tool to read the selected documentation URLs from the identified framework(s) or library(ies).

### 5. Provide Accurate Guidance

After reading the documentation, complete the user's request with:
- Accurate code examples following official patterns
- Clear explanations of concepts
- Links to relevant documentation sections
- Best practices and common pitfalls to avoid
- Cross-framework/library comparisons when relevant

## Notes

- If the question spans multiple frameworks or libraries (e.g., "pandas with scikit-learn", "NumPy arrays in PyTorch"), fetch documentation from all relevant sources
- Always cite the specific documentation sources used
- Prioritize the most recent and framework-specific approaches
- For version-specific questions, note if the documentation may vary by version
- Data science workflows often combine multiple libraries (pandas for data prep, NumPy for computation, Matplotlib for visualization, scikit-learn/TensorFlow/PyTorch for modeling)