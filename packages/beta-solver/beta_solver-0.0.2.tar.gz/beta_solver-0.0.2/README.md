# beta_solver

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active%20learning-orange.svg)

**beta_solver** is a personal project where I implement Machine Learning algorithms from scratch to understand the mathematics behind the "black box."

I am currently practicing core algorithms, starting with **Linear Regression** using the Normal Equation. As I learn and practice more algorithms, I will update this library to include them.

## 🎯 Project Goal
The goal of this project is not to replace libraries like `scikit-learn`, but to:
1.  **Demystify the math** behind ML algorithms.
2.  **Implement pure Python/Numpy solutions** without high-level wrappers.
3.  **Document my learning journey** in code.

---

# 📐 Current Algorithm
## Linear Regression

Right now, the library solves for the coefficient vector $\beta$ using Linear Algebra:

$$\beta = (X^T X)^{-1} (X^T Y)$$

Where:
* $X$: The input feature matrix.
* $Y$: The target vector.
* $\beta$: The resulting coefficients (Intercept + Slopes).

---
## Logistic Regression
Logistic Regression is implemented using the Gradient Descent optimization technique to minimize the Log Loss function.
The model predicts probabilities using the Sigmoid function:
$$P(Y=1|X) = \sigma(X\beta) = \frac{1}{1 + e^{-X\beta}}$$
Where:
* $X$: The input feature matrix.
* $Y$: The target vector (0 or 1).
* $\beta$: The coefficient vector (Intercept + Slopes).

---

## 🚀 Installation

You can install `beta_solver` using pip:

```bash
pip install beta_solver
```

## 🤝 Contributing
This is a learning repository. If you see a way to optimize the math or make the code cleaner, feel free to open a Pull Request!

## 📄 License
Distributed under the MIT License. See LICENSE for more information.

## 👤 Author
**Abhish Bondre**
GitHub: [abhishbondre](https://github.com/abhishbondre)

