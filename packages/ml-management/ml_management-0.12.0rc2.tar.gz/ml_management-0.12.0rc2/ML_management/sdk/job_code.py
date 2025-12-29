import os
import warnings
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel
from sgqlc.operation import Operation

from ML_management.graphql import schema
from ML_management.graphql.schema import BuildArgInput, CodeJob, CustomImage, EnvParamInput
from ML_management.graphql.send_graphql_request import send_graphql_request
from ML_management.mlmanagement.git_info import get_git_info
from ML_management.mlmanagement.log_api import _open_pipe_send_request, _raise_error
from ML_management.mlmanagement.utils import calculate_hash_directory, hash_file
from ML_management.mlmanagement.visibility_options import VisibilityOptions
from ML_management.sdk.job import _get_logs
from ML_management.sdk.parameters import ResourcesForm
from ML_management.sdk.types import JobType
from ML_management.variables import get_log_service_url


class CodeMetaInfo(BaseModel):
    code_id: int
    experiment_name: str


def _get_code_hash(hash_code: str, visibility: VisibilityOptions) -> Optional[int]:
    op = Operation(schema.Query)
    op.get_code_with_hash(hash_code=hash_code, visibility=visibility.name)

    result = send_graphql_request(op=op, json_response=False)
    return result.get_code_with_hash


def _base_query_image(base):
    base.name()
    base.id()
    base.description()
    base.build_args()
    base.visibility()
    base.is_active()
    base.build_job.build_object_name()
    base.build_job.status()
    base.build_job.message()


def delete_image(name: str):
    """
    Marks the image as inactive. You will no longer be able to run tasks with it, but you can view information.

    Parameters
    ----------
    name: str
         The name of the base image.
    Returns
    -------
    None
    """
    op = Operation(schema.Mutation)
    op.delete_image(name=name)
    send_graphql_request(op=op, json_response=False)


def get_available_images() -> List[CustomImage]:
    """Get available images for custom code job.

    Returns
    -------
    List[CustomImage]
        List of instances of the CustomImage.

    """
    op = Operation(schema.Query)
    base = op.available_images()
    _base_query_image(base)

    result = send_graphql_request(op=op, json_response=False)
    return result.available_images


def add_custom_code_job(
    local_path: str,
    bash_commands: List[str],
    image_name: str,
    job_name: Optional[str] = None,
    env_variables: Optional[Dict[str, str]] = None,
    resources: Optional[ResourcesForm] = None,
    is_distributed: bool = False,
    experiment_name: str = "Default",
    experiment_visibility: Union[
        Literal[VisibilityOptions.PRIVATE, VisibilityOptions.PUBLIC], VisibilityOptions
    ] = VisibilityOptions.PRIVATE,
    visibility: Union[Literal["private", "public"], VisibilityOptions] = VisibilityOptions.PRIVATE,
    additional_system_packages: Optional[List[str]] = None,
    verbose: bool = True,
) -> CodeJob:
    """
    Create execution job from arbitrary code.

    The job created by this function can be executed on an arbitrary number of nodes greater than or equal to 1.
    The computing cluster distributes all resources equally among the allocated nodes.
    If such an equal distribution is not possible, the job will be rejected.

    Parameters
    ----------
    local_path: str
        Path to folder with code.
    bash_commands: List[str]
        Commands that will be run in the execution container.
    image_name: str
        The name of the base image on which the job will be executed.
    job_name: Optional[str] = None
        Name of the created job.
    env_variables: Optional[Dict[str, str]] = None
        Environment variables that will be set before starting the job.
    resources: ResourcesForm
        Resources required for job execution.
        They will be allocated on one node, if it is not possible, job will be rejected.
    is_distributed: bool = False
        Distributed mode.
    experiment_name: ExperimentParams
        Name of the experiment. Default: "Default"
    experiment_visibility: Union[Literal['private', 'public'], VisibilityOptions]
        Visibility of experiment if this is new. Default: PRIVATE.
    visibility: Union[Literal['private', 'public'], VisibilityOptions]
        Visibility of this job to other users. Default: PRIVATE.
    additional_system_packages: Optional[List[str]] = None
        List of system libraries for Debian family distributions that need to be installed in the job. Default: None
    verbose: bool = True
        Whether to disable the entire progressbar wrapper.

    Returns
    -------
    CodeJob
        Instance of the Job class.
    """
    visibility = VisibilityOptions(visibility)
    experiment_visibility = VisibilityOptions(experiment_visibility)
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Path: {local_path} does not exist.")

    log_request = {
        "visibility": visibility,
        "experiment_name": experiment_name,
        "experiment_visibility": experiment_visibility,
    }

    hash_code = calculate_hash_directory(local_path) if os.path.isdir(local_path) else hash_file(local_path)
    code_id = _get_code_hash(hash_code, visibility)
    experiment_params = schema.ExperimentInput(experiment_name=experiment_name, visibility=experiment_visibility.name)

    if code_id is None:
        git_info = get_git_info(local_path)
        log_request["hash_code"] = hash_code
        log_request["git_info"] = git_info.model_dump() if git_info else None
        response = _open_pipe_send_request(
            local_path, log_request, url=get_log_service_url("log_job_code"), verbose=verbose
        )
        _raise_error(response)
        result = response.json()
        info = CodeMetaInfo.model_validate(result)
        code_id = info.code_id

    if resources is None:
        resources = ResourcesForm()
    resources = schema.ResourcesInput(
        cpus=resources.cpus,
        memory_per_node=resources.memory_per_node,
        gpu_number=resources.gpu_number,
        gpu_type=resources.gpu_type,
    )
    op = Operation(schema.Mutation)
    mutation = op.add_custom_code_job(
        form=schema.JobCodeParameters(
            code_id=code_id,
            bash_commands=bash_commands,
            experiment_params=experiment_params,
            visibility=VisibilityOptions(visibility).name,
            additional_system_packages=additional_system_packages,
            job_name=job_name,
            image_name=image_name,
            resources=resources,
            is_distributed=is_distributed,
            env_variables=[EnvParamInput(key=key, value=value) for key, value in env_variables.items()]
            if env_variables
            else None,
        )
    )

    mutation.name()
    mutation.id()

    job = send_graphql_request(op, json_response=False)

    return job.add_custom_code_job


