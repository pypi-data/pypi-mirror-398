import warnings
warnings.filterwarnings(
    "ignore",
    message=r".*Converting (A|P) to a CSC.*",
    category=UserWarning,
    module=r"scs(\.|$)"
)
import numbers
import numpy        as     np
import scipy.linalg as     la
import cvxpy        as     cp
from   scipy.sparse import csc_matrix

def CLSPSolveInstance(
    self, problem:         str   = "",   C: np.ndarray |  None  = None,
          S: np.ndarray |  None  = None, M: np.ndarray |  None  = None,
                                         b: np.ndarray |  None  = None,
          m:     int    |  None  = None, p: int        |  None  = None,
          i:     int             = 1,    j: int                 = 1,
          zero_diagonal:   bool  = False,
          r:     int             = 1,    Z: np.ndarray |  None  = None,
          rcond:           float                       |  bool  = False,
          tolerance:       float                       |  None  = None,
          iteration_limit: int                         |  None  = None,
          final: bool            = True, alpha: float  |  None  = None,
          *args, **kwargs
) -> "CLSP":
    """
    Solve the Convex Least Squares Programming (CLSP) problem.

    This method performs a two-step estimation:
    (1) a pseudoinverse-based solution using either the Moore–Penrose or
        Bott–Duffin inverse, optionally iterated for convergence;
    (2) a convex-programming correction using Lasso, Ridge, or Elastic Net
        regularization (if enabled).

    Parameters
    ----------
    problem : str, optional
        Structural template for matrix construction. One of:
        - 'ap'   or 'tm' : allocation or tabular matrix problem.
        - 'cmls' or 'rp' : constrained modular least squares or RP-type.
        - ''     or other: General CLSP problems (user-defined C and/or M).

    C, S, M : np.ndarray or None
        Blocks of the constraint matrix A = [C | S; M | Q].
        If `C` and/or `M` are provided, the matrix A is constructed
        accordingly. If both are None and A is not yet defined, an error
        is raised.

    b : np.ndarray or None
        Right-hand side vector. Must have as many rows as A. Required.

    m, p : int or None
        Dimensions of X ∈ ℝ^{m×p}, relevant for allocation problems ('ap').

    i, j : int, default = 1
        Grouping sizes for row and column sum constraints in AP problems.

    zero_diagonal : bool, default = False
        If True, enforces structural zero diagonals via identity truncation.

    r : int, default = 1
        Number of refinement iterations for the pseudoinverse-based estimator.
        When `r > 1`, the slack block Q is updated iteratively to improve
        feasibility in underdetermined or ill-posed systems.

    Z : np.ndarray or None
        A symmetric idempotent matrix (projector) defining the subspace for
        Bott–Duffin pseudoinversion. If None, the identity matrix is used,
        reducing to the Moore–Penrose case.

    rcond : float or bool, default=False
        Regularization parameter for the Moore-Penrose and Bott-Duffin
        inverses, providing numerically stable inversion and ensuring
        convergence of singular values. If True, an automatic tolerance
        equal to `tolerance` is applied. If set to a float, it specifies
        the relative cutoff below which small singular values are treated
        as zero.

    tolerance : float or None, default = None
        Convergence tolerance for NRMSE change between iterations.

    iteration_limit : int or None, default = None
        Maximum number of iterations allowed in the refinement loop.

    final : bool, default = True
        If True, a convex programming problem is solved to refine `zhat`.
        The resulting solution `z` minimizes a weighted L1/L2 norm around
        `zhat` subject to Az = b.

    alpha : float or None, default = None
        Regularization parameter:
        - α = 0: Lasso (L1 norm)
        - α = 1: Ridge (L2 norm)
        - 0 < α < 1: Elastic Net

    *args, **kwargs : optional
        Additional arguments passed to the CVXPY solver backend.

    Attributes Set
    ---------------
    self.A : np.ndarray
        Canonical design matrix constructed from (C, S, M, Q).

    self.b : np.ndarray
        Conformable right-hand side vector.

    self.Z : np.ndarray
        Projector matrix used for Bott–Duffin inversion.

    self.r : int
        Number of refinement iterations performed.

    self.zhat : np.ndarray
        First-step solution (unregularized pseudoinverse estimate).

    self.alpha : float
        Regularization parameter.

    self.z : np.ndarray
        Final estimate after optional convex refinement.

    self.x, self.y : np.ndarray
        Variable and slack components reshaped from `z`.

    self.nrmse : float
        Normalized root mean squared error over the full system.

    self.r2_partial : float or np.nan
        R² for the M block (if applicable), computed from partial residuals.

    self.nrmse_partial : float
        NRMSE over the M block, if defined.

    self.kappaA, self.kappaB, self.kappaC : float
        Condition numbers for the full, projected, and constrained system.

    self.z_lower, self.z_upper : np.ndarray
        Condition-weighted confidence band for z.

    Returns
    -------
    self

    Raises
    ------
    CLSPError
        If the design matrix A or right-hand side b is malformed, inconsistent,
        or incompatible with the structural assumptions of the problem.
    """
    # (A), (b) Construct a conformable canonical form for the CLSP estimator
    if (C is not None or M is not None) or (m is not None and p is not None):
        self.canonize(problem, C, S, M, None, b,
                               m, p, i, j, zero_diagonal)
    elif self.A is None:
        raise self.error("At least one of C, M, m, or p must be provided.")
    if self.A.shape[0] != self.b.shape[0]:
        raise self.error(f"The matrix A and vector b must have the same "
                         f"number of rows: A has {self.A.shape[0]}, but "
                         f"b has {self.b.shape[0]}")

    # (zhat) (Iterated if r > 1) first-step estimate
    if r < 1:
        raise self.error("Number of refinement iterations r must be ≥ 1.")
    if Z is not None:
        self.Z = Z
    elif self.Z is None:
        self.Z = np.eye(self.A.shape[1], dtype=np.float64)
    if tolerance       is not None:
        self.tolerance       = tolerance
    if iteration_limit is not None:
        self.iteration_limit = iteration_limit
    try:
        if (not np.allclose(self.Z,          self.Z.T, atol=self.tolerance) or
            not np.allclose(self.Z @ self.Z, self.Z,   atol=self.tolerance) or
            self.Z.shape[0] != self.A.shape[1]):
            raise ValueError
    except ValueError:
        raise self.error(f"Matrix Z must be symmetric, idempotent and "
                         f"match the number of columns in A: expected "
                         f"({self.A.shape[1]}, {self.A.shape[1]}), "
                         f"got {self.Z.shape}")
    for n_iter in range(1, 1 +
                           (r if self.A.shape[0] > self.C_idx[0] else 1)):
        # save NRMSE from the previous step, construct Q and Z
        if n_iter > 1:
            nrmse_prev = (np.linalg.norm(self.b  - self.A @ self.zhat) /
                          np.sqrt(self.b.shape[0]) / np.std(self.b))
            Q          = np.diagflat(-np.sign(self.b -
                                     self.A @ self.zhat)[self.C_idx[0]:])
            self.canonize(problem, C, S, M, Q, self.b.reshape(-1, 1),
                                   m, p, i, j, zero_diagonal)
            Z_delta    = self.A.shape[1] - self.Z.shape[0]
            if Z_delta > 0:                            # augment Z by I
               self.Z  = np.block([[self.Z,
                                    np.zeros((self.Z.shape[0], Z_delta))],
                                   [np.zeros((Z_delta, self.Z.shape[1])),
                                    np.eye(Z_delta, dtype=np.float64)]])
        # solve via the Bott–Duffin inverse
        self.zhat      = (la.pinv(self.Z @ (self.A.T @ self.A) @ self.Z,
                          atol=0.0, rtol=(None           if rcond == False else
                                          self.tolerance if rcond == True  else
                                          rcond))
                          @ self.Z @ self.A.T) @ self.b
        self.nrmse     = (lambda residuals, sd:
                          np.linalg.norm(residuals) / np.sqrt(sd.shape[0]) /
                          np.std(sd) if not np.isclose(np.std(sd), 0) else
                          np.inf)(self.b - self.A @ self.zhat, self.b)
        # break on convergence
        self.r         = n_iter
        if n_iter > 1:
            if (abs(self.nrmse - nrmse_prev) < self.tolerance or
                n_iter                       > self.iteration_limit):
                del nrmse_prev, Q
                break
    if not np.all(np.isfinite(self.zhat)):
        self.zhat = np.nan
        raise self.error("Pseudoinverse estimate zhat failed")

    # (z) Final solution (if available), or set self.z = self.zhat
    if final is not None:
        self.final = final
    if alpha is not None:
        self.alpha = np.float64(max(0, min(1, alpha)))
    if self.final:
        # build a convex problem (p_cvx) and its solver (c_cvx)
        A_csc = csc_matrix(self.A.astype(np.float64))
        z_cvx = cp.Variable(A_csc.shape[1])
        d_cvx = z_cvx - self.zhat.flatten()
        if   np.isclose(self.alpha, 0):                # Lasso
            f_obj = cp.norm1(d_cvx)
            s_cvx = cp.ECOS
        elif np.isclose(self.alpha, 1):                # Ridge
            f_obj = cp.sum_squares(d_cvx)
            s_cvx = cp.OSQP
        else:                                          # Elastic Net
            f_obj = ((1 - self.alpha) * cp.norm1(d_cvx)      +
                     self.alpha       * cp.sum_squares(d_cvx))
            s_cvx = cp.SCS
        c_cvx = [A_csc @ z_cvx == self.b.flatten()]
        p_cvx = cp.Problem(cp.Minimize(f_obj), c_cvx)
        # solve
        try:
            kw = {k: v for k, v in kwargs.items()
                       if k not in {"rcond"}}
            p_cvx.solve(*args, solver=s_cvx, verbose=False,
                        **kw)                          # pass arguments
            if z_cvx.value is None:
                warnings.warn(
                    f"Step 2 infeasible ({p_cvx.status}); falling back",
                    category=RuntimeWarning
                )
                self.z     = self.zhat
            else:
                self.z     = z_cvx.value
                self.nrmse = (lambda residuals, sd:
                          np.linalg.norm(residuals) / np.sqrt(sd.shape[0]) /
                          np.std(sd) if not np.isclose(np.std(sd), 0) else
                          np.inf)(self.b - self.A @ self.z,   self.b)
        except (cp.SolverError, ValueError):
            self.z = self.zhat
    else:
        self.z = self.zhat

    # (x), (y) Variable and slack components of z
    self.x = self.z[:self.C_idx[1]].reshape(m if m is not None else -1,
                                            p if p is not None else  1)
    self.y = self.z[self.C_idx[1]:]

    # (kappaC), (kappaB), (kappaA) Condition numbers
    self.kappaC            = np.linalg.cond(        self.A[:self.C_idx[0], :])
    self.kappaB            = np.linalg.cond(self.A @
                                            la.pinv(self.A[:self.C_idx[0], :]))
    self.kappaA            = np.linalg.cond(        self.A)

    # (r2_partial), (nrmse_partial) M-block-based statistics
    if self.A.shape[0]     > self.C_idx[0]:
        M                  = self.A[self.C_idx[0]:, :self.C_idx[1]]
        b_M                = self.b[-M.shape[0]:]
        residuals_M        = b_M - M @ self.x.reshape(-1, 1)
        self.r2_partial    = (lambda residuals, sd:
                          1  -  (np.linalg.norm(residuals) ** 2            /
                          np.linalg.norm(sd - np.mean(sd)) ** 2)
                          if not np.isclose(np.std(sd), 0) else
                          np.nan)(residuals_M,  b_M)
        self.nrmse_partial = (lambda residuals, sd:
                          np.linalg.norm(residuals) / np.sqrt(sd.shape[0]) /
                          np.std(sd) if not np.isclose(np.std(sd), 0) else
                          np.inf)(residuals_M,  b_M)
        del M, b_M, residuals_M

    # (z_lower), (z_upper) Condition-weighted confidence band
    dz           = (self.kappaA                              *
                    np.linalg.norm(self.b - self.A @ self.z) /
                    np.linalg.norm(self.b)
                    if not np.isclose(np.linalg.norm(self.b), 0) else
                    np.inf)
    self.z_lower = self.z * (1 - dz)
    self.z_upper = self.z * (1 + dz)

    # (x_lower), (x_upper), (y_lower), (y_upper)
    self.x_lower = self.z_lower[:self.C_idx[1]].reshape(m if m is not None
                                                          else -1,
                                                        p if p is not None
                                                          else  1)
    self.x_upper = self.z_upper[:self.C_idx[1]].reshape(m if m is not None
                                                          else -1,
                                                        p if p is not None
                                                          else  1)
    self.y_lower = self.z_lower[self.C_idx[1]:]
    self.y_upper = self.z_upper[self.C_idx[1]:]

    return self

