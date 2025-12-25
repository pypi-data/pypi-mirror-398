# pkgs/uniPairs/src/uniPairs/estimator.py
from sklearn.base import BaseEstimator
from abc import ABC, abstractmethod
import numpy as np
import adelie as ad
from scipy.stats import norm, t as t_dist
from sklearn.base import BaseEstimator
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
import warnings
from importlib.metadata import version as pkg_version, PackageNotFoundError
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Literal, Tuple, List, Dict, Any, TypedDict, Union

def generate_lmda_path(
        X: np.ndarray, 
        y: np.ndarray, 
        family: Literal['gaussian', 'binomial', 'cox']='gaussian',
        n_lmdas: int=100, 
        lmda_min_ratio: Optional[float]=None, 
        fit_intercept: bool=True,
) -> np.ndarray:
    """
    Generate a sequence of lambda values for regularized GLM fitting.

    This function computes a decreasing path of penalty values for
    use in Lasso-type models. For Gaussian families, the lambda path is computed
    analytically from the KKT conditions. For Binomial and Cox, the path is obtained
    by calling ``ad.cv_grpnet``.

    Parameters
    ----------
    X : ndarray of shape (n_samples, n_features)
        Design matrix.
    y : ndarray
        Response vector. For ``family='cox'``, ``y`` must be of shape
        ``(n_samples, 2)`` where the columns are ``(time, status)``.
    family : {'gaussian', 'binomial', 'cox'}, default='gaussian'
        Family of the GLM used to determine the lambda path.
    n_lmdas : int, default=100
        Number of lambda values to generate.
    lmda_min_ratio : float, optional
        Ratio of the smallest lambda to the largest lambda. If ``None``:
        - ``1e-4`` is used when ``n_samples > n_features``,
        - ``1e-2`` otherwise.
    fit_intercept : bool, default=True
        Whether to include an intercept term (ignored for the Cox family).

    Returns
    -------
    lmda_path : ndarray of shape (n_lmdas,)
        A decreasing sequence of lambda values, on a log-scale.

    Examples
    --------
    >>> lmda_path = generate_lmda_path(X, y, family='gaussian', n_lmdas=50)
    >>> lmda_path.shape
    (50,)
    """

    n, p = X.shape
    if lmda_min_ratio is None:
        lmda_min_ratio = 1e-4 if n > p else 1e-2
    fit_intercept = False if family == 'cox' else fit_intercept
    if family == "gaussian":
        # glm_family = ad.glm.gaussian(y)
        x_mean = np.mean(X,axis=0)                                                                                     
        x_std = np.std(X,axis=0)                                                                         
        x_std[x_std == 0] = 1   
        zty = (X.T @ y - x_mean * np.sum(y)) / x_std 
        lmda_max = 2 * np.max(np.abs(zty)) / n
        lmda_min = lmda_min_ratio * lmda_max
        return np.logspace(np.log10(lmda_max), np.log10(lmda_min), num=n_lmdas)   
    elif family == "binomial":
        glm_family = ad.glm.binomial(y)
    elif family == "cox":
        glm_family = ad.glm.cox(start=np.zeros(len(y)), stop=y[:, 0], status=y[:, 1])
    else:
        raise ValueError(f"Unsupported family: {family}")
    cv_lasso = ad.cv_grpnet(
        X=X,
        glm=glm_family,
        n_folds=2,
        groups=None,
        min_ratio=lmda_min_ratio,
        intercept=fit_intercept,
        lmda_path_size=n_lmdas,
        constraints=None,
        early_exit=False
    )
    return cv_lasso.lmdas

class OLS(BaseEstimator):
    """
    Ordinary Least Squares (OLS) regression with optional intercept,
    leave-one-out predictions, and p-value estimation.

    Parameters
    ----------
    fit_intercept : bool, default=True
        If True, an intercept term is included in the model.

    vars_names : list of str, optional
        Names of the variables. If None, names are automatically
        generated as ``["X0", "X1", ..., "Xp"]``.

    p_value : bool, default=False
        If True, a two-sided p-value is computed for the last coefficient after fitting.

    preds_loo : bool, default=False
        If True, leave-one-out predictions are computed after fitting.

    Attributes
    ----------
    slopes\_ : ndarray of shape (n_features,)
        Estimated regression coefficients (excluding intercept).

    intercept\_ : float
        Estimated intercept term (if ``fit_intercept=True``).

    preds_loo\_ : ndarray of shape (n_samples,), optional
        Leave-one-out predictions. Present only if ``preds_loo=True``.

    p_value\_ : ndarray of shape (1,), optional
        Two-sided p-value for the last coefficient. Present only if ``p_value=True``.

    vars_names\_ : list of str
        Names of the variables used in the model.

    Examples
    --------
    >>> model = OLS(fit_intercept=True, p_value=True, preds_loo=True)
    >>> model.fit(X, y)
    >>> y_pred = model.predict(X)
    >>> active = model.get_active_variables()
    >>> formula = model.get_fitted_function()
    """
    def __init__(
            self, 
            fit_intercept: bool=True, 
            vars_names: Optional[List[str]]=None, 
            p_value: bool=False, 
            preds_loo: bool=False,
    ) -> None:
        self.slopes_ = None                                                                                                
        self.intercept_ = None                                                                                              
        self.vars_names_ = vars_names                                                                                   
        self.fit_intercept_ = fit_intercept                                                                          
        self.compute_p_value_ = p_value
        self.p_value_ = None
        self.compute_loo_ = preds_loo
        self.preds_loo_ = None

    def set_vars_names(
            self, 
            vars_names: List[str],
    ) -> None:
        self.vars_names_ = vars_names                                                                                    

    def fit(
            self, 
            X: np.ndarray, 
            y: np.ndarray,
    ) -> None:
        X, y = check_X_y(X, y, y_numeric=True)
        n, p = X.shape
        if self.vars_names_ is None:
            self.vars_names_ = [f"X{i}" for i in range(p)]
        if self.fit_intercept_:
            p += 1
            X = np.hstack([np.ones((n, 1)), X])                                                                                                  
        beta, *_ = np.linalg.lstsq(X,y,rcond=None)
        self.slopes_ = beta[1:]
        self.intercept_ = beta[0]  
        if self.compute_loo_ or self.compute_p_value_ : 
            M = np.linalg.pinv(X.T @ X)
            if self.compute_loo_ : 
                M = np.linalg.pinv(X.T @ X)  
                XM = X @ M
                h = np.einsum('ij,ij->i',X, XM)
                self.preds_loo_ = y - (y - X @ beta) / (1.0 - h)
            if self.compute_p_value_ : 
                yhat = X @ beta
                residuals = y - yhat
                rss = np.sum(residuals**2)
                sigma2 = rss / (n - p)
                cov_beta_last = sigma2 * M[-1,-1]        
                se_beta_last = np.sqrt(cov_beta_last)
                t_last = beta[-1] / se_beta_last
                self.p_value_ = 2 * (1 - t_dist.cdf(np.abs(t_last), n - p)).flatten()

    def predict(
            self, 
            X: np.ndarray,
    ) -> np.ndarray:
        check_is_fitted(self)
        X = check_array(X)
        return X @ self.slopes_ + self.intercept_                                                                           

    def get_active_variables(
            self, 
            tolerance: float=1e-10
    ) -> List[str]:
        check_is_fitted(self)
        active_vars = [self.vars_names_[i] for i, slp in enumerate(self.slopes_) if abs(slp) > tolerance]
        return active_vars

    def get_fitted_function(self) -> str:
        check_is_fitted(self)
        fitted_model_rep = [f"{self.intercept_:.3f}"] + [
            f"{self.slopes_[i]:.3f}*" + var for i, var in enumerate(self.vars_names_)
        ]
        return " + ".join(fitted_model_rep)
    
class FamilySpec(TypedDict):
    family: Literal["gaussian", "binomial", "cox"]

