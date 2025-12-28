from unittest.mock import Mock

import pytest

from wallaroo.engine_config import Acceleration
from wallaroo.pipeline import (
    _accel_from_deployment,
    _accel_from_deployment_or_model_configs,
    _accel_from_model_configs,
)


@pytest.mark.parametrize(
    "engine_aux_images,expected_accel",
    [
        (None, str(Acceleration._None)),
        ({}, str(Acceleration._None)),
        ({"images": {}}, str(Acceleration._None)),
        (
            {"images": {"img1": {"accel": str(Acceleration._None)}}},
            str(Acceleration._None),
        ),
        (
            {"images": {"img1": {"accel": str(Acceleration.CUDA)}}},
            str(Acceleration.CUDA),
        ),
        (
            {
                "images": {
                    "img1": {"accel": str(Acceleration.CUDA)},
                    "img2": {"accel": str(Acceleration.CUDA)},
                    "img3": {"accel": str(Acceleration.CUDA)},
                }
            },
            str(Acceleration.CUDA),
        ),
        (
            {
                "images": {
                    "img1": {"accel": str(Acceleration.CUDA)},
                    "img2": {"accel": str(Acceleration.Jetson)},
                    "img3": {"accel": str(Acceleration.OpenVINO)},
                }
            },
            str(Acceleration._None),
        ),
        (
            {
                "images": {
                    "img1": {"accel": str(Acceleration._None)},
                    "img2": {"accel": str(Acceleration.CUDA)},
                    "img3": {"accel": str(Acceleration.CUDA)},
                }
            },
            str(Acceleration.CUDA),
        ),
        (
            {
                "images": {
                    "img1": {"other_field": "value"},
                    "img2": {"accel": str(Acceleration.CUDA)},
                }
            },
            str(Acceleration.CUDA),
        ),
        (
            {
                "images": {
                    "img1": {"other_field": "value"},
                    "img2": {"another_field": "value"},
                }
            },
            str(Acceleration._None),
        ),
    ],
)
def test_accel_from_deployment(engine_aux_images, expected_accel):
    deployment = Mock()
    deployment.engine_config.return_value = {"engineAux": engine_aux_images or {}}
    result = _accel_from_deployment(deployment)
    assert result == expected_accel


@pytest.mark.parametrize(
    "model_configs,expected_accel",
    [
        ([], str(Acceleration._None)),
        (
            [
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration._None))
                    )
                )
            ],
            str(Acceleration._None),
        ),
        (
            [
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
                    )
                )
            ],
            Acceleration.CUDA,
        ),
        (
            [
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
                    )
                ),
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
                    )
                ),
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
                    )
                ),
            ],
            Acceleration.CUDA,
        ),
        (
            [
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
                    )
                ),
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration.Jetson))
                    )
                ),
                Mock(
                    model_version=Mock(
                        return_value=Mock(
                            accel=Mock(return_value=Acceleration.OpenVINO)
                        )
                    )
                ),
            ],
            str(Acceleration._None),
        ),
        (
            [
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration._None))
                    )
                ),
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
                    )
                ),
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
                    )
                ),
            ],
            Acceleration.CUDA,
        ),
    ],
)
def test_accel_from_model_configs(model_configs, expected_accel):
    result = _accel_from_model_configs(model_configs)
    assert result == expected_accel


@pytest.mark.parametrize(
    "deployment,model_configs,expected_accel",
    [
        (None, [], str(Acceleration._None)),
        (
            None,
            [
                Mock(
                    model_version=Mock(
                        return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
                    )
                )
            ],
            Acceleration.CUDA,
        ),
        (
            Mock(
                engine_config=Mock(
                    return_value={"engine": {"accel": str(Acceleration.CUDA)}}
                )
            ),
            [],
            str(Acceleration.CUDA),
        ),
        (
            Mock(
                engine_config=Mock(
                    return_value={
                        "engine": {"accel": str(Acceleration._None)},
                        "engineAux": {
                            "images": {
                                "img1": {"accel": str(Acceleration.CUDA)},
                                "img2": {"accel": str(Acceleration.CUDA)},
                            }
                        },
                    }
                )
            ),
            [],
            str(Acceleration.CUDA),
        ),
        (
            Mock(
                engine_config=Mock(
                    return_value={
                        "engine": {"accel": str(Acceleration._None)},
                        "engineAux": {
                            "images": {
                                "img1": {"accel": str(Acceleration.CUDA)},
                                "img2": {"accel": str(Acceleration.Jetson)},
                            }
                        },
                    }
                )
            ),
            [],
            str(Acceleration._None),
        ),
        (
            Mock(
                engine_config=Mock(
                    return_value={
                        "engine": {"accel": str(Acceleration._None)},
                        "engineAux": {"images": {}},
                    }
                )
            ),
            [],
            str(Acceleration._None),
        ),
        (
            Mock(
                engine_config=Mock(
                    return_value={
                        "engine": {"accel": str(Acceleration._None)},
                        "engineAux": {
                            "images": {
                                "img1": {"accel": str(Acceleration._None)},
                                "img2": {"accel": str(Acceleration.CUDA)},
                            }
                        },
                    }
                )
            ),
            [],
            str(Acceleration.CUDA),
        ),
        (
            Mock(
                engine_config=Mock(
                    return_value={"engine": {"accel": str(Acceleration.default())}}
                )
            ),
            [],
            str(Acceleration.default()),
        ),
        (
            Mock(
                engine_config=Mock(
                    return_value={
                        "engine": {"accel": str(Acceleration._None)},
                        "engineAux": {
                            "images": {"img1": {"accel": str(Acceleration.QAIC)}}
                        },
                    }
                )
            ),
            [],
            str(Acceleration.QAIC),
        ),
    ],
)
def test_accel_from_deployment_or_model_configs(
    deployment, model_configs, expected_accel
):
    result = _accel_from_deployment_or_model_configs(deployment, model_configs)
    assert result == expected_accel


