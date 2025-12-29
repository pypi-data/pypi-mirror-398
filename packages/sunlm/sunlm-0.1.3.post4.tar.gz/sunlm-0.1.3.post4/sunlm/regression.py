# sunlm/regression.py

import pandas as pd
import numpy as np
import statsmodels.api as sm
from patsy import dmatrices


def _format_p_value(p: float) -> str:
    if p < 0.001:
        tag = "(< .001)"
    elif p < 0.01:
        tag = "(< .01)"
    elif p < 0.05:
        tag = "(< .05)"
    else:
        tag = "(n.s.)"
    return f"{p:.3f} {tag}".strip()


def _f3(x):
    """Format numeric values to 3 decimals; keep blanks for NaN."""
    return "" if pd.isna(x) else f"{x:.3f}"


class sunlm_model:
    """
    Social-science–friendly OLS wrapper (SPSS-equivalent, R-style formula).
    """

    def __init__(self, formula: str, data: pd.DataFrame):
        self.formula = formula
        self.data = data
        self.y, self.X = dmatrices(formula, data, return_type="dataframe")
        self.fit_result = sm.OLS(self.y, self.X).fit()

    def summary(self):
        df, stats = self._calculate_metrics()
        print("## 📊 OLS Regression Summary")
        print(df.to_string())
        print("\n## 📈 Model Fit Statistics")
        print(pd.Series(stats).to_string())

    def _calculate_metrics(self):
        model = self.fit_result
        X, y = self.X, self.y.iloc[:, 0]

        intercept = next((c for c in X.columns if "Intercept" in c), None)
        X_vars = X.drop(columns=[intercept], errors="ignore")

        sd_y = y.std(ddof=1)
        R2_full = model.rsquared

        # Base results (numeric first)
        res = pd.DataFrame({
            "Unstd. B": model.params,
            "Std. Err. (unstd)": model.bse,
            "t-value": model.tvalues,
            "p_raw": model.pvalues
        })

        beta, sr2 = [], []

        for v in model.params.index:
            if v == intercept:
                beta.append(np.nan)
                sr2.append(np.nan)
                continue

            sd_x = X_vars[v].std(ddof=1)
            beta.append(model.params[v] * (sd_x / sd_y) if sd_x != 0 else np.nan)

            reduced = sm.OLS(y, X.drop(columns=[v])).fit()
            sr2.append(R2_full - reduced.rsquared)

        res["Std. β"] = beta
        res["Semi-partial R²"] = sr2

        # Format p-values (tagged) and drop raw p
        res["p-value"] = res["p_raw"].apply(_format_p_value)
        res.drop(columns=["p_raw"], inplace=True)

        # Format all numeric columns to 3 decimals
        for col in ["Unstd. B", "Std. Err. (unstd)", "t-value", "Std. β", "Semi-partial R²"]:
            res[col] = res[col].apply(_f3)

        # Model-level statistics (3 decimals)
        stats = {
            "N": f"{int(model.nobs)}",
            "R²": f"{model.rsquared:.3f}",
            "Adj. R²": f"{model.rsquared_adj:.3f}"
        }

        return res, stats


def ols(formula: str, data: pd.DataFrame) -> sunlm_model:
    return sunlm_model(formula, data)