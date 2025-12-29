import sys
import traceback
from typing import Literal, Optional, Union

from sgqlc.operation import Operation

from ML_management import variables
from ML_management.graphql import schema
from ML_management.graphql.schema import CodeJob, LocalJob, MLMJob
from ML_management.graphql.send_graphql_request import send_graphql_request
from ML_management.mlmanagement.batcher import Batcher
from ML_management.mlmanagement.metric_autostepper import MetricAutostepper
from ML_management.mlmanagement.visibility_options import VisibilityOptions
from ML_management.s3.utils import _send_used_buckets_info
from ML_management.variables import DEFAULT_EXPERIMENT


class ActiveJob:
    """
    A context manager that allows for the execution of a task locally.

    This class provides a convenient way to run a job locally.
    """

    def __init__(self, secret_uuid):
        self.secret_uuid = secret_uuid
        self.job = self._start()
        self.__is_distributed = (
            self.job.params.is_distributed if hasattr(self.job, "params") and self.job.params else False
        )

    def __enter__(self) -> "ActiveJob":
        return self

    def _start(self) -> Union[CodeJob, LocalJob, MLMJob]:
        op = Operation(schema.Mutation)
        base_query = op.start_job(secret_uuid=self.secret_uuid)
        _query_job_params(base_query)
        job = send_graphql_request(op=op, json_response=False).start_job
        variables.secret_uuid = self.secret_uuid
        variables.active_job = True
        variables.sent_used_buckets = set(job.list_buckets)
        return job

    def __exit__(self, exc_type, exc_val, exc_tb):
        variables.active_job = False
        if self.__is_distributed:
            Batcher().wait_log_metrics()
            return
        exception_traceback = None
        message = None
        status = "SUCCESSFUL"
        if exc_type:
            exception_traceback = traceback.format_exc()
            message = ": ".join([exc_type.__name__, str(exc_val)])
            status = "FAILED"
        return stop_job(status, message, exception_traceback)


def start_job(
    job_name: Optional[str] = None,
    experiment_name: str = DEFAULT_EXPERIMENT,
    experiment_visibility: Union[Literal["private", "public"], VisibilityOptions] = VisibilityOptions.PRIVATE,
    visibility: Union[Literal["private", "public"], VisibilityOptions] = VisibilityOptions.PRIVATE,
) -> ActiveJob:
    """
    Create local job.

    Usage::

        with start_job('my-beautiful-job') as job:
            mlmanagement.log_metric(...)
            mlmanagement.log_artifacts(...)


    Or::

        start_job('my-beautiful-job')
        mlmanagement.log_metric(...)
        mlmanagement.log_artifacts(...)
        stop_job()


    Parameters
    ----------
    job_name: str | None=None
        Name of the new job. If not passed, it will be generated.
    experiment_name: str = "Default"
        Name of the experiment. Default: "Default"
    experiment_visibility: Union[Literal['private', 'public'], VisibilityOptions]
        Visibility of experiment if this is new. Default: PRIVATE.
    visibility: Union[Literal['private', 'public'], VisibilityOptions]
        Visibility of this job to other users. Default: PRIVATE.

    Returns
    -------
    ActiveJob
        Active job.
    """
    sys.excepthook = _stop_job_at_exception_hook
    visibility = VisibilityOptions(visibility)
    experiment_visibility = VisibilityOptions(experiment_visibility)
    op = Operation(schema.Mutation)
    op.create_local_job(
        job_name=job_name,
        experiment_params=schema.ExperimentInput(
            experiment_name=experiment_name, visibility=experiment_visibility.name
        ),
        visibility=visibility.name,
    )
    secret_uuid = send_graphql_request(op=op, json_response=False).create_local_job
    return ActiveJob(secret_uuid)


def _stop_job_at_exception_hook(exc_type, exc_value, exc_traceback):
    try:
        stop_job("FAILED", f"{exc_type}: {exc_value}")
    except:  # noqa E722
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def stop_job(
    status: Literal["SUCCESSFUL", "FAILED"] = "SUCCESSFUL",
    message: Optional[str] = None,
    exception_traceback: Optional[str] = None,
) -> None:
    """
    Stop local job.

    Parameters
    ----------
    status: Literal["SUCCESSFUL", "FAILED"] = "SUCCESSFUL"
        Status of the job. If not passed, it will be SUCCESSFUL.
    message: Optional[str] = None
        Extra message for the job. Default: None
    exception_traceback: Optional[str] = None
        Error traceback of the job. Default: None

    Returns
    -------
    None
    """
    sys.excepthook = sys.__excepthook__

    Batcher().wait_log_metrics()
    op = Operation(schema.Mutation)
    op.stop_job(
        secret_uuid=variables.get_secret_uuid(), status=status, message=message, exception_traceback=exception_traceback
    )
    try:
        _ = send_graphql_request(op=op, json_response=False).stop_job
    finally:
        variables.secret_uuid = None
        variables.sent_used_buckets.clear()
        if variables.unsent_used_buckets:
            _send_used_buckets_info(list(variables.unsent_used_buckets)[0])
        variables.unsent_used_buckets.clear()
        MetricAutostepper().clear()


def _query_job_params(base_query):
    job_local = base_query.__as__(LocalJob)
    job_code = base_query.__as__(CodeJob)
    job_mlm = base_query.__as__(MLMJob)

    for job in [job_local, job_code, job_mlm]:
        job.name()
        job.id()
        job.status()
        job.registration_timestamp()
        job.start_timestamp()
        job.end_timestamp()
        job.message()
        job.list_buckets()
        job.experiment.name()

    job_code_params = job_code.params()
    job_code_params.resources.cpus()
    job_code_params.resources.memory_per_node()
    job_code_params.resources.gpu_number()
    job_code_params.resources.gpu_type()
    job_code_params.bash_commands()
    job_code_params.image_name()
    job_code_params.code_id()
    job_code_params.is_distributed()

    job_mlm_params = job_mlm.params()
    job_mlm_params.resources.cpus()
    job_mlm_params.is_distributed()
    job_mlm_params.resources.memory_per_node()
    job_mlm_params.resources.gpu_number()
    job_mlm_params.resources.gpu_type()
    job_mlm_params.list_role_model_params()
    job_mlm_params.list_role_data_params()
    job_mlm_params.list_role_data_params.data_params()
    job_mlm_params.list_role_data_params.role()
    job_mlm_params.list_role_model_params.model_params()
    job_mlm_params.list_role_model_params.upload_params()
    job_mlm_params.list_role_model_params.role()
    job_mlm_params.executor_params()
    job_mlm_params.executor_params.executor_method_params()
    job_mlm_params.executor_params.executor_version_choice()