def _get_image_hash(hash_data: str) -> CustomImage:
    op = Operation(schema.Query)
    base = op.get_image_with_hash(hash_data=hash_data)
    _base_query_image(base)

    result = send_graphql_request(op=op, json_response=False)
    return result.get_image_with_hash


def rebuild_image(name: str, build_args: Optional[dict] = None) -> CustomImage:
    """
    Rebuild user image.

    Parameters
    ----------
    name: str
         The name of the base image.
    build_args: Optional[dict] = None
        Commands that will be run in the execution container.
        If None is passed, the previous parameters will be used.
    Returns
    -------
    CustomImage
        Instance of the CustomImage class.
    """
    if build_args is not None:
        build_args = [BuildArgInput(key=key, value=str(value)) for key, value in build_args.items()]
    op = Operation(schema.Mutation)
    base = op.rebuild_image(name=name, build_args=build_args)
    _base_query_image(base)

    result = send_graphql_request(op=op, json_response=False)
    return result.rebuild_image


def log_image(
    local_path: str, name: str, description: str, build_args: Optional[dict] = None, verbose: bool = True
) -> CustomImage:
    """
    Rebuild user image.

    Parameters
    ----------
    local_path: str
        Path to Dockerfile or to folder with Dockerfile.
    name: str
        The name of the image.
    build_args: Optional[dict] = None
        Commands that will be run in the build image.
    description: str
        Description of the image.
    verbose: bool = True
        Whether to disable the entire progressbar wrapper.
    Returns
    -------
    CustomImage
        Instance of the CustomImage class.
    """
    if (os.path.isfile(local_path) and os.path.basename(local_path) != "Dockerfile") or (
        os.path.isdir(local_path) and "Dockerfile" not in os.listdir(local_path)
    ):
        raise Exception(
            "The passed local path must be the path to the Dockerfile or to the directory that contains it."
        )

    hash_data = calculate_hash_directory(local_path) if os.path.isdir(local_path) else hash_file(local_path)
    image = _get_image_hash(hash_data)
    if image:
        warnings.warn("Such an image already exists.")
        return image

    else:
        log_request = {"hash_data": hash_data, "name": name, "description": description}

        response = _open_pipe_send_request(
            local_path, log_request, url=get_log_service_url("log_image"), verbose=verbose
        )
        _raise_error(response)
        result = response.json()
        image_name = result["name"]

        return rebuild_image(image_name, build_args)


def get_build_image_logs(
    name: str,
    stream: bool = True,
    file_name: Optional[str] = None,
) -> None:
    """
    Stream logs of the build job by image name.

    Parameters
    ----------
    name: str
        The name of the image.
    stream: bool = True
        Stream logs or dump all available at the moment.
    file_name: Optional[str] = None
        Name of the file where to save logs. Default: None. If None prints logs to the output.
    """
    _get_logs(
        job_type=JobType.build,
        stream=stream,
        file_name=file_name,
        params={"image_name": name},
    )


def get_image(name: str) -> CustomImage:
    """
    Get image for custom code job.

    Parameters
    ----------
    name: str
    The name of the image.

    Returns
    -------
    CustomImage
        Instance of the CustomImage.

    """
    op = Operation(schema.Query)
    base = op.get_image(name=name)
    _base_query_image(base)

    result = send_graphql_request(op=op, json_response=False).get_image
    return result
