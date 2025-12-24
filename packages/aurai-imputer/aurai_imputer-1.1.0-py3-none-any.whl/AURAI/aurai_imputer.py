"""
AURAIImputer — Production-Ready Single-File Imputer
(FINAL FIXED VERSION: Correct Mask Generation + MC Dropout)
"""

from typing import Optional, List, Tuple, Union, Dict
import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.utils import shuffle as sk_shuffle

import torch
import torch.nn as nn
import torch.nn.functional as F

# Optional FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False

# -----------------------
# Preprocessor
# -----------------------
class MixedPreprocessor:
    def __init__(self, numeric_cols: Optional[List[str]] = None, categorical_cols: Optional[List[str]] = None):
        self.numeric_cols = list(numeric_cols) if numeric_cols else []
        self.categorical_cols = list(categorical_cols) if categorical_cols else []
        self.scaler: Optional[StandardScaler] = StandardScaler() if self.numeric_cols else None
        self.oencoder: Optional[OrdinalEncoder] = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1) if self.categorical_cols else None
        self.categories_: Dict[str, List[str]] = {}
        self.fitted = False

    def fit(self, df: pd.DataFrame):
        if self.numeric_cols:
            self.scaler.fit(df[self.numeric_cols].astype(float).fillna(0.0))
        if self.categorical_cols:
            tmp = df[self.categorical_cols].astype(object).fillna("##MISSING##")
            self.oencoder.fit(tmp)
            for i, col in enumerate(self.categorical_cols):
                self.categories_[col] = list(self.oencoder.categories_[i])
        self.fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        assert self.fitted, "Call fit() before transform()"
        parts = []
        if self.numeric_cols:
            num = df[self.numeric_cols].astype(float).fillna(0.0)
            parts.append(self.scaler.transform(num))
        if self.categorical_cols:
            cat = df[self.categorical_cols].astype(object).fillna("##MISSING##")
            parts.append(self.oencoder.transform(cat))
        if parts:
            return np.concatenate(parts, axis=1)
        else:
            return np.zeros((len(df), 0), dtype=float)

    def inverse_transform_numeric(self, arr_numeric: np.ndarray) -> np.ndarray:
        if self.scaler:
            return self.scaler.inverse_transform(arr_numeric)
        return arr_numeric

    def decode_categorical_from_ordinals(self, arr_ordinals: np.ndarray) -> pd.DataFrame:
        if not self.categorical_cols:
            return pd.DataFrame(index=np.arange(arr_ordinals.shape[0]))
        df_out = {}
        arr = np.asarray(arr_ordinals)
        for j, col in enumerate(self.categorical_cols):
            cats = self.categories_.get(col, [])
            col_idx = np.round(arr[:, j]).astype(int)
            col_idx = np.clip(col_idx, 0, max(0, len(cats) - 1))
            df_out[col] = [cats[i] if (0 <= i < len(cats)) else "##MISSING##" for i in col_idx]
        return pd.DataFrame(df_out)

    def get_splits(self) -> Tuple[int, int]:
        return (len(self.numeric_cols), len(self.categorical_cols))

    def get_categorical_cardinalities(self) -> List[int]:
        return [len(self.categories_.get(c, [])) for c in self.categorical_cols]


# -----------------------
# Gumbel-softmax & categorical sampling
# -----------------------
def gumbel_softmax_sample(logits: torch.Tensor, tau: float = 1.0, hard: bool = False, eps: float = 1e-20):
    U = torch.rand_like(logits)
    g = -torch.log(-torch.log(U + eps) + eps)
    y = (logits + g) / tau
    y = F.softmax(y, dim=-1)
    if hard:
        y_hard = (y == y.max(dim=-1, keepdim=True)[0]).float()
        y = (y_hard - y).detach() + y
    return y

def sample_categorical_from_logits_all(logits_all: torch.Tensor, categorical_splits: List[int],
                                       tau: float = 0.7, hard: bool = True) -> torch.Tensor:
    outs = []
    idx = 0
    for k in categorical_splits:
        logits_k = logits_all[:, idx: idx + k]
        if k == 0:
            outs.append(torch.zeros((logits_all.size(0), 1), dtype=torch.long, device=logits_all.device))
            continue
        y = gumbel_softmax_sample(logits_k, tau=tau, hard=hard)  # (batch,k)
        idxs = torch.argmax(y, dim=-1).unsqueeze(1)  # (batch,1)
        outs.append(idxs)
        idx += k
    return torch.cat(outs, dim=1) if outs else torch.zeros((logits_all.size(0), 0), dtype=torch.long, device=logits_all.device)


