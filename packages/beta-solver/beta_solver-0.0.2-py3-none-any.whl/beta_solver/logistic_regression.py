import numpy as np

def sigmoid(z):
    """
    Sigmoid activation function.

    :param z: Input value or array
    :return: Sigmoid of the input
    """
    return 1 / (1 + np.exp(-z))

def logistic_regression(X, y, learning_rate=0.01, iterations=1000):
    """
    Implements logistic regression using gradient descent.

    :param X: Feature matrix of shape (m, n)
              (m = number of samples, n = number of features)
    :param y: Target vector of shape (m,) containing 0s and 1s
    :param learning_rate: Step size for gradient descent (default 0.01)
    :param iterations: Number of times to run the training loop
    :return: Learned parameters w (weights) and b (bias)
    """

    # m is the number of observations (rows)
    # n is the number of features (columns)
    m, n = X.shape

    # --- 1. Initialization ---
    # Start with weights (w) and bias (b) at 0.
    w = np.zeros(n)
    b = 0.0

    # --- 2. Gradient Descent Loop ---
    for i in range(iterations):

        # --- A. Forward Pass (Prediction) ---
        # Calculate the linear equation: z = w1*x1 + w2*x2 + ... + b
        z = np.dot(X, w) + b

        # Apply the Sigmoid activation function to squash z between 0 and 1
        # y_pred represents the probability that y=1
        y_pred = sigmoid(z)

        # --- B. Backward Pass (Gradient Calculation) ---
        # Calculate how "wrong" the predictions were
        error = y_pred - y

        # Calculate gradient for weights (dw):
        # Formula: (1/m) * sum(error * x)
        dw = (1 / m) * np.dot(X.T, error)

        # Calculate gradient for bias (db):
        # Formula: (1/m) * sum(error)
        db = (1 / m) * np.sum(error)

        # --- C. Update Parameters ---
        # Adjust weights and bias in the opposite direction of the gradient
        # to minimize the error (Loss).
        w = w - learning_rate * dw
        b = b - learning_rate * db

    return w, b