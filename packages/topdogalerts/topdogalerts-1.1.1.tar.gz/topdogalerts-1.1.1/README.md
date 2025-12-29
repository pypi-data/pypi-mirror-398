Official package used by all topdogalerts listeners


Running the topdogalerts Test Suite:
1.) Quick one-liner (from project root
  cd /home/topdog/topdogdata/topdogalerts/shared && \
  python3 -m venv .venv && \
  source .venv/bin/activate && \
  pip install -e ".[test]" && \
  pytest topdogalerts/tests/ -v
2.) Deactivate virtual environment when done
  deactivate

deployment steps:
1.) make and test changes
2.) increment version in pyproject.toml
3.) clean old builds: rm -rf dist build
4.) python3 -m build
5.) python3 -m twine upload dist/*
6.) update requirements.txt with new version