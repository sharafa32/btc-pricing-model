\# =========================================================

\# v2 Bitcoin Valuation Model: Comprehensive Research Log

\# =========================================================

\#

\# PHASE 1: ENVIRONMENT SETUP \& DATA INGESTION

\# Issue: Broken laptop resulted in total loss of local Git state and virtual environment.

\# Options: 1) Extract hard drive from broken laptop. 2) Rebuild pipeline from scratch.

\# Decision: Rebuild from scratch using final v1 scripts provided by AI.

\# Techniques: Python `venv`, Git init, `requests` API integration, `pandas` merge.

\#

\# Issue: Python and Git not recognized in PowerShell on new laptop.

\# Decision: Installed Python and Git via Windows `winget` package manager.

\#

\# Issue: PowerShell execution policy blocked virtual environment activation script.

\# Decision: Ran `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.

\#

\# Issue: Google Trends API (`pytrends`) only returned 23 rows (monthly data) instead of daily.

\# Decision: Changed `timeframe` parameter to a specific date range. Forward-filled the monthly buckets into daily data.

\#

\# Issue: Merged DataFrame had a 0 or NaN in `btc\_price` causing `log(0)` = -inf, resulting in a deviation minimum of -86.

\# Decision: Cleaned price data using `.replace(0, np.nan).ffill()` before applying the log transformation.

\#

\# PHASE 2: FEATURE ENGINEERING \& STATISTICAL FILTERING

\# Issue: Raw trending data (Active Addresses, Network Difficulty) cannot be fed to tree-based models.

\# Options: 1) Log-difference (daily % change). 2) 30-day Z-scores. 3) First-difference.

\# Decision: Used 30-day Z-scores for adoption/flow metrics to capture momentum, and 30-day % changes for macro rates.

\# Techniques: `pandas` rolling windows (`.rolling(30).mean()` / `.std()`).

\#

\# Issue: `dropna()` deleted all pre-2020 data because `futures\_open\_interest` and `etf\_flows\_usd` didn't exist then.

\# Decision: Filled non-existent historical features with 0 (economically accurate) \*before\* running `dropna()`.

\#

\# Issue: Need to filter 25 factors down to a statistically significant set while avoiding multicollinearity.

\# Options: 1) Univariate testing (Granger). 2) Multivariate testing (OLS). 3) Penalized regression (LASSO).

\# Decision: Used Granger Causality (5-day lag) with Benjamini-Hochberg FDR correction as a 1-on-1 bouncer, then LASSO as the multivariate referee.

\# Techniques: `statsmodels.tsa.stattools.grangercausalitytests`, `statsmodels.stats.multitest.multipletests`, `sklearn.linear\_model.LassoCV`.

\#

\# Issue: Granger kept MVRV, MVRV-Z, and Supply-in-Profit, but LASSO dropped them to 0.000 coefficient when differenced.

\# Discovery: These ratios contained target leakage (today's Bitcoin price was in their calculation). The model was cheating.

\# Decision: Permanently dropped all price-derived on-chain ratios. Kept Google Trends (70% influence) and Puell Multiple (30% influence) as the only true exogenous linear predictors.

\#

\# PHASE 3: REGIME CLASSIFICATION (HMM)

\# Issue: Need to mathematically classify market regimes (Bull, Bear, Chop) instead of guessing.

\# Options: 1) Hardcoded rules (e.g., 200-day moving average). 2) Hidden Markov Models (HMM). 3) Jump-Diffusion models.

\# Decision: Used Gaussian HMM.

\# Techniques: `hmmlearn.hmm.GaussianHMM`.

\#

\# Issue: How many regimes to use?

\# Options: 2, 3, 4, 5, or 6 states.

\# Decision: Ran AIC/BIC scoring across all options. Chose 4 regimes as the mathematical "elbow" to prevent overfitting.

\#

\# Issue: Hard labels (0,1,2,3) create artificial cliffs where the market is in a gray area.

\# Decision: Extracted `predict\_proba` (soft probabilities) to feed smooth probability distributions to XGBoost.

\#

\# PHASE 4: XGBOOST \& THE RANDOM WALK TRAP

\# Issue: First XGBoost run hit 0.99 R-squared in training.

\# Options: 1) Accept the model as a massive success. 2) Audit for lookahead bias/cheat codes.

