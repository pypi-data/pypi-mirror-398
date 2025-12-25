# **FitSearchCV**— A smarter `refit` selector for scikit-learn searches

`selector-mean` is a tiny utility that helps reduce **overfitting** and **underfitting** when tuning hyperparameters with scikit-learn’s `GridSearchCV` or `RandomizedSearchCV`.

It provides a single function:

- **`selector_mean(cv_results_, metric=None, use_abs_gap=True, clip01=True)`**  
  A callable you pass to `refit=...` that picks the parameter set balancing **high test performance** and **small train–test gap**.

---

<img width="1112" height="886" alt="Train AccuracyTest Accuracy Poor Generalization Overfitting" src="https://github.com/user-attachments/assets/fe175fa7-1e97-44a2-bf29-4d6684ecd0d3" />  
   
   
   
<img width="1191" height="841" alt="Train AccuracyTest Accuracy Poor Generalization Overfitting (1)" src="https://github.com/user-attachments/assets/16809770-f807-443f-8eb8-9765934c47bf" />


## Best Use cases

- accuracy_score

- balanced_accuracy_score

- precision_score (binary, micro, macro, weighted)

- recall_score (binary, micro, macro, weighted)

- f1_score (binary, micro, macro, weighted)

- roc_auc_score

- average_precision_score

- jaccard_score

---

## Why?

Vanilla `GridSearchCV` usually selects the highest mean test score, which can sometimes favor models with high variance.  
Here, `test` refers to as `validation accuracy`.  
`selector_mean` instead minimizes: `((|train - test|) + (1 - test))/2`  
This prevents both underfittnig and overfitting. 

`|train-test|` is for reducing the gap between train and test accuracy thus decreasing **overfitting**. 

`(1-test)` is for reducing the gap between test accuracy and 1 hence increasing the score thus reducing **underfitting**.

---

## Want to try? 

Just type  
<pre>pip install fitsearchcv</pre>

PyPI link: [PyPI](https://pypi.org/project/fitsearchcv/)

---

## How to Use?

<pre>from fitsearchcv.selectors import selector_mean
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LogisticRegression

lr=LogisticRegression()

param_grid = [
    {'penalty': ['l1'], 'C': [0.1, 1, 10], 'solver': ['liblinear', 'saga']},
    
    {'penalty': ['l2'], 'C': [0.1, 1, 10], 'solver': ['liblinear', 'lbfgs', 'saga', 'sag', 'newton-cg']},
    
    {'penalty': ['elasticnet'], 'C': [0.1, 1, 10], 'solver': ['saga'], 'l1_ratio': [0.0, 0.25, 0.5, 0.75, 1.0]},
    
    {'penalty': [None], 'solver': ['lbfgs', 'sag', 'newton-cg', 'saga']}  
]

grid1=GridSearchCV(estimator=lr,
                   param_grid=param_grid,
                   refit=selector_mean, # added line
                   cv=5, 
                   return_train_score=True,
                   n_jobs=-1)</pre>
