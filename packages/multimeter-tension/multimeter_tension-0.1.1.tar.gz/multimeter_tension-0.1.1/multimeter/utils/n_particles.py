# n_particles.py

import numpy as np
from scipy.stats import norm, kstest, probplot, anderson
from scipy.special import erfcinv
from scipy.linalg import sqrtm

def calculate_R_CM(vectors):
    num_vectors = len(vectors)
    R_CM = np.sum(vectors, axis=0) / num_vectors
    return R_CM

def construct_K(vectors):
    num_vectors = len(vectors)

    R_CM = calculate_R_CM(vectors)

    K_xx = np.sum((vectors[:, 0] - R_CM[0]) ** 2)
    K_yy = np.sum((vectors[:, 1] - R_CM[1]) ** 2)
    K_xy = np.sum((vectors[:, 0] - R_CM[0]) * (vectors[:, 1] - R_CM[1]))
    K_yx = K_xy
    K = np.array([[K_xx, K_xy], [K_yx, K_yy]])
    return K

def compute_inertia_tensor_cm(positions, masses):
    """
    Compute the inertia tensor relative to the center of mass (CM).
    
    Parameters:
    positions : np.ndarray
        Array of shape (N, 3) containing the positions of N particles.
    masses : np.ndarray
        Array of shape (N,) containing the masses of the N particles.
    
    Returns:
    I_cm : np.ndarray
        The 3x3 inertia tensor relative to the center of mass.
    """
    # Compute the total mass
    M = np.sum(masses)
    
    # Compute the center of mass
    R_cm = np.sum(masses[:, np.newaxis] * positions, axis=0) / M
    
    # Compute the positions relative to the center of mass
    rel_positions = positions - R_cm
    
    # Initialize the inertia tensor
    I_cm = np.zeros((2, 2))
    
    # Compute the inertia tensor relative to CM
    for i in range(len(masses)):
        m = masses[i]
        x, y = rel_positions[i]
        
        I_cm[0, 0] += m * (y**2)
        I_cm[1, 1] += m * (x**2)
        
        I_cm[0, 1] -= m * x * y
    
    # Exploit symmetry: I_ji = I_ij
    I_cm[1, 0] = I_cm[0, 1]
    
    return I_cm

def W_ij(diff_mean_i, diff_mean_j, cov_i, cov_j,n_samples):
    
    # Covariance matrices
    #Sigma_X = cov_i
    #Sigma_Y = cov_j 

    # Matrix A (can be arbitrary)
    A = np.dot(sqrtm(np.linalg.inv(cov_i)),sqrtm(np.linalg.inv(cov_j))) #np.random.randn(d, d)  # Random matrix as an example

    # Sampling
    X = np.random.multivariate_normal(diff_mean_i, cov_i, size=n_samples).T  # Shape: (d, n_samples)
    Y = np.random.multivariate_normal(diff_mean_j, cov_j, size=n_samples).T  # Shape: (d, n_samples)

    # Compute W for each sample
    W = np.zeros(n_samples)  # Initialize W
    for i in range(n_samples):
        W[i] = np.dot(X[:, i], np.dot(A, Y[:, i]))  # Shape: (n_samples,)

    return W


def construct_C(vectors):
    L = len(vectors)

    K_xx = np.sum((vectors[:, 0]) ** 2)
    K_yy = np.sum((vectors[:, 1]) ** 2)
    K_xy = np.sum((vectors[:, 0]) * (vectors[:, 1]))
    K_yx = K_xy
    C = np.array([[K_xx, K_xy], [K_yx,K_yy]])/L
    return C