\# Decision: Audited and found the model was using `deviation\_lag1` (yesterday's price) to predict today's price.

\# Techniques: Shifted target to 30-day forward average deviation (`.shift(-30).rolling(30).mean()`) to kill the cheat code.

\#

\# PHASE 5: THE STRUCTURAL BREAK \& LOOKAHEAD AUDIT

\# Issue: 30-day forward model failed catastrophically out-of-sample (Test R-squared = -4.36). Model predicted flat while price went up.

\# Root cause: 2023-2024 ETF regime shift. Retail metrics were flat, but institutional ETFs drove the price.

\# Decision: Added `etf\_flows\_usd` to the XGBoost feature matrix.

\#

\# Issue: After adding ETF flows, model suddenly hit 0.31 R-squared out-of-sample. Too good to be true?

\# Decision: Brutal audit of the pipeline.

\# Discovery: Lookahead bias! HMM (`predict\_proba` on full dataset) and Symbolic Regression were trained on the entire dataset, using future data to classify the past.

\# Fix: Re-fit HMM and Sym Reg \*strictly\* on training data (pre-2023). Used `.predict()` on the test set.

\# Result: R-squared dropped back to -0.32, but RMSE (0.471) still beat the Power Law Benchmark (0.517).

\#

\# PHASE 6: SYMBOLIC REGRESSION (LAYER 1 REPLACEMENT)

\# Goal: Replace hardcoded Power Law with dynamically discovered math.

\# Options: 1) Neural Networks (LSTMs). 2) PySR (Symbolic Regression).

\# Decision: Used PySR (Julia backend) because LSTMs overfit and can't extrapolate exponential trends with only 4,900 rows of data.

\# Techniques: `pysr.PySRRegressor`, Julia compilation.

\#

\# Issue: Unconstrained PySR run 1 discovered a cubic polynomial (`0.0000003968 \* Days^3`). When extrapolated to 2026, it exploded and predicted $13,371.

\# Issue: Unconstrained PySR run 2 discovered a linear equation. It predicted negative prices for Bitcoin's first 3,000 days.

\# Options: 1) Abandon PySR entirely. 2) Constrain PySR with Bitcoin's economic laws.

\# Decision: Constrained PySR. Fed it `log(Days)` as input and `log(Price)` as target. Banned `exp` operator to prevent explosions. Kept `log` and `sqrt` to force decelerating growth.

\# Result: PySR independently discovered a Reciprocal Logarithmic S-Curve: `log(Price) = 58.0 - 405.26 / log(Days)`.

\#

\# Issue: Is this new equation actually better than the Power Law?

\# Decision: Ran Layer 1 Audit on 2023-2024 test set.

\# Result: Constrained SR RMSE (0.3545) halved the Power Law RMSE (0.7929). Proven mathematically superior.

\#

\# PHASE 7: ARCHITECTURAL DEBATES (THEORETICAL)

\# Debate 1: Kalman Filter. Should we use it to dynamically adjust the trend line based on recent errors?

\# Options: 1) Add Kalman Filter to Layer 1. 2) Add to Layer 2. 3) Reject.

\# Decision: Rejected. It is univariate (blind to fundamentals), creates "Too Many Cooks" problem (Layer 1 and Layer 2 fight over prediction space), and resurrects the Random Walk trap.

\#

\# Debate 2: Feeding errors back into PySR.

\# Options: 1) Accept static Gen 1 baseline. 2) Build Boosted Symbolic Regression (Gen 2).

\# Decision (Pending): Proposed Gen 2 Boosted SR (using PySR to evolve an equation that predicts the residuals of Gen 1).

\#

\# PHASE 8: ENVIRONMENT MANAGEMENT \& DEPENDENCIES

\# Issue: NumPy version conflict with `shap`/`numba` causing kernel crashes (Numba needs NumPy < 2.5).

\# Decision: Downgraded NumPy to `<2.5` via pip and restarted Jupyter kernel.

\#

\# Issue: Julia compilation phase freezing Jupyter during PySR initialization.

\# Decision: Pre-compiled PySR backend in PowerShell interactive Python (`>>>`) using a dummy dataset `(\[\[1]], \[1])` before running in Jupyter.

\# =========================================================

