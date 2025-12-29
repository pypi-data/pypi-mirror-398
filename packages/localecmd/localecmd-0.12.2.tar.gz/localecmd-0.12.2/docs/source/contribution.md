# Contribution
Thank you for contributing!
All contribution is welcome

There are several ways on how to contribute:
- Report bugs and request features
- Improve documentation
- Write tutorials and examples
- Extend the package and fix the bugs

[Coderefinery has excellent lessons](https://coderefinery.org/lessons/) on git.
Good resources on documentation writing are on 
[pyOpenSci.org](https://www.pyopensci.org/python-package-guide/documentation/index.html).



## Bugs and feature requests
Did you find a bug or have a feature request? 
File an issue! Go to [Issue tracker](https://codeberg.org/jbox/localecmd/issues)
and press «new issue». 

If it is a bug report, fill in as much information as needed to reproduce the bug:
- What is the error message?
- In what conditions does the bug arise?
- How did you expect that the program would react?
- Error traceback if you get any.
- Error and debug logs if available.

If possible, a minimal working example is super! 
A minimal working example is a short code block that produces the bug or reported behaviour.

## Set up development environment
```
git clone https://codeberg.org/jbox/localecmd.git
cd localecmd
python3 -m venv .venv --prompt localecmd
source .venv/bin/activate
pip install -e .
```
With pip >= 25.1 (from April 2025):
```
pip install --group dev
```
With pip < 25.1 (before April 2025):
```
pip install build pytest pytest-cov ruff mypy commitizen pre-commit twine
pip install myst-parser sphinx sphinx-autodoc2 sphinx-intl
pip install sphinx-markdown-builder sphinx-nefertiti
```
Finally, run
```
pre-commit install
```
Pre-commit will then look for errors with mypy, ruff and pytest 
before committing to main branch.
On other branches, only formatting will be checked.
Pre-commit will also check that [commit message guidelines](#commit-msg) are followed.
To ignore pre-commit for a commit, use the switch `-n` (`--no-verify`),
keep in mind that the pre-commit hooks are for improving code style and formatting the changelog.

## Submit changes
To submit changes, fork https://codeberg.org/jbox/localecmd, and work at your fork.
Then you have to change `jbox` in the git clone command above with you Codeberg username.
Do your changes and create a pull request.
In the pull request, describe changes shortly. 
Ensure that new functionality is tested and documented and that commit messages 
follow guidelines below or are squashed.


(commit-msg)=
### Commit message guidelines
Commit messages should follow 
[conventional angular style](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#-commit-message-guidelines)
Alternatively, commits should be [squashed](https://docs.codeberg.org/git/squash-commits/)
before merging with main branch.
The reason is that the changelog can then be created automatically.

To get help with writing the commit messages, you can use 
[commitizen](https://commitizen-tools.github.io/commitizen/) 
by running `cz commit` instead of `git commit`
If a commit fails because of formatting, check in those changes with `git add` 
and rerun commiting with `cz commit --retry`. 
You may want to review the change with `git diff(tool)` before adding.

Write the commit messages as you would like to see it in the changelog
since that is the reason for these guidelines.

The localecmd package at current does not specify scopes for the commits.

## Improve documentation
Places to start are fixing typos, broken links and docstrings.
Updating docstrings, tutorials and examples is needed and very valuable. 
Even if their code correctness is tested with pytest, 
there may still be problems and pitfalls that should be covered.
Also adding new tutorials and examples is welcome.

The documentation is written in Markdown and parsed with 
[Myst-parser](https://myst-parser.readthedocs.io/).
To check which myst and sphinx extensions are enabled, 
look at the `docs/source/conf.py` file.
Also docstrings are written in Myst Markdown and therefore the style must be 
[Sphinx style](https://www.sphinx-doc.org/en/master/usage/domains/python.html#info-field-lists).

To build the documentation locally, run
```
sphinx-build -b html docs/source docs/html
python -m http.server -d docs/html
```
The built documentation can be opened with a webbrowser on 
[http://0.0.0.0:8000](http://0.0.0.0:8000).

To build and upload the documentation to Codeberg pages, run `bash push-docs.sh`.
This needs writing access to the repository.
IMPORTANT! Commit or stash changes before running the script!
You will find yourself in the main branch afterwards! 

## Improving and extending code
Please follow the following points when coding. 
Remember that the given commands also are run when a commit is made on the main branch.

Docstrings
: Add docstrings to all public functions. 
Describe what the function does, the parameters it takes, returns and what exception it raises.
Use [Sphinx style](https://www.sphinx-doc.org/en/master/usage/domains/python.html#info-field-lists).
You may use [Myst Markdown](https://myst-parser.readthedocs.io/) syntax.
Include types when describing input and output parameters. 
As in the linked example, you can choose if you want to include the type in the saame line or in the line below.

Comments
: Use comments. Add comments for explanations. Why is this code like it is? 
If parts are difficult to understand, use comments to explain what happens.

Documentation
: When changing features, remember to update the documentation accordingly.
Add new sections to documentation when adding new features to describe what it is for.

Testing
: Tests are run with pytest. The command is simply `pytest`. 
This tests the module tests, doctests and other test files. 
Module tests should be in folder `tests`.

: Pytest will generate html files containing the testing coverage. 
These are in folder `htmlcov` and can be opened with a web browser.
Try to achieve full testing coverage.

: Sometimes it is unfeasible to test a block, for example when querying for user input.
Then mark the start of the block with `  # pragma: no cover`.

: Hatch can be used to test all Python versions: `hatch test`. This ignores tests in documentation.

Types
: Use types for all parameters. Typing is checked with 
[mypy](https://mypy.readthedocs.io/).
To check the typing, run `mypy -p localecmd`

Code style
: Code is formatted and linted with [ruff](https://docs.astral.sh/ruff/).
To format the code, run `ruff format`. 
Linting is done by running `ruff check`, possibly with `--fix` and `--unsafe-fixes`.
If `--unsafe-fixes`, check that fixes did not change the functionality of the program.
For example you can stage the changes with `git add`, then fix unsafe, 
and then check changes with git diff(tool).

: Use of both single- and double-quoted strings is allowed.
However, try to use single-quoted strings for identifiers and symbols 
(`print(d['first'])`) and 
double-quoted strings for natural language (`print("Hello, world!")`).
Multiline strings (`""" """`) should always use double quotes.

## Task list for publishing a new version
1. check that
- [X] There are changes to the code: bug fixes or new or changed features
- [X] All functionality is tested in supported versions
- [X] Doctests pass too
- [X] Documentation is read and up to date

2. Update the main branch with all changes that should be included.
3. On the main branch, run `cz bump --dry-run` to check that updating the version works
and that changelog is updated properly
4. Actually bump the version: `cz bump`
5. Build and upload the package to Pypi `python -m build; twine upload dist/*`
6. BUild and upload the documentation with running `bash push-docs.sh`


