# Overview
This Library provides a comprehensive framework for testing the fundamental assumptions of linear regression models. It implements automated diagnostic tools to check whether your regression model meets the statistical requirements necessary for valid inference and prediction.
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
---

## 📌 Purpose

Linear regression relies on several statistical assumptions (linearity, normality, homoscedasticity, independence, etc.). Many students and early researchers struggle with:

* Knowing **which tests** to apply
* Guide for interpreting **statistical results**
* Presenting **clear diagnostics and plots**

**AssumpHelper** addresses these challenges by offering a structured, reusable workflow that checks regression assumptions and explains the results in a clear and organized way.

---

## ✨ Features

* Automated **linear regression assumption testing**
* Built‑in **statistical tests** with interpretation guides
* **Visualization support** for diagnostics
* Beginner‑friendly design with clear outputs
* Modular structure for easy extension
* Suitable for academic, research, and learning purposes

### Supported Assumption Checks

* **Linearity** (e.g., Ramsey RESET Test)
* **Homoscedasticity** (Breusch–Pagan Test)
* **Normality of Residuals** (Shapiro–Wilk Test)
* **Independence of Errors** (Durbin–Watson Test)

---

## 📂 Project Structure

```
AssumpHelper/
│
├── assumphelper/
│   ├── __init__.py
│   ├── check.py
│   ├── exceptions.py
│   ├── hypothesis.py
│   ├── utilities.py
│   │
│   ├── linearity.py
│   ├── normality.py
│   ├── homoscedasticity.py
│   ├── independence.py
│   │
│   ├── linplot_interpretation_guide.txt
│   ├── normplot_interpretation_guide.txt
│   ├── homplot_interpretation_guide.txt
│   └── indepplot_interpretation_guide.txt
│
├── DOCS/
│   ├── examples/
│   │   └── examples.ipynb
│   │
│   └── tests/
│       └── test_assumphelper_assert_errors.ipynb
│
├── README.md
├── requirements.txt
├── setup.py
└── .gitignore
```

---

## ⚙️ Installation

Install the required packages using pip:

```bash
pip install assumphelper
```

---

## 🚀 Sample Usage

```python
import numpy as np
from sklearn.linear_model import LinearRegression
import assumphelper as ah

np.random.seed(42)

# Generate clean linear data
n = 100
X = np.linspace(1, 50, n).reshape(-1, 1)
y = 2.5 * X.ravel() + 15 + np.random.normal(0, 2, n)

#Checking Linearity
model = LinearRegression()

linearity = ah.Linearity(model, X, y)
linearity.fit()
linearity.test()
```
RESET Test for Linearity
F-statistic: 5.2888      p-value: 0.0710

Interpretation:


If alpha = 0.05 and p-value > 0.05: Assumption of Linearity is NOT VIOLATED.
```python
linearity.plot()
```
<img width="859" height="678" alt="image" src="https://github.com/user-attachments/assets/ebef0c33-fca4-4b1f-853c-73720fe33039" />
Interpretation Guide:

Linearity Plot (Residuals vs Fitted Values)

If the plot shows a random scatter of points around the horizontal axis with no clear curve, the relationship between the predictors and the outcome is linear.
> The assumption of linearity is NOT VIOLATED.

If the plot shows a curve or systematic pattern in the scatter of points, the relationship between the predictors and the outcome is not linear.
> The assumption of linearity is VIOLATED.

Always double check with the RESET test.
(<Figure size 800x600 with 1 Axes>,
 <Axes: title={'center': 'Residuals vs Fitted Plot'}, xlabel='Fitted Values', ylabel='Residuals'>)
---

## 📊 Outputs

AssumpHelper provides:

* Test statistics and their p‑values
* Plain‑language interpretation (Pass / Violation)
* Diagnostic plots (residuals vs fitted, Q‑Q plots, etc.)
* Structured interpretation guides for reports and presentations

---

## 🎓 Intended Users

* Students learning **linear regression**
* Beginners who want clarity without losing rigor

---

## 🧠 Inspiration

This project is inspired by common regression workflows in:

* Statistics & Econometrics courses
* Python libraries such as `statsmodels` and `scikit‑learn`
* The need for **simpler interpretation** of assumption tests

---

## 🔧 Requirements

* Python **3.7+**
* numpy
* pandas
* scipy
* statsmodels
* matplotlib
* seaborn

(See `requirements.txt` for the full list.)


---

## 📜 License

This project is released under the **MIT License**.

---

## 👤 Author

# Developers
**[Kirsten Roise G. Moog]** 

Our distinguish Leader &  Inceptionist & Structural Design 

**[Rodel P. Badilla]**

Our Assistant Leader
# Leaders Roles
- Designed clean separation of concerns  
- Implementing codes engine  
- Created visualization tools
- Enhanced plotting capabilities 

**[Hannah Dennisse Y. Aque]**

**[James Walte C. Prollo]**

**[Zell Caamino]**

# Roles

Back (support)
- Built comprehensive test suite  
- Wrote user documentation.
- Quality assurance

Note: This diagnostic framework helps ensure the validity of your regression analysis by systematically checking fundamental statistical assumptions. Regular use of these tools will improve the reliability and interpretability of your regression models.


