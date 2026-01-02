# Package Maintenance

## Development Environment

First, [install uv](https://docs.astral.sh/uv/getting-started/installation/).

### Set up
    uv sync
    uv tree

## Maintenance

### Lint code
    uv run bin/lint.sh

### Build artifacts
    uv build

## Publish

### Bump package version
    uv version --bump [major|minor|patch]
    V=v$(uv version --short) && git add pyproject.toml uv.lock && git commit -m $V && git tag -a -m $V $V

### Authenticate
See [the PyPI docs](https://pypi.org/help/#apitoken) to generate a token. See [the uv docs](https://docs.astral.sh/uv/guides/package/#publishing-your-package) for options to configure the token.

### Upload
    rm -f dist/* && uv build && uv publish --token pypi-………
