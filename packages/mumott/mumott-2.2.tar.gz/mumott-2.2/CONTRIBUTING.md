# Contribution guidelines

* **Please read the contribution guidelines**.<br>
  You have done well so far but keep on reading all the way to the **bottom of this page**.

* Please remember and apply the contribution guidelines!

## General guidelines

* Use [expressive function and variable names](https://xkcd.com/910/), e.g.,
  * Good: `get_residuals` (function or method returning something), `residuals` (property), `compute_residuals` (subroutine-like behavior that does *not* return a result but changes existing data structures)
  * Avoid: `get_res`, `r`, `res`, `calc_arr` or similar

* Please keep in mind that documentation ([docstrings](https://en.wikipedia.org/wiki/Docstring)), sensible comments, and testing are crucial for us to be able to maintain this code.
  The code base uses the [NumPy docstring style](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html) throughout.
  You can consult existing code for examples.

* Always imagine someone else has to be able to read your code.
  Hence please do your best at writing [*clean and structured* code](https://www.xkcd.com/1513/).
  Note that [PEP8]((https://www.Python.org/dev/peps/pep-0008/)) and [pyflakes](https://pypi.Python.org/pypi/pyflakes) compliance are enforced when merging into master.
  To this end, the CI contains the `style_check` job.
  To check the compliance of your code locally, we recommend using [`flake8`](https://flake8.pycqa.org/)
  The code base uses single quotes ( `'`) for regular strings and triple double quotes (`"""`) for multi-line strings.

* Aim for concise yet expressive commit messages.

* Please use spaces.
  While you are entitled to [your own opinion](http://lea.verou.me/2012/01/why-tabs-are-clearly-superior/) this project uses spaces and not tabs.
  Even if you are geeky enough to care and like [Silicon Valley](https://www.youtube.com/watch?v=SsoOG6ZeyUI) you should know that [developers who use spaces make more money](https://stackoverflow.blog/2017/06/15/developers-use-spaces-make-money-use-tabs/).
  Also the use of spaces is strongly recommended by the [PEP8](https://www.Python.org/dev/peps/pep-0008/) standard.


## Tests

The code base includes integration, regression, and unit tests, which are handled through [`pytest`](https://docs.pytest.org/).
[Code coverage](https://coverage.readthedocs.io/) can be a useful tool to [find untested code](https://mumott.org/htmlcov/).

`pytest` can be used at very different levels of complexity.
The basic principle is that any function that starts with `test_*` in files that start with `test_` and reside in the `tests` directory are collected and run by `pytest`.
A test function typically carries out one or a few small tasks and ensures the correct/expected outcome is obtained using `assert` statements; compare, e.g., the tests in [`tests/cpu_tests/unit_tests/test_data_container.py`](tests/cpu_tests/unit_tests/test_data_container.py).

`pytest` provides several very useful advanced functionalities via predefined objects and decorators.
For example, one can try out several different cases of input/output data through the same function  by using the `@pytest.mark.parametrize` decorator; compare, e.g., the `test_probed_coordinates` function in [`tests/cpu_tests/unit_tests/test_sigtt.py`](tests/cpu_tests/unit_tests/test_sigtt.py).

There is also the `@pytest.fixture` decorator, which allows you to set up a "fixture" (say an object that needs to be prepared or a set of data) to be used in several different tests.
This functionality is used to a limited extent in mumott to initialize objects and define default parameters.

There are even built-in fixtures, such as `caplog`, which when specified as a test function argument captures the output of logging prints.

Another useful construct is `with pytest.raises(...)`, which allows you to ensure that the code fails correctly when expected to do so; see, e.g., [`tests/cpu_tests/unit_tests/test_stack.py`](tests/cpu_tests/unit_tests/test_stack.py).


## Examples in docstrings

The CI runs `xdoctest`, which collects all test blocks from the docstrings in the documentation and runs them.
A code block is marked with triple `>` signs.
It commonly comes under the `Example(s)` section of a docstring.
The expected output can be indicated by providing it directly after the code block.
In the latter part `...` implies "continue with whatever".
```python
Example
-------
This tests something.

>>> import numpy as np
>>> a = np.array(range(100))
>>> print(a)
[ 0  1  2  3  4  5 ...
```
