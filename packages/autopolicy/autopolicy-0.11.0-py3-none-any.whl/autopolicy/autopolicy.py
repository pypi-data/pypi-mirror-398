from joblib import Parallel, delayed
from sklearn.model_selection import KFold
from autogluon.tabular import TabularPredictor
import numpy as np

from .policy import Policy

class AutoPolicy:
    def __init__(
        self,
        predictor:TabularPredictor,
        label:str,
        bin_col:str,
        cost_bad:float=1.0,
        cost_miss:float=0.2,
        folds:int=3,
        iters:int=40,
        seed:int=42,
        n_jobs:int=-1,
    ):
        self.p = predictor
        self.label = label
        self.bin_col = bin_col
        self.cb = cost_bad
        self.cm = cost_miss
        self.folds = folds
        self.iters = iters
        self.n_jobs = n_jobs
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def _sample(self):
        ga = self.rng.uniform(0.65, 0.95)
        gd = self.rng.uniform(0.05, ga - 0.05)
        return dict(
            global_approve=ga,
            global_decline=gd,
            sensitivity=self.rng.uniform(0.1, 1.0),
            n_bins=int(self.rng.integers(3, 8)),
        )

    def _fold_cost(self, h, df, tr, va):
        p = Policy(
            self.p,
            self.label,
            self.bin_col,
            **h
        ).fit(df.iloc[tr])
        return p.cost(df.iloc[va], self.cb, self.cm)

    def _evaluate_sample(self, df, splits, h):
        costs = [self._fold_cost(h, df, tr, va) for tr, va in splits]
        return h, float(np.mean(costs))

    def fit(self, train_data):
        kf = KFold(self.folds, shuffle=True, random_state=self.seed)
        splits = list(kf.split(train_data))
        samples = [self._sample() for _ in range(self.iters)]

        results = Parallel(n_jobs=self.n_jobs, prefer="threads")(
            delayed(self._evaluate_sample)(train_data, splits, h)
            for h in samples
        )

        best, _ = min(results, key=lambda x: x[1])

        return Policy(self.p,self.label,self.bin_col,**best).fit(train_data)
