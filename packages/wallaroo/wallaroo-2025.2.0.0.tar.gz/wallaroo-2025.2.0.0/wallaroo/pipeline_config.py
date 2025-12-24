import warnings
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
)

import polars

from .model_config import ModelConfig
from .model_version import ModelVersion

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client
    from .pipeline import Pipeline


class ValidDataType(str, Enum):
    f32 = "f32"
    f64 = "f64"
    i8 = "i8"
    u8 = "u8"
    i16 = "i16"
    u16 = "u16"
    i32 = "i32"
    u32 = "u32"
    i64 = "i64"
    u64 = "u64"


class ModelConfigsForStep:
    def __init__(self, model_configs: List[ModelConfig]):
        self.model_configs = model_configs


class ModelForStep:
    def __init__(self, name, version, sha):
        self.name = name
        self.version = version
        self.sha = sha

    def to_json(self):
        return {"name": self.name, "version": self.version, "sha": self.sha}

    @classmethod
    def from_json(cls, json_dict: Dict[str, str]):
        return cls(json_dict["name"], json_dict["version"], json_dict["sha"])

    @classmethod
    def from_model(cls, model: ModelVersion):
        return cls(
            model.name(),
            model.version(),
            model.sha(),
        )

    def __eq__(self, obj):
        return (
            isinstance(obj, ModelForStep)
            and self.name == obj.name
            and self.version == obj.version
            and self.sha == obj.sha
        )

    def __repr__(self):
        return str(self.to_json())


class ModelWeight:
    def __init__(self, weight: float, model: ModelForStep):
        self.weight = weight
        self.model = model

    def to_json(self):
        return {"model": self.model.to_json(), "weight": self.weight}

    @classmethod
    def from_json(cls, json_dict: Dict[str, Any]):
        return cls(json_dict["weight"], ModelForStep.from_json(json_dict["model"]))

    @classmethod
    def from_tuple(cls, tup: Tuple[float, ModelVersion]):
        (weight, model) = tup
        return ModelWeight(weight, ModelForStep.from_model(model))

    def __eq__(self, obj):
        return (
            isinstance(obj, ModelWeight)
            and self.weight == obj.weight
            and self.model == obj.model
        )

    def __repr__(self):
        return str(self.to_json())


class RowToModel:
    def __init__(self, row_index: int, model: ModelForStep):
        self.row_index = row_index
        self.model = model

    def to_json(self):
        return {"row_index": self.row_index, "model": self.model.to_json()}

    @classmethod
    def from_json(cls, json_dict: Dict[str, Any]):
        return cls(json_dict["row_index"], ModelForStep.from_json(json_dict["model"]))

    def __eq__(self, obj):
        return (
            isinstance(obj, RowToModel)
            and self.row_index == obj.row_index
            and self.model == obj.model
        )

    def __repr__(self):
        return str(self.to_json())


class Step:
    def to_json(self):
        pass

    def is_inference_step(self):
        return False

    def __repr__(self):
        return repr(self.to_json())

    def _repr_html_(self):
        return repr(self.to_json())

    def shortname(self):
        """A short name to represent this Step in Jupyter tables."""
        return self.__class__.__name__

    @staticmethod
    def from_json(json_dict: Dict):
        step_name = next(iter(json_dict))
        # TODO update this to use a switch statement in 3.10
        from_json_dispatch = {
            "Average": Average,
            "AuditResults": AuditResults,
            "Check": Check,
            "ColumnsSelect": ColumnsSelect,
            "ColumnsToRows": ColumnsToRows,
            "ModelInference": ModelInference,
            "RowsToModels": RowsToModels,
            "Nth": Nth,
            "MetaValueSplit": MetaValueSplit,
            "RandomSplit": RandomSplit,
            "MultiOut": MultiOut,
        }
        if step_name not in from_json_dispatch.keys():
            raise RuntimeError(f"An invalid step definition was given {step_name}")
        return from_json_dispatch[step_name].from_json(json_dict[step_name])  # type: ignore


class Steps(List[Step]):
    def _repr_html_(self):
        return "<br/>".join([x.shortname() for x in self])


