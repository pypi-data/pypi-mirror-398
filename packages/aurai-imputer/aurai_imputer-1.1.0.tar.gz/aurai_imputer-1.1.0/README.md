# AURAI – Adaptive Uncertainty-Regularized Autoencoder Imputer
**Author:** Abdul Mofique Siddiqui  
**License:** MIT  
**Install via pip:**
```bash
pip install aurai-imputer
```
Import it in your Python code:
```python
from AURAI import AURAIImputer
```

## Overview
AURAI (Adaptive Uncertainty-Regularized Autoencoder Imputer) is an advanced hybrid imputation framework that combines:
* A mask-aware Variational Autoencoder (VAE)
* Latent-space nearest-neighbor refinement
* A feature-wise adaptive gating mechanism
* Monte-Carlo–based uncertainty estimation

AURAI supports both numerical and categorical datasets and performs reliably under:
* MCAR (Missing Completely At Random)
* MAR (Missing At Random)
* MNAR (Missing Not At Random)

The imputer also produces confidence intervals for each filled value, making it suitable for decision-critical applications.

## Installation
Install the package via pip:
```bash
pip install aurai-imputer
```

## How It Works
* **Global VAE Module** Learns latent structure and reconstructs both numeric and categorical distributions.
* **Latent-Space KNN Module** Uses nearest neighbors in latent space to refine local predictions.
* **Adaptive Gating** Produces a learnable per-feature weight that blends global (VAE) and local (KNN) imputations.
* **Uncertainty Estimation** Monte-Carlo sampling over latent variables yields:
   * Posterior means
   * 95% confidence intervals
* **Mixed Data Support** Uses `StandardScaler` + `OrdinalEncoder` to handle mixed data seamlessly.

## Getting Started

### 1. Import the package
```python
from AURAI import AURAIImputer
```

### 2. Initialize the imputer
```python
imputer = AURAIImputer()
```

### 3. Fit the model
```python
imputer.fit(df)
```
* `df`: pandas DataFrame containing numerical and/or categorical columns

### 4. Impute missing values
```python
imputed = imputer.transform(df)
```
Returns a NumPy array with missing values filled.

### 5. Impute with uncertainty intervals
```python
mean, lower, upper = imputer.transform(df, return_intervals=True)
```

## API Reference

### AURAIImputer()
Initializes the imputer.
Supports optional parameters such as latent dimension, Monte Carlo samples, neighbors count, etc.

### `.fit(df)`
Fits the model to training data.

**Parameters:**
* `df`: pandas DataFrame with mixed features

### `.transform(df, return_intervals=False)`
Returns imputed values.

**Input:**
* `df`: DataFrame or numpy array with missing values

**Output:**
* A NumPy array with imputed values
* If `return_intervals=True`: returns `(mean, lower, upper)`

### `.save(path)`
Saves:
* model weights
* preprocessor
* metadata

### `.load(path)`
Loads a previously saved AURAI model.

## Example Usage

### Example 1: Basic Imputation
```python
from AURAI import AURAIImputer
import pandas as pd

df = pd.read_csv("data.csv")
imputer = AURAIImputer()
imputer.fit(df)
imputed = imputer.transform(df)
```

### Example 2: Imputation with Uncertainty
```python
mean, lower, upper = imputer.transform(df, return_intervals=True)
```
### Example 3: Demo
```python

import numpy as np
import pandas as pd
import os
import shutil

from AURAI import AURAIImputer  


# ============================================
# Example demo
# ============================================
def run_demo():
    print("[Example] Running AURAIImputer quick demo...")

    # Create synthetic demo dataset
    np.random.seed(42)
    N = 400
    age = np.random.randint(18, 70, N)
    income = age * 1200 + np.random.randn(N) * 5000
    job = np.random.choice(["eng", "sales", "hr", "dev"], N)
    score = income / 800 + np.random.randn(N) * 3

    df = pd.DataFrame({
        "age": age,
        "income": income,
        "job": job,
        "score": score
    })

    # Introduce 20% missingness
    rng = np.random.default_rng(42)
    df_missing = df.mask(rng.random(df.shape) < 0.2)

    print("\nMissing% per col:\n", df_missing.isnull().mean())

    # Initialize imputer
    imputer = AURAIImputer(
        latent_dim=32,
        mc_samples=100,
        faiss_enabled=False,
        verbose=True,
        min_latent_std=1e-2,
        min_num_std=1e-2
    )

    # Fit the model
    imputer.fit(df_missing, epochs=10, batch_size=128, lr=1e-3)

    # Perform imputation with intervals and decoded DataFrame output
    final_df, lower, upper = imputer.transform(
        df_missing,
        return_intervals=True,
        return_df=True
    )

    print("\nFirst 5 rows of decoded final imputed DataFrame:")
    print(final_df.head())

    # Check interval degeneracy
    mean_arr, low_arr, high_arr = imputer.transform(df_missing, return_intervals=True)
    print("\nZero-width intervals:", np.sum(np.isclose(low_arr, high_arr)), "/", low_arr.size)

    # Save/load test
    save_dir = "aurai_demo_saved"
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)

    imputer.save(save_dir)
    imputer2 = AURAIImputer.load(save_dir)

    print("\nSave & load smoke test OK:", isinstance(imputer2, AURAIImputer))
    print("\n[Example] Demo finished.")


# Only run demo when file is executed directly
if __name__ == "__main__":
    run_demo()

```
## Internals
* **Variational Autoencoder (VAE)** Learns global structure and reconstructs numeric means, variances, and categorical logits.
* **Latent-Space Nearest Neighbor Search** Provides local refinement to improve imputation accuracy.
* **Gating Network** Learns per-feature blending weights for global + local fusion.
* **Cluster Regularization** Encourages structured and stable latent geometry.
* **Monte Carlo Sampling** Produces mean predictions and confidence intervals.

## Notes
* Works with both numeric and categorical data.
* Performs well under MCAR, MAR, and MNAR.
* Provides uncertainty intervals for downstream tasks.
* GPU recommended for training large datasets.

## Author
Abdul Mofique Siddiqui

## License
This project is licensed under the MIT License.