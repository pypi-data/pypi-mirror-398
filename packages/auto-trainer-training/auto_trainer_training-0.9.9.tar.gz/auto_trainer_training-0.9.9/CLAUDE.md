### Code Style
* Always prefer double quotes to single quotes for Python, Javascript, and Typescript strings where possible.
* Never use single character variable names, even in loops.  For example, use `idx` rather than `i`.
* Pay attention to the Python way of doing things, such as using "is False" rather than "== False" and similar "Pythonic" standards

### Type Hints
* When including type hints, remember that when returning or expecting and instance of the current class, you can use `Self` from the typing package.

### Comments
- Do not include comments that state the obvious.
- Only use comments to explain why something is done, not what is done, and only if it is an unusual behavior.

### Testing
When running pytest, ensure the correct conda environment is loaded and that the namespace package source directory
is included in the python path.

Example:
```bash
export PATH=~/miniforge3/envs/auto-trainer/bin:$PATH && export CONDA_PREFIX=~/miniforge3/envs/auto-trainer-training
export PYTHONPATH=$PYTHONPATH:./src
pytest
```

Use pytest structuring for tests, not the unittest module, even if the test is called a "unit test" generically.