# -----------------------
# Model components (With MC Dropout)
# -----------------------
class Encoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: List[int], latent_dim: int, mask_concat: bool = True):
        super().__init__()
        self.base_in = input_dim
        self.mask_concat = mask_concat
        total_in = input_dim * 2 if mask_concat else input_dim
        layers = []
        prev = total_in
        for h in hidden_dims:
            layers.append(nn.Linear(prev, h))
            layers.append(nn.ReLU(inplace=True))
            layers.append(nn.Dropout(0.2)) # MC Dropout
            prev = h
        self.net = nn.Sequential(*layers)
        self.mu = nn.Linear(prev, latent_dim)
        self.logvar = nn.Linear(prev, latent_dim)

    def forward(self, x: torch.Tensor, mask: torch.Tensor):
        if self.mask_concat:
            xm = torch.cat([x, mask], dim=1)
        else:
            xm = x
        h = self.net(xm)
        return self.mu(h), self.logvar(h), h

class Decoder(nn.Module):
    def __init__(self, latent_dim: int, hidden_dims: List[int], numeric_out: int, cat_total_dim: int):
        super().__init__()
        layers = []
        prev = latent_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev, h))
            layers.append(nn.ReLU(inplace=True))
            layers.append(nn.Dropout(0.2)) # MC Dropout
            prev = h
        self.net = nn.Sequential(*layers)
        self.out_numeric = nn.Linear(prev, numeric_out) if numeric_out > 0 else None
        self.out_num_logvar = nn.Linear(prev, numeric_out) if numeric_out > 0 else None
        self.out_cat_logits = nn.Linear(prev, cat_total_dim) if cat_total_dim > 0 else None

    def forward(self, z: torch.Tensor):
        h = self.net(z)
        num_mu = self.out_numeric(h) if self.out_numeric is not None else None
        num_logvar = self.out_num_logvar(h) if self.out_num_logvar is not None else None
        cat_logits = self.out_cat_logits(h) if self.out_cat_logits is not None else None
        return num_mu, num_logvar, cat_logits

class GatingPerFeature(nn.Module):
    def __init__(self, latent_dim: int, out_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, max(64, latent_dim)),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2), # MC Dropout
            nn.Linear(max(64, latent_dim), out_dim),
            nn.Sigmoid()
        )
    def forward(self, z_mu: torch.Tensor):
        return self.net(z_mu)


# -----------------------
# Latent index
# -----------------------
class LatentIndexFAISS:
    def __init__(self, dim: int, use_gpu: bool = False):
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS not installed")
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)

    def build(self, latents: np.ndarray, values: np.ndarray):
        self.index.reset()
        self.index.add(latents.astype('float32'))
        self.values = values.astype('float32')

    def query(self, q: np.ndarray, k: int = 5):
        D, I = self.index.search(q.astype('float32'), k)
        neigh = np.stack([self.values[I[i]] for i in range(I.shape[0])], axis=0)
        return neigh.mean(axis=1)

class LatentIndexCPU:
    def __init__(self):
        self.latents = None
        self.values = None

    def build(self, latents: np.ndarray, values: np.ndarray):
        self.latents = latents.astype('float32')
        self.values = values.astype('float32')

    def query(self, q: np.ndarray, k: int = 5):
        dif = self.latents[None, :, :] - q[:, None, :]
        d2 = (dif ** 2).sum(-1)
        idx = np.argpartition(d2, min(k, d2.shape[1]) - 1, axis=1)[:, :min(k, d2.shape[1])]
        m = q.shape[0]
        mvals = np.stack([self.values[idx[i]] for i in range(m)], axis=0)
        return mvals.mean(axis=1)


