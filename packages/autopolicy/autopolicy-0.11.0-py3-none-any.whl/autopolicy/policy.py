import os, json
from dataclasses import dataclass
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

# =========================
# Core Data Structures
# =========================

@dataclass
class Thresholds:
    approve: float
    decline: float

# =========================
# Policy
# =========================

class Policy:
    A, D, R = 1, 0, -1  # approve / decline / review

    def __init__(
        self,
        predictor: Any,
        label: str,
        bin_col: str,
        n_bins: int = 5,
        binning: str = "quantile",
        global_approve: float = 0.8,
        global_decline: float = 0.4,
        sensitivity: float = 0.5,
        monotonic: bool = True,
    ):
        assert 0 < global_decline < global_approve < 1
        self.p = predictor
        self.label = label
        self.bin_col = bin_col
        self.n_bins = n_bins
        self.binning = binning
        self.ga = global_approve
        self.gd = global_decline
        self.s = sensitivity
        self.monotonic = monotonic
        self.bins: Optional[list] = None
        self.th: Dict[str, Thresholds] = {}

    # -------------------------
    # Utilities
    # -------------------------

    def _proba(self, df):
        p = self.p.predict_proba(df)
        if not isinstance(p, pd.DataFrame):
            p = pd.DataFrame(p, index=df.index)
        return p.iloc[:, 1]

    def _make_bins(self, s):
        uniq = np.unique(s)

        if len(uniq) <= 1:
            v = uniq[0]
            self.bins = [v - 1e-9, v + 1e-9]
            return

        if self.binning == "quantile":
            b = np.quantile(s, np.linspace(0, 1, self.n_bins + 1))
            b[0] -= 1e-9
            b[-1] += 1e-9  # make right edge inclusive when using right=False
        else:
            b = np.linspace(s.min(), s.max(), self.n_bins + 1)

        self.bins = np.unique(b).tolist()

    def _assign_bins(self, s):
        return pd.cut(s, self.bins, right=False, duplicates="drop")

    # -------------------------
    # Fit
    # -------------------------

    def fit(self, df: pd.DataFrame):
        p = self._proba(df)
        gmean = p.mean()
        self._make_bins(df[self.bin_col])
        bins = self._assign_bins(df[self.bin_col])

        items = []
        for b, g in p.groupby(bins, observed=True):
            lift = g.mean() - gmean
            adj = lift * self.s
            a = np.clip(self.ga - adj, 0, 1)
            d = np.clip(self.gd - adj, 0, a)
            items.append((b, Thresholds(a, d)))

        items.sort(key=lambda x: x[0].left)

        if self.monotonic:
            ma = md = 0
            out = []
            for b, t in items:
                a = max(t.approve, ma)
                d = max(t.decline, md)
                d = min(d, a)
                ma, md = a, d
                out.append((b, Thresholds(a, d)))
            items = out

        self.th = {str(b): t for b, t in items}
        return self

    # -------------------------
    # Apply
    # -------------------------

    def apply(self, df: pd.DataFrame) -> pd.Series:
        p = self._proba(df)
        bins = self._assign_bins(df[self.bin_col])

        def decide(prob, b):
            t = self.th.get(str(b))
            if not t: return self.R
            if prob >= t.approve: return self.A
            if prob <= t.decline: return self.D
            return self.R

        return pd.Series(
            (decide(pi, bi) for pi, bi in zip(p, bins)),
            index=df.index
        )

    # -------------------------
    # Cost
    # -------------------------

    def cost(self, df, c_bad=5.0, c_miss=1.0):
        d = self.apply(df)
        y = df[self.label]
        bad = ((d == self.A) & (y == 0)).sum()
        miss = ((d == self.D) & (y == 1)).sum()
        return c_bad * bad + c_miss * miss

    # -------------------------
    # Evaluation
    # -------------------------

    def evaluate(self, df: pd.DataFrame) -> dict:
        if self.bins is None or not self.th:
            raise RuntimeError("Policy must be fit or loaded before evaluation.")

        df_local = df.copy()
        df_local["_decision"] = self.apply(df_local)
        df_local["_bin"] = self._assign_bins(df_local[self.bin_col])

        y = df_local[self.label]
        n = len(df_local)

        approve = df_local["_decision"] == self.A
        decline = df_local["_decision"] == self.D
        review = df_local["_decision"] == self.R

        def rate(mask):
            return float(mask.mean()) if n else 0.0

        bad_approves_total = int((approve & (y == 0)).sum())
        missed_declines_total = int((decline & (y == 1)).sum())

        overall = {
            "automation_rate": rate(approve | decline),
            "approve_rate": rate(approve),
            "decline_rate": rate(decline),
            "review_rate": rate(review),
            "bad_approve_total": bad_approves_total,
            "bad_approve_percent": float(bad_approves_total / n) if n else 0.0,
            "missed_decline_total": missed_declines_total,
            "missed_decline_percent": float(missed_declines_total / n) if n else 0.0,
        }

        by_bin = {}
        for b, g in df_local.groupby("_bin", observed=True):
            if len(g) == 0:
                continue

            m = len(g)
            approve_b = g["_decision"] == self.A
            decline_b = g["_decision"] == self.D
            review_b = g["_decision"] == self.R

            bad_b = int((approve_b & (g[self.label] == 0)).sum())
            miss_b = int((decline_b & (g[self.label] == 1)).sum())

            by_bin[str(b)] = {
                "count": int(m),
                "approve_rate": float(approve_b.mean()),
                "decline_rate": float(decline_b.mean()),
                "review_rate": float(review_b.mean()),
                "bad_approve": bad_b,
                "bad_approve_percent": float(bad_b / m) if m else 0.0,
                "missed_decline": miss_b,
                "missed_decline_percent": float(miss_b / m) if m else 0.0,
            }

        return {"overall": overall, "by_bin": by_bin}

    # -------------------------
    # Predict
    # -------------------------

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.bins is None or not self.th:
            raise RuntimeError("policy must be fit or loaded before prediction.")

        proba = self.p.predict_proba(df)
        if not isinstance(proba, pd.DataFrame):
            proba = pd.DataFrame(proba, index=df.index)
        else:
            proba = proba.copy()
            proba.index = df.index

        if proba.shape[1] < 2:
            raise ValueError("predict_proba must return at least two probability columns.")

        preds = proba.iloc[:, :2].copy()
        preds.columns = ["prob_0", "prob_1"]

        bins = self._assign_bins(df[self.bin_col])

        def decide(prob, b):
            t = self.th.get(str(b))
            if not t:
                return self.R
            if prob >= t.approve:
                return self.A
            if prob <= t.decline:
                return self.D
            return self.R

        decisions = pd.Series(
            (decide(pi, bi) for pi, bi in zip(preds["prob_1"], bins)),
            index=df.index,
        )

        out = df.copy()
        out[["_prob_0", "_prob_1"]] = preds
        out["_decision"] = decisions
        return out

    # -------------------------
    # Persistence
    # -------------------------

    def save(self, path):
        os.makedirs(path, exist_ok=True)
        json.dump(
            dict(
                label=self.label,
                bin_col=self.bin_col,
                n_bins=self.n_bins,
                binning=self.binning,
                ga=self.ga,
                gd=self.gd,
                s=self.s,
                monotonic=self.monotonic,
                bins=self.bins,
                th={k: vars(v) for k, v in self.th.items()},
            ),
            open(f"{path}/policy.json", "w"),
            indent=2,
        )

    @staticmethod
    def load(path, predictor):
        d = json.load(open(f"{path}/policy.json"))
        p = Policy(predictor, d["label"], d["bin_col"],
                   d["n_bins"], d["binning"],
                   d["ga"], d["gd"], d["s"], d["monotonic"])
        p.bins = d["bins"]
        p.th = {k: Thresholds(**v) for k, v in d["th"].items()}
        return p
