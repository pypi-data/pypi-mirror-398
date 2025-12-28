from importlib import resources

from . import graphql


def named(name: str) -> str:
    """Returns text from resources in the package."""

    return (
        resources.files(graphql)
        .joinpath(f"{name}.graphql")
        .open("r", encoding="utf8")
        .read()
    )
