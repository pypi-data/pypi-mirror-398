# Castor Extractor <img src="https://app.castordoc.com/images/castor_icon_dark.svg" width=30 />

This library contains utilities to extract your metadata assets into `JSON` or `CSV` files, on your local machine.
After extraction, those files can be pushed to Castor for ingestion.

- Visualization assets are typically:
  - `dashboards`
  - `users`
  - `folders`
  - ...

- Warehouse assets are typically:
  - `databases`
  - `schemas`
  - `tables`
  - `columns`
  - `queries`
  - ...

It also embeds utilities to help you push your metadata to Castor:

- `File Checker` to validate your [generic](https://docs.castordoc.com/integrations/data-warehouses/generic-warehouse) CSV files before pushing to Castor
- `Uploader` to push extracted files to our Google-Cloud-Storage (GCS)

## Table of contents

- [Castor Extractor](#castor-extractor-)
  - [Table of contents](#table-of-contents)
  - [Installation](#installation)
    - [Create castor-env](#create-castor-env)
    - [PIP install](#pip-install)
    - [Create the output directory](#create-the-output-directory)
  - [Contact](#contact)

## Installation

Requirements: **python3.10+**
<img src="https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg" width=20 />

### Create castor-env

We advise to create a dedicated [Python environment](https://docs.python.org/3/library/venv.html).

Here's an example using `Pyenv`:

- Install Pyenv

```bash
brew install pyenv
brew install pyenv-virtualenv
```

- [optional] Update your `.bashrc` if you encounter this [issue](https://stackoverflow.com/questions/45577194/failed-to-activate-virtualenv-with-pyenv/45578839)

```bash
eval "$(pyenv init -)"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
```

- [optional] Install python 3.10+ if needed

```bash
pyenv versions # check your local python installations

# install Python if none of the installed versions satisfy requirements 3.9+
# in this example, we will install Python 3.11.9
pyenv install -v 3.11.9
```

- Create your virtual env

```bash
pyenv virtualenv 3.11.9 castor-env # create a dedicated env
pyenv shell castor-env # activate the environment

# optional checks
python --version # should be `3.11.9`
pyenv version # should be `castor-env`
```

### PIP install

⚠️ `castor-env` must be created AND activated first.

```bash
pyenv shell castor-env
(castor-env) $ # this means the environment is now active
```

ℹ️ please upgrade `PIP` before installing Castor.

```bash
pip install --upgrade pip
```

Run the following command to install `castor-extractor`:

```bash
pip install castor-extractor
```

Depending on your use case, you can also install one of the following `extras`:

```bash
pip install castor-extractor[bigquery]
pip install castor-extractor[databricks]
pip install castor-extractor[looker]
pip install castor-extractor[lookerstudio]
pip install castor-extractor[metabase]
pip install castor-extractor[mysql]
pip install castor-extractor[powerbi]
pip install castor-extractor[qlik]
pip install castor-extractor[postgres]
pip install castor-extractor[redshift]
pip install castor-extractor[snowflake]
pip install castor-extractor[sqlserver]
pip install castor-extractor[strategy]
pip install castor-extractor[tableau]
```

### Create the output directory

```bash
mkdir /tmp/castor
```

You will provide this path in the `extraction` scripts as follows:

```bash
castor-extract-bigquery --output=/tmp/castor
```

Alternatively, you can also set the following `ENV` in your `bashrc`:

```bash
export CASTOR_OUTPUT_DIRECTORY="/tmp/castor"
````

## Contact

For any questions or bug report, contact us at [support@coalesce.io](mailto:support@coalesce.io)

[Catalog from Coalesce](https://castordoc.com) helps you find, understand, use your data assets