class GLM(BaseEstimator):
    """
    Generalized Linear Model (GLM) wrapper using `adelie.grpnet` for
    Gaussian, Binomial (logistic), and Cox proportional hazards regression.

    Supports optional intercept, leave-one-out (LOO) predictions, and
    likelihood ratio p-values.

    Parameters
    ----------
    fit_intercept : bool, default=True
        Whether to include an intercept term. For Cox regression, the
        intercept is always excluded.

    vars_names : list of str, optional
        Names of predictor variables. If None, names are generated as
        ``["X0", "X1", ..., "Xp"]``.

    family_spec : dict, optional
        Dictionary containing the model family. Must contain key
        ``"family"`` with one of ``{"gaussian", "binomial", "cox"}``.

        Examples:
        ``{"family": "binomial"}``

    p_value : bool, default=False
        If True, computes a two-sided p-value via a likelihood ratio test
        comparing the full model vs. the model without the last coefficient.

    preds_loo : bool, default=False
        If True, computes leave-one-out linear predictors following Rad &
        Maleki (2020).

    Attributes
    ----------
    slopes\_ : ndarray of shape (n_features,)
        Estimated regression coefficients.

    intercept\_ : float
        Estimated intercept. Zero for Cox models.

    preds_loo\_ : ndarray of shape (n_samples,), optional
        Leave-one-out predictions if ``preds_loo=True``.

    p_value\_ : float, optional
        Two-sided p-value for the last predictor coefficient.

    vars_names\_ : list of str
        Names of variables used in the model.

    offset\_ : ndarray or None
        Optional observation-specific offsets supplied to the GLM.

    Examples
    --------
    >>> glm = GLM(family_spec={"family": "binomial"}, preds_loo=True)
    >>> glm.fit(X, y)
    >>> eta = glm.predict(X)               # linear predictor
    >>> p = glm.predict(X, response_scale=True)  # inverse-link
    >>> active = glm.get_active_variables()
    >>> formula = glm.get_fitted_function()
    """
    def __init__(
            self, 
            fit_intercept: bool=True, 
            vars_names: Optional[List[str]]=None, 
            family_spec: Optional[FamilySpec]=None, 
            p_value: bool=False, 
            preds_loo: bool=False,
    ) -> None:
        self.vars_names_ = vars_names
        self.family_spec_ = family_spec
        self.family_ = self.family_spec_["family"].lower()
        self.fit_intercept_ = False if (self.family_=='cox') else fit_intercept 
        self.slopes_ = None
        self.intercept_ = None
        self.compute_p_value_ = p_value
        self.p_value_ = None
        self.compute_loo_ = preds_loo
        self.preds_loo_ = None
        self.offset_ = None

    def _check_input(
            self, 
            X: np.ndarray, 
            y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        if self.family_ == "cox":
            X = check_array(X)
            y = np.asarray(y, dtype=float)
            if y.ndim != 2 or y.shape[1] != 2:
                raise ValueError(f"For Cox family, y must be of shape (n_samples, 2): (time, status). Got {y.shape}.")
        else:
            X, y = check_X_y(X, y, y_numeric=True)
        return X, y
    
    def set_vars_names(
            self, 
            vars_names: List[str],
    ) -> None:
        self.vars_names_ = vars_names

    def _inverse_link(
            self, 
            eta: np.ndarray,
    ) -> np.ndarray:
        if self.family_  == "binomial":
            return 1./(1.+np.exp(-eta))
        elif self.family_  == "cox":
            return np.exp(eta)
        else:
            raise NotImplementedError(f"Family '{self.family_ }' not supported.")

    def fit(
            self, 
            X: np.ndarray, 
            y: np.ndarray,
            offset: Optional[np.ndarray]=None,
    ) -> None:
        self._check_input(X, y)
        n, p = X.shape
        self.offset_ = offset
        if self.vars_names_ is None:
            self.vars_names_ = [f"X{i}" for i in range(p)]

        self.X_mean_ = np.mean(X, axis=0)
        self.X_std_ = np.std(X, axis=0)
        self.X_std_[self.X_std_ == 0] = 1.0
        X_std = (X - self.X_mean_) / self.X_std_

        if self.family_ == "binomial":
            state = ad.grpnet(
                X=np.asfortranarray(X_std),
                glm=ad.glm.binomial(y=y, link="logit"),
                lmda_path=np.array([0.0]),
                intercept=self.fit_intercept_,
                early_exit=False,
                progress_bar=False,
                offsets=self.offset_
            )
            slopes_std = state.betas.toarray()[0]
            intercept_std = state.intercepts[0]
            self.slopes_ = slopes_std / self.X_std_
            self.intercept_ = intercept_std - (self.X_mean_ / self.X_std_) @ slopes_std
            if self.compute_loo_ : 
                assert p==1
                eta_hat = self.predict(X, response_scale=False, offset=self.offset_)
                glm_binomial = ad.glm.binomial(y=y, link="logit")
                grad_binomial = np.empty_like(eta_hat)
                hess_binomial = np.empty_like(eta_hat)
                glm_binomial.gradient(eta_hat,grad_binomial)
                glm_binomial.hessian(eta_hat,grad_binomial,hess_binomial)
                hess_binomial += 1e-15
                Z = eta_hat + grad_binomial / hess_binomial
                h = X_std[:,0]**2*hess_binomial
                h /= np.sum(h)
                self.preds_loo_ = Z -(Z-eta_hat)/(1.-h)

            if self.compute_p_value_ :
                state_null = ad.grpnet(
                    X=np.asfortranarray(X_std[:,:-1]),
                    glm=ad.glm.binomial(y=y, link="logit"),
                    lmda_path=np.array([0.0]),
                    intercept=self.fit_intercept_,
                    early_exit=False,
                    progress_bar=False,
                    offsets=self.offset_ 
                )
                slopes_std_null = state_null.betas.toarray()[0]
                intercept_std_null = state_null.intercepts[0]
                eta_null = X_std[:,:-1] @ slopes_std_null + intercept_std_null
                eta_full = X_std @ slopes_std + intercept_std
                log_likelihood_null = np.sum(y*eta_null - np.logaddexp(0,eta_null))
                log_likelihood_full = np.sum(y*eta_full - np.logaddexp(0,eta_full))
                self.p_value_ = 2 * (1 - norm.cdf(np.sqrt(2*(log_likelihood_full-log_likelihood_null))))

        elif self.family_ == "cox":
            state = ad.grpnet(
                X=np.asfortranarray(X_std),
                glm=ad.glm.cox(start=np.zeros(n),stop=y[:, 0],status=y[:, 1],dtype=np.float64),
                lmda_path=np.array([0.0]),
                intercept=False,
                early_exit=False,
                progress_bar=False,
                offsets=self.offset_
            )
            slopes_std = state.betas.toarray()[0]
            self.slopes_ = slopes_std / self.X_std_
            self.intercept_ = 0.0
            if self.compute_loo_ : 
                # conforming to Rad et Maleki 2020
                assert p == 1
                eta_hat = X_std@slopes_std
                glm_cox = ad.glm.cox(start=np.zeros(n),stop=y[:, 0],status=y[:, 1],dtype=np.float64)
                grad_cox = np.empty_like(eta_hat)
                hess_cox = np.empty_like(eta_hat)
                glm_cox.gradient(eta_hat,grad_cox)
                glm_cox.hessian(eta_hat,grad_cox,hess_cox)
                hess_cox += 1e-15
                Z = eta_hat + grad_cox / hess_cox
                h = X_std[:,0]**2*hess_cox
                h /= np.sum(h)
                self.preds_loo_ = Z -(Z-eta_hat)/(1.-h)
            if self.compute_p_value_ :
                state_null = ad.grpnet(
                    X=np.asfortranarray(X_std[:, :-1]),
                    glm=ad.glm.cox(start=np.zeros(n),stop=y[:, 0],status=y[:, 1],dtype=np.float64),
                    lmda_path=np.array([0.0]),
                    intercept=False,
                    early_exit=False,
                    progress_bar=False,
                    offsets=self.offset_
                )
                slopes_std_null = state_null.betas.toarray()[0]
                eta_null = X_std[:,:-1] @ slopes_std_null 
                eta_full = X_std @ slopes_std 
                log_likelihood_null = -n*ad.glm.cox(start=np.zeros(n),stop=y[:, 0],status=y[:, 1],dtype=np.float64).loss(eta_null)
                log_likelihood_full = -n*ad.glm.cox(start=np.zeros(n),stop=y[:, 0],status=y[:, 1],dtype=np.float64).loss(eta_full)
                self.p_value_ = 2 * (1 - norm.cdf(np.sqrt(2*(log_likelihood_full-log_likelihood_null))))

        else:
            raise NotImplementedError(f"Family {self.family_} not implemented.")
        
    def predict(
            self, 
            X: np.ndarray, 
            response_scale: bool=False, 
            offset: Optional[np.ndarray]=None,
    ) -> np.ndarray:
        check_is_fitted(self, ["slopes_", "intercept_"])
        X = check_array(X)
        eta_hat = X @ self.slopes_ + self.intercept_
        if offset is not None : 
            eta_hat += offset
        return self._inverse_link(eta_hat) if response_scale else eta_hat
    
    def get_active_variables(
            self, 
            tolerance: float=1e-10,
    ) -> List[str]:
        check_is_fitted(self)
        return [self.vars_names_[i] for i, slp in enumerate(self.slopes_) if abs(slp) > tolerance]

    def get_fitted_function(self) -> str:
        check_is_fitted(self)
        fitted_model_rep = [f"{self.intercept_:.3f}"] + [
            f"{self.slopes_[i]:.3f}*" + var for i, var in enumerate(self.vars_names_)
        ]
        return " + ".join(fitted_model_rep)

class Lasso(BaseEstimator):
    """
    Lasso regression using `adelie.grpnet` for Gaussian, Binomial (logistic),
    or Cox proportional hazards models.

    The model standardizes inputs, fits a regularization path over
    ``lmda_path_`` (lambda values), and returns intercepts and slopes on the
    original data scale.

    Parameters
    ----------
    lmda_path : ndarray of shape (n_lambdas,), optional
        Regularization path to use. If None, it is generated automatically
        via :func:`generate_lmda_path`.

    fit_intercept : bool, default=True
        Whether to include an intercept term. For Cox models, the intercept
        is always excluded.

    vars_names : list of str, optional
        Names of variables used in the model. If None, they are generated automatically
        as ``["X0", "X1", ..., "Xp"]``.

    family_spec : dict, optional
        Dictionary containing the response family. Must include key
        ``"family"`` with one of: ``{"gaussian", "binomial", "cox"}``.

        Examples
        --------
        >>> {"family": "binomial"}

    Attributes
    ----------
    lmda_path\_ : ndarray of shape (n_lmdas,)
        Lambda values used during fitting.

    slopes\_ : ndarray of shape (n_lmdas, n_features)
        Regression coefficients for each lambda.

    intercept\_ : ndarray of shape (n_lmdas, 1)
        Intercept for each lambda.

    vars_names\_ : list of str
        Names of variables in the model.

    X_mean\_ : ndarray of shape (n_features,)
        Feature means used for standardization.

    X_std\_ : ndarray of shape (n_features,)
        Feature standard deviations used for standardization.

    offset\_ : ndarray or None
        Observation-specific offset passed into the GLM, if provided.

    Examples
    --------
    >>> model = Lasso(family_spec={"family": "binomial"})
    >>> model.fit(X, y)
    >>> y_pred = model.predict(X, response_scale=True)
    >>> active = model.get_active_variables(lmda=0.1)
    >>> formula = model.get_fitted_function()
    """
    def __init__(
            self, 
            lmda_path: Optional[np.ndarray]=None, 
            fit_intercept: bool=True, 
            vars_names: Optional[List[str]]=None, 
            family_spec: Optional[FamilySpec]=None,
    ) -> None:
        self.family_spec_ = family_spec or {"family": "gaussian"}
        self.family_ = self.family_spec_["family"].lower()
        self.lmda_path_ = lmda_path                                                                                   
        self.slopes_ = None                                                                                                
        self.intercept_ = None                                                                                             
        self.vars_names_ = vars_names                                                                                  
        self.fit_intercept_ = False if (self.family_=='cox') else fit_intercept                                                                          
        self.X_mean_ = None
        self.X_std_ = None
        self.offset_ = None

    def set_vars_names(
            self, 
            vars_names: List[str],
    ) -> None:
        self.vars_names_ = vars_names                                                                                

    def set_lmda_path(
            self, 
            lmda_path: np.ndarray,
    ) -> None:
        self.lmda_path_ = lmda_path

    def fit_gaussian(
            self, 
            X_std: np.ndarray, 
            y: np.ndarray,
    ) -> None: 
        if self.lmda_path_ is None:
            self.lmda_path_ = generate_lmda_path(X_std, y, family='gaussian')
        state = ad.grpnet(
            X=np.asfortranarray(X_std),
            glm=ad.glm.gaussian(y=y),
            lmda_path=self.lmda_path_,
            intercept=self.fit_intercept_,
            early_exit=False,
            progress_bar=False,
            offsets=self.offset_
        )
        slopes_std = state.betas.toarray()                                                                                
        intercept_std = state.intercepts                                                                                
        self.slopes_ = slopes_std / self.X_std_[None, :]
        correction = (self.X_mean_ / self.X_std_) @ slopes_std.T
        self.intercept_ = intercept_std - correction
        self.intercept_ = self.intercept_[:, None]

    def fit_cox(
            self, 
            X_std: np.ndarray, 
            y: np.ndarray,
    ) -> None:
        if self.lmda_path_ is None:
            self.lmda_path_ = generate_lmda_path(X_std, y, family='cox')
        state = ad.grpnet(
            X=np.asfortranarray(X_std),
            glm=ad.glm.cox(start=np.zeros(X_std.shape[0]), stop=y[:, 0], status=y[:, 1], dtype=np.float64),
            lmda_path=self.lmda_path_,
            intercept=self.fit_intercept_,
            early_exit=False,
            progress_bar=False,
            offsets=self.offset_
        )
        slopes_std = state.betas.toarray()                                                                          
        self.slopes_ = slopes_std / self.X_std_[np.newaxis, :]
        self.intercept_ = np.zeros((self.slopes_.shape[0], 1)) 
    
    def fit_binomial(
            self, 
            X_std: np.ndarray, 
            y: np.ndarray,
    ) -> None:
        if self.lmda_path_ is None:
            self.lmda_path_ = generate_lmda_path(X_std,y, family='binomial')
        state = ad.grpnet(
            X = np.asfortranarray(X_std),
            glm = ad.glm.binomial(y=y,link='logit'),
            lmda_path=self.lmda_path_,
            intercept=self.fit_intercept_,
            early_exit=False,
            progress_bar=False,
            offsets=self.offset_
        )
        slopes_std = state.betas.toarray()                                                                               
        intercept_std = state.intercepts    
        self.slopes_ = slopes_std / self.X_std_[np.newaxis, :]
        correction = (self.X_mean_ / self.X_std_) @ slopes_std.T
        self.intercept_ = intercept_std - correction
        self.intercept_ = self.intercept_[:, None]

    def _check_and_std_input(
            self, 
            X: np.ndarray, 
            y: np.ndarray,
            tolerance: float=1e-10,
    ) -> Tuple[np.ndarray, np.ndarray]:
        if self.family_ == "cox":
            X = check_array(X)
            y = np.asarray(y, dtype=float)
            if y.ndim != 2 or y.shape[1] != 2:
                raise ValueError(f"For Cox family, y must be of shape (n_samples, 2): (time, status). Got {y.shape}.")
        else:
            X, y = check_X_y(X, y, y_numeric=True)
        self.X_std_ = np.std(X, axis=0, ddof=1)
        zero_std_mask = np.abs(self.X_std_) < tolerance
        if np.any(zero_std_mask):
            warnings.warn(f"Features at indices {np.where(zero_std_mask)[0]} have zero standard deviation and will be removed.")
            X = X[:, ~zero_std_mask]
        self.X_mean_ = np.mean(X, axis=0)
        self.X_std_ = self.X_std_[~zero_std_mask]
        X = (X - self.X_mean_) / self.X_std_
        return X, y
          
    def fit(
            self, 
            X: np.ndarray, 
            y: np.ndarray,
            offset: Optional[np.ndarray]=None, 
            tolerance: float=1e-10,
    ) -> None:
        X, y = self._check_and_std_input(X, y, tolerance=tolerance)
        self.offset_ = offset
        if self.family_ == "gaussian":
            self.fit_gaussian(X, y)
        elif self.family_ == "cox":
            self.fit_cox(X, y)
        elif self.family_ == "binomial":
            self.fit_binomial(X, y)
        else:
            raise NotImplementedError(f"Family {self.family_} not implemented.")
    
    def _inverse_link(
            self, 
            eta: np.ndarray,
    ) -> np.ndarray:
        if self.family_  == "binomial":
            return 1./(1.+np.exp(-eta))
        elif self.family_  == "cox":
            return np.exp(eta)
        else:
            raise NotImplementedError(f"Family '{self.family_ }' not supported.")

    def predict(
            self, 
            X: np.ndarray, 
            response_scale: bool=False, 
            offset: Optional[np.ndarray]=None,
    ) -> np.ndarray:
        check_is_fitted(self)
        X = check_array(X)
        eta_hat = X @ self.slopes_.T + self.intercept_.T
        if offset is not None:
            eta_hat += offset[:,None]
        return self._inverse_link(eta_hat) if response_scale else eta_hat
    
    def get_active_variables(
            self, 
            lmda: Optional[float]=None, 
            tolerance: float=1e-10,
    ) -> List[str]:
        check_is_fitted(self)
        j = int(np.argmin(np.abs(self.lmda_path_ - lmda))) if lmda is not None else 0
        return [self.vars_names_[i] for i, slp in enumerate(self.slopes_[j]) if abs(slp) > tolerance]

    def get_fitted_function(
            self, 
            lmda: Optional[float]=None, 
            tolerance: float=1e-10,
    ) -> str:
        check_is_fitted(self)
        j = int(np.argmin(np.abs(self.lmda_path_ - lmda))) if lmda is not None else 0
        fitted_model_rep = [f"{self.intercept_[j,0]:.3f}"] + [
            f"{self.slopes_[j,i]:.3f}*" + var
            for i, var in enumerate(self.vars_names_)
            if np.abs(self.slopes_[j, i]) > tolerance
        ]
        return " + ".join(fitted_model_rep)

class Stage1Results(TypedDict):
    intercepts: np.ndarray
    slopes: np.ndarray
    loo_preds: np.ndarray

class UniLasso(BaseEstimator):
    """
    UniLasso regression using `adelie.grpnet` for Gaussian, Binomial (logistic),
    or Cox proportional hazards models.

    Parameters
    ----------
    lmda_path : ndarray of shape (n_lmdas,), optional
        Regularization path. If None, it is generated automatically using
        the leave-one-out predictions from stage 1.

    fit_intercept : bool, default=True
        Include an intercept term in the non-negative Lasso stage.
        This is ignored for Cox models.

    vars_names : list of str, optional
        Feature names. If None, automatically generated as
        ``["X0", "X1", ..., "Xp"]``.

    family_spec : dict, optional
        Must contain key ``"family"`` with one of: ``{"gaussian", "binomial", "cox"}``.

    Attributes
    ----------
    uni_slopes\_ : ndarray of shape (n_features,)
        Slopes from the univariate models.

    uni_intercepts\_ : ndarray of shape (n_features,)
        Intercepts from the univariate models.

    loo_preds\_ : ndarray of shape (n_samples, n_features)
        Leave-one-out predictions from the univariate models.

    slopes\_ : ndarray of shape (n_lmdas, n_features)
        Final UniLasso slopes.

    intercept\_ : ndarray of shape (n_lmdas, 1)
        Final UniLasso intercepts.

    vars_names\_ : list of str
        Variable names used in the model.

    lmda_path\_ : ndarray of shape (n_lmdas,)
        Lambda values used in stage 2.

    Examples
    --------
    >>> model = UniLasso(family_spec={"family": "gaussian"})
    >>> model.fit(X, y)
    >>> y_hat = model.predict(X)
    >>> active = model.get_active_variables(lmda=0.1)
    >>> model.get_fitted_function()
    """
    def __init__(
            self, 
            lmda_path: Optional[np.ndarray]=None, 
            fit_intercept: bool=True, 
            vars_names: Optional[List[str]]=None, 
            family_spec: Optional[FamilySpec]=None,
    ) -> None:
        self.family_spec_ = family_spec or {"family": "gaussian"}
        self.family_ = self.family_spec_["family"].lower()
        self.lmda_path_ = lmda_path
        self.slopes_ = None
        self.intercept_ = None
        self.loo_slopes_ = None
        self.loo_intercept_ = None
        self.loo_preds_ = None
        self.uni_slopes_ = None
        self.uni_intercepts_ = None
        self.vars_names_ = vars_names
        self.fit_intercept_ = False if (self.family_=='cox') else fit_intercept
        self.offset_ = None

    def set_vars_names(
            self, 
            vars_names: List[str],
    ) -> None:
        self.vars_names_ = vars_names

    def set_lmda_path(
            self, 
            lmda_path: np.ndarray,
    ) -> None:
        self.lmda_path_ = lmda_path

    def _fit_univariate_gaussian(
            self, 
            X: np.ndarray,
            y: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        n_samples, _ = X.shape
        y = y[:, np.newaxis]                                                                                                
        x_mean = np.mean(X, axis=0, keepdims=True)                                                                         
        x_std = np.std(X, axis=0, keepdims=True)
        x_std[x_std == 0] = 1.0  
        x_prec = 1.0 / x_std                                                                                              
        y_mean = np.mean(y)                                                                                           
        Z = (X - x_mean) * x_prec                                                                                
        szy = np.mean(Z * y, axis=0, keepdims=True)                                                                 
        intercepts = y_mean - szy * x_mean * x_prec                                                                 
        slopes = szy * x_prec                                                                                         
        preds = szy * Z + y_mean                                                                                      
        H = (1.0 + Z*Z) / n_samples                                                                                 
        loo_preds = (-H * y + preds) / (1.0 - H)                                                                    
        if self.offset_ is not None:
            loo_preds += self.offset_[:,None]
        return {
            "intercepts": intercepts[0, :],
            "slopes": slopes[0, :],
            "preds": preds,
            "loo_preds": loo_preds,
        }

    def _fit_univariate_binomial(
            self, 
            X: np.ndarray,
            y: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        n, p = X.shape
        intercepts = np.empty(p)
        slopes = np.empty(p)
        preds = np.empty((n, p))
        loo_preds = np.empty((n, p))
        for j in range(p):
            glm = GLM(family_spec={"family": "binomial"}, p_value=False, preds_loo=True)
            glm.fit(X[:, j:j+1], y, offset=self.offset_)
            intercepts[j] = glm.intercept_
            slopes[j] = glm.slopes_[0]
            preds[:, j] = glm.predict(X[:, j:j+1], response_scale=False, offset=self.offset_)
            loo_preds[:, j] = glm.preds_loo_
        return {
            "intercepts": intercepts,
            "slopes": slopes,
            "preds": preds,
            "loo_preds": loo_preds,
        }

    def _fit_univariate_cox(
            self, 
            X: np.ndarray,
            y: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        n, p = X.shape
        intercepts = np.zeros(p)
        slopes = np.empty(p)
        preds = np.empty((n, p))
        loo_preds = np.empty((n, p))
        for j in range(p):
            glm = GLM(family_spec={"family": "cox"}, p_value=False, preds_loo=True)
            glm.fit(X[:, j:j+1], y, offset=self.offset_)
            intercepts[j] = glm.intercept_
            slopes[j] = glm.slopes_[0]
            preds[:, j] = glm.predict(X[:, j:j+1], response_scale=False, offset=self.offset_)
            loo_preds[:, j] = glm.preds_loo_
        return {
            "intercepts": intercepts,
            "slopes": slopes,
            "preds": preds,
            "loo_preds": loo_preds,
        }

    def _fit_univariate_model(
            self,
            X: np.ndarray,
            y: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        res = None
        if self.family_ == "gaussian":
            res = self._fit_univariate_gaussian(X, y)
        elif self.family_ == "binomial":
            res = self._fit_univariate_binomial(X, y)
        elif self.family_ == "cox":
            res = self._fit_univariate_cox(X, y)
        else:
            raise NotImplementedError(f"Family {self.family_} not implemented.")
        return res
    
    def _fit_gaussian(
            self, 
            X: np.ndarray, 
            y: np.ndarray,
    ) -> None:
        stage1 = self._fit_univariate_gaussian(X, y) if self.offset_ is None else self._fit_univariate_gaussian(X, y-self.offset_) 
        self._final_stage_lasso(X, y, stage1, "gaussian")

    def _fit_binomial(
            self, 
            X: np.ndarray, 
            y: np.ndarray,
    ) -> None:
        stage1 = self._fit_univariate_binomial(X, y)
        self._final_stage_lasso(X, y, stage1, "binomial")

    def _fit_cox(
            self, 
            X: np.ndarray,
            y: np.ndarray,
    ) -> None:
        stage1 = self._fit_univariate_cox(X, y)
        self._final_stage_lasso(X, y, stage1, "cox")

    def _final_stage_lasso(
            self, 
            X: np.ndarray,
            y: np.ndarray,
            stage1_results: Stage1Results, 
            family: Literal["gaussian", "binomial", "cox"]
    ) -> None:
        n, p = X.shape
        self.uni_intercepts_ = stage1_results["intercepts"]
        self.uni_slopes_ = stage1_results["slopes"]
        self.loo_preds_ = stage1_results["loo_preds"]
        if self.vars_names_ is None:
            self.vars_names_ = [f"X{i}" for i in range(p)]
        if self.lmda_path_ is None:
            self.lmda_path_ = generate_lmda_path(self.loo_preds_, y, family=family)
        glm_map = {
            "gaussian": ad.glm.gaussian(y=y) if family == "gaussian" else None,
            "binomial": ad.glm.binomial(y=y, link="logit") if family == "binomial" else None,
            "cox": ad.glm.cox(start=np.zeros(n), stop=y[:, 0], status=y[:, 1], dtype=np.float64) if family == "cox" else None,
        }
        state = ad.grpnet(
            X=np.asfortranarray(self.loo_preds_),
            glm=glm_map[family],
            lmda_path=self.lmda_path_,
            intercept=self.fit_intercept_,
            early_exit=False,
            constraints=[ad.constraint.lower(np.zeros(1)) for _ in range(p)],
            progress_bar=False,
            alpha=1.0,
            offsets=self.offset_
        )
        ad_slopes = state.betas.toarray()
        ad_intercepts = getattr(state, "intercepts", np.zeros(ad_slopes.shape[0]))
        self.slopes_ = ad_slopes * self.uni_slopes_    
        if self.fit_intercept_ : 
            self.intercept_ = ad_intercepts + np.sum(self.uni_intercepts_ * ad_slopes, axis=1)
            self.intercept_ = self.intercept_[:, None]  
        else : 
            self.intercept_ = np.zeros((self.slopes_.shape[0],1))

    def fit(
            self, 
            X: np.ndarray, 
            y: np.ndarray,
            offset: Optional[np.ndarray]=None
    ) -> None:
        if self.family_ == "cox":
            X = check_array(X)
            y = np.asarray(y, dtype=float)
            if y.ndim != 2 or y.shape[1] != 2:
                raise ValueError(f"For Cox family, y must be of shape (n_samples, 2): (time, status). Got {y.shape}.")
        else:
            X, y = check_X_y(X, y, y_numeric=True)
        self.offset_ = offset
        if self.family_ == "gaussian":
            self._fit_gaussian(X, y)
        elif self.family_ == "binomial":
            self._fit_binomial(X, y)
        elif self.family_ == "cox":
            self._fit_cox(X, y)
        else:
            raise NotImplementedError(f"Family {self.family_} not implemented.")

    def _inverse_link(
            self, 
            eta: np.ndarray,
    ) -> np.ndarray:
        if self.family_  == "binomial":
            return 1./(1.+np.exp(-eta))
        elif self.family_  == "cox":
            return np.exp(eta)
        else:
            raise NotImplementedError(f"Family '{self.family_ }' not supported.")

    def predict(
            self, 
            X: np.ndarray, 
            response_scale: bool=False, 
            offset: Optional[np.ndarray]=None,
    ) -> np.ndarray:
        check_is_fitted(self)
        X = check_array(X)
        eta_hat = X @ self.slopes_.T + self.intercept_.T
        if offset is not None:
            eta_hat += offset
        return self._inverse_link(eta_hat) if response_scale else eta_hat

    def get_active_variables(
            self, 
            lmda: Optional[float]=None, 
            tolerance: float=1e-10
    ) -> List[str]:
        check_is_fitted(self)
        j = int(np.argmin(np.abs(self.lmda_path_ - lmda))) if lmda is not None else 0
        return [self.vars_names_[i] for i, b in enumerate(self.slopes_[j]) if abs(b) > tolerance]

    def get_fitted_function(
            self, 
            lmda: Optional[float]=None, 
            tolerance: float=1e-10
    ) -> str:
        check_is_fitted(self)
        j = int(np.argmin(np.abs(self.lmda_path_ - lmda))) if lmda is not None else 0
        terms = [f"{self.intercept_[j,0]:.3f}"]
        terms += [f"{self.slopes_[j,i]:.3f}*{v}" for i,v in enumerate(self.vars_names_) if abs(self.slopes_[j,i])>tolerance]
        return " + ".join(terms)
    
class CVResult(TypedDict):
    cv_errors: np.ndarray
    lmda_path: np.ndarray
    prevalidated_preds: np.ndarray
    best_lmda: float
    n_folds: int
    active_set: List[str]

def cv(
        base: Union[UniLasso, Lasso], 
        X: np.ndarray, 
        y: np.ndarray, 
        n_folds: int, 
        lmda_path: Optional[np.ndarray]=None, 
        plot_cv_curve: bool=False, 
        cv1se: bool=False, 
        seed: int=305, 
        save_plots: Optional[str]=None, 
        offset: Optional[np.ndarray]=None,
) -> CVResult:
    """
    Cross-validation for Lasso or UniLasso models.

    If ``lmda_path`` is not provided:

    - For ``UniLasso``: the path is generated from the leave-one-out
      predictions of the univariate models.
    - For ``Lasso``: the path is generated from the design matrix ``X``.

    Parameters
    ----------
    base : UniLasso or Lasso instance
        The model to cross-validate. Must implement ``fit`` and ``predict`` and
        contain the attribute ``family_``.

    X : ndarray of shape (n_samples, n_features)
        Design matrix.

    y : ndarray
        Response vector for Gaussian/Binomial, or array of shape ``(n_samples, 2)``
        for Cox models, containing ``(time, status)``.

    n_folds : int
        Number of cross-validation folds.

    lmda_path : ndarray of shape (n_lmdas,), optional
        Regularization path. If None, it is generated automatically.

    plot_cv_curve : bool, default=False
        If True, plots the cross-validation R2 curve against ``-log(lambda)`` and
        annotates model size along the curve.

    cv1se : bool, default=False
        If True, selects the largest lambda within one standard error of the
        minimum validation error (1-SE rule). Otherwise, selects the minimizer.

    seed : int, default=305
        Random seed for fold shuffling.

    save_plots : str, optional
        If provided, the CV plot is saved to this file path.

    offset : ndarray, optional
        Optional observation specific offset added during fitting and prediction.

    Returns
    -------
    cv_result : dict
        A dictionary with the following fields:

        - ``cv_errors`` : ndarray of shape (n_folds, n_lmdas)
            Validation losses for each fold and lambda.

        - ``lmda_path`` : ndarray of shape (n_lmdas,)
            The lambda path used.

        - ``prevalidated_preds`` : ndarray of shape (n_samples,)
            Out-of-fold predictions at the selected lambda.

        - ``best_lmda`` : float
            Selected value of lambda.

        - ``n_folds`` : int
            Number of folds used.

        - ``active_set`` : list of str
            Names of active variables at the selected lambda.

    Examples
    --------
    >>> model = UniLasso(family_spec={"family": "gaussian"})
    >>> results = cv(model, X, y, n_folds=5)
    >>> results["best_lmda"]
    0.031
    >>> results["active_set"]
    ['X2', 'X7']
    >>> y_hat = model.predict(X)
    """
    def _glm_loss(
            y: np.ndarray, 
            eta_hat: np.ndarray, 
            family: str,
    ):
        if family == "gaussian":
            return np.mean((y - eta_hat)**2)
        elif family == "binomial":
            return ad.glm.binomial(y=y, link="logit").loss(eta_hat)
        elif family == "cox":
            n = y.shape[0]
            return ad.glm.cox(start=np.zeros(n), stop=y[:, 0], status=y[:, 1]).loss(eta_hat)
        else:
            raise NotImplementedError(f"Loss not implemented for {family}.")

    def _glm_r2(
            y: np.ndarray, 
            eta_hat: np.ndarray, 
            family: str,
    ):
        n = y.shape[0]
        if family == "gaussian":
            return 1. - np.mean((y - eta_hat)**2)/np.var(y)
        elif family == "binomial":
            y_bar = np.mean(y)
            eta_null = np.full_like(eta_hat, np.log(y_bar/(1-y_bar)))
            ll_sat = np.sum(y*np.log(y + 1e-15) + (1-y)*np.log(1-y + 1e-15))
            ll_model = np.sum(y*eta_hat - np.logaddexp(0, eta_hat))
            ll_null  = np.sum(y*eta_null - np.logaddexp(0, eta_null))
            return 1 - (ll_sat - ll_model)/(ll_sat - ll_null)
        elif family == "cox":
            l_sat = -n*ad.glm.cox(start=np.zeros(n), stop=y[:, 0], status=y[:, 1]).loss_full()
            l_model = -n*ad.glm.cox(start=np.zeros(n), stop=y[:, 0], status=y[:, 1]).loss(eta_hat)
            l_null = -n*ad.glm.cox(start=np.zeros(n), stop=y[:, 0], status=y[:, 1]).loss(np.zeros_like(eta_hat))
            return 1. - (l_sat-l_model)/(l_sat-l_null)
        else:
            raise NotImplementedError(f"Loss not implemented for {family}.")
    
    n, _ = X.shape
    rng = np.random.default_rng(seed)
    permutation = rng.permutation(n)
    fold_indices = np.array_split(permutation, n_folds)
    cv_errors, cv_r2s = [], []
    fam = base.family_
    if lmda_path is None:
        if getattr(base, "lmda_path_", None) is not None:
            lmda_path = base.lmda_path_
        else:
            if isinstance(base, UniLasso):
                Z = UniLasso(family_spec=base.family_spec_, fit_intercept=base.fit_intercept_)._fit_univariate_model(X, y)["loo_preds"]
            else : 
                Z = X
            lmda_path = generate_lmda_path(Z, y, family=fam)
    base.set_lmda_path(lmda_path)
    n_lmdas = len(lmda_path)
    prevalidated_preds = np.zeros((n, n_lmdas))
    for i in range(n_folds):
        train_indices = np.concatenate([fold_indices[j] for j in range(n_folds) if j != i])
        val_indices = fold_indices[i]
        X_train, y_train = X[train_indices], y[train_indices]
        X_val, y_val = X[val_indices], y[val_indices]
        offset_val = None if offset is None else offset[val_indices]
        offset_train = None if offset is None else offset[train_indices]
        base.fit(X_train, y_train, offset=offset_train)
        eta_val_hat = base.predict(X_val, response_scale=False, offset=offset_val)
        cv_errors.append(np.array([_glm_loss(y_val, eta_val_hat[:, k], fam) for k in range(n_lmdas)]))
        cv_r2s.append(np.array([_glm_r2(y_val, eta_val_hat[:, k], fam) for k in range(n_lmdas)]))
        prevalidated_preds[val_indices, :] = eta_val_hat
    cv_errors = np.stack(cv_errors)
    cv_r2s = np.stack(cv_r2s)
    cv_errors_mean = cv_errors.mean(axis=0)
    col = int(np.argmin(cv_errors_mean))
    if cv1se:
        se = float(np.std(cv_errors[:, col], ddof=1) / np.sqrt(n_folds))
        mask = cv_errors_mean <= (cv_errors_mean.min() + se)
        best_lmda_index = int(np.where(mask)[0][0])
    else:
        best_lmda_index = col
    best_lmda = float(lmda_path[best_lmda_index])
    prevalidated_preds = prevalidated_preds[:, best_lmda_index]
    if plot_cv_curve:
        base.fit(X, y)
        model_sizes = np.array([len(base.get_active_variables(lmda)) for lmda in base.lmda_path_])
    base.set_lmda_path(np.array([best_lmda]))
    base.fit(X, y)
    if plot_cv_curve:
        fig, ax = plt.subplots(figsize=(10, 5))
        xs = -np.log(lmda_path)
        cv_means = np.mean(cv_r2s, axis=0)
        cv_stds = np.std(cv_r2s, axis=0) / np.sqrt(n_folds)
        ax.plot(xs, cv_means, color="red", linewidth=2, label=f"CV R2")
        n_points = len(xs)
        n_labels = min(20, n_points)
        label_idxs = np.linspace(0, n_points - 1, n_labels, dtype=int)
        ax.errorbar(
            xs[label_idxs],
            cv_means[label_idxs],
            yerr=cv_stds[label_idxs],
            fmt="o",
            color="red",
            ecolor="black",
            elinewidth=0.8,
            capsize=3,
        )
        ymin, ymax = ax.get_ylim()
        y_offset = 0.02 * (ymax - ymin)
        for idx in label_idxs:
            x = xs[idx]
            yv = cv_means[idx]
            sz = model_sizes[idx]
            ax.text(x, yv + y_offset, str(sz), ha="center", va="bottom", fontsize=10, color="darkred")
        ax.set_title(f"best -log(λ) = {-np.log(best_lmda):.2f} | n_folds={n_folds}", fontsize=16, pad=15)
        ax.set_xlabel(r"$-\log(\lambda)$", fontsize=14)
        ylab = {
            "gaussian": "CV R²",
            "binomial": "CV Pseudo-R² (Deviance Explained)",
            "cox":      "CV Partial-Likelihood Pseudo-R²",
        }[fam]
        ax.set_ylabel(ylab, fontsize=14)
        ax.legend(loc="upper right", fontsize=12)
        ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
        active_vars = base.get_active_variables(best_lmda)
        chunk_size = 10
        chunks = [active_vars[i : i + chunk_size] for i in range(0, len(active_vars), chunk_size)]
        lines = [", ".join(map(str, chunk)) for chunk in chunks]
        text_str = "Active Set:\n" + "\n".join(lines)
        ax.text(
            0.50,
            0.10,
            text_str,
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=11,
            bbox=dict(facecolor="white", edgecolor="gray", alpha=0.6),
        )
        plt.tight_layout()
        if save_plots is not None:
            plt.savefig(save_plots, dpi=300)
        plt.show()
    return {
        "cv_errors": cv_errors,
        "lmda_path": lmda_path,
        "prevalidated_preds": prevalidated_preds,
        "best_lmda": best_lmda,
        "n_folds": n_folds,
        "active_set": base.get_active_variables(best_lmda),
    }

class BaseInteractionModel(BaseEstimator, ABC):
    """
    Base class for interaction discovery models.

    This class implements the common logic required for fitting models with
    pairwise interactions. It provides:

    - input standardization,
    - selection of interaction candidates or explicit interaction pairs,
    - optional hierarchy constraints (weak, strong),
    - fitting of triplet regressions for screening interactions,
    - p-value based interaction selection,
    - plotting utilities.

    Actual estimation of main effects and interactions must be implemented in
    subclasses via ``fit``, ``predict``, ``get_active_variables`` and
    ``get_fitted_function``.

    Parameters
    ----------
    interaction_candidates : list of int, optional
        Indices of features that are allowed to form interactions. If provided,
        all pairs ``(j, k)`` are generated such that ``j`` is in this list and
        ``k`` ranges over all other features. Mutually exclusive with
        ``interaction_pairs``.

    interaction_pairs : list of tuple(int, int), optional
        Explicit list of feature index pairs to consider as interactions.
        Mutually exclusive with ``interaction_candidates``.

    vars_names : list of str, optional
        Variable names. If None, names are generated as ``["X0", ..., "Xp"]``.

    zero_cutoff : float, default=1e-20
        Numerical tolerance used to determine whether a p-value is considered
        zero when scanning interactions.

    interactions_threshold : float, optional
        Absolute threshold for selecting interaction pairs. If None,
        the data-adaptive largest log-gap rule is used.

    save_plots : str, optional
        Directory where plots will be saved. If None, figures are not saved.

    family_spec : dict, optional
        Must contain a ``"family"`` key. Supports:
        ``"gaussian"``, ``"binomial"``, ``"cox"``.

    plot_cv_curve : bool, default=False
        Whether to plot cross-validation curves when applicable.

    cv1se : bool, default=False
        Whether to apply the 1-SE rule when choosing the optimal lambda.

    verbose : bool, default=False
        If True, prints progress and diagnostic information during fitting.

    Attributes
    ----------
    family\_ : str
        Lowercase model family name: ``"gaussian"``, ``"binomial"`` or ``"cox"``.

    interaction_candidates\_ : ndarray of shape (m,), optional
        Standardized version of ``interaction_candidates``.

    interaction_pairs\_ : ndarray of shape (k, 2), optional
        Standardized version of ``interaction_pairs``.

    triplet_regressors\_ : dict
        Dictionary mapping feature pairs ``(j, k)`` to triplet regressors.

    allowed_pairs\_ : list of tuple(int, int)
        Interaction pairs allowed after applying hierarchy constraints and
        removing unstable pairs.

    selected_pairs\_ : ndarray of shape (r, 2)
        Interaction pairs selected based on p-values.

    instable_pairs\_ : list of tuple(int, int)
        Pairs excluded because the triplet model was numerically unstable
        (rank deficiency, large condition number or leverage).

    main_effects_names\_ : list of str
        Names of main effect variables.

    interactions_names\_ : list of str
        Names of interactions ``"Xj*Xk"``.

    main_effects_active_set\_ : list of int, optional
        Active main effects when hierarchy is imposed.

    pvals\_ : dict
        Mapping from ``(name_j, name_k)`` to p-values for screening interactions.
        Only for allowed pairs.

    Notes
    -----
    **Triplet regression.**
    For each pair of features ``(j, k)``, a local model is fit on:

    .. math::
        [1, X_j, X_k, X_j X_k]

    to assess whether an interaction is statistically significant.

    **Hierarchy constraints.**
    If ``hierarchy = "strong"`` then only interactions with *both*
    variables active are allowed. If ``"weak"``, at least one must be active.

    **Unstable pairs.**
    Models with rank deficiency, large condition number or unit leverage are
    flagged as unstable and removed before selection.

    **Interaction selection.**
    If ``interactions_threshold`` is given:

    .. math::
        p_{jk} \\le \\text{threshold}

    Otherwise, the data-adaptive largest log-gap rule determines the cutoff.

    Subclasses must implement:

    - ``fit(X, y, **kwargs)``,
    - ``predict(X)``,
    - ``get_active_variables()``,
    - ``get_fitted_function()``.
    """
    def __init__(
        self,
        interaction_candidates: Optional[List[int]]=None,
        interaction_pairs: Optional[List[Tuple[int,int]]]=None,
        vars_names: Optional[List[str]]=None,
        zero_cutoff: float=1e-20,
        interactions_threshold: Optional[float]=None,
        save_plots: Optional[str]=None,
        family_spec: Optional[FamilySpec]=None,
        plot_cv_curve: bool=False,
        cv1se: bool=False,
        verbose: bool=False,
    ) -> None:
        if interaction_candidates is not None and interaction_pairs is not None:
            raise ValueError("Specify only one of interaction_candidates or interaction_pairs, not both.")
        self.family_spec_ = family_spec or {"family": "gaussian"}
        self.family_ = self.family_spec_["family"].lower()
        self.plot_cv_curve_ = plot_cv_curve
        self.cv1se_ = cv1se
        self.verbose_ = verbose
        self.interaction_candidates_ = np.asarray(interaction_candidates, dtype=int) if interaction_candidates is not None else None
        self.interaction_pairs_ = np.asarray(interaction_pairs, dtype=int) if interaction_pairs is not None else None
        self.vars_names_ = vars_names
        self.zero_cutoff_ = zero_cutoff
        self.interactions_threshold_ = interactions_threshold
        self.save_plots_ = save_plots
        self.triplet_regressors_ = None
        self.instable_pairs_ = []
        self.selected_pairs_ = None
        self.main_effects_names_ = None
        self.interactions_names_ = None
        self.hierarchy_ = None
        self.allowed_pairs_ = None
        self.n_features_ = None
        self.pvals_ = None
        self.main_effects_active_set_ = None

    @property
    def version(self) -> str:
        try:
            return pkg_version("uniPairs")
        except PackageNotFoundError:
            from uniPairs import __version__ as local_version
            return local_version
        
    def _check_and_std_input(
            self, 
            X: np.ndarray, 
            y: np.ndarray, 
            tolerance: float=1e-10,
    ) -> Tuple[np.ndarray, np.ndarray]:
        if self.family_ == "cox":
            X = check_array(X)
            y = np.asarray(y, dtype=float)
            if y.ndim != 2 or y.shape[1] != 2:
                raise ValueError(f"For Cox family, y must be of shape (n_samples, 2): (time, status). Got {y.shape}.")
        else:
            X, y = check_X_y(X, y, y_numeric=True)
        self.main_effects_stds = np.std(X, axis=0, ddof=1)
        zero_std_mask = np.abs(self.main_effects_stds) < tolerance
        if np.any(zero_std_mask):
            warnings.warn(f"Features at indices {np.where(zero_std_mask)[0]} have zero standard deviation and will be removed.")
            X = X[:, ~zero_std_mask]
        self.main_effects_means = np.mean(X, axis=0)
        self.main_effects_stds = self.main_effects_stds[~zero_std_mask]
        X = (X - self.main_effects_means) / self.main_effects_stds
        _, p = X.shape
        self.n_features_ = p
        if self.interaction_pairs_ is not None:
            if self.interaction_pairs_.max() >= p:
                raise ValueError("interaction_pairs contain indices out of range for X.")
        if self.interaction_candidates_ is not None:
            if self.interaction_candidates_.max() >= p:
                raise ValueError("interaction_candidates contain indices out of range for X.")
        return X, y
    
    def _init_triplet_model(
            self, 
            var_names: List[str],
    ) -> Union[OLS, GLM]:
        if self.family_ == "gaussian":
            return OLS(vars_names=var_names, fit_intercept=True, p_value=True)
        else:
            return GLM(family_spec=self.family_spec_, vars_names=var_names, fit_intercept=True, p_value=True)

    def _fit_triplet_models(
            self, 
            X: np.ndarray, 
            y: np.ndarray,
    ) -> None:
        if self.verbose_:
            print("Fitting triplet models ...")
        n, p = X.shape
        if not (n > 3):
            raise ValueError("Need at least 4 samples to fit triplet models.")
        active = set(self.main_effects_active_set_) if self.main_effects_active_set_ is not None else set()
        if len(active) == 0:
            self.hierarchy_ = None
        self._get_allowed_pairs(p, active)

        if self.verbose_:
            print(f"Fitting {p*(p-1)//2} triplet models...")
        self.triplet_regressors_ = {
            j: {
                k: self._init_triplet_model(
                    [self.main_effects_names_[j],
                     self.main_effects_names_[k],
                     f"{self.main_effects_names_[j]}*{self.main_effects_names_[k]}"]
                )
                for k in range(j + 1, p)
            }
            for j in range(p - 1)
        }
        total_pairs = len(self.allowed_pairs_)
        for count, (j, k) in enumerate(self.allowed_pairs_, start=1):
            A = np.column_stack([np.ones((n, 1)), X[:, j], X[:, k], X[:, j] * X[:, k]])
            rank = np.linalg.matrix_rank(A)
            cond_number = np.linalg.cond(A)
            if rank < 4 or cond_number > 1e12 or self._has_unit_leverage(A): 
                self.instable_pairs_.append((j, k))
            else : 
                self.triplet_regressors_[j][k].fit(A[:,1:], y)
            if self.verbose_ and count % max(1, total_pairs // 10) == 0:
                print(f"Progress: {count}/{total_pairs} triplets fitted...")
        if self.verbose_:
            print(f"Triplet models complete. {len(self.instable_pairs_)} unstable.")
        if self.instable_pairs_ is not None : 
            self.allowed_pairs_ = list(set(self.allowed_pairs_) - set(self.instable_pairs_))

    def _get_allowed_pairs(
            self, 
            p: int, 
            active: Optional[List[int]]=None
    ) -> None:
        
        if self.interaction_pairs_ is not None:
            self.allowed_pairs_ = [tuple(pair) for pair in self.interaction_pairs_]
        elif self.interaction_candidates_ is not None:
            allowed_pairs = []
            for j in self.interaction_candidates_:
                for k in range(p):
                    if j != k:
                        allowed_pairs.append((min(j, k), max(j, k)))
            self.allowed_pairs_ = list(set(allowed_pairs))
        else : 
            self.allowed_pairs_ = [(j, k) for j in range(p - 1) for k in range(j + 1, p)]
        
        if active is not None : 
            if self.hierarchy_ == "strong":
                self.allowed_pairs_ = [(j,k) for (j,k) in self.allowed_pairs_ if (j in active and k in active)]
            elif self.hierarchy_ == "weak":
                self.allowed_pairs_ = [(j,k) for (j,k) in self.allowed_pairs_ if (j in active or k in active)]
            elif self.hierarchy_ is not None:
                raise ValueError("incorrect value for hierarchy")
            
        if self.instable_pairs_ is not None : 
            self.allowed_pairs_ = list(set(self.allowed_pairs_) - set(self.instable_pairs_))
    
    def _scan_interactions(self) -> None:
        if self.verbose_:
            print("Scanning interactions ...")
        pvals_ea = {(j, k): self.triplet_regressors_[j][k].p_value_ for (j, k) in self.allowed_pairs_}
        pvals_ea_sorted = sorted(pvals_ea.items(), key=lambda x: x[1])
        num_zeros = len(pvals_ea_sorted) - len([p for _, p in pvals_ea_sorted if p > self.zero_cutoff_])

        if self.interactions_threshold_ is not None:
            selected_pairs = [pair for (pair, pval) in pvals_ea_sorted if pval <= self.interactions_threshold_]
        else:
            tmp = [pval for _, pval in pvals_ea_sorted if pval > self.zero_cutoff_]
            if len(tmp) <= 1:
                selected_pairs = [pair for (pair, _) in pvals_ea_sorted]
            else:
                tmp = np.log(np.array(tmp))
                i_tmp = np.argmax(tmp[1:] - tmp[:-1]) + num_zeros
                selected_pairs = [pair for (pair, _) in pvals_ea_sorted[: i_tmp + 1]]

        self.selected_pairs_ = np.array(selected_pairs)
        self.pvals_ = {(self.main_effects_names_[j],self.main_effects_names_[k]):pval for (j,k),pval in pvals_ea.items()}
        if self.verbose_:
            add_on_tmp = "largest log-gap rule" if self.interactions_threshold_ is None else f" threshold={self.interactions_threshold_:.2e}"
            print(f"Selected {len(selected_pairs)} interaction pairs. ({add_on_tmp})")

    def _plot_cv_curve(
            self, 
            p: int,
    ) -> None:
        
        scan_coefs = np.zeros((p, p))
        pvals = np.ones((p, p))
        for j, k in self.allowed_pairs_:
            pvals[j, k] = self.triplet_regressors_[j][k].p_value_
            scan_coefs[j, k] = np.abs(self.triplet_regressors_[j][k].slopes_[-1])
        mask = np.triu(np.ones_like(pvals, dtype=bool), k=1)
        pv = pvals[mask]
        plt.figure(figsize=(8, 5))
        plt.hist(-np.log(np.maximum(pv,self.zero_cutoff_)), bins=int(len(pv) / 20), edgecolor="black")
        sel_pv = [pvals[j, k] for j, k in self.selected_pairs_]
        plt.scatter(-np.log(np.maximum(sel_pv,self.zero_cutoff_)), np.zeros_like(sel_pv), color="orange", s=50, label="selected pairs", zorder=10)
        title = "Interaction -log(p-values) from triplet models | " 
        title += "largest log-gap rule" if self.interactions_threshold_ is None else f" threshold={self.interactions_threshold_:.2e}"
        plt.title(title)
        plt.xlabel("-log(p-value)")
        plt.ylabel("Count")
        plt.legend()
        plt.tight_layout()
        if self.save_plots_:
            plt.savefig(self.save_plots_+"/interaction_pvalues_histogram.png", dpi=300)
        plt.show()

        mask = np.tril(np.ones_like(pvals, dtype=bool), k=0)
        plt.figure(figsize=(8, 8))
        ax = sns.heatmap(
            pvals,
            mask=mask,
            cmap="viridis",
            xticklabels=self.main_effects_names_,
            yticklabels=self.main_effects_names_,
            vmin=0,
            vmax=1,
            square=True,
            cbar_kws={"shrink": 0.8},
        )
        ax.set_facecolor("white")
        for j, k in self.selected_pairs_:
            ax.text(k + 0.5, j + 0.5, "★", ha="center", va="center", color="white", fontsize=16, zorder=10)
        plt.title(title)
        plt.tight_layout()
        if self.save_plots_:
            plt.savefig(self.save_plots_+"/interaction_pvalues_heatmap.png", dpi=300)
        plt.show()

    def _make_interactions(
            self, 
            X: np.ndarray, 
            S: np.ndarray, 
            M: Optional[np.ndarray]=None, 
            vars_names: Optional[List[str]]=None,
    ) -> Tuple[np.ndarray, List[str]]:
        n, p = X.shape
        assert isinstance(S, np.ndarray)
        if M is None : 
            M = np.ones((p,p))

        if S.ndim == 1:
            assert np.all(S[:-1]<=S[1:]) 
            pp = len(S)
            num_pairs = pp * (pp - 1) // 2
            if self.verbose_:
                print(f"Constructing interaction matrix with # pairs = {num_pairs}")
            out = np.empty((n, num_pairs))
            colnames = []
            idx = 0
            for j in range(pp - 1):
                for k in range(j + 1, pp):
                    out[:, idx] = X[:, S[j]] * X[:, S[k]] * M[S[j],S[k]]
                    colnames.append(f"{vars_names[S[j]]}*{vars_names[S[k]]}" if vars_names is not None else f"X{S[j]}*X{S[k]}")
                    idx += 1  
        elif S.ndim == 2:
            assert S.shape[1] == 2
            num_pairs = S.shape[0]
            if self.verbose_:
                print(f"Constructing interaction matrix with # pairs = {num_pairs}")
            out = np.empty((n, num_pairs))
            colnames = []
            for i in range(num_pairs):
                j, k = S[i]
                assert j < k
                out[:, i] = X[:, j] * X[:, k] * M[j,k]
                colnames.append(f"{vars_names[j]}*{vars_names[k]}" if vars_names is not None else f"X{j}*X{k}")
        else:
            raise ValueError("S must be either 1D or 2D array")
        return out, colnames

    def _inverse_link(
            self, 
            eta: np.ndarray,
    ) -> np.ndarray:
        if self.family_  == "binomial":
            return 1./(1.+np.exp(-eta))
        elif self.family_  == "cox":
            return np.exp(eta)
        else:
            raise NotImplementedError(f"Family '{self.family_ }' not supported.")

    def _has_unit_leverage(
            self, 
            X: np.ndarray, 
            tolerance: float=1e-10,
    ) -> bool:
        Q, _ = np.linalg.qr(X)
        h = np.sum(Q**2, axis=1)
        return np.any(h >= 1 - tolerance)
    
    @abstractmethod
    def fit(
        self, 
        X: np.ndarray, 
        y: np.ndarray, 
        **kwargs: Any,
    ) -> None:
        pass

    @abstractmethod
    def get_active_variables(self) -> List[str]:
        pass

    @abstractmethod
    def get_fitted_function(
        self, 
        tolerance: float=1e-10,
    ) -> str:
        pass

    @abstractmethod
    def predict(
        self, 
        X: np.ndarray,
    ) -> np.ndarray:
        pass
  
class UniPairsTwoStage(BaseInteractionModel):
    """
    Two-stage UniPairs model for estimation of main effects and interactions.

    Parameters
    ----------
    hierarchy : {"weak", "strong", None}, optional
        Type of hierarchy constraint enforced between main effects and
        interactions. If None, no hierarchy is used.

    lmda_path_main_effects : ndarray of shape (n_lmdas,), optional
        Lambda path for the UniLasso in stage 1. If None, it is generated
        automatically.

    lmda_path_interactions : ndarray of shape (n_lmdas,), optional
        Lambda path for the Lasso in stage 2. If None, it is generated
        automatically.

    n_folds_main_effects : int, default=10
        Number of folds for cross-validation of main effects.

    n_folds_interactions : int, default=10
        Number of folds for cross-validation of interactions.

    **kwargs : dict
        Additional keyword arguments passed to ``BaseInteractionModel``.

    Attributes
    ----------
    main_effects_regressor\_ : UniLasso
        Fitted model for main effects after stage 1.

    interactions_regressor\_ : Lasso
        Fitted model for interaction terms after stage 2.

    lmda_path_main_effects\_ : ndarray of shape (n_lmdas,)
        Lambda path used in stage 1.

    lmda_path_interactions\_ : ndarray of shape (n_lmdas,)
        Lambda path used in stage 2.

    stage1_cv_errors\_ : ndarray of shape (n_folds_main_effects, n_lmdas)
        Cross-validation errors for main effects.

    stage2_cv_errors\_ : ndarray of shape (n_folds_interactions, n_lmdas)
        Cross-validation errors for interactions.

    main_effects_active_set\_ : ndarray of indices
        Set of active main effects.

    interactions_active_set\_ : ndarray of indices
        Set of active interactions.

    selected_pairs\_ : ndarray of shape (r, 2)
        Interaction index pairs selected after triplet screening.

    Notes
    -----
    This estimator fits a linear model of the form using 
    a **two-stage procedure**.

    **Stage 1 — Main effects:**

    A UniLasso regression is used to select and estimate main effects. The
    regularization parameter is selected via K-fold cross-validation using
    ``n_folds_main_effects``. The path of lambda values (``n_lmdas`` long)
    may be user-specified or generated automatically.

    **Stage 2 — Interaction screening and refitting:**
    
    Triplet regressions are fit for every allowed pair ``(j, k)`` to obtain
    p-values for interaction terms. Unstable models (rank deficiency, large
    condition number, or unit leverage) are discarded.

    Interaction candidates are selected either via a user-defined p-value
    threshold or the largest log-gap rule. A Lasso model is then fitted on
    the selected interaction features with cross-validation using ``n_folds_interactions`` and a separate
    ``n_lmdas`` lambda path.

    Both stages apply hierarchy if specified:

    - ``hierarchy="strong"``: interactions allowed only if **both** main effects are active,
    - ``hierarchy="weak"``: allowed if **at least one** is active,
    - ``None``: no hierarchy imposed.

    Coefficients are finally converted back to the **original scale** of the
    input variables.

    During prediction, interaction features are generated for only
    the selected pairs, and both components are added. 
    If a non-Gaussian family is used, ``response_scale=True`` applies the inverse
    link.

    Examples
    --------
    >>> model = UniPairsTwoStage(
    ...     interaction_candidates=[0, 3, 5],
    ...     hierarchy="weak",
    ...     n_folds_main_effects=5,
    ...     n_folds_interactions=5,
    ... )
    >>> model.fit(X, y)
    >>> y_pred = model.predict(X)
    >>> model.get_active_variables()
    ['X0', 'X3', 'X5', 'X0*X3']
    """
    
    def __init__(
        self,
        hierarchy: Optional[Literal["weak", "strong"]]=None,
        lmda_path_main_effects: Optional[np.ndarray]=None,
        lmda_path_interactions: Optional[np.ndarray]=None,
        n_folds_main_effects: int=10,
        n_folds_interactions: int=10,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        if hierarchy not in (None, "weak", "strong"):
            raise ValueError("hierarchy must be one of None, 'weak', or 'strong'.")
        self.hierarchy_ = hierarchy
        self.main_effects_regressor_ = UniLasso(lmda_path=lmda_path_main_effects, family_spec=self.family_spec_)
        self.interactions_regressor_ = Lasso(lmda_path=lmda_path_interactions, family_spec=self.family_spec_)
        self.n_folds_main_effects_ = n_folds_main_effects
        self.n_folds_interactions_ = n_folds_interactions
        self.stage1_cv_errors_ = None
        self.stage2_cv_errors_ = None
        self.lmda_path_main_effects_ = lmda_path_main_effects
        self.lmda_path_interactions_ = lmda_path_interactions
        
    def _regress_main_effects(
            self, 
            X: np.ndarray, 
            y: np.ndarray, 
            tolerance: float=1e-10,
    ) -> None:
        if self.verbose_:
            print("[Stage 1] Fitting main effects with UniLasso...")
        self.main_effects_names_ = self.vars_names_ or [f"X{j}" for j in range(self.n_features_)]
        self.main_effects_regressor_.set_vars_names(self.main_effects_names_)
        save_plots = self.save_plots_+"/main_effects_cv_curve_unilasso.png" if self.save_plots_ else None
        cv_results = cv(
            base=self.main_effects_regressor_,
            X=X,
            y=y,
            n_folds=self.n_folds_main_effects_,
            lmda_path=self.lmda_path_main_effects_,
            plot_cv_curve=self.plot_cv_curve_,
            save_plots=save_plots,
            cv1se=self.cv1se_,
        ) 
        self.lmda_path_main_effects_ = cv_results["lmda_path"]
        self.stage1_cv_errors_ = cv_results["cv_errors"]
        self.prevalidated_preds_ = cv_results["prevalidated_preds"]                                                     
        main_effects_slopes = self.main_effects_regressor_.slopes_                                               
        self.main_effects_active_set_ = np.where(np.abs(main_effects_slopes) > tolerance)[1]
        if len(self.main_effects_active_set_) == 0:
            self.hierarchy_ = None
            warnings.warn("no main effects found. Dropping the hierarchy constraint") 
        if self.verbose_:
            n_active = len(self.main_effects_active_set_)
            print(f"[Stage 1] Done. Active main effects: {n_active}/{self.n_features_}")

    def _regress_interactions(
            self, 
            X: np.ndarray, 
            y: np.ndarray, 
            tolerance: float=1e-10
    ) -> None:
        if self.verbose_:
            print("[Stage 2] Fitting interactions with Lasso...")

        _, p = X.shape
        check_is_fitted(self.main_effects_regressor_)
        if self.triplet_regressors_ is None:
            raise RuntimeError("triplet_regressors_ not initialized. Call _fit_triplet_models first.")

        self._scan_interactions()
        if self.plot_cv_curve_:
            self._plot_cv_curve(p)

        stage2_X, self.interactions_names_ = self._make_interactions(X, self.selected_pairs_, vars_names=self.main_effects_names_)       
        self.interactions_regressor_.set_vars_names(self.interactions_names_)
        if self.family_spec_['family'] == 'gaussian' : 
            stage2_y = y - self.prevalidated_preds_  
            offset = None
        else : 
            offset = self.prevalidated_preds_ 
            stage2_y = y

        save_plots = self.save_plots_+"/interactions_cv_curve_lasso.png" if self.save_plots_ else None
        cv_results = cv(
            base=self.interactions_regressor_,
            X=stage2_X,
            y=stage2_y,
            n_folds=self.n_folds_interactions_,
            lmda_path=self.lmda_path_interactions_,
            plot_cv_curve=self.plot_cv_curve_,
            save_plots=save_plots,
            cv1se=False,
            offset=offset
        )
        self.lmda_path_interactions_ = cv_results["lmda_path"]
        self.stage2_cv_errors_ = cv_results["cv_errors"]
        stage2_slopes = self.interactions_regressor_.slopes_                                                               
        self.interactions_active_set_ = np.where(np.abs(stage2_slopes) > tolerance)[1]
        if self.verbose_:
            n_active = len(self.interactions_active_set_)
            print(f"[Stage 2] Done. Active interactions: {n_active}/{len(self.selected_pairs_)}")

    def _convert_to_original_scale(self) -> None:
        main_slopes = np.empty((1, self.n_features_))
        main_intercept = 0.0
        interactions_slopes = np.empty((1, len(self.selected_pairs_)))
        interactions_intercept = 0.0

        for idx, (j, k) in enumerate(self.selected_pairs_):
            interactions_slopes[0, idx] = self.interactions_regressor_.slopes_[0, idx] / (self.main_effects_stds[j] * self.main_effects_stds[k])
            interactions_intercept += interactions_slopes[0, idx] * (self.main_effects_means[j] * self.main_effects_means[k])
        self.interactions_regressor_.slopes_ = interactions_slopes
        self.interactions_regressor_.intercept_[0,0] = self.interactions_regressor_.intercept_[0,0] + interactions_intercept

        for j in range(self.n_features_):
            main_slopes[0, j] = self.main_effects_regressor_.slopes_[0, j] / self.main_effects_stds[j]
            for idx, (jj, kk) in enumerate(self.selected_pairs_):
                if jj == j:
                    main_slopes[0, j] -= self.interactions_regressor_.slopes_[0, idx] * self.main_effects_means[kk] 
                if kk == j:
                    main_slopes[0, j] -= self.interactions_regressor_.slopes_[0, idx] * self.main_effects_means[jj]
            main_intercept -= self.main_effects_regressor_.slopes_[0, j] * self.main_effects_means[j] / self.main_effects_stds[j]
        self.main_effects_regressor_.slopes_ = main_slopes
        self.main_effects_regressor_.intercept_[0,0] = self.main_effects_regressor_.intercept_[0,0] + main_intercept

    def fit(
            self, 
            X: np.ndarray, 
            y: np.ndarray, 
            tolerance: float=1e-10
    ) -> None:
        X, y = self._check_and_std_input(X, y, tolerance)
        print(f"=== Starting UniPairs-2stage fit with {self.n_features_} features ===")
        self._regress_main_effects(X, y, tolerance=tolerance)
        if self.n_features_ == 1:
            if self.verbose_:
                print("[Stage 2] Skipped (only one feature).")
            return
        self._fit_triplet_models(X, y)
        self._regress_interactions(X, y, tolerance=tolerance)
        self._convert_to_original_scale()
        self.main_effects_active_set_ = np.where(np.abs(self.main_effects_regressor_.slopes_) > tolerance)[1]
        self.interactions_active_set_ = np.where(np.abs(self.interactions_regressor_.slopes_) > tolerance)[1]
        if self.verbose_:
            print("=== UniPairs-2stage fit complete ===\n")

    def get_active_variables(self) -> List[str]:
        check_is_fitted(self.main_effects_regressor_)
        check_is_fitted(self.interactions_regressor_)
        active_vars = []
        for i in self.main_effects_active_set_:
            active_vars.append(self.main_effects_names_[i])
        if self.n_features_ > 1:
            for i in self.interactions_active_set_:
                active_vars.append(self.interactions_names_[i])
        return active_vars

    def get_fitted_function(
            self, 
            tolerance: float=1e-10
    ) -> str:
        check_is_fitted(self.main_effects_regressor_)
        check_is_fitted(self.interactions_regressor_)
        fitted_model_rep = self.main_effects_regressor_.get_fitted_function(self.main_effects_regressor_.lmda_path_[0], tolerance)+ " + "
        if self.n_features_ > 1:
            fitted_model_rep = fitted_model_rep + self.interactions_regressor_.get_fitted_function(self.interactions_regressor_.lmda_path_[0], tolerance)
        return fitted_model_rep

    def predict(
            self, 
            X: np.ndarray, 
            response_scale: bool=False
    ) -> np.ndarray:
        check_is_fitted(self.main_effects_regressor_)
        check_is_fitted(self.interactions_regressor_)
        X = check_array(X)
        y1_pred = self.main_effects_regressor_.predict(X)[:, 0]                                                           
        y2_pred = 0
        if self.n_features_ > 1:
            stage2_X, _ = self._make_interactions(X, self.selected_pairs_)
            y2_pred = self.interactions_regressor_.predict(stage2_X)[:, 0]                                          
        eta_hat = y1_pred + y2_pred
        return self._inverse_link(eta_hat) if response_scale else eta_hat
  
class UniPairsOneStage(BaseInteractionModel):
    """
    One-stage UniPairs model for estimation of main effects and interactions.

    Parameters
    ----------
    lmda_path : ndarray of shape (n_lmdas,), optional
        Lambda path for the joint UniLasso fit. If None, it is generated
        automatically.

    n_folds : int, default=10
        Number of folds for cross-validation when selecting the regularization
        parameter.

    **kwargs : dict
        Additional keyword arguments passed to ``BaseInteractionModel`` such as
        hierarchy, plotting options, and verbosity.

    Attributes
    ----------
    regressor\_ : UniLasso
        Fitted UniLasso model containing both main-effect and interaction terms.

    lmda_path\_ : ndarray of shape (n_lmdas,)
        Lambda path used during CV.

    cv_errors\_ : ndarray of shape (n_folds, n_lmdas)
        Cross-validation errors over the lambda path.

    selected_pairs\_ : ndarray of shape (r, 2)
        Interaction index pairs retained after triplet screening.

    main_effects_active_set\_ : ndarray of indices
        Active main effects identified after rescaling.

    interactions_active_set\_ : ndarray of indices
        Active interaction effects identified after rescaling.

    Notes
    -----
    This estimator fits a linear model in both main effects and interactions 
    in **one-stage**.

    Triplet regressions are fit for every allowed pair ``(j, k)`` to obtain
    p-values for interaction terms. Unstable models (rank deficiency, large
    condition number, or unit leverage) are discarded.

    Interaction candidates are selected either via a user-defined p-value
    threshold or the largest log-gap rule.

    After screening, a **single UniLasso model** is fitted on the expanded design
    combining all main effects and the selected interactions.

    Cross-validation over a path of ``n_lmdas`` lambda values is performed once,
    using ``n_folds`` folds.

    All coefficients are finally transformed back to the **original scale** of the
    input variables. Active sets for both main effects and interactions are
    extracted from the refitted coefficients.

    During prediction, interaction features are generated only for the
    selected pairs, stacked alongside main effects, and passed through the model.
    If a non-Gaussian family is used, ``response_scale=True`` applies the inverse
    link.

    Examples
    --------
    >>> model = UniPairsOneStage(
    ...     n_folds=5,
    ... )
    >>> model.fit(X, y)
    >>> y_pred = model.predict(X)
    >>> model.get_active_variables()
    ['X0', 'X1*X4', 'X3']

    """
    def __init__(
        self, 
        lmda_path: Optional[np.ndarray]=None, 
        n_folds: int=10, 
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.regressor_ = UniLasso(lmda_path=lmda_path, family_spec=self.family_spec_)
        self.n_folds_ = n_folds
        self.cv_errors_ = None
        self.lmda_path_ = lmda_path
        self.hierarchy_ = None

    def _convert_to_original_scale_and_get_active_sets(
            self, 
            tolerance: float=1e-10,
    ) -> None:
        main_effects_slopes = self.regressor_.slopes_[:1,:self.n_features_]                                                          
        interactions_slopes = self.regressor_.slopes_[:1,self.n_features_:]
        main_effects_new_slopes = np.empty_like(main_effects_slopes)
        interactions_new_slopes = np.empty_like(interactions_slopes)
        intercept_new = self.regressor_.intercept_.copy()
        for idx, (j, k) in enumerate(self.selected_pairs_):
            interactions_new_slopes[0, idx] = interactions_slopes[0, idx] / (self.main_effects_stds[j] * self.main_effects_stds[k])
            intercept_new += interactions_new_slopes[0, idx] * (self.main_effects_means[j] * self.main_effects_means[k])
        for j in range(self.n_features_):
            main_effects_new_slopes[0, j] = main_effects_slopes[0, j] / self.main_effects_stds[j]
            for idx, (jj, kk) in enumerate(self.selected_pairs_):
                if jj == j:
                    main_effects_new_slopes[0, j] -= interactions_new_slopes[0, idx] * self.main_effects_means[kk] 
                if kk == j:
                    main_effects_new_slopes[0, j] -= interactions_new_slopes[0, idx] * self.main_effects_means[jj]
            intercept_new -= main_effects_slopes[0, j] * self.main_effects_means[j] / self.main_effects_stds[j]
        
        self.main_effects_active_set_ = np.where(np.abs(main_effects_new_slopes) > tolerance)[1]
        self.interactions_active_set_ = np.where(np.abs(interactions_new_slopes) > tolerance)[1]

        self.regressor_.slopes_ = np.hstack([main_effects_new_slopes, interactions_new_slopes])
        self.regressor_.intercept_ = intercept_new

    def fit(
            self, 
            X: np.ndarray, 
            y: np.ndarray, 
            tolerance: float=1e-10,
    ) -> None:
        X, y = self._check_and_std_input(X, y, tolerance)
        self.main_effects_names_ = self.vars_names_ or [f"X{j}" for j in range(self.n_features_)]
        if self.verbose_:
            print(f"=== Starting UniPairs fit with {self.n_features_} features ===")
        if self.n_features_ > 1 : 
            self._fit_triplet_models(X, y)
            self._scan_interactions()
            if self.plot_cv_curve_:
                self._plot_cv_curve(self.n_features_)
            interactions_X, self.interactions_names_ = self._make_interactions(X, self.selected_pairs_, vars_names=self.main_effects_names_)        
            full_X = np.hstack([X,interactions_X])
        else :
            full_X = X
            self.interactions_names_ = []
        self.regressor_.set_vars_names(self.main_effects_names_+self.interactions_names_)
        if self.verbose_:
            print("Cross-validating UniLasso ...")
        save_plots = self.save_plots_+"/cv_curve_unilasso.png" if self.save_plots_ else None
        cv_results = cv(
            base=self.regressor_,
            X=full_X,
            y=y,
            n_folds=self.n_folds_,
            lmda_path=self.lmda_path_ ,
            plot_cv_curve=self.plot_cv_curve_,
            save_plots=save_plots,
            cv1se=self.cv1se_
        ) 
        self.lmda_path_ = cv_results['lmda_path']
        self.cv_errors_ = cv_results['cv_errors']
        self._convert_to_original_scale_and_get_active_sets(tolerance)
        if self.verbose_:
            print("=== UniPairs fit complete ===\n")

    def get_active_variables(self) -> List[str]:
        check_is_fitted(self.regressor_)
        active_vars = []
        for i in self.main_effects_active_set_:
            active_vars.append(self.main_effects_names_[i])
        if self.n_features_>1:
            for i in self.interactions_active_set_:
                active_vars.append(self.interactions_names_[i])
        return active_vars
    
    def get_fitted_function(
            self, 
            tolerance: float=1e-10,
    ) -> str:
        check_is_fitted(self.regressor_)
        return self.regressor_.get_fitted_function(self.regressor_.lmda_path_[0],tolerance) 
         
    def predict(
            self, 
            X: np.ndarray, 
            response_scale: bool=False
    ) -> np.ndarray:
        check_is_fitted(self.regressor_)
        X = check_array(X)
        if self.n_features_>1:
            interactions_X, _ = self._make_interactions(X,self.selected_pairs_)
            full_X = np.hstack([X,interactions_X])
        else : 
            full_X = X
        eta_hat = self.regressor_.predict(full_X)[:,0]   
        return self._inverse_link(eta_hat) if response_scale else eta_hat  

class UniPairs(BaseEstimator):
    """
    Unified wrapper for UniPairs interaction models.

    This class provides a high-level interface for fitting either the **one-stage**
    or **two-stage** UniPairs procedure. It delegates all computations to an
    internal model (``UniPairsOneStage`` or ``UniPairsTwoStage``).

    Parameters
    ----------
    two_stage : bool, default=True
        Determines which UniPairs procedure to use:

        - ``True``: use the two-stage UniPairs estimator  
        - ``False``: use the one-stage UniPairs estimator  

    **kwargs : dict
        Additional keyword arguments forwarded directly to the selected internal
        model. 

    Attributes
    ----------
    model\_ : UniPairsOneStage or UniPairsTwoStage
        The underlying fitted UniPairs estimator. Set after calling ``fit``.

    two_stage : bool
        Whether the wrapper is using the two-stage or one-stage method.

    kwargs : dict
        Saved keyword arguments passed at construction time.

    version : str or None
        Version string inherited from the internal estimator (read-only).  
        Returns ``None`` if the model has not yet been fitted.

    Notes
    -----
    This class does **not** implement modeling logic itself. Instead:

    1. During ``fit``:

    - If ``two_stage=True``, an instance of ``UniPairsTwoStage`` is created and
        fitted.

    - If ``two_stage=False``, an instance of ``UniPairsOneStage`` is created and
        fitted.

    2. All subsequent calls to ``predict``, ``get_active_variables``,
    ``get_fitted_function`` are delegated to the fitted internal model.

    Examples
    --------
    >>> model = UniPairs(two_stage=True, n_folds=5)
    >>> model.fit(X, y)
    >>> y_pred = model.predict(X)
    >>> model.get_active_variables()
    ['X0', 'X2', 'X0*X2']

    Switching to one-stage:

    >>> model = UniPairs(two_stage=False, n_folds=5)
    >>> model.fit(X, y)
    >>> model.get_fitted_function()
    '1.203 + 0.44*X0 + 0.08*X0*X3'

    """
    def __init__(
            self, 
            two_stage: bool=True, 
            **kwargs: Any,
    ):
        self.two_stage = two_stage
        self.kwargs = kwargs
        self.model_ = None    

    def fit(
            self, 
            X: np.ndarray, 
            y: np.ndarray, 
            **fit_kwargs: Any,
    ) -> None:
        if self.two_stage:
            self.model_ = UniPairsTwoStage(**self.kwargs)
        else:
            self.model_ = UniPairsOneStage(**self.kwargs)
        return self.model_.fit(X, y, **fit_kwargs)

    def predict(
            self, 
            X: np.ndarray, 
            **kwargs: Any,
    ) -> np.ndarray:
        return self.model_.predict(X, **kwargs)

    def get_active_variables(
            self, 
            *args: Any, 
            **kwargs: Any,
    ) -> List[str]:
        return self.model_.get_active_variables(*args, **kwargs)

    def get_fitted_function(
            self, 
            *args: Any, 
            **kwargs: Any,
    ) -> str:
        return self.model_.get_fitted_function(*args, **kwargs)

    @property
    def version(self) -> Optional[str]:
        return self.model_.version if self.model_ is not None else None