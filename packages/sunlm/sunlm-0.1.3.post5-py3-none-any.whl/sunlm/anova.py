# sunlm_anova.py

import re
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from patsy import build_design_matrices
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from scipy.stats import f as f_dist
from scipy.stats import t as t_dist


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
    return "" if pd.isna(x) else f"{x:.3f}"


def _is_categorical_series(s: pd.Series, max_levels_numeric: int = 10) -> bool:
    """
    SPSS-like heuristic:
    - object/category/bool => categorical
    - integer with few unique levels (e.g., 0/1/2 treatments) => categorical
    - float codes like 0.0/1.0/2.0 with few levels => categorical
    """
    if pd.api.types.is_object_dtype(s) or pd.api.types.is_categorical_dtype(s) or pd.api.types.is_bool_dtype(s):
        return True

    if pd.api.types.is_integer_dtype(s):
        nunique = s.nunique(dropna=True)
        return 2 <= nunique <= max_levels_numeric

    if pd.api.types.is_float_dtype(s):
        vals = s.dropna().unique()
        if len(vals) == 0:
            return False
        near_int = (abs(vals - vals.round()) < 1e-9).all()
        if near_int:
            nunique = pd.Series(vals.round()).nunique()
            return 2 <= nunique <= max_levels_numeric

    return False


def _upgrade_bare_C_to_sum(rhs: str) -> str:
    """
    Convert C(x) -> C(x, Sum) but keep:
      - C(x, Something) unchanged
      - C(x, Sum) unchanged
    """
    pattern = r"C\(\s*([A-Za-z_]\w*)\s*\)"
    return re.sub(pattern, r"C(\1, Sum)", rhs)


def _auto_sum_code_formula(
    formula: str,
    data: pd.DataFrame,
    *,
    max_levels_numeric: int = 10,
    force_categorical: list[str] | None = None,
    exclude_categorical: list[str] | None = None,
) -> str:
    """
    SPSS-like behavior:
    1) Upgrade bare C(x) to C(x, Sum)
    2) For categorical predictors written as plain x on RHS, rewrite to C(x, Sum)
    """
    if "~" not in formula:
        raise ValueError("Formula must contain '~' (e.g., 'y ~ x1 + x2').")

    force_categorical = set(force_categorical or [])
    exclude_categorical = set(exclude_categorical or [])

    lhs, rhs = formula.split("~", 1)
    lhs, rhs = lhs.strip(), rhs.strip()

    # (1) If user wrote C(x) without contrast, treat it as Sum coding
    rhs = _upgrade_bare_C_to_sum(rhs)

    # detect categorical columns
    cat_cols = []
    for col in data.columns:
        if col in exclude_categorical:
            continue
        if col in force_categorical:
            cat_cols.append(col)
            continue
        if _is_categorical_series(data[col], max_levels_numeric=max_levels_numeric):
            cat_cols.append(col)

    # replace longer names first to avoid partial overlaps
    for col in sorted(cat_cols, key=len, reverse=True):
        # already coded?
        if re.search(rf"C\(\s*{re.escape(col)}\s*(,|\))", rhs):
            continue
        # replace standalone token occurrences only
        pattern = rf"(?<![\w\.]){re.escape(col)}(?![\w\.])"
        rhs = re.sub(pattern, f"C({col}, Sum)", rhs)

    return f"{lhs} ~ {rhs}"


def _pretty_source_name(src: str) -> str:
    """
    Make Source names SPSS-like:
    - C(x, Sum)            -> x (factor)
    - C(x, Sum):C(y, Sum)  -> x × y
    """
    if src in ["Corrected Model", "Intercept", "Error", "Total", "Corrected Total"]:
        return src

    if ":" in src:
        parts = src.split(":")
        clean = []
        for p in parts:
            p = re.sub(r"C\(\s*(\w+)\s*,\s*Sum\s*\)", r"\1", p)
            clean.append(p)
        return " × ".join(clean)

    src = re.sub(r"C\(\s*(\w+)\s*,\s*Sum\s*\)", r"\1 (factor)", src)
    return src


