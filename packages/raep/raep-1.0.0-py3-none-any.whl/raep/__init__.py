"""
RAEP: Rapid Enzyme/Non-Enzyme Prediction
========================================

RAEP is an efficient machine learning tool for predicting whether a protein
sequence is an enzyme or non-enzyme. It combines multi-physicochemical
sequence features (Pseudo-AAC, CTD, windowed AAC) with an XGBoost classifier.

Key features:
- Fast single-sequence and batch prediction (including FASTA files)
- Built-in parallelized feature extraction
- Simple Python API and command-line interface (CLI)

Quick start:
    >>> from raep import RAEP
    >>> predictor = RAEP()
    >>> pred = predictor.predict("MKVL...")
    >>> prob = predictor.predict_proba("MKVL...")

The package includes a pre-trained model (`enzyme_xgb_model.pkl`). Custom models
can be loaded via the `model_path` argument.

Author: DHY  
License: MIT  
Version: 1.0.0
"""

from .model import RAEP

__version__ = "1.0.0"
__author__ = "DHY"
__email__ = "dhy.scut@outlook.com"

__all__ = ['RAEP']  
