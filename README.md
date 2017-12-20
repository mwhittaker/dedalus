# Dedalus [![Build Status](https://travis-ci.org/mwhittaker/dedalus.svg?branch=master)](https://travis-ci.org/mwhittaker/dedalus)
A Dedalus interpreter. The syntax and semantics of Dedalus (and Dedalus+ and
Dedalus^S) are defined in [1] and [2].

## Getting Started
This project uses Python 3.6. We recommend using `conda` and `pip` to install
the right version of Python and all of the dependencies:

```bash
conda create --name dedalus python=3.6.1
source activate dedalus
pip install -r requirements.txt
```

Then, use [`dedalus.py`](dedalus/dedalus.py) to manipulate Dedalus programs:

```bash
./dedalus/dedalus.py parse examples/paths.json
./dedalus/dedalus.py desugar examples/paths.json
./dedalus/dedalus.py typecheck examples/paths.json
./dedalus/dedalus.py typecheck examples/paths.json
./dedalus/dedalus.py pdg examples/paths.json
./dedalus/dedalus.py is_dedalus_s examples/paths.json
./dedalus/dedalus.py run examples/paths.json
./dedalus/dedalus.py repl examples/paths.json
```

## Syntax Highlighting
For Dedalus syntax highlighting, see https://github.com/mwhittaker/dedalus-vim.

- [\[1]: Alvaro, Peter, et al. "Dedalus: Datalog in time and space." _Datalog Reloaded_ (2011): 262-281.][alvaro_paper]
- [\[2]: Marczak, William, et al. "Confluence analysis for distributed programs: A model-theoretic approach." _Datalog in Academia and Industry_ (2012): 135-147.][marczak_paper]

[alvaro_paper]: https://scholar.google.com/scholar?cluster=4658639044512647014
[marczak_paper]: https://scholar.google.com/scholar?cluster=17678162482015246510
