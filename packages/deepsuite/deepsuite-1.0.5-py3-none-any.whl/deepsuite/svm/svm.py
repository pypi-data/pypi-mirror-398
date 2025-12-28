"""Support Vector Machine (SVM).
Classifier utilizing PyTorch and
support vector regression (SVR) principles.
"""

from collections.abc import Callable
from typing import Any

import torch

from deepsuite.svm.kernels import linear_kernel
from deepsuite.utils.device import get_best_device


class SVM:
    """Support Vector Machine (SVM) Classifier.

    utilizing PyTorch and support vector regression
    (SVR) principles. This implementation uses the dual
    form of the SVM optimization problem and allows
    for the use of different kernel functions.

    Example:
        >>> from deepsuite.svm import SVM
        >>> from deepsuite.svm.kernels import rbf_kernel
        >>> model = SVM(kernel=rbf_kernel, c=1.0, gamma=0.5)

        >>> model.fit(X_train, y_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(
        self,
        kernel: Callable[[torch.Tensor, torch.Tensor], torch.Tensor] = linear_kernel,
        c: float = 1.0,
        **kernel_params: Any,
    ) -> None:
        """Initialize the SVM classifier.

        Args:
            kernel (Callable): Kernel function to be used. Default is linear kernel.
            c (float): Regularization parameter. Default is 1.0.
            **kernel_params: Additional parameters for the kernel function.
        """
        self.kernel = kernel
        self.c = c
        self.alpha = None
        self.support_vectors = None
        self.support_labels = None
        self.b = None
        self.kernel_params = kernel_params
        self.device = get_best_device()

    def __call__(self, *args, **kwds):
        """Call the SVM model to make predictions.
        This method allows the SVM instance to be called like a function.
        It first fits the model if it hasn't been fitted yet, and then makes predictions.

        Args:
            *args: Positional arguments for the fit method.
            **kwds: Keyword arguments for the fit method.

        Returns:
            torch.Tensor: Predicted labels for the input data.

        Example:
            >>> fit = SVM()(X_train, y_train, X_test)
        """
        self.fit(*args, **kwds)

    def fit(self, X: torch.Tensor, y: torch.Tensor, epochs=500, lr=1e-2) -> None:
        """Fit the SVM model to the training data.

        Args:
            X (torch.Tensor): Training data of shape (n_samples, n_features).
            y (torch.Tensor): Labels of shape (n_samples,).
            epochs (int): Number of training epochs. Default is 500.
            lr (float): Learning rate for the optimizer. Default is 1e-2.

        Returns:
            None
        """
        X = X.to(self.device)
        y = y.to(self.device).float()
        n_samples = X.shape[0]

        # Gram-Matrix mit dem Kernel
        K = self.kernel(X, X, **self.kernel_params).to(self.device)  # [n_samples x n_samples]

        # Lagrange-Multiplikatoren
        alpha = torch.zeros(n_samples, requires_grad=True)

        optimizer = torch.optim.SGD([alpha], lr=lr)

        for _ in range(epochs):
            optimizer.zero_grad()

            # Dual-Objective (zu maximieren)
            loss = 0.5 * torch.sum(
                (alpha.view(-1, 1) * alpha.view(1, -1)) * (y.view(-1, 1) * y.view(1, -1)) * K
            ) - torch.sum(alpha)

            (-loss).backward()  # Wir minimieren den loss
            optimizer.step()

            # Optional: Clipping von alpha für Hard-Margin SVM
            with torch.no_grad():
                alpha.clamp_(0, self.c)

        # Support-Vektoren extrahieren
        support_mask = alpha > 1e-5
        self.alpha = alpha[support_mask]
        self.support_vectors = X[support_mask]
        self.support_labels = y[support_mask]

        # Bias b berechnen
        K_sv = self.kernel(self.support_vectors, self.support_vectors, **self.kernel_params)
        decision = (self.alpha * self.support_labels).view(1, -1) @ K_sv.T  # shape: (1, n_support)
        self.b = torch.mean(self.support_labels - decision.view(-1))

    def predict(self, X: torch.Tensor) -> torch.Tensor:
        """Predict the labels for the input data.

        Args:
            X (torch.Tensor): Input data of shape (n_samples, n_features).

        Returns:
            torch.Tensor: Predicted labels of shape (n_samples,).
        """
        assert self.alpha is not None, "Model must be fitted before prediction"
        X = X.to(self.device)
        K = self.kernel(X, self.support_vectors, **self.kernel_params).to(
            self.device
        )  # [n_test x n_support]
        decision = torch.sum(self.alpha * self.support_labels * K, dim=1) + self.b
        return torch.sign(decision)
