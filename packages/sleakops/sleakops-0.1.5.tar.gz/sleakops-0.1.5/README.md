## How to install

Generate environment file

```bash
cp local.env .env
```

### Without Docker

Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

Install in editable mode
```bash
pip install -e .
```

Run the CLI commands
```bash
sleakops [COMMANDS...]
```

#### Examples

Build a project
```bash
sleakops build --project core --branch qa --wait
```

Build a project with an environment

```bash
sleakops build --project core --branch qa --environment production --wait
```

Deploy a project

```bash
sleakops deploy --project core --branch qa --wait
```

Show help

```bash
sleakops --help
```


### With Docker

Run a build
```bash
docker compose run cli python sleakops.py build --project core --branch qa --wait
```

#### Build with environment specification
When you have multiple projects with the same branch, you can specify the environment to differentiate between them:
```bash
docker compose run cli python sleakops.py build --project core --branch qa --environment production --wait
```

Run a deployment
```bash
docker compose run cli python sleakops.py deployment --project core --branch qa --wait
```

Run help
```bash
docker compose run cli python sleakops.py --help 
```


## Execute tests

### Prerequisites

Make sure you have the virtual environment activated and dependencies installed:
```bash
source venv/bin/activate
pip install -e .
```

### Running All Tests

Execute the complete test suite:
```bash
python -m pytest tests/ -v
```
