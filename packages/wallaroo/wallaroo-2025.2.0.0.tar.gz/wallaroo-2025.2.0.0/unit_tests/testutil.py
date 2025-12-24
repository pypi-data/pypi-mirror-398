import json
import pprint
from typing import Tuple

import gql  # type: ignore
import httpx


def new_gql_client(endpoint: str) -> gql.Client:
    """Returns a GQL client in a test scenario.

    The endpoint specified does not have to be valid, as long as the `responses`
    library is used to intercept requests and return a corresponding
    response.
    """
    return gql.Client(
        transport=gql.transport.httpx.HTTPXTransport(url=endpoint),
        fetch_schema_from_transport=False,
    )


def query_name_matcher(query_name: str):
    """Returns a matcher that matches a GQL query of a particular name.

    It's difficult to match particular GQL queries, as the endpoint never
    changes (unlike REST queries); different queries are only differentiated by
    the body. We can differentiate queries by:

    * making sure that each query is given a unique name - GQL queries typically
      start with a string like `query FooBar {`, so by keeping the `FooBar`
      portion unique we can pick out specific queries
    * using this function to generate a `responses` matcher for the specified
      query_name. When specified in the `match` parameter to a response, the
      corresponding response will only be returned if the request matches the
      specified query name.
    """

    def match(request: httpx.Request) -> Tuple[bool, str]:
        request_str = request.content.decode("UTF-8")
        return ("query {}".format(query_name) in request_str, "query not found in body")

    return match


def mutation_name_matcher(mutation_name: str):
    """Returns a matcher that matches a GQL mutation of a particular name.

    It's difficult to match particular GQL mutations, as the endpoint never
    changes (unlike REST queries); different mutations are only differentiated by
    the body. We can differentiate mutations by:

    * making sure that each mutation is given a unique name - GQL mutations
      typically start with a string like `mutation FooBar {`, so by keeping the
      `FooBar` portion unique we can pick out specific mutations
    * using this function to generate a `responses` matcher for the specified
      mutation_name. When specified in the `match` parameter to a response, the
      corresponding response will only be returned if the request matches the
      specified mutation name.
    """

    def match(request: httpx.Request) -> Tuple[bool, str]:
        request_str = request.content.decode("UTF-8")
        return (
            "mutation {}(".format(mutation_name) in request_str,
            "mutation not found in body",
        )

    return match


def json_body_printer():
    """Returns a matcher that prints the request body.

    This matcher is useful for printing out request bodies so that one can debug
    why other matchers are not matching. Add a catch-all response to print out
    every request:

    responses.add(
        responses.POST,
        "http://api-lb/v1/graphql",
        status=200,
        match=[testutil.json_body_printer()],
    )
    """

    def match(request: httpx.Request) -> Tuple[bool, str]:
        data = json.loads(request.content.decode("UTF-8"))
        print("REQUEST BODY:")
        pprint.pprint(data)
        return (False, "")

    return match


def variables_matcher(variables: str):
    """Returns a matcher that matches a variables that are passed in to the GQL query.

    * This matcher makes sure that we are passing in the right variables for the GQL query.

    * using this function to generate a `responses` matcher for the specified set of
      variables. When specified in the `match` parameter to a response, the
      corresponding response will only be returned if the request matches the
      specified set of variables.
    """

    def match(request: httpx.Request) -> Tuple[bool, str]:
        request_str = request.content.decode("UTF-8")
        return (
            '"variables": {}'.format(variables) in request_str,
            "variables not found in body",
        )

    return match