class Average(Step):
    def to_json(self):
        return {"Average": {}}

    @staticmethod
    def from_json(json_dict: Dict):
        return Average()

    def __eq__(self, obj):
        return isinstance(Average, obj)


class AuditResults(Step):
    def __init__(self, start: int, end: Optional[int] = None):
        self.start = start
        self.end = end

    def to_json(self):
        return {"AuditResults": {"from": self.start, "to": self.end}}

    @staticmethod
    def from_json(json_dict: Dict):
        return AuditResults(start=json_dict["from"], end=json_dict["to"])

    def __eq__(self, obj):
        return (
            isinstance(obj, AuditResults)
            and self.start == obj.start
            and self.end == obj.end
        )

    def shortname(self):
        return f"Audit [{self.start}:{self.end}]"


class Check(Step):
    def __init__(self, validations: List[str]):
        self.tree = validations

    def to_json(self):
        return {"Check": {"tree": self.tree}}

    @classmethod
    def from_validation_dict(cls, validations: Dict[str, polars.Expr]):
        if "count" in validations:
            del validations["count"]
            warnings.warn("'count' is not a valid name for a validation")

        return cls(
            [expr.alias(key).meta.write_json() for key, expr in validations.items()]
        )

    @staticmethod
    def from_json(json_dict: Dict):
        tree = json_dict["tree"]
        return Check(tree)

    def __eq__(self, obj):
        return isinstance(obj, Check) and self.tree == obj.tree


class ColumnsSelect(Step):
    def __init__(self, columns: List[int]):
        self.columns = columns

    def to_json(self):
        return {"ColumnsSelect": {"columns": self.columns}}

    @staticmethod
    def from_json(json_dict: Dict):
        return ColumnsSelect(json_dict["columns"])

    def __eq__(self, obj):
        return isinstance(obj, ColumnsSelect) and self.columns == obj.columns

    def shortname(self):
        return f"ColumnsSelect [{self.columns}]"


class ColumnsToRows(Step):
    def to_json(self):
        return {"ColumnsToRows": {}}

    @staticmethod
    def from_json(json_dict: Dict):
        return ColumnsToRows()

    def __eq__(self, obj):
        return isinstance(obj, ColumnsToRows)


class ModelInference(Step):
    def __init__(self, models: List[ModelForStep]):
        self.models = models

    def to_json(self):
        jsonified_models = list(map(lambda m: m.to_json(), self.models))
        return {"ModelInference": {"models": jsonified_models}}

    def _repr_html_(self):
        return ",".join(
            [
                f"<tr><th>ModelInference</th><td>{m.name}</td><td>{m.version}</td></tr>"
                for m in self.models
            ]
        )

    @staticmethod
    def from_json(json_dict: Dict):
        return ModelInference(list(map(ModelForStep.from_json, json_dict["models"])))

    def is_inference_step(self):
        return True

    def shortname(self):
        return ",".join([m.name for m in self.models])

    def __eq__(self, obj):
        return isinstance(obj, ModelInference) and self.models == obj.models


class RowsToModels(Step):
    def __init__(self, rows_to_models: List[RowToModel]):
        self.rows_to_models = rows_to_models

    def to_json(self):
        jsonified_list = list(map(lambda m: m.to_json(), self.rows_to_models))
        return {"RowsToModels": {"rows_to_models": jsonified_list}}

    @staticmethod
    def from_json(json_dict: Dict):
        return RowsToModels(
            list(map(RowToModel.from_json, json_dict["rows_to_models"]))
        )

    def is_inference_step(self):
        return True

    def __eq__(self, obj):
        return (
            isinstance(obj, RowsToModels) and self.rows_to_models == obj.rows_to_models
        )


class Nth(Step):
    def __init__(self, index: int):
        self.index = index

    def to_json(self):
        return {"Nth": {"index": self.index}}

    @staticmethod
    def from_json(json_dict: Dict):
        return Nth(json_dict["index"])

    def __eq__(self, obj):
        return isinstance(obj, Nth) and self.index == obj.index

    def shortname(self):
        return f"Select [{self.index}]"


class MultiOut(Step):
    def to_json(self):
        return {"MultiOut": {}}

    @staticmethod
    def from_json(json_dict: Dict):
        return MultiOut()

    def __eq__(self, obj):
        return isinstance(obj, MultiOut)


