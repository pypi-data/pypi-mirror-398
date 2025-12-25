Official package used by all topdogalerts listeners

deployment steps:
1.) make and test changes
2.) increment version in pyproject.toml
3.) clean old builds: rm -rf dist build
4.) python3 -m build
5.) python3 -m twine upload dist/*
6.) update requirements.txt with new version