# Contributing to KELE

Thanks for your interest in contributing to KELE!
Any kinds of contributions are welcome.

## How to contribute to KELE

If you have/implemented an idea or find/fixed a bug, use GitHub issues or pull requests.
Providing a minimum working example for bugs would be helpful.
If you have any questions, please use the GitHub discussions.

## Code structure

The code structure of KELE is following the standard Python package structure.
We organize the package code into the folder named `KELE`, the tests into the folder named `tests`,
and the documents into the folder named `docs`.
The file `pyproject.toml` is used to define the package metadata.
There are also some other files such as `.ruff.toml`, `mypy.ini`, `.pre-commit-config.yaml` used to format and lint the code.

## How to get involved

Please learn the basic Git usage to contribute to KELE.
We use the git flow mode to merge the pull requests.
Please provide the essential information with proper formatting in the git commit message and the pull request description.

Please make sure that your code is properly formatted, linted and typed when you submit a pull request.
The comments in the code are expected to be enough for other developers to understand your code.
Please add docstrings to the code in reStructuredText style.
If necessary, please update documentations and add tests for your changes.
Any warning should be fixed when submitting a pull request.
At last, please check carefully on the correctness and the robustness of the code when submitting a pull request.

## Running tests in PRs

Note: the full test CI (including `pytest` and the `example static` checks) runs by default only when the PR is opened, reopened, or moved from draft to open (ready for review).

For the **last commit** in your PR, please make sure the test CI is executed either:

- manually in GitHub Actions (Run workflow), or
- by sending message `@testbot pytest/example/all` in PRs' comments, or including tags in the last commit message:
  - `[pytest]` to trigger `pytest` checks
  - `[example]` to trigger the `example static` checks
  - `[test_all]` to trigger the above all check

## Other principles
1. In Python code conventions, functions (classes) with leading underscores are private, while those without underscore are external. 
When calling other modules, only functions (classes) without underscores should be used. 
Do not modify the input and output of these functions (classes) unless necessary, nor increase the number of public functions (classes). 
If any changes are required, it's better to discuss and explain your designs in advance; otherwise, they might be refused to merge.

2. Using `codetag` to emphasize your comments that need closer inspection or review. Please see [ref1](https://github.com/Davmuz/codetag) and [ref2](https://www.zhihu.com/question/19563346).
Meanwhile, we add an extra tag `risk` to warn possible design flaws of algorithms or data structures because KELE is a new forward chaining approach for [Assertional Logic](https://link.springer.com/chapter/10.1007/978-3-319-63703-7_9) and still in process.

---

Thanks! :heart: :heart: :heart:

USTC Knowledge Computing Lab
