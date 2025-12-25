# Building spydlog

```bash
# Setup the virtual environment (use your target python version)
python -m venv venv
source venv/bin/activate # call venv\Scripts\activate on Windows
pip install scikit-build-core cibuildwheel pytest pytest-cov # or pip install -r requirements.txt

# Either
# Build the package
python -m build

# Install the package
pip install -e .

# After modifying c++, use
pip install -e . --force-reinstall

# Or
# Build the wheel
python -m build --wheel

# Install the wheel
pip install dist/spydlog-*.whl

# Run the tests
pytest -v tests/
```
