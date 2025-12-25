# uniPairs

_Univariate–guided interaction modeling in Python._

`uniPairs` implements procedures for discovering and estimating pairwise interactions in high-dimensional generalized linear models, built on top of the [`adelie`](https://jamesyang007.github.io/adelie) library.

The package provides:

- **UniLasso**
- **Lasso / GLM wrappers** over `adelie.grpnet` for Gaussian, binomial and Cox models  
- **UniPairs (one-stage and two-stage)** interaction models:
  - support for Gaussian, logistic, and Cox regression

---

## Installation

```bash
pip install uniPairs

## Citation

If you use this package in your research, please cite:

```bibtex
@article{echarghaoui2025univariate, 
  title={Univariate-Guided Interaction Modeling}, 
  author={Echarghaoui, Aymen and Tibshirani, Robert}, 
  journal={arXiv preprint arXiv:2512.14413}, 
  year={2025} 
}