def CLSPSolve(
    self, tolerance:      float       | None = None,
          alpha: float  | list[float] | None = None,
          *args, **kwargs
) -> "CLSP":
    """
    Solve the Convex Least Squares Programming (CLSP) problem setting a given
    or selecting the best alpha for Step 2, based on a list or error rule.

    This method performs a two-step estimation:
    (1) a pseudoinverse-based solution using either the Moore–Penrose or
        Bott–Duffin inverse, optionally iterated for convergence;
    (2) a convex-programming correction using Lasso, Ridge, or Elastic Net
        regularization (if enabled).

    Parameters
    ----------
    tolerance : float or None, default = None
        Convergence tolerance for NRMSE change between iterations.

    alpha : float or list[float] or None, default = None
        Regularization parameter:
        - α = 0: Lasso (L1 norm)
        - α = 1: Ridge (L2 norm)
        - 0 < α < 1: Elastic Net
        If a scalar float is provided, that value is used after clipping
        to [0, 1]. If a list/iterable of floats is provided, each candidate
        is evaluated via a full solve, and the α with the smallest NRMSE is
        selected. If None, α is chosen, based on an error rule:
        α = min(1.0, nrmse_{α=0} / (nrmse_{α=0} + nrmse_{α=1} + tolerance))

    The selected value is stored in `self.alpha` and then passed to
    `CLSPSolveInstance(..., alpha=self.alpha)`.

    Returns
    -------
    self
    """
    # process keywords and define ancillary functions
    kw       = {k: v for k, v in kwargs.items()
                     if k not in {"tolerance", "final", "alpha"}}
    to_alpha = lambda a: np.float64(max(0.0, min(1.0, float(a))))
    to_nrmse = lambda n: np.float64(n if np.isfinite(n) else np.inf)

    # process alpha
    if tolerance is not None:
        self.tolerance = tolerance
    if   (alpha  is not None and isinstance(alpha, numbers.Real) and
          np.isfinite(alpha)):
        self.alpha = to_alpha(alpha)
    elif (alpha  is not None and isinstance(alpha, list)):
        result = {a: to_nrmse(CLSPSolveInstance(self, tolerance=self.tolerance,
                                                      final=True, alpha=to_alpha(a),
                                                      *args, **kw).nrmse)
                  for a in alpha
                  if isinstance(a, numbers.Real) and  np.isfinite(a)}
        if result:
            self.alpha = to_alpha(min(result, key=result.get))
        else:
            alpha = None
    if   (alpha  is None):                             # error rule
        nrmse_alpha0 = to_nrmse(CLSPSolveInstance(self, tolerance=self.tolerance,
                                                        final=True, alpha=0.0,
                                                        *args, **kw).nrmse)
        nrmse_alpha1 = to_nrmse(CLSPSolveInstance(self, tolerance=self.tolerance,
                                                        final=True, alpha=1.0,
                                                        *args, **kw).nrmse)
        denominator = nrmse_alpha0 + nrmse_alpha1 + self.tolerance
        if np.isfinite(denominator) and denominator > 0.0:
            self.alpha = min(1.0, nrmse_alpha0 / denominator)
        else:
            self.alpha = 0.5

    return CLSPSolveInstance(self, tolerance=self.tolerance,
                                   final=True, alpha=self.alpha, *args, **kw)
