# Python SDK for Wallaroo

This repo contains the python SDK used to interface with the Wallaroo API. The structure is as follows:

- Package name: Wallaroo
- Modules contained: sdk
- [SDK documentation](https://wallaroolabs.github.io/wallaroo-docs/sdk.html)

## Building

Building the SDK requires `Python`, `Rust`, and `NodeJS` to be installed in your environment.

This SDK has moved from using setuptools to using Hatch.

To build both `wheel` and `sdist` targets, you must be in the `platform` directory, or use the `-C` flag to target it.

```sh
# From <your path>/platform
make sdk
```

or

```sh
# From <your path>/platform/sdk
make -C .. sdk
```

The `make sdk` command generates an OpenAPI schema from all of our Rust microservices and then creates a Python Client in `wallaroo/wallaroo_ml_ops_api_client` for you to easily query the microservices with.

## Installation

`hatch` handles environments on its own and using it with environment management tools like `pyenv`, `conda` etc. is not preferred.

> [!TIP]
> It is possible to use `hatch` together with `Python` versions installed with `pyenv` in case a specific version is desired.
> For example, you can use `hatch` under `3.10` installed with `pyenv` by configuring the project to use that version
> via `pyenv local 3.10`.

Assuming the desired `Python` version is activated, to install `hatch` globally simply run:

```bash
pip install hatch==1.13.0
```

Then you can create the default development environment with:

```bash
hatch env create
```

> [!NOTE]
> The project dependencies for the default development environment are specified in [pyproject.toml](https://github.com/WallarooLabs/platform/blob/main/sdk/pyproject.toml#L22). Additional environments can be set under the `tool.hatch.envs.<env-name>` configuration where extra requirements particular to the environment can be specified.

> [!NOTE]
> Environment specific scripts can be specified under the `tool.hatch.envs.<env-name>.scripts` configuration.

Here's an example of how to run the `format` script for the `test` environment:

```bash
hatch run test:format
```

> [!TIP]
> `hatch` uses caching which sometimes may confuse installation and potentially raise errors.
> Running `hatch env prune` removes the created environments and recreating them usually helps resolve such issues.

### Configuring `VSCode` with `hatch`

As seen on the official [docs](https://hatch.pypa.io/1.12/how-to/integrate/vscode/) you can set up `VSCode` to use environments specified by `hatch`.

> [!TIP]
> Sometimes `VSCode` might not find a newly installed environment and usually restarting it resolves the issue.

#### Activate `hatch` environment

When in development mode it's preferred to configure `VSCode` to point to the `test` environment that will enable you to add and debug tests.

You can do so as follows:

- Press `cmd` + `shift` + `p`, type `Python: Select Interpreter` and hit enter;
- From the drop-down list select `test` under `Hatch`.

    ![alt text](assets/image-3.png)

#### Configure tests

`SDK` uses `pytest` for its testing suite and to discover all tests under `unit_tests` the following steps are needed:

- Press `cmd` + `shift` + `p`, type `Python: Configure Tests` and hit enter;
- From the drop-down list select `pytest`;

    ![alt text](assets/image.png)

- Point to the `unit_tests` directory.

    ![alt text](assets/image-1.png)

If everything is done correctly you should be able to see all tests under `Testing` on the left:

![alt text](assets/image-2.png)

### Configure `ruff`

You can install the `ruff` [extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) from the `VSCode` marketplace.

For formatting and linting during saving you have to also add the following configuration to your VSCode `settings.json` file:

```json
{
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        "source.organizeImports": "explicit"
    },
    "editor.formatOnSaveMode": "file",
}
```

Via console you can format the code with:

```sh
hatch run test:fix_format
```

or lint the code with:

```sh
hatch run test:fix_lint
```

## Tests

To execute all tests run:

```sh
make unit_tests
```

To execute a specific test run, for example:

```sh
pytest -k test_client
```

To update snapshots used for testing, you can run:

```sh
pytest -k test_checks --snapshot-update
```

## Build

Make sure you have the latest version of 'build'

```sh
make build-sdk
```

This will generate a distribution package in the dist directory.

## Generate Documentation

pdoc3 is used to generate the documentation for the SDK.
To generate the documentation run:

```sh
make doc
```

This will generate documentation files in the [docs/html](docs/html/) directory

To remove generated files:

```sh
make clean
```

## To serve docs locally
From [sdk](/) directory serve the docs in your local, by running the command below. It will open up a browser window pointing at `http://localhost:8080/wallaroo.html`

```sh
make doc-serve
```

## readthedocs.com Documentation

Extensive user-facing documentation is hosted by [ReadTheDocs](https://readthedocs.com). The system is configured to point to the `platform` repo. Documentation can be generated for a specific branch or tag by going to the [Versions](https://readthedocs.com/projects/wallaroo-platform/versions/) page and activating the version.

Release documentation can be published by activing the tag that corresponds to the release and changing the "Privacy Level" to `Public`.

## Deployment

To deploy the SDK to PyPI, `hatch publish` will upload both `whl` and `sdist` targets. Ideally, only the `whl` should need to be published, and excludes the documentation and unit testing around the SDK that end users might not need (and maybe even 'should not have') access to.

To test your configuration and see what the deployment looks like, you can locally set up a simple PyPI server.

To start the server on port 8080:

```sh
python -m pip install pypiserver passlib
python -m htpasswd -sc htpasswd.txt <username>
python -m pypiserver run -p 8080 -P htpasswd.txt ~/packages -v
```

To test publish:

```sh
hatch config set publish.index.repos.private.url 'http://localhost:8080'
hatch publish -r private
```

The packages will be found in `~/packages`. `unzip` can be used to extract `.whl`s, `tar` for the `tar.gz` sdist target.

To test that the created `whl` was successfully uploaded, you can install it with:

```sh
pip install --extra-index-url http://localhost:8080 wallaroo
```
