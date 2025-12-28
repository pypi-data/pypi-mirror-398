import datetime
from typing import TYPE_CHECKING, Any, Dict, List, cast

from dateutil import parser as dateparse

from .model_version import ModelVersion
from .object import (
    DehydratedValue,
    Object,
    RequiredAttributeMissing,
    gql,
    rehydrate,
    value_if_present,
)
from .pipeline import Pipeline

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client


class Comment(Object):
    """Comment that may be attached to models and pipelines."""

    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
        self.client = client
        super().__init__(
            gql_client=client._gql_client if client is not None else None,
            data=data,
        )

    def _fill(self, data: Dict[str, Any]) -> None:
        """Fills an object given a response dictionary from the GraphQL API.

        Only the primary key member must be present; other members will be
        filled in via rehydration if their corresponding member function is
        called.
        """
        for required_attribute in ["id"]:
            if required_attribute not in data:
                raise RequiredAttributeMissing(
                    self.__class__.__name__, required_attribute
                )
        # Required
        self._id = data["id"]

        # Optional
        self._user_id = value_if_present(data, "user_id")
        self._message = value_if_present(data, "message")
        self._updated_at = (
            dateparse.isoparse(data["updated_at"])
            if "updated_at" in data
            else DehydratedValue()
        )

    def _fetch_attributes(self) -> Dict[str, Any]:
        """Fetches all member data from the GraphQL API."""
        return self._gql_client.execute(
            gql.gql(
                """
            query CommentById($comment_id: bigint!){
            comment_by_pk(id: $comment_id){
                id
                updated_at
                message
                user_id
                
            }
            }
            """
            )
        )["comment_by_pk"]

    def id(self) -> int:
        return self._id

    @rehydrate("_user_id")
    def user_id(self) -> str:
        return cast(str, self._user_id)

    @rehydrate("_message")
    def message(self) -> str:
        return cast(str, self._message)

    @rehydrate("_updated_at")
    def updated_at(self) -> datetime.datetime:
        return cast(datetime.datetime, self._updated_at)

    def list_model_versions(self) -> List[ModelVersion]:
        """Lists the models this comment is on."""
        res = self._gql_client.execute(
            gql.gql(
                """
            query ModelsForComment($comment_id: bigint!){
            comment_by_pk(id:$comment_id){
                    model_variant_comments {
                model {
                    id
                    file_name
                    model_id
                    sha
                    owner_id
                    visibility
                    updated_at
                }

                }
                
            }
            }
            """
            )
        )
        list_of_models = []
        for v in res["comment_by_pk"]["model_variant_comments"]:
            list_of_models.append(ModelVersion(client=self.client, data=v["model"]))
        return list_of_models

    def list_pipelines(self) -> List[Pipeline]:
        """Lists the models this comment is on."""
        res = self._gql_client.execute(
            gql.gql(
                """
            query PipelinesForComment($comment_id: bigint!){
            comment_by_pk(id:$comment_id){
                pipeline_comments {
                    pipeline{
                    id
                    owner_id
                    updated_at
                    visibility
                    }
                }

            }
            }
            """
            )
        )
        list_of_pipelines = []
        for v in res["comment_by_pk"]["pipeline_comments"]:
            list_of_pipelines.append(Pipeline(client=self.client, data=v["pipeline"]))
        return list_of_pipelines

    def add_to_model(self, model_pk_id: int):
        data = self._gql_client.execute(
            gql.gql(
                """
            mutation AddCommentToModel($model_pk_id: bigint!, $comment_id: bigint!) {
            insert_model_variant_comment(objects: {
                  model_pk_id : $model_pk_id,
                  comment_id: $comment_id
            }) {
                returning {
                    model_pk_id
                    comment_id
                }
            }
            }            
            """
            ),
            variable_values={
                "model_pk_id": model_pk_id,
                "comment_id": self._id,
            },
        )
        return data["insert_model_variant_comment"]["returning"][0]

    def remove_from_model(self, model_id: int):
        data = self._gql_client.execute(
            gql.gql(
                """
            mutation RemoveCommentFromModel($model_id: bigint!, $comment_id: bigint!) {
            delete_model_variant_comment(
                    where: {
                        _and: [
                            { model_id: {_eq: $model_id} } 
                            { comment_id: {_eq: $comment_id} }
                        ]
                    }
                    ) 
                {
                returning {
                    model_id
                    comment_id
                }

                }

            }
            """
            ),
            variable_values={
                "model_id": model_id,
                "comment_id": self._id,
            },
        )
        return data["delete_model_variant_comment"]["returning"][0]

    def add_to_pipeline(self, pipeline_id: int):
        data = self._gql_client.execute(
            gql.gql(
                """
            mutation AddCommentToPipeline($pipeline_pk_id: bigint!, $comment_id: bigint!) {
            insert_pipeline_comment(objects: {
                pipeline_pk_id : $pipeline_id,
                  comment_id: $comment_id
            }) {
                returning {
                    pipeline_pk_id
                    comment_id
                }
            }
            }            
            """
            ),
            variable_values={
                "pipeline_pk_id": pipeline_id,
                "comment_id": self._id,
            },
        )
        return data["insert_pipeline_comment"]["returning"][0]

    def remove_from_pipeline(self, pipeline_pk_id: int):
        data = self._gql_client.execute(
            gql.gql(
                """
            mutation RemoveCommentFromPipeline($pipeline_pk_id: bigint!, $comment_pk_id: bigint!) {
            delete_pipeline_comment(
                    where: {
                        _and: [
                            { pipeline_pk_id: {_eq: $pipeline_pk_id} } 
                            { comment_pk_id: {_eq: $comment_pk_id} }
                        ]
                    }
                    ) 
                {
                returning {
                    pipeline_pk_id
                    comment_pk_id
                }

                }
            }
            """
            ),
            variable_values={
                "pipeline_pk_id": pipeline_pk_id,
                "comment_pk_id": self._id,
            },
        )
        return data["delete_pipeline_comment"]["returning"][0]