class MetaValueSplit(Step):
    def __init__(
        self, split_key: str, control: ModelForStep, routes: Dict[str, ModelForStep]
    ):
        self.split_key = split_key
        self.control = control
        self.routes = routes

    def to_json(self):
        jsonified_routes = dict(
            zip(self.routes, map(lambda v: v.to_json(), self.routes.values()))
        )
        return {
            "MetaValueSplit": {
                "split_key": self.split_key,
                "control": self.control.to_json(),
                "routes": jsonified_routes,
            }
        }

    @staticmethod
    def from_json(json_dict: Dict):
        json_routes = json_dict["routes"]
        routes = dict(
            zip(json_routes, map(ModelForStep.from_json, json_routes.values()))
        )
        return MetaValueSplit(
            json_dict["split_key"], ModelForStep.from_json(json_dict["control"]), routes
        )

    def is_inference_step(self):
        return True

    def __eq__(self, obj):
        return (
            isinstance(obj, MetaValueSplit)
            and self.control == obj.control
            and self.routes == obj.routes
        )

    def shortname(self):
        return f"Key Split [{self.split_key}]"


class RandomSplit(Step):
    def __init__(self, weights: List[ModelWeight], hash_key: Optional[str] = None):
        self.hash_key = hash_key
        self.weights = weights

    def to_json(self):
        # TODO This is wrong
        jsonified_model_weights = list(map(lambda v: v.to_json(), self.weights))
        return {
            "RandomSplit": {
                "hash_key": self.hash_key,
                "weights": jsonified_model_weights,
            }
        }

    @staticmethod
    def from_json(json_dict: Dict):
        weights = list(map(ModelWeight.from_json, json_dict["weights"]))
        return RandomSplit(weights, hash_key=json_dict.get("hash_key"))

    def is_inference_step(self):
        return True

    def __eq__(self, obj):
        return (
            isinstance(obj, RandomSplit)
            and self.weights == obj.weights
            and self.hash_key == obj.hash_key
        )


class PipelineConfig:
    def __init__(
        self,
        pipeline_name: str,
        steps: Iterable[Step],
    ):
        self.pipeline_name = pipeline_name
        self.steps = steps

    def __eq__(self, other):
        return self.pipeline_name == other.pipeline_name and self.steps == other.steps

    def __repr__(self):
        return f"PipelineConfig({repr(self.pipeline_name)}, {repr(self.steps)})"

    @classmethod
    def from_json(Klass, json):
        return Klass(json["id"], [Step.from_json(v) for v in json["steps"]])

    def to_json(self):
        return {
            "id": self.pipeline_name,
            "steps": [s.to_json() for s in self.steps],
        }


