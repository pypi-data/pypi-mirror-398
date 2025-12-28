from typing import TYPE_CHECKING, Any, Dict, List, cast

from . import queries
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


class Tag(Object):
    """Tags that may be attached to models and pipelines."""

    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
        self.client = client
        super().__init__(
            gql_client=client._gql_client if client is not None else None,
            data=data,
        )

    def __repr__(self) -> str:
        return str(
            {
                "id": self.id(),
                "tag": self.tag(),
                "models": self.model_tags(),
                "pipelines": self.pipeline_tags(),
            }
        )

    @staticmethod
    def _create_tag(client, tag_text: str):
        res = client._gql_client.execute(
            gql.gql(queries.named("CreateTag")),
            variable_values={
                "tag_text": tag_text,
            },
        )
        return Tag(client, res["insert_tag"]["returning"][0])

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
        self._tag = value_if_present(data, "tag")

        # Optional
        self._model_tags = (
            [
                ModelVersion(self.client, model_tag["model"])
                for model_tag in data["model_tags"]
            ]
            if "model_tags" in data
            else DehydratedValue()
        )

        # Optional
        self._pipeline_tags = (
            [
                Pipeline(self.client, pipeline_tag["pipeline"])
                for pipeline_tag in data["pipeline_tags"]
            ]
            if "pipeline_tags" in data
            else DehydratedValue()
        )

    def _fetch_attributes(self) -> Dict[str, Any]:
        """Fetches all member data from the GraphQL API."""
        return self._gql_client.execute(
            gql.gql(
                f"""
            query TagById {{
                tag_by_pk(id: {self._id}) {{
                    id
                    tag
                    model_tags {{
                      model {{
                        id
                        model_id
                        models_pk_id
                        model_version
                        
                      }}
                    }}
                    pipeline_tags {{
                      pipeline {{
                        id
                        pipeline_id
                        pipeline_versions {{
                            id
                            version
                        }}
                      }}
                    }}
                }}
            }}
            """
            )
        )["tag_by_pk"]

    def id(self) -> int:
        return self._id

    @rehydrate("_tag")
    def tag(self) -> str:
        return cast(str, self._tag)

    @rehydrate("_model_tags")
    def model_tags(self) -> List[ModelVersion]:
        return cast(List[ModelVersion], self._model_tags)

    @rehydrate("_pipeline_tags")
    def pipeline_tags(self) -> List[Pipeline]:
        return cast(List[Pipeline], self._pipeline_tags)

    def list_model_versions(self) -> List[ModelVersion]:
        """Lists the model versions this tag is on."""
        res = self._gql_client.execute(
            gql.gql(
                """
            query ModelsByTagId($tag_id: bigint!){
            tag_by_pk(id:$tag_id){
                model_tags {
                model {
                    id
                    model_id
                    model_version
                    sha
                    file_name
                    updated_at
                    visibility
                }
                }
            }
            }
            """
            ),
            variable_values={
                "tag_id": self._id,
            },
        )
        list_of_models = []
        if res["tag_by_pk"]:
            for v in res["tag_by_pk"]["model_tags"]:
                list_of_models.append(ModelVersion(client=self.client, data=v["model"]))
        return list_of_models

    def add_to_model(self, model_id: int):
        data = self._gql_client.execute(
            gql.gql(
                """
            mutation AddTagToModel($model_id: bigint!, $tag_id: bigint!) {
            insert_model_tag(objects: {
                model_id : $model_id,
           		  tag_id: $tag_id
            }) {
                returning {
                    model_id
                    tag_id
                }
            }
            }            
            """
            ),
            variable_values={
                "model_id": model_id,
                "tag_id": self._id,
            },
        )
        return data["insert_model_tag"]["returning"][0]

    def remove_from_model(self, model_id: int):
        data = self._gql_client.execute(
            gql.gql(
                """
            mutation RemoveTagFromModel($model_id: bigint!, $tag_id: bigint!) {
            delete_model_tag(
                    where: {
                        _and: [
                            { model_id: {_eq: $model_id} } 
                            { tag_id: {_eq: $tag_id} }
                        ]
                    }
                    ) 
                {
                returning {
                    model_id
                    tag_id
                }

                }

            }
            """
            ),
            variable_values={
                "model_id": model_id,
                "tag_id": self._id,
            },
        )
        return data["delete_model_tag"]["returning"][0]

    def list_pipelines(self) -> List[Pipeline]:
        """Lists the pipelines this tag is on."""
        res = self._gql_client.execute(
            gql.gql(
                """
            query PipelinesByTagId($tag_id: bigint!){
            tag_by_pk(id:$tag_id){
                pipeline_tags {
                pipeline {
                    id
                    pipeline_id
                    created_at
                    updated_at
                    owner_id
                }
                }
            }
            }
            """
            ),
            variable_values={
                "tag_id": self._id,
            },
        )
        list_of_pipelines = []
        if res["tag_by_pk"]:
            for v in res["tag_by_pk"]["pipeline_tags"]:
                list_of_pipelines.append(
                    Pipeline(client=self.client, data=v["pipeline"])
                )
        return list_of_pipelines

    def add_to_pipeline(self, pipeline_id: int):
        data = self._gql_client.execute(
            gql.gql(
                """
            mutation AddTagToPipeline($pipeline_id: bigint!, $tag_id: bigint!) {
            insert_pipeline_tag(objects: {
                pipeline_pk_id : $pipeline_id,
           		  tag_pk_id: $tag_id
            }) {
                returning {
                    pipeline_pk_id
                    tag_pk_id
                }
            }
            }            
            """
            ),
            variable_values={
                "pipeline_id": pipeline_id,
                "tag_id": self._id,
            },
        )
        return data["insert_pipeline_tag"]["returning"][0]

    def remove_from_pipeline(self, pipeline_id: int):
        data = self._gql_client.execute(
            gql.gql(
                """
            mutation RemoveTagFromPipeline($pipeline_id: bigint!, $tag_id: bigint!) {
            delete_pipeline_tag(
                    where: {
                        _and: [
                            { pipeline_pk_id: {_eq: $pipeline_id} } 
                            { tag_pk_id: {_eq: $tag_id} }
                        ]
                    }
                    ) 
                {
                returning {
                    pipeline_pk_id
                    tag_pk_id
                }

                }

            }
            """
            ),
            variable_values={
                "pipeline_id": pipeline_id,
                "tag_id": self._id,
            },
        )
        return data["delete_pipeline_tag"]["returning"][0]


class Tags(List[Tag]):
    """Wraps a list of tags for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(tag):
            models = [model for model in tag.model_tags()]
            pipelines = [pipeline for pipeline in tag.pipeline_tags()]
            model_ids = list(set(m.models_pk_id() for m in models))
            models_dict = {}
            for m in models:
                if m.models_pk_id() in model_ids:
                    if m.name() not in models_dict:
                        models_dict[m.name()] = []
                    models_dict[m.name()].append(m.version())

            return (
                "<tr>"
                + f"<td>{tag.id()}</td>"
                + f"<td>{tag.tag()}</td>"
                + f"<td>{[(key, value) for key, value in models_dict.items()]}</td>"
                + f"<td>{[(p.name(), [pv.name() for pv in p.versions()]) for p in pipelines]}</td>"
                + "</tr>"
            )

        fields = ["id", "tag", "models", "pipelines"]

        if not self:
            return "(no tags)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )
