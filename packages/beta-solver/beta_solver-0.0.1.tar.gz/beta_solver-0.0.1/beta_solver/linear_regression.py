import numpy as np

def multiply_matrices(matrix1, matrix2):
    """
    Multiplies two matrices.

    :param matrix1: First matrix
    :param matrix2: Second matrix
    :return: The product of the two matrices
    """
    rows1, cols1 = matrix1.shape
    rows2, cols2 = matrix2.shape

    # Check if multiplication is possible (cols1 == rows2)
    if cols1 != rows2:
        raise ValueError("Incompatible dimensions for matrix multiplication.")

    # Initialize the result matrix with zeros
    result = np.zeros((rows1, cols2))

    # Perform matrix multiplication manually
    for i in range(rows1):
        for j in range(cols2):
            for k in range(cols1):
                result[i, j] += matrix1[i, k] * matrix2[k, j]

    return result


def transpose_matrix(matrix):
    """
    Transposes a matrix.

    :param matrix: Input matrix
    :return: Transposed matrix
    """
    rows, cols = matrix.shape
    transposed = np.zeros((cols, rows))

    for i in range(rows):
        for j in range(cols):
            transposed[j, i] = matrix[i, j]
    return transposed


# Function to compute the inverse of an m x m matrix
def compute_inverse(matrix):
    # Check if the matrix is square (m x m)
    rows, cols = matrix.shape
    if rows != cols:
        return "Matrix is not square, cannot compute inverse."

    # Try to compute the inverse using NumPy
    try:
        inverse_matrix = np.linalg.inv(matrix)
        return inverse_matrix
    except np.linalg.LinAlgError:
        return "Matrix is not invertible (determinant is zero)."

def linear_regression(X, y):
    """
    Solves for beta using the Normal Equation:
    beta = (X^T * X)^-1 * (X^T * Y)
    :param X: The arrays of independent variable
    :param y: The array of dependent variable
    :return: slope, intercept
    """
    # 1. Add Intercept (Column of 1s)
    x_bias = np.insert(X, 0, 1, axis=1)

    # 2. Transpose X
    x_transposed = transpose_matrix(x_bias)

    # 3. Calculate X^T * X
    xt_x = multiply_matrices(x_transposed, x_bias)

    # 4. Calculate Inverse: (X^T * X)^-1
    xt_x_inv = compute_inverse(xt_x)

    # 5. Calculate X^T * Y
    y_alter = y.reshape(-1, 1)  # Ensure y is a column vector
    xt_y = multiply_matrices(x_transposed, y_alter)

    # 6. Final Calculation: (X^T * X)^-1 * (X^T * Y)
    beta = multiply_matrices(xt_x_inv, xt_y)

    return beta