class PipelineConfigBuilder:
    def __init__(
        self,
        client: "Client",
        pipeline_name: str,
    ):
        import re

        regex = r"[a-z0-9]([-a-z0-9]*[a-z0-9])?"
        comp = re.compile(regex)
        if not comp.fullmatch(pipeline_name):
            raise RuntimeError(
                f"Pipeline name `{pipeline_name}` must conform to {regex}"
            )

        self.client = client
        self.pipeline_name = pipeline_name
        self.steps: List[Step] = []
        self.model_configs: List[Optional[ModelConfigsForStep]] = []
        self.visibility = None

    def config(self) -> "PipelineConfig":
        return PipelineConfig(self.pipeline_name, self.steps)

    def upload(self) -> "Pipeline":
        return self.client._upload_pipeline_variant(self.pipeline_name, self.config())

    def _add_step(
        self, step: Step, configs: Optional[ModelConfigsForStep] = None
    ) -> "PipelineConfigBuilder":
        self.model_configs.append(configs)
        self.steps.append(step)
        return self

    def _check_replacement_bounds(self, index: int):
        if index > len(self.steps):
            raise IndexError(f"Step index {index} out of bounds")

    def _model_configs(self) -> List[ModelConfig]:
        """returns a list of all model configs"""
        configs = []
        for maybe_config in self.model_configs:
            if maybe_config:
                configs.extend(maybe_config.model_configs)

        return configs

    def _insert_step(
        self, index: int, step: Step, configs: Optional[ModelConfigsForStep] = None
    ) -> "PipelineConfigBuilder":
        self.model_configs.insert(index, configs)
        self.steps.insert(index, step)
        return self

    def remove_step(self, index: int):
        """Remove a step at a given index"""
        self._check_replacement_bounds(index)
        del self.model_configs[index]
        del self.steps[index]

    def _replace_step_at_index(
        self, index: int, step: Step, configs: Optional[ModelConfigsForStep] = None
    ) -> "PipelineConfigBuilder":
        self._check_replacement_bounds(index)
        self.model_configs[index] = configs
        self.steps[index] = step
        return self

    def add_model_step(self, model: ModelVersion) -> "PipelineConfigBuilder":
        """Perform inference with a single model."""
        return self._add_step(
            ModelInference([ModelForStep.from_model(model)]),
            ModelConfigsForStep([model.config()]),
        )

    def replace_with_model_step(
        self, index: int, model: ModelVersion
    ) -> "PipelineConfigBuilder":
        """Replaces the step at the given index with a model step"""
        config = ModelConfigsForStep([model.config()])
        step = ModelInference([ModelForStep.from_model(model)])
        return self._replace_step_at_index(index, step, config)

    def add_multi_model_step(
        self, models: Iterable[ModelVersion]
    ) -> "PipelineConfigBuilder":
        """Perform inference on the same input data for any number of models."""
        model_configs = [m.config() for m in models]
        models_for_step = [ModelForStep.from_model(m) for m in models]
        return self._add_step(
            ModelInference(models_for_step), ModelConfigsForStep(model_configs)
        )

    def replace_with_multi_model_step(
        self, index: int, models: Iterable[ModelVersion]
    ) -> "PipelineConfigBuilder":
        """Replaces the step at the index with a multi model step"""
        model_configs = [m.config() for m in models]
        models_for_step = [ModelForStep.from_model(m) for m in models]
        config = ModelConfigsForStep(model_configs)
        step = ModelInference(models_for_step)
        return self._replace_step_at_index(index, step, config)

    def _audit_from_slice_str(self, audit_slice: str) -> "AuditResults":
        slice_split = audit_slice.split(":")
        start = 0
        end = None
        if slice_split[0]:
            start = int(slice_split[0])
        if len(slice_split) > 1 and slice_split[1]:
            end = int(slice_split[1])
        return AuditResults(start, end)

    def add_audit(self, audit_slice: str) -> "PipelineConfigBuilder":
        """Run audit logging on a specified `slice` of model outputs.

        The slice must be in python-like format. `start:`, `start:end`, and
        `:end` are supported.
        """
        self.model_configs.append(None)
        return self._add_step(self._audit_from_slice_str(audit_slice))

    def replace_with_audit(
        self, index: int, audit_slice: str
    ) -> "PipelineConfigBuilder":
        """Replaces the step at the index with an audit step"""
        return self._replace_step_at_index(
            index, self._audit_from_slice_str(audit_slice)
        )

    def add_select(self, index: int) -> "PipelineConfigBuilder":
        """Select only the model output with the given `index` from an array of
        outputs.
        """
        return self._add_step(Nth(index))

    def add_multi_out(self):
        return self._add_step(MultiOut())

    def replace_with_select(
        self, step_index: int, select_index: int
    ) -> "PipelineConfigBuilder":
        """Replaces the step at the index with a select step"""
        return self._replace_step_at_index(step_index, Nth(select_index))

    def add_key_split(
        self, default: ModelVersion, meta_key: str, options: Dict[str, ModelVersion]
    ) -> "PipelineConfigBuilder":
        """Split traffic based on the value at a given `meta_key` in the input data,
        routing to the appropriate model.

        If the resulting value is a key in `options`, the corresponding model is used.
        Otherwise, the `default` model is used for inference.
        """

        control = ModelForStep.from_model(default)
        model_configs = [m.config() for m in options.values()]
        routes = dict(zip(options, map(ModelForStep.from_model, options.values())))
        configs = [default.config(), *model_configs]
        return self._add_step(
            MetaValueSplit(meta_key, control, routes), ModelConfigsForStep(configs)
        )

    def replace_with_key_split(
        self,
        index: int,
        default: ModelVersion,
        meta_key: str,
        options: Dict[str, ModelVersion],
    ) -> "PipelineConfigBuilder":
        """Replace the step at the index with a key split step"""
        control = ModelForStep.from_model(default)
        model_configs = [m.config() for m in options.values()]
        routes = dict(zip(options, map(ModelForStep.from_model, options.values())))
        configs = [default.config(), *model_configs]
        return self._replace_step_at_index(
            index,
            MetaValueSplit(meta_key, control, routes),
            ModelConfigsForStep(configs),
        )

    def add_random_split(
        self,
        weighted: Iterable[Tuple[float, ModelVersion]],
        hash_key: Optional[str] = None,
    ) -> "PipelineConfigBuilder":
        """Routes inputs to a single model, randomly chosen from the list of
        `weighted` options.

        Each model receives inputs that are approximately proportional to the
        weight it is assigned.  For example, with two models having weights 1
        and 1, each will receive roughly equal amounts of inference inputs. If
        the weights were changed to 1 and 2, the models would receive roughly
        33% and 66% respectively instead.

        When choosing the model to use, a random number between 0.0 and 1.0 is
        generated. The weighted inputs are mapped to that range, and the random
        input is then used to select the model to use. For example, for the
        two-models equal-weight case, a random key of 0.4 would route to the
        first model. 0.6 would route to the second.

        To support consistent assignment to a model, a `hash_key` can be
        specified. This must be between 0.0 and 1.0. The value at this key, when
        present in the input data, will be used instead of a random number for
        model selection.
        """
        weights = list(map(ModelWeight.from_tuple, weighted))
        self.model_configs.append(
            ModelConfigsForStep([m.config() for (_, m) in weighted])
        )
        return self._add_step(RandomSplit(weights, hash_key))

    def replace_with_random_split(
        self,
        index: int,
        weighted: Iterable[Tuple[float, ModelVersion]],
        hash_key: Optional[str] = None,
    ) -> "PipelineConfigBuilder":
        """Replace the step at the index with a random split step"""
        weights = list(map(ModelWeight.from_tuple, weighted))
        return self._replace_step_at_index(
            index,
            RandomSplit(weights, hash_key),
            ModelConfigsForStep([m.config() for (_, m) in weighted]),
        )

    def add_shadow_deploy(
        self, champion: ModelVersion, challengers: Iterable[ModelVersion]
    ) -> "PipelineConfigBuilder":
        """Create a "shadow deployment" experiment pipeline. The `champion`
        model and all `challengers` are run for each input. The result data for
        all models is logged, but the output of the `champion` is the only
        result returned.

        This is particularly useful for "burn-in" testing a new model with real
        world data without displacing the currently proven model.

        This is currently implemented as three steps: A multi model step, an audit step, and
        a select step. To remove or replace this step, you need to remove or replace
        all three. You can remove steps using pipeline.remove_step
        """
        # TODO This should be a single step and the backend can implement it as 3 steps
        return (
            self.add_multi_model_step([champion, *challengers])
            .add_audit("1:")
            .add_multi_out()
        )

    def replace_with_shadow_deploy(
        self, index: int, champion: ModelVersion, challengers: Iterable[ModelVersion]
    ) -> "PipelineConfigBuilder":
        return (
            self.replace_with_multi_model_step(index, [champion, *challengers])
            ._insert_step(index + 1, self._audit_from_slice_str("1:"))
            ._insert_step(index + 2, MultiOut())
        )

    def _add_instrument(self, step: Step) -> "PipelineConfigBuilder":
        self._insert_step(len(self.steps), step)
        return self

    def add_validations(self, **validations: polars.Expr) -> "PipelineConfigBuilder":
        """Add a dict of `validations` to run on every row."""
        return self._add_instrument(Check.from_validation_dict(validations))

    def replace_with_validations(
        self, index: int, **validations: polars.Expr
    ) -> "PipelineConfigBuilder":
        """Replace the step at the given index with a different validation dict"""
        return self._replace_step_at_index(
            index, Check.from_validation_dict(validations)
        )

    def clear(self) -> "PipelineConfigBuilder":
        """
        Remove all steps from the pipeline. This might be desireable if replacing models, for example.
        """
        self.steps = []
        self.model_configs = []
        return self