# -----------------------
# Internal network wrapper
# -----------------------
class _UAINetwork(nn.Module):
    def __init__(self, input_dim: int, latent_dim: int, enc_hidden: List[int], dec_hidden: List[int],
                 num_numeric: int, cat_total_dim: int, mask_concat: bool = True):
        super().__init__()
        self.encoder = Encoder(input_dim, hidden_dims=enc_hidden, latent_dim=latent_dim, mask_concat=mask_concat)
        self.decoder = Decoder(latent_dim, hidden_dims=dec_hidden, numeric_out=num_numeric, cat_total_dim=cat_total_dim)

    def forward_full(self, x: torch.Tensor, mask: torch.Tensor):
        mu, logvar, _ = self.encoder(x, mask)
        std = (0.5 * logvar).exp()
        eps = torch.randn_like(std)
        z = mu + eps * std
        num_mu, num_logvar, cat_logits = self.decoder(z)
        return num_mu, num_logvar, cat_logits, mu, logvar

    def encode_mu_logvar(self, x: torch.Tensor, mask: torch.Tensor):
        mu, logvar, _ = self.encoder(x, mask)
        return mu, logvar

    def decode_from_z(self, z: torch.Tensor):
        return self.decoder(z)


# -----------------------
# Loss helpers
# -----------------------
def _gaussian_nll(mu_pred: torch.Tensor, logvar_pred: torch.Tensor, x_true: torch.Tensor, mask: torch.Tensor):
    var = torch.exp(logvar_pred).clamp(min=1e-6)
    se = (x_true - mu_pred) ** 2
    nll = 0.5 * (torch.log(2 * np.pi * var) + se / var)
    denom = mask.sum().clamp(min=1.0)
    return (nll * mask).sum() / denom

def _kl_divergence(mu: torch.Tensor, logvar: torch.Tensor):
    return -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp()) / mu.size(0)


