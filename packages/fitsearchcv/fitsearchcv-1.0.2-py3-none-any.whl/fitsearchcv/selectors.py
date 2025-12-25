import numpy as np

def selector_mean(results, metric=None, clip01=True):

    """
    Custom refit selector for higher-is-better metrics bounded in [0, 1]
    (e.g., accuracy, F1, ROC-AUC, average precision).

    Objective:
        0.5 * |mean_train - mean_test| + 0.5 * (1 - mean_test)

    Selects the parameter set that balances generalization stability
    and validation performance.
    """

    if metric is None:
        train_key = "mean_train_score"
        test_key  = "mean_test_score"
    else:
        train_key = f"mean_train_{metric}"
        test_key  = f"mean_test_{metric}"

    if train_key not in results or test_key not in results:
        raise KeyError(f"Missing keys in cv_results_: {train_key}, {test_key}")

    train = np.asarray(results[train_key], dtype=float)
    test  = np.asarray(results[test_key],  dtype=float)

    if clip01:
        train = np.clip(train, 0.0, 1.0)
        test  = np.clip(test,  0.0, 1.0)

    overfit_penalty = np.abs(train - test)
    underfit_penalty = 1.0 - test

    objective = 0.5 * overfit_penalty + 0.5 * underfit_penalty
    objective = np.where(np.isfinite(objective), objective, np.inf)

    return int(np.nanargmin(objective))
