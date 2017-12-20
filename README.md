# Dedalus [![Build Status](https://travis-ci.org/mwhittaker/dedalus.svg?branch=master)](https://travis-ci.org/mwhittaker/dedalus)
A Dedalus interpreter. The syntax and semantics of Dedalus (and Dedalus+ and
Dedalus^S) are defined in [[1]][alvaro_paper] and [[2]][marczak_paper].

## Getting Started
This project uses Python 3.6. We recommend using `conda` and `pip` to install
the right version of Python and all of the dependencies:

```bash
conda create --name dedalus python=3.6.1
source activate dedalus
pip install -r requirements.txt
```

## Syntax Highlighting
For Dedalus syntax highlighting, see https://github.com/mwhittaker/dedalus-vim.

\[1]: Alvaro, Peter, et al. "Dedalus: Datalog in time and space." _Datalog Reloaded_ (2011): 262-281.

\[2]: Marczak, William, et al. "Confluence analysis for distributed programs: A model-theoretic approach." _Datalog in Academia and Industry_ (2012): 135-147.

[alvaro_paper]: https://scholar.google.com/scholar?cluster=4658639044512647014
[marczak_paper]: https://scholar.google.com/scholar?cluster=17678162482015246510
