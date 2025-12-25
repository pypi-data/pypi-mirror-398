pip install hatch

rm -rf dist
poetry version 0.1.15
hatch build
git tag v0.1.15
git push --tags



poetry env remove python3.13
rm -rf ~/.cache/pypoetry
rm -rf ~/.local/share/pypoetry


curl -sSL https://install.python-poetry.org | python3 -


poetry config virtualenvs.in-project true
poetry config virtualenvs.create true
poetry config virtualenvs.prefer-active-python true

python3.13 -m venv .venv
source .venv/bin/activate

poetry install




./scripts/bump_version.sh patch