def test_accel_from_deployment_or_model_configs_with_deployment_and_model_configs():
    deployment = Mock(
        engine_config=Mock(
            return_value={
                "engine": {"accel": str(Acceleration._None)},
                "engineAux": {"images": {"img1": {"accel": str(Acceleration.CUDA)}}},
            }
        )
    )
    model_configs = [
        Mock(
            model_version=Mock(
                return_value=Mock(accel=Mock(return_value=Acceleration.Jetson))
            )
        )
    ]
    result = _accel_from_deployment_or_model_configs(deployment, model_configs)
    assert result == str(Acceleration.CUDA)


def test_accel_from_deployment_or_model_configs_deployment_priority():
    deployment = Mock(
        engine_config=Mock(return_value={"engine": {"accel": str(Acceleration.CUDA)}})
    )
    model_configs = [
        Mock(
            model_version=Mock(
                return_value=Mock(accel=Mock(return_value=Acceleration.Jetson))
            )
        )
    ]
    result = _accel_from_deployment_or_model_configs(deployment, model_configs)
    assert result == str(Acceleration.CUDA)


def test_accel_from_deployment_missing_images():
    deployment = Mock()
    deployment.engine_config.return_value = {"engineAux": {"other_field": "value"}}
    result = _accel_from_deployment(deployment)
    assert result == str(Acceleration._None)


def test_accel_from_deployment_empty_images_dict():
    deployment = Mock()
    deployment.engine_config.return_value = {"engineAux": {"images": {}}}
    result = _accel_from_deployment(deployment)
    assert result == str(Acceleration._None)


def test_accel_from_deployment_images_without_accel_field():
    deployment = Mock()
    deployment.engine_config.return_value = {
        "engineAux": {
            "images": {
                "img1": {"other_field": "value"},
                "img2": {"another_field": "value"},
            }
        }
    }
    result = _accel_from_deployment(deployment)
    assert result == str(Acceleration._None)


def test_accel_from_model_configs_all_none_accels():
    model_configs = [
        Mock(
            model_version=Mock(
                return_value=Mock(accel=Mock(return_value=Acceleration._None))
            )
        ),
        Mock(
            model_version=Mock(
                return_value=Mock(accel=Mock(return_value=Acceleration._None))
            )
        ),
        Mock(
            model_version=Mock(
                return_value=Mock(accel=Mock(return_value=Acceleration._None))
            )
        ),
    ]
    result = _accel_from_model_configs(model_configs)
    assert result == str(Acceleration._None)


def test_accel_from_model_configs_mixed_none_and_non_none():
    model_configs = [
        Mock(
            model_version=Mock(
                return_value=Mock(accel=Mock(return_value=Acceleration._None))
            )
        ),
        Mock(
            model_version=Mock(
                return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
            )
        ),
        Mock(
            model_version=Mock(
                return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
            )
        ),
    ]
    result = _accel_from_model_configs(model_configs)
    assert result == Acceleration.CUDA


def test_accel_from_deployment_or_model_configs_deployment_none_model_configs_none():
    result = _accel_from_deployment_or_model_configs(None, [])
    assert result == str(Acceleration._None)


def test_accel_from_deployment_or_model_configs_deployment_none_with_model_configs():
    model_configs = [
        Mock(
            model_version=Mock(
                return_value=Mock(accel=Mock(return_value=Acceleration.CUDA))
            )
        )
    ]
    result = _accel_from_deployment_or_model_configs(None, model_configs)
    assert result == Acceleration.CUDA


def test_accel_from_deployment_or_model_configs_deployment_with_engine_accel_none_fallback():
    deployment = Mock(
        engine_config=Mock(
            return_value={
                "engine": {"accel": str(Acceleration._None)},
                "engineAux": {"images": {"img1": {"accel": str(Acceleration.QAIC)}}},
            }
        )
    )
    result = _accel_from_deployment_or_model_configs(deployment, [])
    assert result == str(Acceleration.QAIC)


def test_accel_from_deployment_or_model_configs_deployment_with_default_engine_accel():
    deployment = Mock(
        engine_config=Mock(
            return_value={"engine": {"accel": str(Acceleration.default())}}
        )
    )
    result = _accel_from_deployment_or_model_configs(deployment, [])
    assert result == str(Acceleration.default())


def test_accel_from_deployment_or_model_configs_deployment_missing_engine_key():
    deployment = Mock()
    deployment.engine_config.return_value = {"other_field": "value"}
    result = _accel_from_deployment_or_model_configs(deployment, [])
    assert result == str(Acceleration._None)


def test_accel_from_deployment_or_model_configs_deployment_missing_accel_key():
    deployment = Mock()
    deployment.engine_config.return_value = {"engine": {"other_field": "value"}}
    result = _accel_from_deployment_or_model_configs(deployment, [])
    assert result == str(Acceleration._None)
