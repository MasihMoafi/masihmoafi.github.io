---
layout: post
title: "Double-Tower Gated Transformers for Forex Signals"
meta: "Applying a dual-tower transformer architecture to high-frequency trading data."
---

Predicting financial markets is notoriously difficult because price action is extremely noisy and non-stationary. In my recent experiments on 1-minute EUR/USD forex data, I shifted from standard Gradient Boosting models (like LightGBM) to a custom **Gated Transformer Network (GTN)**.

### The Double-Tower Architecture
The core innovation in this model is its dual-tower structure. Instead of flattening all data into a single sequence, the GTN processes information across two distinct dimensions:
1. **The Feature Tower**: Learns complex relationships between technical indicators (ATR, multi-timeframe rolling means, session overlaps).
2. **The Time Tower**: Processes the sequential nature of the data. 

Interestingly, I found that replacing standard sinusoidal positional encodings with **learned time embeddings** resulted in a noticeable performance bump. The model learned to inherently recognize the difference between the London and New York overlaps versus the quiet Asian sessions.

### Framing the Problem: TP/SL Logic
Most predictive models ask: *"Will the price move up or down in the next N hours?"* This fixed-horizon approach is brittle.
Instead, we frame the problem as: *"Will the price hit a predefined Take Profit (TP) before it hits the Stop Loss (SL) within a 24-hour lookahead window?"*

This strictly aligns the machine learning objective with actual trading mechanics (like a 1:2 Risk/Reward ratio).

### Overcoming the "Keep" Bias
Because financial data spends most of its time ranging, the models naturally overfit to the "keep" (do nothing) class, resulting in zero generated signals. 
To combat this, the GTN employs a heavily weighted cross-entropy loss function alongside a custom cost matrix that penalizes missed trades (false negatives) differently than bad trades (false positives), achieving a Composite Score of 0.36. 

While the system is robust, extracting a consistently positive Sharpe ratio from 1-minute data remains an ongoing battle against market noise.
