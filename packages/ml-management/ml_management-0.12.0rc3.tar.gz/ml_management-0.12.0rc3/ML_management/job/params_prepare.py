from ML_management.mlmanagement.load_api import deserialize_kwargs_to_annotation


def method_params_prepare(model, method_name: str, params: dict) -> dict:
    return deserialize_kwargs_to_annotation(getattr(model, method_name), params)
