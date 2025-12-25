# Unitelabs SiLA Python Library

A Python library for creating SiLA 2 clients and servers. This flexible and unopinionated library gives you everything needed to create a SiLA 2 1.1 compliant Python application. It adheres to the [SiLA 2 specification](https://sila2.gitlab.io/sila_base/) and is used by the [UniteLabs CDK](https://gitlab.com/unitelabs/cdk/python-cdk) to enable rapid development of cloud-native SiLA Servers with a code-first approach.

## Getting Started

### Prerequisites

Ensure you have Python 3.9+ installed. You can install Python from [python.org](https://www.python.org/downloads/).

### Quickstart

To get started quickly with your first connector, we recommend to use our [UniteLabs CDK](https://gitlab.com/unitelabs/cdk/python-cdk). Use [Cookiecutter](https://www.cookiecutter.io) to create your project base on our [Connector Factory](https://gitlab.com/unitelabs/cdk/connector-factory) starter template:

```
cookiecutter git@gitlab.com:unitelabs/cdk/connector-factory.git
```

### Installation

Install the latest version of the library into your Python project:

```python
pip install unitelabs-sila
```

## Usage

To start using the SiLA Python library in your project:

1. Import and configure your SiLA server instance:

    ```python
    import asyncio

    from sila.server import Server
    from your_project.features import your_feature

    async def main():
        server = Server({"port": 50000})
        server.add_feature(your_feature)
        await server.start()

    asyncio.run(main())
    ```

2. To implement a custom SiLA Feature, create a feature definition following the SiLA2 specification:

    ```python
    from sila.server import Feature, UnobservableCommand

    your_feature = Feature(...)
    your_method = UnobservableCommand(...)
    your_method.add_to_feature(your_feature)
    ```

3. Run your server:

    ```bash
    $ python your_script.py
    ```

> Important: Without implementing the required SiLA Service Feature, your SiLA Server will not be fully compliant with the standard. For easier compliance, consider using the [UniteLabs CDK](https://gitlab.com/unitelabs/cdk/python-cdk), which handles this automatically.

## Contribute

Submit and share your work!  
https://hub.unitelabs.io

We encourage you to submit feature requests and bug reports through the GitLab issue system. Please include a clear description of the issue or feature you are proposing. If you have further questions, issues, or suggestions for improvement, don't hesitate to reach out to us at [developers@unitelabs.io](mailto:developers+sila@unitelabs.io).

Join the conversation! Stay up to date with the latest developments by joining the Python channel in the [SiLA Slack](https://sila-standard.org/slack).

## License

Distributed under the MIT License. See [MIT license](LICENSE) for more information.
