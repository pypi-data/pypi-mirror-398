## cs-models

This package provides a reusable library to connect to the cs database.

### Setup

1. Install `pyenv`
    ```shell
    brew install pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
    echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.zshrc
    ```
2. Install Python
    ```shell
    pyenv install
    ```
3. Setup project
    ```shell
    chmod a+x bin/*
    . ./bin/bootstrap.sh
    ```

### Commands

**List commands**

`inv -l`

### Usage

**Configure the database in your app**

```
from cs_models.database import get_db_session

db_uri = 'mysql+pymysql://%s:%s@%s/%s?charset=utf8mb4' % (
    'root',
    'password',
    'host',
    'db',
)
engine, db_session, Base = database.get_db_session(db_uri)
```

### How to apply migrations?

1. Update `sqlalchemy.url` in `alembic.ini` to point to MySQL DB
2. Get current migration version
   ```shell
   alembic current
   ```
3. Create migration file
   ```shell
   alembic revision -m "create account table"
   ```
4. Implement `upgrade()` and `downgrade()` in the generated migration file. Your migration should be backwards-compatible and revertible.
5. Apply migrations
   ```shell
   alembic upgrade head
   ```
6. BE CAREFUL! Verify all is good. If you want to revert the migration, then run:
   ```shell
   alembic downgrade -1
   ```

Reference: https://alembic.sqlalchemy.org/en/latest/tutorial.html#create-a-migration-script

### How to release a new version?

1. Update the `version` in `setup.py`
   ```
   setuptools.setup(
       ...
       version='0.0.9',
       ...
   )
   ```

2. Publish to PyPI repository

   ```shell
   inv deploy
   ```

3. Upgrade `cs-models` python dependency in downstream applications
