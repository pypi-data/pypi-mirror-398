# `ydata` profile

## Run the streamlit app

```
$ cd ydata_profile
$ streamlit run src/ydata_profile/streamlit_app.py
```

## Instructions for building the package


### Usage

```
from ydata_profile import run_ydata_profile
run_ydata_profile()     # this will open the streamlit app on the browser
```

#### Update dependencies

If any dependencies are required, edit the `pyproject.toml` file, `[project]` field, and add a `dependencies` key with a `List[str]` value, where each string is a `pip`-readable dependency.

#### Upload

1. Building the package before uploading:

   `$ python -m build   # (from 'ydata_profile')`.

2. Upload the package to pypi:

   `$ python -m twine upload --repository pypi dist/LAST_VERSION`

#### Test

3. Install the package from pypi
    `python -m pip install --index-url https://pypi.org`
