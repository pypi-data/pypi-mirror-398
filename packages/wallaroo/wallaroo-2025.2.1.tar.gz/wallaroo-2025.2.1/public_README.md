# Wallaroo SDK

## Introduction

> The easy way to deploy, run, and observe your ML in production at scale.

Wallaroo is purpose-built from the ground up to be the easy way to deploy and manage Machine Learning (ML) models and Large Language Models (LLM) in production without heavy weight containers.

## Documentation

The following guides have comprehensive tutorials and references for interacting with the Wallaroo ML environment.

* [Wallaroo 101](https://docs.wallaroo.ai/wallaroo-101/)
* [The Definitive Introductory Guide](https://docs.wallaroo.ai/wallaroo-complete-introduction/)
* [Wallaroo SDK Guides](https://docs.wallaroo.ai/wallaroo-developer-guides/wallaroo-sdk-guides/)
* [Community Edition](https://portal.wallaroo.community/)

## Installation

The Wallaroo SDK is available by default inside your Wallaroo installation's JupyterHub development environment. You can also install this package from PyPI:

```sh
pip install wallaroo
```

## Quickstart

The guides and documentation site are great resources for using the Wallaroo SDK. When installing the package from PyPI, the only difference is that you will need to configure the Wallaroo Client to point to your cluster's DNS. This can be a Community Edition internet-accessible URL or an isolated, intranet-accessible URL for Enterprise deployments.

In your Python environment of choice, pass your cluster's URL to the Client's constructor:
```python
import wallaroo
wallaroo_client = wallaroo.Client(api_endpoint="https://<DOMAIN>.wallaroo.community")
```

With that, you'll be prompted to log in, and you'll be all set to use the library outside of the Jupyter environment!

## Community Edition

The [Community Edition](https://portal.wallaroo.community/) is a free, cloud-based installation of the Wallaroo production environment. It provides a convenient way to test out the various Community features of the platform, such as our ultrafast inference engine and performance metrics.

You can sign up for the Community Edition via this Portal: [https://portal.wallaroo.community/](https://portal.wallaroo.community/)