class sunlm_anova_model:
    """
    SPSS-like ANOVA:
      - Type III SS
      - Sum(effect) coding by default (C(x, Sum))
      - Bare C(x) is upgraded to C(x, Sum)
      - SPSS-like table rows (Corrected Model / Error / Total / Corrected Total)
      - 3-decimal formatting + tagged p-values
      - Pretty Source names (factor / ×)

    Notes on Bonferroni (SPSS-like EMMs):
      Pairwise comparisons are conducted using Bonferroni-adjusted tests based on
      estimated marginal means (EMMs), following the SPSS UNIANOVA procedure.
      Continuous covariates are held constant at their overall sample means.
      For categorical factors other than the target factor, EMMs are computed using
      equal weighting across factor levels (i.e., equal cell weights), regardless of
      observed cell sizes. Standard errors of mean differences are derived using the
      model-based covariance matrix of parameter estimates.
    """

    def __init__(
        self,
        formula: str,
        data: pd.DataFrame,
        *,
        max_levels_numeric: int = 10,
        force_categorical: list[str] | None = None,
        exclude_categorical: list[str] | None = None,
    ):
        self.formula_original = formula
        self.data = data

        self.formula = _auto_sum_code_formula(
            formula,
            data,
            max_levels_numeric=max_levels_numeric,
            force_categorical=force_categorical,
            exclude_categorical=exclude_categorical,
        )

        # IMPORTANT: formula API preserves design_info required for typ=3
        self.fit = smf.ols(self.formula, data=self.data).fit()
        self.anova_table = anova_lm(self.fit, typ=3)

    def _spss_like_table(self) -> pd.DataFrame:
        a = self.anova_table.copy()

        resid_name = next((idx for idx in a.index if str(idx).lower() in ["residual", "resid"]), "Residual")
        ss_error = float(a.loc[resid_name, "sum_sq"])
        df_error = float(a.loc[resid_name, "df"])
        ms_error = ss_error / df_error if df_error else np.nan

        n = int(self.fit.nobs)
        ss_corrected_total = float(self.fit.centered_tss)      # SPSS "Corrected Total"
        ss_total = float(self.fit.uncentered_tss)              # SPSS "Total"
        ss_corrected_model = float(self.fit.ess)               # SPSS "Corrected Model"
        df_model = float(self.fit.df_model)
        ms_model = ss_corrected_model / df_model if df_model else np.nan
        F_model = (ms_model / ms_error) if (ms_error and not np.isnan(ms_error)) else np.nan
        p_model = f_dist.sf(F_model, df_model, df_error) if not np.isnan(F_model) else np.nan

        def _pes(ss):
            return ss / (ss + ss_error) if (ss_error + ss) != 0 else np.nan

        rows = []

        rows.append({
            "Source": "Corrected Model",
            "sum_sq": ss_corrected_model,
            "df": df_model,
            "mean_sq": ms_model,
            "F": F_model,
            "p_value_raw": p_model,
            "Partial Eta Squared": _pes(ss_corrected_model),
        })

        for idx in a.index:
            if idx == resid_name:
                continue

            ss = float(a.loc[idx, "sum_sq"])
            df = float(a.loc[idx, "df"])
            ms = ss / df if df else np.nan
            Fv = float(a.loc[idx, "F"]) if "F" in a.columns else np.nan
            pv = float(a.loc[idx, "PR(>F)"]) if "PR(>F)" in a.columns else np.nan

            rows.append({
                "Source": str(idx),
                "sum_sq": ss,
                "df": df,
                "mean_sq": ms,
                "F": Fv,
                "p_value_raw": pv,
                "Partial Eta Squared": _pes(ss),
            })

        rows.append({
            "Source": "Error",
            "sum_sq": ss_error,
            "df": df_error,
            "mean_sq": ms_error,
            "F": np.nan,
            "p_value_raw": np.nan,
            "Partial Eta Squared": np.nan,
        })

        rows.append({
            "Source": "Total",
            "sum_sq": ss_total,
            "df": float(n),
            "mean_sq": np.nan,
            "F": np.nan,
            "p_value_raw": np.nan,
            "Partial Eta Squared": np.nan,
        })

        rows.append({
            "Source": "Corrected Total",
            "sum_sq": ss_corrected_total,
            "df": float(n - 1),
            "mean_sq": np.nan,
            "F": np.nan,
            "p_value_raw": np.nan,
            "Partial Eta Squared": np.nan,
        })

        out = pd.DataFrame(rows)

        # Pretty Source names
        out["Source"] = out["Source"].apply(_pretty_source_name)

        # Format columns to 3 decimals like SPSS, and apply tagged p-values
        out["sum_sq"] = out["sum_sq"].apply(_f3)
        out["df"] = out["df"].apply(lambda x: "" if pd.isna(x) else f"{x:.0f}")
        out["mean_sq"] = out["mean_sq"].apply(_f3)
        out["F"] = out["F"].apply(_f3)

        out["p-value"] = out["p_value_raw"].apply(lambda p: "" if pd.isna(p) else _format_p_value(float(p)))
        out.drop(columns=["p_value_raw"], inplace=True)

        out["Partial Eta Squared"] = out["Partial Eta Squared"].apply(_f3)

        out = out[["Source", "sum_sq", "df", "mean_sq", "F", "p-value", "Partial Eta Squared"]]
        return out

    def summary(self):
        print("## Tests of Between-Subjects Effects")
        print(f"Dependent Variable: {self.fit.model.endog_names}")
        print(self._spss_like_table().to_string(index=False))
        print(f"\nR Squared = {self.fit.rsquared:.3f} (Adjusted R Squared = {self.fit.rsquared_adj:.3f})")

    def TukeyHSD(self, factor: str = None, *, which: str = None, alpha: float = 0.05):
        if factor is None and which is None:
            raise ValueError("Specify factor via positional argument or which='factor'.")

        factor_name = factor if factor is not None else which
        y_name = self.fit.model.endog_names

        if factor_name not in self.data.columns:
            raise ValueError(f"Factor '{factor_name}' not found in data.")

        tukey = pairwise_tukeyhsd(
            endog=self.data[y_name],
            groups=self.data[factor_name],
            alpha=alpha
        )

        mse = float(self.fit.mse_resid)

        groups = tukey.groupsunique
        group_sizes = {g: int((self.data[factor_name] == g).sum()) for g in groups}

        i_idx, j_idx = tukey._multicomp.pairindices

        rows = []
        for k in range(len(tukey.meandiffs)):
            g1 = groups[i_idx[k]]
            g2 = groups[j_idx[k]]
            n1 = group_sizes[g1]
            n2 = group_sizes[g2]
            se = np.sqrt(mse * (1.0 / n1 + 1.0 / n2))

            rows.append({
                "group1": g1,
                "group2": g2,
                "meandiff": float(tukey.meandiffs[k]),
                "Std. Error": float(se),
                "p-value": float(tukey.pvalues[k]),
                "lower": float(tukey.confint[k, 0]),
                "upper": float(tukey.confint[k, 1]),
            })

        df = pd.DataFrame(rows)

        for col in ["meandiff", "Std. Error", "lower", "upper"]:
            df[col] = df[col].apply(_f3)

        df["p-value"] = df["p-value"].apply(_format_p_value)

        print(f"\n## Tukey HSD for {factor_name} (alpha={alpha})")
        print(df.to_string(index=False))

    def Bonferroni(self, factor: str = None, *, which: str = None, alpha: float = 0.05):
        """
        SPSS-like EMM Bonferroni pairwise comparisons.

        Note. Pairwise comparisons were conducted using Bonferroni-adjusted tests
        based on estimated marginal means (EMMs), following the SPSS UNIANOVA procedure.
        Continuous covariates were held constant at their overall sample means.
        For categorical factors other than the target factor, EMMs were computed using
        equal weighting across factor levels (i.e., equal cell weights), regardless of
        the observed cell sizes. Standard errors of mean differences were derived using
        the model-based covariance matrix of parameter estimates. P values were adjusted
        using the Bonferroni correction.
        """
        if factor is None and which is None:
            raise ValueError("Specify factor via positional argument or which='factor'.")

        factor_name = factor if factor is not None else which
        y_name = self.fit.model.endog_names

        if factor_name not in self.data.columns:
            raise ValueError(f"Factor '{factor_name}' not found in data.")

        # levels of target factor
        levels = pd.Series(self.data[factor_name]).dropna().unique()
        levels = np.array(sorted(levels, key=lambda x: str(x)))

        # model pieces
        design_info = self.fit.model.data.design_info
        params = self.fit.params.values
        covb = np.asarray(self.fit.cov_params())
        df_error = float(self.fit.df_resid)

        rhs = self.formula.split("~", 1)[1]

        # categorical vars mentioned as C(x, Sum) on RHS
        cat_vars = re.findall(r"C\(\s*([A-Za-z_]\w*)\s*,\s*Sum\s*\)", rhs)
        cat_vars = list(dict.fromkeys(cat_vars))
        other_factors = [v for v in cat_vars if v != factor_name]

        # covariates: numeric & NOT categorical & appears on RHS
        cov_means = {}
        for col in self.data.columns:
            if col == y_name or col == factor_name:
                continue
            s = self.data[col]
            if pd.api.types.is_numeric_dtype(s) and (not _is_categorical_series(s)):
                if re.search(rf"(?<![\w\.]){re.escape(col)}(?![\w\.])", rhs):
                    cov_means[col] = float(s.mean())

        # equal-weights grid for other factors
        factor_levels = {}
        for v in other_factors:
            lv = pd.Series(self.data[v]).dropna().unique()
            factor_levels[v] = np.array(sorted(lv, key=lambda x: str(x)))

        def _make_equal_weight_grid(target_level):
            if len(other_factors) == 0:
                grid = pd.DataFrame({factor_name: [target_level]})
            else:
                prod = pd.MultiIndex.from_product(
                    [factor_levels[v] for v in other_factors],
                    names=other_factors
                ).to_frame(index=False)
                grid = prod.copy()
                grid[factor_name] = target_level

            # ensure all columns exist for design-matrix building
            base = self.data.iloc[0:1].copy()
            for c, m in cov_means.items():
                base[c] = m

            for col in self.data.columns:
                if col == y_name:
                    continue
                if col not in grid.columns:
                    grid[col] = base.iloc[0][col]

            for c, m in cov_means.items():
                grid[c] = m

            return grid

        def _L_mu_se_for_level(lv):
            grid = _make_equal_weight_grid(lv)
            X = build_design_matrices([design_info], grid, return_type="dataframe")[0].to_numpy()
            L = X.mean(axis=0)  # equal weights across other-factor levels
            mu = float(L @ params)
            var = float(L @ covb @ L.T)
            se = np.sqrt(max(var, 0.0))
            return L, mu, se

        Lvec, emm = {}, {}
        for lv in levels:
            L, mu, _ = _L_mu_se_for_level(lv)
            Lvec[lv], emm[lv] = L, mu

        m_tests = int(len(levels) * (len(levels) - 1) / 2)
        tcrit = float(t_dist.ppf(1 - (alpha / (2 * m_tests)), df_error)) if m_tests > 0 else np.nan

        rows = []
        for i in range(len(levels)):
            for j in range(i + 1, len(levels)):
                g1, g2 = levels[i], levels[j]
                Ld = (Lvec[g2] - Lvec[g1])

                diff = float(emm[g2] - emm[g1])  # group2 - group1
                var_d = float(Ld @ covb @ Ld.T)
                se_d = np.sqrt(max(var_d, 0.0))

                tval = diff / se_d if se_d != 0 else np.nan
                p_raw = 2 * t_dist.sf(abs(tval), df_error) if not np.isnan(tval) else np.nan
                p_adj = min(p_raw * m_tests, 1.0) if not pd.isna(p_raw) else np.nan

                lower = diff - tcrit * se_d if not np.isnan(tcrit) else np.nan
                upper = diff + tcrit * se_d if not np.isnan(tcrit) else np.nan

                rows.append({
                    "group1": g1,
                    "group2": g2,
                    "meandiff": diff,
                    "Std. Error": se_d,
                    "t": tval,
                    "p-value": p_adj,
                    "lower": lower,
                    "upper": upper,
                })

        df_out = pd.DataFrame(rows)

        for col in ["meandiff", "Std. Error", "t", "lower", "upper"]:
            df_out[col] = df_out[col].apply(_f3)

        df_out["p-value"] = df_out["p-value"].apply(lambda p: "" if pd.isna(p) else _format_p_value(float(p)))

        print(f"\n## Bonferroni Pairwise Comparisons for {factor_name} (alpha={alpha})")
        print(df_out.to_string(index=False))


def aov(
    formula: str,
    data: pd.DataFrame,
    *,
    max_levels_numeric: int = 10,
    force_categorical: list[str] | None = None,
    exclude_categorical: list[str] | None = None,
) -> sunlm_anova_model:
    return sunlm_anova_model(
        formula,
        data,
        max_levels_numeric=max_levels_numeric,
        force_categorical=force_categorical,
        exclude_categorical=exclude_categorical,
    )