# -----------------------
# Main AURAIImputer
# -----------------------
class AURAIImputer:
    def __init__(self,
                 latent_dim: int = 64,
                 enc_hidden: List[int] = [256, 128],
                 dec_hidden: List[int] = [128, 256],
                 beta: float = 0.1,
                 lambda_cluster: float = 0.01,
                 mc_samples: int = 50,
                 categorical_temperature: float = 0.7,
                 k_neighbors: int = 5,
                 faiss_enabled: bool = False,
                 mask_concat: bool = True,
                 device: Optional[Union[str, torch.device]] = None,
                 verbose: bool = True,
                 min_latent_std: float = 1e-2,
                 min_num_std: float = 0.05,
                 jitter_scale: float = 0.05):
        self.latent_dim = latent_dim
        self.enc_hidden = enc_hidden
        self.dec_hidden = dec_hidden
        self.beta = beta
        self.lambda_cluster = lambda_cluster
        self.mc_samples = mc_samples
        self.cat_temp = categorical_temperature
        self.k_neighbors = k_neighbors
        self.faiss_enabled = faiss_enabled and FAISS_AVAILABLE
        self.mask_concat = mask_concat
        self.device = torch.device(device) if device else (torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu'))
        self.verbose = verbose
        self.min_latent_std = float(min_latent_std)
        self.min_num_std = float(min_num_std)
        self.jitter_scale = float(jitter_scale)

        self.preprocessor: Optional[MixedPreprocessor] = None
        self.model: Optional[_UAINetwork] = None
        self.gating: Optional[GatingPerFeature] = None
        self.categorical_splits: List[int] = []
        self.num_numeric = 0
        self.num_categorical = 0
        self.input_dim = 0
        self.latent_index = None
        self._is_fitted = False

    def _create_mask_from_df(self, df: pd.DataFrame) -> np.ndarray:
        """Helper to generate mask from DataFrame in correct column order"""
        mask_parts = []
        if self.preprocessor.numeric_cols:
            mask_parts.append(df[self.preprocessor.numeric_cols].notna().astype(float).values)
        if self.preprocessor.categorical_cols:
            mask_parts.append(df[self.preprocessor.categorical_cols].notna().astype(float).values)
        
        if not mask_parts:
            return np.ones((len(df), 0))
        return np.concatenate(mask_parts, axis=1)

    def fit(self,
            df: pd.DataFrame,
            numeric_cols: Optional[List[str]] = None,
            categorical_cols: Optional[List[str]] = None,
            epochs: int = 30,
            batch_size: int = 256,
            lr: float = 1e-3,
            shuffle: bool = True):
        
        # 1. SETUP
        if numeric_cols is None or categorical_cols is None:
            numeric_detect = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_detect = df.select_dtypes(exclude=[np.number]).columns.tolist()
            if numeric_cols is None: numeric_cols = numeric_detect
            if categorical_cols is None: categorical_cols = cat_detect

        self.preprocessor = MixedPreprocessor(numeric_cols=numeric_cols, categorical_cols=categorical_cols)
        self.preprocessor.fit(df)
        X = self.preprocessor.transform(df)
        self.num_numeric, self.num_categorical = self.preprocessor.get_splits()
        self.categorical_splits = self.preprocessor.get_categorical_cardinalities()
        self.input_dim = X.shape[1]

        # FIX: Generate mask from raw DF, not from transformed X (which has NaNs filled)
        mask = self._create_mask_from_df(df)
        
        X_filled = X.copy()
        # Ensure consistency just in case
        X_filled[mask == 0] = 0.0

        cat_total_dim = int(sum(self.categorical_splits)) if len(self.categorical_splits) > 0 else 0
        numeric_out = int(self.num_numeric)
        self.model = _UAINetwork(input_dim=self.input_dim, latent_dim=self.latent_dim,
                                 enc_hidden=self.enc_hidden, dec_hidden=self.dec_hidden,
                                 num_numeric=numeric_out, cat_total_dim=cat_total_dim,
                                 mask_concat=self.mask_concat).to(self.device)
        self.gating = GatingPerFeature(latent_dim=self.latent_dim, out_dim=self.input_dim).to(self.device)

        # 2. COLD START
        if self.verbose: print("[fit] Building initial latent index (cold start)...")
        self._rebuild_latent_index(X_filled, mask)

        optimizer = torch.optim.Adam(list(self.model.parameters()) + list(self.gating.parameters()), lr=lr)
        n = X_filled.shape[0]
        indices = np.arange(n)

        # 3. TRAINING LOOP
        for ep in range(epochs):
            if shuffle: indices = sk_shuffle(indices, random_state=ep)
            epoch_loss = 0.0
            count = 0
            self.model.train()
            self.gating.train()

            for start in range(0, n, batch_size):
                batch_idx = indices[start: start + batch_size]
                xb = torch.tensor(X_filled[batch_idx], dtype=torch.float32, device=self.device)
                mb = torch.tensor(mask[batch_idx], dtype=torch.float32, device=self.device)

                optimizer.zero_grad()
                num_mu, num_logvar, cat_logits, mu, logvar = self.model.forward_full(xb, mb)

                if self.num_numeric > 0:
                    nll_num = _gaussian_nll(num_mu, num_logvar, xb[:, :self.num_numeric], mb[:, :self.num_numeric])
                else:
                    nll_num = torch.tensor(0.0, device=self.device)

                ce_cat = torch.tensor(0.0, device=self.device)
                if self.num_categorical > 0:
                    start_idx = 0
                    true_cat_ordinals = xb[:, self.num_numeric:].long()
                    cat_obs_mask = mb[:, self.num_numeric:]
                    for f_idx, card in enumerate(self.categorical_splits):
                        logits_f = cat_logits[:, start_idx:start_idx + card]
                        true_idx = true_cat_ordinals[:, f_idx]
                        valid_mask = (true_idx >= 0) & (cat_obs_mask[:, f_idx] > 0.5)
                        if valid_mask.any():
                            ce_cat = ce_cat + F.cross_entropy(logits_f[valid_mask], true_idx[valid_mask], reduction='mean')
                        start_idx += card

                kl = _kl_divergence(mu, logvar)
                cluster_reg = mu.var(dim=0).mean()
                vae_loss = nll_num + ce_cat + self.beta * kl + self.lambda_cluster * cluster_reg

                # Active Gating Loss
                mu_detached = mu.detach().cpu().numpy()
                neigh_vals_np = self.latent_index.query(mu_detached, k=self.k_neighbors)
                neigh_vals = torch.tensor(neigh_vals_np, dtype=torch.float32, device=self.device)

                vae_recon_list = []
                if self.num_numeric > 0: vae_recon_list.append(num_mu)
                if self.num_categorical > 0:
                    cat_recon_parts = []
                    start_idx = 0
                    for card in self.categorical_splits:
                        l_f = cat_logits[:, start_idx:start_idx+card]
                        cat_recon_parts.append(torch.argmax(l_f, dim=1).unsqueeze(1).float())
                        start_idx += card
                    vae_recon_list.append(torch.cat(cat_recon_parts, dim=1))
                vae_recon_combined = torch.cat(vae_recon_list, dim=1)

                alpha = self.gating(mu)
                if neigh_vals.shape[1] != vae_recon_combined.shape[1]: neigh_vals = vae_recon_combined 
                gated_output = alpha * vae_recon_combined + (1.0 - alpha) * neigh_vals
                
                diff = (gated_output - xb) * mb
                gating_loss = (diff ** 2).sum() / (mb.sum().clamp(min=1.0))
                
                total_loss = vae_loss + 10.0 * gating_loss
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(list(self.model.parameters()) + list(self.gating.parameters()), max_norm=5.0)
                optimizer.step()
                epoch_loss += total_loss.item() * xb.shape[0]
                count += xb.shape[0]

            if self.verbose: print(f"[fit] Epoch {ep+1}/{epochs} loss={epoch_loss / max(1,count):.6f}")
            self._rebuild_latent_index(X_filled, mask)

        self._is_fitted = True
        return self

    def _rebuild_latent_index(self, X_filled: np.ndarray, mask: np.ndarray):
        self.model.eval()
        with torch.no_grad():
            Xt = torch.tensor(X_filled, dtype=torch.float32, device=self.device)
            Mt = torch.tensor(mask, dtype=torch.float32, device=self.device)
            mu_all, _ = self.model.encode_mu_logvar(Xt, Mt)
            mu_np = mu_all.cpu().numpy().astype('float32')
        values = X_filled.astype('float32')
        if self.faiss_enabled:
            idx = LatentIndexFAISS(dim=mu_np.shape[1])
            idx.build(mu_np, values)
            self.latent_index = idx
        else:
            idx = LatentIndexCPU()
            idx.build(mu_np, values)
            self.latent_index = idx

    def _decode_and_fill(self, mean_arr: np.ndarray, df_missing: pd.DataFrame, clip_to_observed: bool = True) -> pd.DataFrame:
        assert isinstance(df_missing, pd.DataFrame), "df_missing must be a DataFrame for decode_and_fill"
        num_cols = self.preprocessor.numeric_cols
        cat_cols = self.preprocessor.categorical_cols
        n_num = len(num_cols)
        n_cat = len(cat_cols)

        if n_num > 0:
            mean_numeric_scaled = mean_arr[:, :n_num]
            mean_numeric = self.preprocessor.inverse_transform_numeric(mean_numeric_scaled)
            if clip_to_observed:
                for j, c in enumerate(num_cols):
                    try:
                        obs_min = float(df_missing[c].dropna().min())
                        obs_max = float(df_missing[c].dropna().max())
                        if np.isfinite(obs_min) and np.isfinite(obs_max):
                            mean_numeric[:, j] = np.clip(mean_numeric[:, j], obs_min, obs_max)
                    except Exception: pass
        else:
            mean_numeric = np.zeros((mean_arr.shape[0], 0))

        if n_cat > 0:
            cat_segment = mean_arr[:, n_num:n_num + n_cat]
            cat_ordinals = np.round(cat_segment).astype(int)
            cat_df = self.preprocessor.decode_categorical_from_ordinals(cat_ordinals)
        else:
            cat_df = pd.DataFrame(index=np.arange(mean_arr.shape[0]))

        num_df = pd.DataFrame(mean_numeric, columns=num_cols) if n_num > 0 else pd.DataFrame(index=np.arange(mean_arr.shape[0]))
        decoded_combined = pd.concat([num_df.reset_index(drop=True), cat_df.reset_index(drop=True)], axis=1)

        final_df = df_missing.copy()
        for c in num_cols:
            if c not in decoded_combined.columns: continue
            decoded_col = pd.Series(decoded_combined[c].values, index=final_df.index).astype(float)
            missing_mask = final_df[c].isnull()
            if missing_mask.any(): final_df.loc[missing_mask, c] = decoded_col.loc[missing_mask].values

        for c in cat_cols:
            if c not in decoded_combined.columns: continue
            decoded_col = pd.Series(decoded_combined[c].values, index=final_df.index).astype(object)
            missing_mask = final_df[c].isnull()
            if missing_mask.any(): final_df.loc[missing_mask, c] = decoded_col.loc[missing_mask].values

        return final_df

    def transform(self,
                  df_or_array: Union[pd.DataFrame, np.ndarray],
                  mask: Optional[np.ndarray] = None,
                  mc_samples: Optional[int] = None,
                  return_intervals: bool = False,
                  return_samples: bool = False,
                  return_df: bool = False) -> Union[np.ndarray, Tuple]:
        assert self._is_fitted, "Call fit() first."
        
        # 1. HANDLE INPUT AND MASK GENERATION FIRST
        if isinstance(df_or_array, pd.DataFrame):
            original_df = df_or_array.copy()
            # FIX: Create mask from DataFrame BEFORE preprocessing destroys NaNs
            if mask is None:
                mask = self._create_mask_from_df(df_or_array)
            X = self.preprocessor.transform(df_or_array).astype('float32')
        else:
            X = df_or_array.copy().astype('float32')
            original_df = None
            if mask is None:
                mask = (~np.isnan(X)).astype(float)

        X_obs = X.copy()
        X_obs[mask == 0] = 0.0

        mc = int(mc_samples) if mc_samples is not None else int(self.mc_samples)
        model = self.model
        gating = self.gating
        
        # KEY FIX: Force model into training mode to enable Dropout during inference
        # This creates 'Monte Carlo Dropout' uncertainty
        model.train() 
        gating.train()

        samples = []
        with torch.no_grad():
            Xt = torch.tensor(X_obs, dtype=torch.float32, device=self.device)
            Mt = torch.tensor(mask, dtype=torch.float32, device=self.device)
            
            # 1. Encode Mean (Deterministic if not for dropout)
            mu, logvar = model.encode_mu_logvar(Xt, Mt)
            nrows = Xt.size(0)

            for t in range(mc):
                # 2. Sample Latent Z (Boosted Noise for Diversity)
                eff_std = (0.5 * logvar).exp().clamp(min=self.min_latent_std * 2.0)
                z = mu + torch.randn_like(eff_std) * eff_std

                # 3. Decode
                num_mu, num_logvar, cat_logits = model.decode_from_z(z)

                if num_mu is not None and num_logvar is not None:
                    # Scale floor helps ensure numerical stability
                    num_std = (0.5 * num_logvar).exp().clamp(min=self.min_num_std)
                    num_sample = num_mu + torch.randn_like(num_std) * num_std
                elif num_mu is not None:
                    jitter = torch.randn_like(num_mu) * self.min_num_std
                    num_sample = num_mu + jitter
                else:
                    num_sample = torch.zeros((nrows, 0), device=z.device)

                if self.num_categorical > 0 and cat_logits is not None:
                    cat_sample_idxs = sample_categorical_from_logits_all(cat_logits, self.categorical_splits,
                                                                         tau=self.cat_temp, hard=True)
                    cat_sample_float = cat_sample_idxs.float()
                    recon_numeric = torch.cat([num_sample, cat_sample_float], dim=1)
                else:
                    recon_numeric = num_sample

                # 4. Neighbor Query using Z + Jitter
                try:
                    z_numpy = z.cpu().numpy()
                    local_vals = self.latent_index.query(z_numpy, k=self.k_neighbors)
                    local_vals = torch.tensor(local_vals, dtype=torch.float32, device=self.device)
                    # Add jitter to neighbors to prevent zero-width intervals in sparse data
                    if self.jitter_scale > 0:
                        local_vals = local_vals + torch.randn_like(local_vals) * self.jitter_scale
                    if local_vals.shape[1] != recon_numeric.shape[1]: local_vals = recon_numeric
                except Exception:
                    local_vals = recon_numeric

                # 5. Gating using Z
                alpha = gating(z)
                if alpha.shape[1] != recon_numeric.shape[1]:
                    alpha = alpha.mean(dim=1, keepdim=True).repeat(1, recon_numeric.shape[1])

                gated = alpha * recon_numeric + (1.0 - alpha) * local_vals
                
                # Apply observation noise to the final result to guarantee non-zero width
                if self.jitter_scale > 0:
                    gated = gated + torch.randn_like(gated) * (self.jitter_scale * 0.5)

                filled = Xt * Mt + gated * (1.0 - Mt)
                samples.append(filled.cpu().numpy())

        arr = np.stack(samples, axis=0)  # (mc, n, d)
        mean_imp = arr.mean(axis=0)

        # Cleanup: Return model to eval mode
        model.eval()
        gating.eval()

        if return_intervals:
            lower = np.percentile(arr, 2.5, axis=0)
            upper = np.percentile(arr, 97.5, axis=0)
            
            # Pass back the mask so we know which are missing
            missing_mask_np = (mask == 0)

            if return_df:
                if original_df is None: raise ValueError("return_df requires DataFrame")
                final_df = self._decode_and_fill(mean_imp, original_df, clip_to_observed=True)
                n_num = self.num_numeric
                if n_num > 0:
                    lower_num = self.preprocessor.inverse_transform_numeric(lower[:, :n_num])
                    upper_num = self.preprocessor.inverse_transform_numeric(upper[:, :n_num])
                else:
                    lower_num, upper_num = lower, upper
                return final_df, lower_num, upper_num, missing_mask_np
            else:
                if return_samples: return arr, mean_imp, lower, upper, missing_mask_np
                return mean_imp, lower, upper, missing_mask_np

        if return_df:
            if original_df is None: raise ValueError("return_df requires DataFrame")
            final_df = self._decode_and_fill(mean_imp, original_df, clip_to_observed=True)
            if return_samples: return arr, final_df
            return final_df

        if return_samples: return arr, mean_imp
        return mean_imp

    def save(self, path: str):
        os.makedirs(path, exist_ok=True)
        torch.save(self.model.state_dict(), os.path.join(path, "model.pth"))
        torch.save(self.gating.state_dict(), os.path.join(path, "gating.pth"))
        meta = {
            "latent_dim": self.latent_dim,
            "enc_hidden": self.enc_hidden,
            "dec_hidden": self.dec_hidden,
            "beta": self.beta,
            "lambda_cluster": self.lambda_cluster,
            "mc_samples": self.mc_samples,
            "cat_temp": self.cat_temp,
            "k_neighbors": self.k_neighbors,
            "faiss_enabled": self.faiss_enabled,
            "mask_concat": self.mask_concat,
            "num_numeric": self.num_numeric,
            "num_categorical": self.num_categorical,
            "categorical_splits": self.categorical_splits,
            "input_dim": self.input_dim,
            "min_latent_std": self.min_latent_std,
            "min_num_std": self.min_num_std,
            "jitter_scale": self.jitter_scale
        }
        with open(os.path.join(path, "meta.json"), "w") as f: json.dump(meta, f)
        with open(os.path.join(path, "preprocessor.pkl"), "wb") as f: pickle.dump(self.preprocessor, f)
        return path

    @classmethod
    def load(cls, path: str, device: Optional[Union[str, torch.device]] = None):
        with open(os.path.join(path, "meta.json"), "r") as f: meta = json.load(f)
        obj = cls(latent_dim=meta.get("latent_dim", 64),
                  enc_hidden=meta.get("enc_hidden", [256,128]),
                  dec_hidden=meta.get("dec_hidden", [128,256]),
                  beta=meta.get("beta", 0.1),
                  lambda_cluster=meta.get("lambda_cluster", 0.01),
                  mc_samples=meta.get("mc_samples", 50),
                  categorical_temperature=meta.get("cat_temp", 0.7),
                  k_neighbors=meta.get("k_neighbors", 5),
                  faiss_enabled=meta.get("faiss_enabled", False),
                  mask_concat=meta.get("mask_concat", True),
                  device=device,
                  min_latent_std=meta.get("min_latent_std", 1e-2),
                  min_num_std=meta.get("min_num_std", 1e-2),
                  jitter_scale=meta.get("jitter_scale", 1e-3))
        with open(os.path.join(path, "preprocessor.pkl"), "rb") as f: obj.preprocessor = pickle.load(f)
        obj.num_numeric = int(meta.get("num_numeric", 0))
        obj.num_categorical = int(meta.get("num_categorical", 0))
        obj.categorical_splits = meta.get("categorical_splits", [])
        obj.input_dim = int(meta.get("input_dim", 0))
        cat_total_dim = int(sum(obj.categorical_splits)) if obj.categorical_splits else 0
        obj.model = _UAINetwork(input_dim=obj.input_dim, latent_dim=obj.latent_dim,
                                enc_hidden=obj.enc_hidden, dec_hidden=obj.dec_hidden,
                                num_numeric=obj.num_numeric, cat_total_dim=cat_total_dim,
                                mask_concat=obj.mask_concat).to(obj.device)
        obj.gating = GatingPerFeature(latent_dim=obj.latent_dim, out_dim=obj.input_dim).to(obj.device)
        obj.model.load_state_dict(torch.load(os.path.join(path, "model.pth"), map_location=obj.device))
        obj.gating.load_state_dict(torch.load(os.path.join(path, "gating.pth"), map_location=obj.device))
        obj._is_fitted = True
        return obj


# -----------------------
# Example usage
# -----------------------
if __name__ == "__main__":
    import shutil
    print("[Example] Running AURAIImputer with fixed mask logic...")

    np.random.seed(42)
    N = 400
    age = np.random.randint(18, 70, N)
    income = age * 1200 + np.random.randn(N) * 5000
    job = np.random.choice(["eng", "sales", "hr", "dev"], N)
    score = income / 800 + np.random.randn(N) * 3

    df = pd.DataFrame({"age": age, "income": income, "job": job, "score": score})
    rng = np.random.default_rng(42)
    df_missing = df.mask(rng.random(df.shape) < 0.2)

    print("\nMissing% per col:\n", df_missing.isnull().mean())

    imputer = AURAIImputer(latent_dim=32, mc_samples=100, faiss_enabled=False, verbose=True,
                           min_latent_std=1e-2, min_num_std=1e-2, jitter_scale=0.1)
    
    imputer.fit(df_missing, epochs=10, batch_size=128, lr=1e-3)

    # Get mean + intervals and decoded DataFrame
    # Note: transform now returns missing_mask when return_intervals is True
    final_df, lower_num, upper_num, missing_mask = imputer.transform(df_missing, return_intervals=True, return_df=True)

    print("\nFirst 5 rows of decoded final imputed DataFrame:")
    print(final_df.head())

    # Diagnostics: zero-width intervals?
    mean_arr, low, high, missing_mask_arr = imputer.transform(df_missing, return_intervals=True)
    
    print(f"\n{'='*60}")
    print("UNCERTAINTY DIAGNOSTICS (MISSING VALUES ONLY)")
    print(f"{'='*60}")
    print(f"Missing mask shape: {missing_mask_arr.shape}")
    print(f"Missing mask sum: {missing_mask_arr.sum()}")
    
    if missing_mask_arr.any():
        missing_low = low[missing_mask_arr == 1]
        missing_high = high[missing_mask_arr == 1]
        missing_widths = missing_high - missing_low
        
        total_missing = missing_mask_arr.sum()
        zero_width = np.sum(np.isclose(missing_low, missing_high, atol=1e-6))
        
        print(f"Zero-width intervals: {zero_width} / {total_missing} ({100*zero_width/total_missing:.1f}%)")
        print(f"Mean interval width: {missing_widths.mean():.4f}")
        
        if zero_width < total_missing * 0.1:
            print("\nSUCCESS: Robust uncertainty intervals generated!")
        else:
            print("\nWARNING: Intervals still collapsed.")
    else:
        print("ERROR: No missing values detected in mask!")

    # Save & load smoke test
    save_dir = "aurai_demo_saved"
    try:
        if os.path.exists(save_dir):
            shutil.rmtree(save_dir)
    except Exception:
        pass

    imputer.save(save_dir)
    imputer2 = AURAIImputer.load(save_dir)
    print(f"\nSave & load test: {isinstance(imputer2, AURAIImputer)}")

    print("\n[Example] Demo finished.")