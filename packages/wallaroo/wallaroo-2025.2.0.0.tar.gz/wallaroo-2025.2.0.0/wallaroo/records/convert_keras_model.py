# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = convert_keras_model_from_dict(json.loads(json_string))

from typing import Optional, Any, List, TypeVar, Type, cast, Callable


T = TypeVar("T")


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


class ConvertKerasMutation:
    ok: Optional[bool]
    model: int

    def __init__(self, ok: Optional[bool], model: int) -> None:
        self.ok = ok
        self.model = model

    @staticmethod
    def from_dict(obj: Any) -> "ConvertKerasMutation":
        assert isinstance(obj, dict)
        ok = from_union([from_bool, from_none], obj.get("ok"))
        model = from_int(obj.get("model"))
        return ConvertKerasMutation(ok, model)

    def to_dict(self) -> dict:
        result: dict = {}
        result["ok"] = from_union([from_bool, from_none], self.ok)
        result["model"] = from_int(self.model)
        return result


class Data:
    convert_keras: Optional[ConvertKerasMutation]

    def __init__(self, convert_keras: Optional[ConvertKerasMutation]) -> None:
        self.convert_keras = convert_keras

    @staticmethod
    def from_dict(obj: Any) -> "Data":
        assert isinstance(obj, dict)
        convert_keras = from_union(
            [ConvertKerasMutation.from_dict, from_none], obj.get("convertKeras")
        )
        return Data(convert_keras)

    def to_dict(self) -> dict:
        result: dict = {}
        result["convertKeras"] = from_union(
            [lambda x: to_class(ConvertKerasMutation, x), from_none], self.convert_keras
        )
        return result


class Error:
    message: str

    def __init__(self, message: str) -> None:
        self.message = message

    @staticmethod
    def from_dict(obj: Any) -> "Error":
        assert isinstance(obj, dict)
        message = from_str(obj.get("message"))
        return Error(message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["message"] = from_str(self.message)
        return result


class ConvertKerasModel:
    data: Optional[Data]
    errors: Optional[List[Error]]

    def __init__(self, data: Optional[Data], errors: Optional[List[Error]]) -> None:
        self.data = data
        self.errors = errors

    @staticmethod
    def from_dict(obj: Any) -> "ConvertKerasModel":
        assert isinstance(obj, dict)
        data = from_union([Data.from_dict, from_none], obj.get("data"))
        errors = from_union(
            [lambda x: from_list(Error.from_dict, x), from_none], obj.get("errors")
        )
        return ConvertKerasModel(data, errors)

    def to_dict(self) -> dict:
        result: dict = {}
        result["data"] = from_union([lambda x: to_class(Data, x), from_none], self.data)
        result["errors"] = from_union(
            [lambda x: from_list(lambda x: to_class(Error, x), x), from_none],
            self.errors,
        )
        return result


def convert_keras_model_from_dict(s: Any) -> ConvertKerasModel:
    return ConvertKerasModel.from_dict(s)


def convert_keras_model_to_dict(x: ConvertKerasModel) -> Any:
    return to_class(ConvertKerasModel, x)
