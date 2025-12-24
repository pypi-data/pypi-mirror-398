from wallaroo.wallaroo_ml_ops_api_client.models.model_status import ModelStatus


def model_status_to_string(status: ModelStatus) -> str:
    if status == ModelStatus.PENDING_LOAD_NATIVE:
        return "pending loading to a native runtime"
    elif status == ModelStatus.ATTEMPTING_LOAD_NATIVE:
        return "attempting loading to a native runtime"
    elif status == ModelStatus.PENDING_LOAD_CONTAINER:
        return "pending loading to a container runtime"
    elif status == ModelStatus.ATTEMPTING_LOAD_CONTAINER:
        return "attempting loading to a container runtime"
    elif status == ModelStatus.UPLOADING:
        return "uploading"
    elif status == ModelStatus.ERROR:
        return "error"
    elif status == ModelStatus.READY:
        return "ready"
    else:
        return f"unknown status: {status}"


def is_attempting_load(status: ModelStatus) -> bool:
    return (
        status == ModelStatus.ATTEMPTING_LOAD_CONTAINER
        or status == ModelStatus.ATTEMPTING_LOAD_NATIVE
    )
