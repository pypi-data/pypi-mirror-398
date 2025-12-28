# Optimus: Semantic–Harmfulness-Based Jailbreak Scoring

## Overview

This repository provides an implementation of **Optimus**, a continuous metric for evaluating jailbreak prompts in large language models. The metric jointly considers **semantic similarity** to a harmful target intent and the **estimated harmfulness** of the prompt content.

Unlike binary jailbreak success metrics such as **Attack Success Rate (ASR)**, Optimus produces a real-valued score in the range **[0, 1]**. This enables finer-grained evaluation by penalizing trivial paraphrases, benign rewrites, and low-risk prompts, while highlighting prompts that are both semantically aligned with harmful intent and likely to induce unsafe behavior.

The core implementation is provided through the `JBScoreCalculator` class.

---

## Key Features

- Semantic similarity computation using **Sentence-BERT** embeddings  
- Harmfulness estimation using an **NLI-style sequence classification model**  
- Continuous jailbreak scoring metric (**Optimus**)  
- Compatible with **CPU and GPU** execution via PyTorch  
- Modular design enabling replacement of encoders or classifiers  

---

## Dependencies

The following libraries are required:

- Python **3.9 or higher**
- PyTorch
- HuggingFace Transformers
- Sentence-Transformers
- NumPy

### Installation

```bash
pip install torch transformers sentence-transformers numpy
