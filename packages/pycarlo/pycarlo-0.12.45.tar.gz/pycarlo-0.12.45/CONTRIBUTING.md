# Contribution Guidelines

This is primarily for Monte Carlo developers. External contributions are welcome, but you may want
to reach out though support first to discuss your proposed changes.

## Setting up for development

```sh
make install-dev
```

This will create a virtual environment, install dependencies, and set up pre-commit hooks.

## Updating Typed Schema to Match GraphQL API

The schema is automatically kept up-to-date by our CI pipeline when changes are merged to the API
repo. You typically don't need to run `make generate` unless you're testing or debugging an issue
locally.

If you do need to manually update the schema for testing on your development machine, use
`make generate`. This will fetch the latest schema from the API and regenerate the Python types,
including any customizations.

## Schema Customizations

The generated `schema.py` is automatically modified during the build process to apply the following
customizations. See [pycarlo/lib/README.md](pycarlo/lib/README.md) for more details. If you need to
make additional customizations, you need to do so through that process.

## Testing

`make test` can be used to run all tests locally. CircleCI manages testing for deployment.

## Releases

Our CI pipeline is configured to automatically update the schema and run tests when changes are
merged to the default branch in our API repo. It will also automatically deploy a new versioned
release.

### Custom Releases

If you need to make a custom release, create a PR against `main`.

When ready to release after merging, create a new
[Github release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
with a tag using semantic versioning (e.g. `v0.42.0`) and CircleCI will test and publish to PyPI.
Note that an existing version will not be deployed.
