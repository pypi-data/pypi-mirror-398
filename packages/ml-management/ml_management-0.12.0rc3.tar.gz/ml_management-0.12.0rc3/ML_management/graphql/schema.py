import sgqlc.types


schema = sgqlc.types.Schema()


__docformat__ = 'markdown'


########################################################################
# Scalars and Enumerations
########################################################################
Boolean = sgqlc.types.Boolean

class ExecutionJobType(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `CODE`None
    * `LOCAL`None
    * `MLM`None
    '''
    __schema__ = schema
    __choices__ = ('CODE', 'LOCAL', 'MLM')


class ExperimentSortBy(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `experiment_id`None
    * `name`None
    '''
    __schema__ = schema
    __choices__ = ('experiment_id', 'name')


Float = sgqlc.types.Float

ID = sgqlc.types.ID

Int = sgqlc.types.Int

class JSON(sgqlc.types.Scalar):
    '''The `JSON` scalar type represents JSON values as specified by
    [ECMA-404](http://www.ecma-
    international.org/publications/files/ECMA-ST/ECMA-404.pdf).
    '''
    __schema__ = schema


class JobStatus(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `CANCELED`None
    * `CANCELLING`None
    * `FAILED`None
    * `PLANNED`None
    * `REGISTERED`None
    * `REJECTED`None
    * `RUNNING`None
    * `SUCCESSFUL`None
    * `UNKNOWN`None
    '''
    __schema__ = schema
    __choices__ = ('CANCELED', 'CANCELLING', 'FAILED', 'PLANNED', 'REGISTERED', 'REJECTED', 'RUNNING', 'SUCCESSFUL', 'UNKNOWN')


class JobsSortBy(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `metrics`None
    * `name`None
    * `registration_timestamp`None
    '''
    __schema__ = schema
    __choices__ = ('metrics', 'name', 'registration_timestamp')


class Long(sgqlc.types.Scalar):
    '''The `Long` scalar type represents long int type.'''
    __schema__ = schema


class MetricAxis(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `autostep`None
    * `relative`None
    * `step`None
    * `timestamp`None
    '''
    __schema__ = schema
    __choices__ = ('autostep', 'relative', 'step', 'timestamp')


class MetricOptionInput(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `latest`None
    * `max`None
    * `mean`None
    * `median`None
    * `min`None
    '''
    __schema__ = schema
    __choices__ = ('latest', 'max', 'mean', 'median', 'min')


class ModelType(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `DATASET_LOADER`None
    * `EXECUTOR`None
    * `MODEL`None
    '''
    __schema__ = schema
    __choices__ = ('DATASET_LOADER', 'EXECUTOR', 'MODEL')


class ObjectSortBy(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `creation_timestamp`None
    * `name`None
    '''
    __schema__ = schema
    __choices__ = ('creation_timestamp', 'name')


class ObjectVersionSortBy(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `creation_timestamp`None
    * `name`None
    * `version`None
    '''
    __schema__ = schema
    __choices__ = ('creation_timestamp', 'name', 'version')


class SortDirection(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `ascending`None
    * `descending`None
    '''
    __schema__ = schema
    __choices__ = ('ascending', 'descending')


String = sgqlc.types.String

class UploadModelMode(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `new_model`None
    * `new_version`None
    '''
    __schema__ = schema
    __choices__ = ('new_model', 'new_version')


class UploadModelType(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `new_model`None
    * `new_version`None
    * `root`None
    '''
    __schema__ = schema
    __choices__ = ('new_model', 'new_version', 'root')


class VisibilityOptions(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `PRIVATE`None
    * `PUBLIC`None
    '''
    __schema__ = schema
    __choices__ = ('PRIVATE', 'PUBLIC')


class VisibilityOptionsLower(sgqlc.types.Enum):
    '''Enumeration Choices:

    * `private`None
    * `public`None
    '''
    __schema__ = schema
    __choices__ = ('private', 'public')



########################################################################
# Input Objects
########################################################################
class BuildArgInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('key', 'value')
    key = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='key')

    value = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='value')



class DataParamsInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('collector_method_params', 'collector_name', 'dataset_loader_version_choice', 'list_dataset_loader_method_params')
    collector_method_params = sgqlc.types.Field(sgqlc.types.non_null('MethodParamsInput'), graphql_name='collectorMethodParams')

    collector_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='collectorName')

    dataset_loader_version_choice = sgqlc.types.Field(sgqlc.types.non_null('ObjectIdVersionOptionalInput'), graphql_name='datasetLoaderVersionChoice')

    list_dataset_loader_method_params = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('MethodParamsInput'))), graphql_name='listDatasetLoaderMethodParams')



class EnvParamInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('key', 'value')
    key = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='key')

    value = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='value')



class ExecutorParamsInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('executor_method_params', 'executor_version_choice')
    executor_method_params = sgqlc.types.Field(sgqlc.types.non_null('MethodParamsInput'), graphql_name='executorMethodParams')

    executor_version_choice = sgqlc.types.Field(sgqlc.types.non_null('ObjectIdVersionOptionalInput'), graphql_name='executorVersionChoice')



class ExperimentFilterSettings(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('description', 'experiment_id', 'name', 'owner_ids', 'tag', 'visibility')
    description = sgqlc.types.Field(String, graphql_name='description')

    experiment_id = sgqlc.types.Field(Int, graphql_name='experimentId')

    name = sgqlc.types.Field(String, graphql_name='name')

    owner_ids = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(String)), graphql_name='ownerIds')

    tag = sgqlc.types.Field('TagFilterSettings', graphql_name='tag')

    visibility = sgqlc.types.Field(VisibilityOptions, graphql_name='visibility')



class ExperimentInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('experiment_name', 'visibility')
    experiment_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='experimentName')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class ExperimentSortBySortingInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('direction', 'sort_field')
    direction = sgqlc.types.Field(sgqlc.types.non_null(SortDirection), graphql_name='direction')

    sort_field = sgqlc.types.Field(sgqlc.types.non_null(ExperimentSortBy), graphql_name='sortField')



class GpuResources(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('count',)
    count = sgqlc.types.Field(Int, graphql_name='count')



class JobCodeParameters(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('additional_system_packages', 'bash_commands', 'code_id', 'env_variables', 'experiment_params', 'image_name', 'is_distributed', 'job_name', 'resources', 'visibility')
    additional_system_packages = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(String)), graphql_name='additionalSystemPackages')

    bash_commands = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='bashCommands')

    code_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='codeId')

    env_variables = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(EnvParamInput)), graphql_name='envVariables')

    experiment_params = sgqlc.types.Field(sgqlc.types.non_null(ExperimentInput), graphql_name='experimentParams')

    image_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='imageName')

    is_distributed = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isDistributed')

    job_name = sgqlc.types.Field(String, graphql_name='jobName')

    resources = sgqlc.types.Field(sgqlc.types.non_null('ResourcesInput'), graphql_name='resources')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class JobFilterSettings(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('buckets_used', 'dataset_loader_version', 'end_interval', 'executor_version', 'experiment_id', 'experiment_name', 'gpu_resources', 'init_model_version', 'job_ids', 'job_name', 'job_type', 'metrics', 'owner_ids', 'start_interval', 'status', 'visibility')
    buckets_used = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(String)), graphql_name='bucketsUsed')

    dataset_loader_version = sgqlc.types.Field('ObjectIdVersionOptionalInput', graphql_name='datasetLoaderVersion')

    end_interval = sgqlc.types.Field('TimestampInterval', graphql_name='endInterval')

    executor_version = sgqlc.types.Field('ObjectIdVersionOptionalInput', graphql_name='executorVersion')

    experiment_id = sgqlc.types.Field(Int, graphql_name='experimentId')

    experiment_name = sgqlc.types.Field(String, graphql_name='experimentName')

    gpu_resources = sgqlc.types.Field(GpuResources, graphql_name='gpuResources')

    init_model_version = sgqlc.types.Field('ObjectIdVersionOptionalInput', graphql_name='initModelVersion')

    job_ids = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(Int)), graphql_name='jobIds')

    job_name = sgqlc.types.Field(String, graphql_name='jobName')

    job_type = sgqlc.types.Field(ExecutionJobType, graphql_name='jobType')

    metrics = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(String)), graphql_name='metrics')

    owner_ids = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(String)), graphql_name='ownerIds')

    start_interval = sgqlc.types.Field('TimestampInterval', graphql_name='startInterval')

    status = sgqlc.types.Field(JobStatus, graphql_name='status')

    visibility = sgqlc.types.Field(VisibilityOptions, graphql_name='visibility')



class JobParameters(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('additional_system_packages', 'env_variables', 'executor_params', 'experiment_params', 'is_distributed', 'job_name', 'list_role_data_params', 'list_role_model_params', 'resources', 'visibility')
    additional_system_packages = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(String)), graphql_name='additionalSystemPackages')

    env_variables = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(EnvParamInput)), graphql_name='envVariables')

    executor_params = sgqlc.types.Field(sgqlc.types.non_null(ExecutorParamsInput), graphql_name='executorParams')

    experiment_params = sgqlc.types.Field(ExperimentInput, graphql_name='experimentParams')

    is_distributed = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isDistributed')

    job_name = sgqlc.types.Field(String, graphql_name='jobName')

    list_role_data_params = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null('RoleDataParamsInput')), graphql_name='listRoleDataParams')

    list_role_model_params = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null('RoleModelParamsInput')), graphql_name='listRoleModelParams')

    resources = sgqlc.types.Field(sgqlc.types.non_null('ResourcesInput'), graphql_name='resources')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class JobToMetricInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('job_id', 'metric_name')
    job_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='jobId')

    metric_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='metricName')



class JobsSorting(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('direction', 'metric_sort_field', 'sort_field')
    direction = sgqlc.types.Field(sgqlc.types.non_null(SortDirection), graphql_name='direction')

    metric_sort_field = sgqlc.types.Field('ShowMetricInput', graphql_name='metricSortField')

    sort_field = sgqlc.types.Field(sgqlc.types.non_null(JobsSortBy), graphql_name='sortField')



class MethodParamsInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('method_name', 'method_params')
    method_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='methodName')

    method_params = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='methodParams')



class MetricInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('autostep', 'key', 'step', 'timestamp', 'value')
    autostep = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='autostep')

    key = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='key')

    step = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='step')

    timestamp = sgqlc.types.Field(Long, graphql_name='timestamp')

    value = sgqlc.types.Field(sgqlc.types.non_null(Float), graphql_name='value')



class MetricInterval(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('end', 'start')
    end = sgqlc.types.Field(Long, graphql_name='end')

    start = sgqlc.types.Field(Long, graphql_name='start')



class ModelParamsInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('list_model_method_params', 'model_version_choice')
    list_model_method_params = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(MethodParamsInput))), graphql_name='listModelMethodParams')

    model_version_choice = sgqlc.types.Field(sgqlc.types.non_null('ModelVersionChoice'), graphql_name='modelVersionChoice')



class ModelServingInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('gpu', 'model_version')
    gpu = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='gpu')

    model_version = sgqlc.types.Field(sgqlc.types.non_null('ObjectIdVersionInput'), graphql_name='modelVersion')



class ModelVersionChoice(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'version')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    version = sgqlc.types.Field(Int, graphql_name='version')



class ObjectFilterSettings(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('creation_interval', 'description', 'last_updated_interval', 'name', 'owner_ids', 'tag', 'visibility')
    creation_interval = sgqlc.types.Field('TimestampInterval', graphql_name='creationInterval')

    description = sgqlc.types.Field(String, graphql_name='description')

    last_updated_interval = sgqlc.types.Field('TimestampInterval', graphql_name='lastUpdatedInterval')

    name = sgqlc.types.Field(String, graphql_name='name')

    owner_ids = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(String)), graphql_name='ownerIds')

    tag = sgqlc.types.Field('TagFilterSettings', graphql_name='tag')

    visibility = sgqlc.types.Field(VisibilityOptions, graphql_name='visibility')



class ObjectIdVersionInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'version')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    version = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='version')



class ObjectIdVersionOptionalInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'version')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    version = sgqlc.types.Field(Int, graphql_name='version')



class ObjectSortBySortingInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('direction', 'sort_field')
    direction = sgqlc.types.Field(sgqlc.types.non_null(SortDirection), graphql_name='direction')

    sort_field = sgqlc.types.Field(sgqlc.types.non_null(ObjectSortBy), graphql_name='sortField')



class ObjectVersionFilterSettings(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('creation_interval', 'description', 'last_updated_interval', 'owner_ids', 'tag', 'version', 'visibility')
    creation_interval = sgqlc.types.Field('TimestampInterval', graphql_name='creationInterval')

    description = sgqlc.types.Field(String, graphql_name='description')

    last_updated_interval = sgqlc.types.Field('TimestampInterval', graphql_name='lastUpdatedInterval')

    owner_ids = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(String)), graphql_name='ownerIds')

    tag = sgqlc.types.Field('TagFilterSettings', graphql_name='tag')

    version = sgqlc.types.Field(Int, graphql_name='version')

    visibility = sgqlc.types.Field(VisibilityOptions, graphql_name='visibility')



class ObjectVersionOptionalInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('name', 'version')
    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    version = sgqlc.types.Field(Int, graphql_name='version')



class ObjectVersionSortBySortingInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('direction', 'sort_field')
    direction = sgqlc.types.Field(sgqlc.types.non_null(SortDirection), graphql_name='direction')

    sort_field = sgqlc.types.Field(sgqlc.types.non_null(ObjectVersionSortBy), graphql_name='sortField')



class ParamInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('key', 'value')
    key = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='key')

    value = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='value')



class ResourcesInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('cpus', 'gpu_number', 'gpu_type', 'memory_per_node')
    cpus = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='cpus')

    gpu_number = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='gpuNumber')

    gpu_type = sgqlc.types.Field(String, graphql_name='gpuType')

    memory_per_node = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='memoryPerNode')



class RoleDataParamsInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('data_params', 'role')
    data_params = sgqlc.types.Field(sgqlc.types.non_null(DataParamsInput), graphql_name='dataParams')

    role = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='role')



class RoleModelParamsInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('model_params', 'role', 'upload_params')
    model_params = sgqlc.types.Field(sgqlc.types.non_null(ModelParamsInput), graphql_name='modelParams')

    role = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='role')

    upload_params = sgqlc.types.Field('UploadModelParamsInput', graphql_name='uploadParams')



class RoleObjectVersionInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('object_version', 'role')
    object_version = sgqlc.types.Field(sgqlc.types.non_null(ObjectIdVersionInput), graphql_name='objectVersion')

    role = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='role')



class ShowMetricInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('metric_name', 'metric_option')
    metric_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='metricName')

    metric_option = sgqlc.types.Field(sgqlc.types.non_null(MetricOptionInput), graphql_name='metricOption')



class TagFilterSettings(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('key', 'value')
    key = sgqlc.types.Field(String, graphql_name='key')

    value = sgqlc.types.Field(String, graphql_name='value')



class TimestampInterval(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('end', 'start')
    end = sgqlc.types.Field(Long, graphql_name='end')

    start = sgqlc.types.Field(Long, graphql_name='start')



class UpdateObjectForm(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('new_description', 'new_name', 'new_visibility')
    new_description = sgqlc.types.Field(String, graphql_name='newDescription')

    new_name = sgqlc.types.Field(String, graphql_name='newName')

    new_visibility = sgqlc.types.Field(VisibilityOptions, graphql_name='newVisibility')



class UpdateObjectVersionForm(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('new_description', 'new_visibility')
    new_description = sgqlc.types.Field(String, graphql_name='newDescription')

    new_visibility = sgqlc.types.Field(VisibilityOptions, graphql_name='newVisibility')



class UploadModelParamsInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('description', 'new_model_name', 'new_model_visibility', 'prepare_new_model_inference', 'start_build_new_model_image', 'upload_model_mode')
    description = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='description')

    new_model_name = sgqlc.types.Field(String, graphql_name='newModelName')

    new_model_visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='newModelVisibility')

    prepare_new_model_inference = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='prepareNewModelInference')

    start_build_new_model_image = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='startBuildNewModelImage')

    upload_model_mode = sgqlc.types.Field(sgqlc.types.non_null(UploadModelMode), graphql_name='uploadModelMode')




########################################################################
# Output Objects and Interfaces
########################################################################
class ArtifactPath(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('content_type', 'isdir', 'path', 'size')
    content_type = sgqlc.types.Field(String, graphql_name='contentType')

    isdir = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isdir')

    path = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='path')

    size = sgqlc.types.Field(Long, graphql_name='size')



class Artifacts(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_artifacts', 'source_path')
    list_artifacts = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ArtifactPath))), graphql_name='listArtifacts', args=sgqlc.types.ArgDict((
        ('path', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='path', default='')),
))
    )
    '''Arguments:

    * `path` (`String!`)None (default: `""`)
    '''

    source_path = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='sourcePath')



class AvailableResources(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('cpu_limit', 'gpus', 'memory_per_node_limit')
    cpu_limit = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='cpuLimit')

    gpus = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('GPUInfoGQL'))), graphql_name='gpus')

    memory_per_node_limit = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='memoryPerNodeLimit')



class BuildJob(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('build_object_name', 'end_timestamp', 'id', 'message', 'start_timestamp', 'status')
    build_object_name = sgqlc.types.Field(String, graphql_name='buildObjectName')

    end_timestamp = sgqlc.types.Field(Long, graphql_name='endTimestamp')

    id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='id')

    message = sgqlc.types.Field(String, graphql_name='message')

    start_timestamp = sgqlc.types.Field(Long, graphql_name='startTimestamp')

    status = sgqlc.types.Field(sgqlc.types.non_null(JobStatus), graphql_name='status')



class CodeJob(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('artifacts', 'available_metrics', 'code_job', 'end_timestamp', 'experiment', 'git_info', 'id', 'is_active', 'latest_metrics', 'list_buckets', 'list_params', 'list_result_model_version', 'message', 'metric_history', 'name', 'owner', 'params', 'registration_timestamp', 'show_metrics', 'start_timestamp', 'status', 'visibility')
    artifacts = sgqlc.types.Field(sgqlc.types.non_null(Artifacts), graphql_name='artifacts')

    available_metrics = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='availableMetrics')

    code_job = sgqlc.types.Field(Artifacts, graphql_name='codeJob')

    end_timestamp = sgqlc.types.Field(Long, graphql_name='endTimestamp')

    experiment = sgqlc.types.Field('Experiment', graphql_name='experiment')

    git_info = sgqlc.types.Field('GitInfo', graphql_name='gitInfo')

    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    latest_metrics = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='latestMetrics')

    list_buckets = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='listBuckets')

    list_params = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('Param'))), graphql_name='listParams')

    list_result_model_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('ModelVersionInfo'))), graphql_name='listResultModelVersion', args=sgqlc.types.ArgDict((
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    message = sgqlc.types.Field(String, graphql_name='message')

    metric_history = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(JSON))), graphql_name='metricHistory', args=sgqlc.types.ArgDict((
        ('metric', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='metric', default=None)),
))
    )
    '''Arguments:

    * `metric` (`String!`)None
    '''

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    params = sgqlc.types.Field(sgqlc.types.non_null('JobCodeParams'), graphql_name='params')

    registration_timestamp = sgqlc.types.Field(sgqlc.types.non_null(Long), graphql_name='registrationTimestamp')

    show_metrics = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='showMetrics', args=sgqlc.types.ArgDict((
        ('metric_names', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ShowMetricInput))), graphql_name='metricNames', default=None)),
))
    )
    '''Arguments:

    * `metric_names` (`[ShowMetricInput!]!`)None
    '''

    start_timestamp = sgqlc.types.Field(Long, graphql_name='startTimestamp')

    status = sgqlc.types.Field(sgqlc.types.non_null(JobStatus), graphql_name='status')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class CustomImage(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('build_args', 'build_job', 'description', 'id', 'is_active', 'name', 'owner', 'visibility')
    build_args = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='buildArgs')

    build_job = sgqlc.types.Field(BuildJob, graphql_name='buildJob')

    description = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='description')

    id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='id')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class DataParams(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('collector_method_params', 'collector_name', 'dataset_loader_version_choice', 'list_dataset_loader_method_params')
    collector_method_params = sgqlc.types.Field(sgqlc.types.non_null('MethodParams'), graphql_name='collectorMethodParams')

    collector_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='collectorName')

    dataset_loader_version_choice = sgqlc.types.Field(sgqlc.types.non_null('ObjectVersion'), graphql_name='datasetLoaderVersionChoice')

    list_dataset_loader_method_params = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('MethodParams'))), graphql_name='listDatasetLoaderMethodParams')



class DataSchema(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('collector_method_schema', 'dataset_loader_method_schemas', 'role')
    collector_method_schema = sgqlc.types.Field(sgqlc.types.non_null('MethodSchema'), graphql_name='collectorMethodSchema')

    dataset_loader_method_schemas = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('MethodSchema'))), graphql_name='datasetLoaderMethodSchemas')

    role = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='role')



class DatasetLoaderInfo(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'creation_timestamp', 'description', 'init_dataset_loader_version', 'is_active', 'last_updated_timestamp', 'latest_dataset_loader_version', 'list_dataset_loader_version', 'name', 'owner', 'pagination_dataset_loader_version', 'tags', 'visibility')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    creation_timestamp = sgqlc.types.Field(sgqlc.types.non_null(Long), graphql_name='creationTimestamp')

    description = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='description')

    init_dataset_loader_version = sgqlc.types.Field(sgqlc.types.non_null('DatasetLoaderVersionInfo'), graphql_name='initDatasetLoaderVersion')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    last_updated_timestamp = sgqlc.types.Field(Long, graphql_name='lastUpdatedTimestamp')

    latest_dataset_loader_version = sgqlc.types.Field('DatasetLoaderVersionInfo', graphql_name='latestDatasetLoaderVersion')

    list_dataset_loader_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('DatasetLoaderVersionInfo'))), graphql_name='listDatasetLoaderVersion', args=sgqlc.types.ArgDict((
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    pagination_dataset_loader_version = sgqlc.types.Field(sgqlc.types.non_null('DatasetLoaderVersionPagination'), graphql_name='paginationDatasetLoaderVersion', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectVersionFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectVersionFilterSettings`)None (default:
      `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    tags = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('Tag'))), graphql_name='tags')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class DatasetLoaderPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_dataset_loader', 'total')
    list_dataset_loader = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(DatasetLoaderInfo))), graphql_name='listDatasetLoader')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class DatasetLoaderVersionInfo(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'artifacts', 'build_env', 'creation_timestamp', 'dataset_loader', 'dataset_loader_method_schema_names', 'dataset_loader_method_schemas', 'description', 'get_conda_env', 'git_info', 'hash_artifacts', 'is_active', 'last_updated_timestamp', 'list_deployed_jobs', 'list_requirements', 'name', 'owner', 'pagination_deployed_jobs', 'tags', 'version', 'visibility')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    artifacts = sgqlc.types.Field(sgqlc.types.non_null(Artifacts), graphql_name='artifacts')

    build_env = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('EnvParam'))), graphql_name='buildEnv')

    creation_timestamp = sgqlc.types.Field(sgqlc.types.non_null(Long), graphql_name='creationTimestamp')

    dataset_loader = sgqlc.types.Field(sgqlc.types.non_null(DatasetLoaderInfo), graphql_name='datasetLoader')

    dataset_loader_method_schema_names = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='datasetLoaderMethodSchemaNames')

    dataset_loader_method_schemas = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='datasetLoaderMethodSchemas')

    description = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='description')

    get_conda_env = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='getCondaEnv')

    git_info = sgqlc.types.Field('GitInfo', graphql_name='gitInfo')

    hash_artifacts = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='hashArtifacts')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    last_updated_timestamp = sgqlc.types.Field(Long, graphql_name='lastUpdatedTimestamp')

    list_deployed_jobs = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('CodeJobLocalJobMLMJob'))), graphql_name='listDeployedJobs')

    list_requirements = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='listRequirements')

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    pagination_deployed_jobs = sgqlc.types.Field(sgqlc.types.non_null('JobPagination'), graphql_name='paginationDeployedJobs', args=sgqlc.types.ArgDict((
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
))
    )
    '''Arguments:

    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    '''

    tags = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('Tag'))), graphql_name='tags')

    version = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='version')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class DatasetLoaderVersionPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_dataset_loader_version', 'total')
    list_dataset_loader_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(DatasetLoaderVersionInfo))), graphql_name='listDatasetLoaderVersion')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class EnvParam(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('key', 'value')
    key = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='key')

    value = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='value')



class ExecutorInfo(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'creation_timestamp', 'description', 'init_executor_version', 'is_active', 'last_updated_timestamp', 'latest_executor_version', 'list_executor_version', 'name', 'owner', 'pagination_executor_version', 'tags', 'visibility')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    creation_timestamp = sgqlc.types.Field(sgqlc.types.non_null(Long), graphql_name='creationTimestamp')

    description = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='description')

    init_executor_version = sgqlc.types.Field(sgqlc.types.non_null('ExecutorVersionInfo'), graphql_name='initExecutorVersion')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    last_updated_timestamp = sgqlc.types.Field(Long, graphql_name='lastUpdatedTimestamp')

    latest_executor_version = sgqlc.types.Field('ExecutorVersionInfo', graphql_name='latestExecutorVersion')

    list_executor_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('ExecutorVersionInfo'))), graphql_name='listExecutorVersion', args=sgqlc.types.ArgDict((
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    pagination_executor_version = sgqlc.types.Field(sgqlc.types.non_null('ExecutorVersionPagination'), graphql_name='paginationExecutorVersion', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectVersionFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectVersionFilterSettings`)None (default:
      `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    tags = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('Tag'))), graphql_name='tags')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class ExecutorPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_executor', 'total')
    list_executor = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ExecutorInfo))), graphql_name='listExecutor')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class ExecutorParams(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('executor_method_params', 'executor_version_choice')
    executor_method_params = sgqlc.types.Field(sgqlc.types.non_null('MethodParams'), graphql_name='executorMethodParams')

    executor_version_choice = sgqlc.types.Field(sgqlc.types.non_null('ObjectVersion'), graphql_name='executorVersionChoice')



class ExecutorVersionInfo(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'artifacts', 'available_collectors', 'available_dataset_loader_versions', 'available_dataset_loaders', 'available_model_versions', 'available_models', 'build_env', 'build_job', 'creation_timestamp', 'description', 'desired_dataset_loader_methods', 'desired_dataset_loader_patterns', 'desired_model_methods', 'desired_model_patterns', 'executor', 'executor_method_schema', 'executor_method_schema_name', 'get_conda_env', 'git_info', 'hash_artifacts', 'is_active', 'job_json_schema', 'job_json_schema_for_dataset_loaders', 'job_json_schema_for_models', 'job_json_schema_for_role_dataset_loader', 'job_json_schema_for_role_model', 'last_updated_timestamp', 'list_deployed_jobs', 'list_requirements', 'name', 'owner', 'pagination_available_collectors', 'pagination_available_dataset_loader_versions', 'pagination_available_dataset_loaders', 'pagination_available_model_versions', 'pagination_available_models', 'pagination_deployed_jobs', 'tags', 'version', 'visibility')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    artifacts = sgqlc.types.Field(sgqlc.types.non_null(Artifacts), graphql_name='artifacts')

    available_collectors = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('InlineCollector'))), graphql_name='availableCollectors')

    available_dataset_loader_versions = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('InlineObjectVersion'))), graphql_name='availableDatasetLoaderVersions', args=sgqlc.types.ArgDict((
        ('dataset_loader_aggr_id', sgqlc.types.Arg(Int, graphql_name='datasetLoaderAggrId', default=None)),
        ('role', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='role', default=None)),
))
    )
    '''Arguments:

    * `dataset_loader_aggr_id` (`Int`)None (default: `null`)
    * `role` (`String!`)None
    '''

    available_dataset_loaders = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('InlineObject'))), graphql_name='availableDatasetLoaders', args=sgqlc.types.ArgDict((
        ('role', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='role', default=None)),
))
    )
    '''Arguments:

    * `role` (`String!`)None
    '''

    available_model_versions = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('InlineObjectVersion'))), graphql_name='availableModelVersions', args=sgqlc.types.ArgDict((
        ('model_aggr_id', sgqlc.types.Arg(Int, graphql_name='modelAggrId', default=None)),
        ('role', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='role', default=None)),
))
    )
    '''Arguments:

    * `model_aggr_id` (`Int`)None (default: `null`)
    * `role` (`String!`)None
    '''

    available_models = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('InlineObject'))), graphql_name='availableModels', args=sgqlc.types.ArgDict((
        ('role', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='role', default=None)),
))
    )
    '''Arguments:

    * `role` (`String!`)None
    '''

    build_env = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(EnvParam))), graphql_name='buildEnv')

    build_job = sgqlc.types.Field(BuildJob, graphql_name='buildJob')

    creation_timestamp = sgqlc.types.Field(sgqlc.types.non_null(Long), graphql_name='creationTimestamp')

    description = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='description')

    desired_dataset_loader_methods = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='desiredDatasetLoaderMethods')

    desired_dataset_loader_patterns = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='desiredDatasetLoaderPatterns')

    desired_model_methods = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='desiredModelMethods')

    desired_model_patterns = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='desiredModelPatterns')

    executor = sgqlc.types.Field(sgqlc.types.non_null(ExecutorInfo), graphql_name='executor')

    executor_method_schema = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='executorMethodSchema')

    executor_method_schema_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='executorMethodSchemaName')

    get_conda_env = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='getCondaEnv')

    git_info = sgqlc.types.Field('GitInfo', graphql_name='gitInfo')

    hash_artifacts = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='hashArtifacts')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    job_json_schema = sgqlc.types.Field(sgqlc.types.non_null('JobSchema'), graphql_name='jobJsonSchema', args=sgqlc.types.ArgDict((
        ('dataset_loaders', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(RoleObjectVersionInput))), graphql_name='datasetLoaders', default=None)),
        ('models', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(RoleObjectVersionInput))), graphql_name='models', default=None)),
))
    )
    '''Arguments:

    * `dataset_loaders` (`[RoleObjectVersionInput!]!`)None
    * `models` (`[RoleObjectVersionInput!]!`)None
    '''

    job_json_schema_for_dataset_loaders = sgqlc.types.Field(sgqlc.types.non_null('JobDatasetLoadersSchema'), graphql_name='jobJsonSchemaForDatasetLoaders', args=sgqlc.types.ArgDict((
        ('dataset_loaders', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(RoleObjectVersionInput))), graphql_name='datasetLoaders', default=None)),
))
    )
    '''Arguments:

    * `dataset_loaders` (`[RoleObjectVersionInput!]!`)None
    '''

    job_json_schema_for_models = sgqlc.types.Field(sgqlc.types.non_null('JobModelsSchema'), graphql_name='jobJsonSchemaForModels', args=sgqlc.types.ArgDict((
        ('models', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(RoleObjectVersionInput))), graphql_name='models', default=None)),
))
    )
    '''Arguments:

    * `models` (`[RoleObjectVersionInput!]!`)None
    '''

    job_json_schema_for_role_dataset_loader = sgqlc.types.Field(sgqlc.types.non_null(DataSchema), graphql_name='jobJsonSchemaForRoleDatasetLoader', args=sgqlc.types.ArgDict((
        ('collector_name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='collectorName', default=None)),
        ('dataset_loader', sgqlc.types.Arg(sgqlc.types.non_null(RoleObjectVersionInput), graphql_name='datasetLoader', default=None)),
))
    )
    '''Arguments:

    * `collector_name` (`String!`)None
    * `dataset_loader` (`RoleObjectVersionInput!`)None
    '''

    job_json_schema_for_role_model = sgqlc.types.Field(sgqlc.types.non_null('RoleMethodSchema'), graphql_name='jobJsonSchemaForRoleModel', args=sgqlc.types.ArgDict((
        ('model', sgqlc.types.Arg(sgqlc.types.non_null(RoleObjectVersionInput), graphql_name='model', default=None)),
))
    )
    '''Arguments:

    * `model` (`RoleObjectVersionInput!`)None
    '''

    last_updated_timestamp = sgqlc.types.Field(Long, graphql_name='lastUpdatedTimestamp')

    list_deployed_jobs = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('CodeJobLocalJobMLMJob'))), graphql_name='listDeployedJobs')

    list_requirements = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='listRequirements')

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    pagination_available_collectors = sgqlc.types.Field(sgqlc.types.non_null('InlineCollectorPagination'), graphql_name='paginationAvailableCollectors', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    '''

    pagination_available_dataset_loader_versions = sgqlc.types.Field(sgqlc.types.non_null('InlineObjectVersionPagination'), graphql_name='paginationAvailableDatasetLoaderVersions', args=sgqlc.types.ArgDict((
        ('dataset_loader_aggr_id', sgqlc.types.Arg(Int, graphql_name='datasetLoaderAggrId', default=None)),
        ('filter_settings', sgqlc.types.Arg(ObjectVersionFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('role', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='role', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `dataset_loader_aggr_id` (`Int`)None (default: `null`)
    * `filter_settings` (`ObjectVersionFilterSettings`)None (default:
      `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `role` (`String!`)None
    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    pagination_available_dataset_loaders = sgqlc.types.Field(sgqlc.types.non_null('InlineObjectPagination'), graphql_name='paginationAvailableDatasetLoaders', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('role', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='role', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `role` (`String!`)None
    * `sorting` (`[ObjectSortBySortingInput!]`)None (default: `null`)
    '''

    pagination_available_model_versions = sgqlc.types.Field(sgqlc.types.non_null('InlineObjectVersionPagination'), graphql_name='paginationAvailableModelVersions', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectVersionFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('model_aggr_id', sgqlc.types.Arg(Int, graphql_name='modelAggrId', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('role', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='role', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectVersionFilterSettings`)None (default:
      `null`)
    * `limit` (`Int`)None (default: `null`)
    * `model_aggr_id` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `role` (`String!`)None
    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    pagination_available_models = sgqlc.types.Field(sgqlc.types.non_null('InlineObjectPagination'), graphql_name='paginationAvailableModels', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('role', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='role', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `role` (`String!`)None
    * `sorting` (`[ObjectSortBySortingInput!]`)None (default: `null`)
    '''

    pagination_deployed_jobs = sgqlc.types.Field(sgqlc.types.non_null('JobPagination'), graphql_name='paginationDeployedJobs', args=sgqlc.types.ArgDict((
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
))
    )
    '''Arguments:

    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    '''

    tags = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('Tag'))), graphql_name='tags')

    version = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='version')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class ExecutorVersionPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_executor_version', 'total')
    list_executor_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ExecutorVersionInfo))), graphql_name='listExecutorVersion')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class Experiment(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('description', 'experiment_id', 'is_active', 'list_job', 'name', 'owner', 'pagination_job', 'tags', 'visibility')
    description = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='description')

    experiment_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='experimentId')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    list_job = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('CodeJobLocalJobMLMJob'))), graphql_name='listJob')

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    pagination_job = sgqlc.types.Field(sgqlc.types.non_null('JobPagination'), graphql_name='paginationJob', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(JobFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(JobsSorting, graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`JobFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`JobsSorting`)None (default: `null`)
    '''

    tags = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('Tag'))), graphql_name='tags')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class ExperimentPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_experiment', 'total')
    list_experiment = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Experiment))), graphql_name='listExperiment')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class GPUInfoGQL(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('number', 'type')
    number = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='number')

    type = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='type')



class GitInfo(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('branch_name', 'repo_name', 'sha')
    branch_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='branchName')

    repo_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='repoName')

    sha = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='sha')



class InlineCollector(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('name',)
    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')



class InlineCollectorPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_inline_object', 'total')
    list_inline_object = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(InlineCollector))), graphql_name='listInlineObject')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class InlineObject(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'name')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')



class InlineObjectPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_inline_object', 'total')
    list_inline_object = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(InlineObject))), graphql_name='listInlineObject')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class InlineObjectVersion(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'name', 'version')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    version = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='version')



class InlineObjectVersionPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_inline_object_version', 'total')
    list_inline_object_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(InlineObjectVersion))), graphql_name='listInlineObjectVersion')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class JobCodeParams(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('additional_system_packages', 'bash_commands', 'code_id', 'env_variables', 'image_name', 'is_distributed', 'resources')
    additional_system_packages = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(String)), graphql_name='additionalSystemPackages')

    bash_commands = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='bashCommands')

    code_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='codeId')

    env_variables = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(EnvParam))), graphql_name='envVariables')

    image_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='imageName')

    is_distributed = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isDistributed')

    resources = sgqlc.types.Field(sgqlc.types.non_null('ResourcesParams'), graphql_name='resources')



class JobDatasetLoadersSchema(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_role_dataset_loader_method_schemas',)
    list_role_dataset_loader_method_schemas = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('RoleMethodSchema'))), graphql_name='listRoleDatasetLoaderMethodSchemas')



class JobInfoResponse(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('message', 'status')
    message = sgqlc.types.Field(String, graphql_name='message')

    status = sgqlc.types.Field(sgqlc.types.non_null(JobStatus), graphql_name='status')



class JobModelsSchema(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_role_model_method_schemas',)
    list_role_model_method_schemas = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('RoleMethodSchema'))), graphql_name='listRoleModelMethodSchemas')



class JobPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_job', 'total')
    list_job = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('CodeJobLocalJobMLMJob'))), graphql_name='listJob')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class JobParams(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('additional_system_packages', 'env_variables', 'executor_params', 'executor_version', 'is_distributed', 'list_dataset_loader_versions', 'list_init_role_model_version', 'list_role_data_params', 'list_role_model_params', 'resources')
    additional_system_packages = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null(String)), graphql_name='additionalSystemPackages')

    env_variables = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(EnvParam))), graphql_name='envVariables')

    executor_params = sgqlc.types.Field(sgqlc.types.non_null(ExecutorParams), graphql_name='executorParams')

    executor_version = sgqlc.types.Field(ExecutorVersionInfo, graphql_name='executorVersion')

    is_distributed = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isDistributed')

    list_dataset_loader_versions = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('RoleDatasetLoaderVersion'))), graphql_name='listDatasetLoaderVersions')

    list_init_role_model_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('RoleModelVersion'))), graphql_name='listInitRoleModelVersion')

    list_role_data_params = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null('RoleDataParams')), graphql_name='listRoleDataParams')

    list_role_model_params = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.non_null('RoleModelParams')), graphql_name='listRoleModelParams')

    resources = sgqlc.types.Field(sgqlc.types.non_null('ResourcesParams'), graphql_name='resources')



class JobSchema(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('executor_method_schema', 'list_role_dataset_loader_method_schemas', 'list_role_model_method_schemas')
    executor_method_schema = sgqlc.types.Field(sgqlc.types.non_null('MethodSchema'), graphql_name='executorMethodSchema')

    list_role_dataset_loader_method_schemas = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('RoleMethodSchema'))), graphql_name='listRoleDatasetLoaderMethodSchemas')

    list_role_model_method_schemas = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('RoleMethodSchema'))), graphql_name='listRoleModelMethodSchemas')



class LocalJob(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('artifacts', 'available_metrics', 'end_timestamp', 'experiment', 'id', 'is_active', 'latest_metrics', 'list_buckets', 'list_params', 'list_result_model_version', 'message', 'metric_history', 'name', 'owner', 'registration_timestamp', 'show_metrics', 'start_timestamp', 'status', 'visibility')
    artifacts = sgqlc.types.Field(sgqlc.types.non_null(Artifacts), graphql_name='artifacts')

    available_metrics = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='availableMetrics')

    end_timestamp = sgqlc.types.Field(Long, graphql_name='endTimestamp')

    experiment = sgqlc.types.Field(Experiment, graphql_name='experiment')

    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    latest_metrics = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='latestMetrics')

    list_buckets = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='listBuckets')

    list_params = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('Param'))), graphql_name='listParams')

    list_result_model_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('ModelVersionInfo'))), graphql_name='listResultModelVersion', args=sgqlc.types.ArgDict((
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    message = sgqlc.types.Field(String, graphql_name='message')

    metric_history = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(JSON))), graphql_name='metricHistory', args=sgqlc.types.ArgDict((
        ('metric', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='metric', default=None)),
))
    )
    '''Arguments:

    * `metric` (`String!`)None
    '''

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    registration_timestamp = sgqlc.types.Field(sgqlc.types.non_null(Long), graphql_name='registrationTimestamp')

    show_metrics = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='showMetrics', args=sgqlc.types.ArgDict((
        ('metric_names', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ShowMetricInput))), graphql_name='metricNames', default=None)),
))
    )
    '''Arguments:

    * `metric_names` (`[ShowMetricInput!]!`)None
    '''

    start_timestamp = sgqlc.types.Field(Long, graphql_name='startTimestamp')

    status = sgqlc.types.Field(sgqlc.types.non_null(JobStatus), graphql_name='status')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class MLMJob(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('artifacts', 'available_metrics', 'end_timestamp', 'experiment', 'id', 'is_active', 'latest_metrics', 'list_buckets', 'list_params', 'list_result_model_version', 'message', 'metric_history', 'name', 'owner', 'params', 'registration_timestamp', 'show_metrics', 'start_timestamp', 'status', 'visibility')
    artifacts = sgqlc.types.Field(sgqlc.types.non_null(Artifacts), graphql_name='artifacts')

    available_metrics = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='availableMetrics')

    end_timestamp = sgqlc.types.Field(Long, graphql_name='endTimestamp')

    experiment = sgqlc.types.Field(Experiment, graphql_name='experiment')

    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    latest_metrics = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='latestMetrics')

    list_buckets = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='listBuckets')

    list_params = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('Param'))), graphql_name='listParams')

    list_result_model_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('ModelVersionInfo'))), graphql_name='listResultModelVersion', args=sgqlc.types.ArgDict((
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    message = sgqlc.types.Field(String, graphql_name='message')

    metric_history = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(JSON))), graphql_name='metricHistory', args=sgqlc.types.ArgDict((
        ('metric', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='metric', default=None)),
))
    )
    '''Arguments:

    * `metric` (`String!`)None
    '''

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    params = sgqlc.types.Field(sgqlc.types.non_null(JobParams), graphql_name='params')

    registration_timestamp = sgqlc.types.Field(sgqlc.types.non_null(Long), graphql_name='registrationTimestamp')

    show_metrics = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='showMetrics', args=sgqlc.types.ArgDict((
        ('metric_names', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ShowMetricInput))), graphql_name='metricNames', default=None)),
))
    )
    '''Arguments:

    * `metric_names` (`[ShowMetricInput!]!`)None
    '''

    start_timestamp = sgqlc.types.Field(Long, graphql_name='startTimestamp')

    status = sgqlc.types.Field(sgqlc.types.non_null(JobStatus), graphql_name='status')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class MethodParams(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('method_name', 'method_params')
    method_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='methodName')

    method_params = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='methodParams')



class MethodSchema(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('json_schema', 'schema_name')
    json_schema = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='jsonSchema')

    schema_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='schemaName')



class MetricNamePagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_metric_name', 'total')
    list_metric_name = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='listMetricName')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class MetricToJson(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('job_metrics', 'metric_name')
    job_metrics = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(JSON))), graphql_name='jobMetrics')

    metric_name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='metricName')



class ModelInfo(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'creation_timestamp', 'description', 'init_model_version', 'is_active', 'last_updated_timestamp', 'latest_model_version', 'list_model_version', 'name', 'owner', 'pagination_model_version', 'tags', 'visibility')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    creation_timestamp = sgqlc.types.Field(sgqlc.types.non_null(Long), graphql_name='creationTimestamp')

    description = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='description')

    init_model_version = sgqlc.types.Field(sgqlc.types.non_null('ModelVersionInfo'), graphql_name='initModelVersion')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    last_updated_timestamp = sgqlc.types.Field(sgqlc.types.non_null(Long), graphql_name='lastUpdatedTimestamp')

    latest_model_version = sgqlc.types.Field('ModelVersionInfo', graphql_name='latestModelVersion')

    list_model_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('ModelVersionInfo'))), graphql_name='listModelVersion', args=sgqlc.types.ArgDict((
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    pagination_model_version = sgqlc.types.Field(sgqlc.types.non_null('ModelVersionPagination'), graphql_name='paginationModelVersion', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectVersionFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectVersionFilterSettings`)None (default:
      `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    tags = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('Tag'))), graphql_name='tags')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class ModelPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_model', 'total')
    list_model = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ModelInfo))), graphql_name='listModel')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class ModelParams(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_model_method_params', 'model_version_choice')
    list_model_method_params = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(MethodParams))), graphql_name='listModelMethodParams')

    model_version_choice = sgqlc.types.Field(sgqlc.types.non_null('ObjectVersion'), graphql_name='modelVersionChoice')



class ModelVersionInfo(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'artifacts', 'available_collectors', 'available_dataset_loader_versions', 'available_dataset_loaders', 'available_executor_versions', 'available_executors', 'build_env', 'build_job', 'creation_timestamp', 'description', 'get_conda_env', 'git_info', 'group_secret_uuid', 'hash_artifacts', 'is_active', 'last_updated_timestamp', 'list_deployed_jobs', 'list_job', 'list_requirements', 'model', 'model_method_schemas', 'name', 'owner', 'pagination_available_collectors', 'pagination_available_dataset_loader_versions', 'pagination_available_dataset_loaders', 'pagination_available_executor_versions', 'pagination_available_executors', 'pagination_deployed_jobs', 'pagination_job', 'parent_job', 'root_model_version', 'source_executor_version', 'source_model_version', 'tags', 'upload_model_type', 'venv_build_job', 'version', 'visibility')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    artifacts = sgqlc.types.Field(sgqlc.types.non_null(Artifacts), graphql_name='artifacts')

    available_collectors = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(InlineCollector))), graphql_name='availableCollectors')

    available_dataset_loader_versions = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(InlineObjectVersion))), graphql_name='availableDatasetLoaderVersions', args=sgqlc.types.ArgDict((
        ('dataset_loader_aggr_id', sgqlc.types.Arg(Int, graphql_name='datasetLoaderAggrId', default=None)),
))
    )
    '''Arguments:

    * `dataset_loader_aggr_id` (`Int`)None (default: `null`)
    '''

    available_dataset_loaders = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(InlineObject))), graphql_name='availableDatasetLoaders')

    available_executor_versions = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(InlineObjectVersion))), graphql_name='availableExecutorVersions', args=sgqlc.types.ArgDict((
        ('executor_aggr_id', sgqlc.types.Arg(Int, graphql_name='executorAggrId', default=None)),
))
    )
    '''Arguments:

    * `executor_aggr_id` (`Int`)None (default: `null`)
    '''

    available_executors = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(InlineObject))), graphql_name='availableExecutors')

    build_env = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(EnvParam))), graphql_name='buildEnv')

    build_job = sgqlc.types.Field(BuildJob, graphql_name='buildJob')

    creation_timestamp = sgqlc.types.Field(sgqlc.types.non_null(Long), graphql_name='creationTimestamp')

    description = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='description')

    get_conda_env = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='getCondaEnv')

    git_info = sgqlc.types.Field(GitInfo, graphql_name='gitInfo')

    group_secret_uuid = sgqlc.types.Field(String, graphql_name='groupSecretUuid')

    hash_artifacts = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='hashArtifacts')

    is_active = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isActive')

    last_updated_timestamp = sgqlc.types.Field(Long, graphql_name='lastUpdatedTimestamp')

    list_deployed_jobs = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('CodeJobLocalJobMLMJob'))), graphql_name='listDeployedJobs')

    list_job = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('CodeJobLocalJobMLMJob'))), graphql_name='listJob')

    list_requirements = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='listRequirements')

    model = sgqlc.types.Field(sgqlc.types.non_null(ModelInfo), graphql_name='model')

    model_method_schemas = sgqlc.types.Field(sgqlc.types.non_null(JSON), graphql_name='modelMethodSchemas')

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    owner = sgqlc.types.Field(sgqlc.types.non_null('User'), graphql_name='owner')

    pagination_available_collectors = sgqlc.types.Field(sgqlc.types.non_null(InlineCollectorPagination), graphql_name='paginationAvailableCollectors', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    '''

    pagination_available_dataset_loader_versions = sgqlc.types.Field(sgqlc.types.non_null(InlineObjectVersionPagination), graphql_name='paginationAvailableDatasetLoaderVersions', args=sgqlc.types.ArgDict((
        ('dataset_loader_aggr_id', sgqlc.types.Arg(Int, graphql_name='datasetLoaderAggrId', default=None)),
        ('filter_settings', sgqlc.types.Arg(ObjectVersionFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `dataset_loader_aggr_id` (`Int`)None (default: `null`)
    * `filter_settings` (`ObjectVersionFilterSettings`)None (default:
      `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    pagination_available_dataset_loaders = sgqlc.types.Field(sgqlc.types.non_null(InlineObjectPagination), graphql_name='paginationAvailableDatasetLoaders', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ObjectSortBySortingInput!]`)None (default: `null`)
    '''

    pagination_available_executor_versions = sgqlc.types.Field(sgqlc.types.non_null(InlineObjectVersionPagination), graphql_name='paginationAvailableExecutorVersions', args=sgqlc.types.ArgDict((
        ('executor_aggr_id', sgqlc.types.Arg(Int, graphql_name='executorAggrId', default=None)),
        ('filter_settings', sgqlc.types.Arg(ObjectVersionFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectVersionSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `executor_aggr_id` (`Int`)None (default: `null`)
    * `filter_settings` (`ObjectVersionFilterSettings`)None (default:
      `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ObjectVersionSortBySortingInput!]`)None (default:
      `null`)
    '''

    pagination_available_executors = sgqlc.types.Field(sgqlc.types.non_null(InlineObjectPagination), graphql_name='paginationAvailableExecutors', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ObjectSortBySortingInput!]`)None (default: `null`)
    '''

    pagination_deployed_jobs = sgqlc.types.Field(sgqlc.types.non_null(JobPagination), graphql_name='paginationDeployedJobs', args=sgqlc.types.ArgDict((
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
))
    )
    '''Arguments:

    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    '''

    pagination_job = sgqlc.types.Field(sgqlc.types.non_null(JobPagination), graphql_name='paginationJob', args=sgqlc.types.ArgDict((
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
))
    )
    '''Arguments:

    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    '''

    parent_job = sgqlc.types.Field('CodeJobLocalJobMLMJob', graphql_name='parentJob')

    root_model_version = sgqlc.types.Field(sgqlc.types.non_null('ModelVersionInfo'), graphql_name='rootModelVersion')

    source_executor_version = sgqlc.types.Field(ExecutorVersionInfo, graphql_name='sourceExecutorVersion')

    source_model_version = sgqlc.types.Field('ModelVersionInfo', graphql_name='sourceModelVersion')

    tags = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('Tag'))), graphql_name='tags')

    upload_model_type = sgqlc.types.Field(sgqlc.types.non_null(UploadModelType), graphql_name='uploadModelType')

    venv_build_job = sgqlc.types.Field(BuildJob, graphql_name='venvBuildJob')

    version = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='version')

    visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility')



class ModelVersionPagination(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_model_version', 'total')
    list_model_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ModelVersionInfo))), graphql_name='listModelVersion')

    total = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='total')



class Mutation(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('add_custom_code_job', 'add_image', 'add_ml_job', 'add_used_buckets_in_job', 'cancel_build_job_for_executor_version', 'cancel_build_job_for_model_version', 'cancel_job', 'cancel_venv_build_job_for_model_version', 'create_experiment', 'create_local_job', 'delete_experiment_tag', 'delete_finished_jobs', 'delete_image', 'delete_object_tag', 'delete_object_version_tag', 'delete_object_versions', 'delete_objects', 'log_metric', 'log_metrics', 'log_param', 'log_params', 'rebuild_image', 'rebuild_model_version_image', 'rebuild_no_model_executor_version_image', 'rename_experiment', 'reset_experiment_tags', 'reset_object_tags', 'reset_object_version_tags', 'serve_model', 'set_experiment_tags', 'set_object_tags', 'set_object_version_tags', 'set_visibility_image', 'start_job', 'stop_job', 'stop_model_serving', 'update_experiment', 'update_job', 'update_object', 'update_object_version')
    add_custom_code_job = sgqlc.types.Field(sgqlc.types.non_null(CodeJob), graphql_name='addCustomCodeJob', args=sgqlc.types.ArgDict((
        ('form', sgqlc.types.Arg(sgqlc.types.non_null(JobCodeParameters), graphql_name='form', default=None)),
))
    )
    '''Arguments:

    * `form` (`JobCodeParameters!`)None
    '''

    add_image = sgqlc.types.Field(sgqlc.types.non_null(CustomImage), graphql_name='addImage', args=sgqlc.types.ArgDict((
        ('description', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='description', default='')),
        ('image', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='image', default='prebuild')),
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
        ('tag', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='tag', default=None)),
        ('visibility', sgqlc.types.Arg(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility', default='PUBLIC')),
))
    )
    '''Arguments:

    * `description` (`String!`)None (default: `""`)
    * `image` (`String!`)None (default: `"prebuild"`)
    * `name` (`String!`)None
    * `tag` (`String!`)None
    * `visibility` (`VisibilityOptions!`)None (default: `PUBLIC`)
    '''

    add_ml_job = sgqlc.types.Field(sgqlc.types.non_null(MLMJob), graphql_name='addMlJob', args=sgqlc.types.ArgDict((
        ('form', sgqlc.types.Arg(sgqlc.types.non_null(JobParameters), graphql_name='form', default=None)),
))
    )
    '''Arguments:

    * `form` (`JobParameters!`)None
    '''

    add_used_buckets_in_job = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='addUsedBucketsInJob', args=sgqlc.types.ArgDict((
        ('buckets', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='buckets', default=None)),
        ('secret_uuid', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='secretUuid', default=None)),
))
    )
    '''Arguments:

    * `buckets` (`[String!]!`)None
    * `secret_uuid` (`String!`)None
    '''

    cancel_build_job_for_executor_version = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='cancelBuildJobForExecutorVersion', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
        ('version', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='version', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    * `version` (`Int!`)None
    '''

    cancel_build_job_for_model_version = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='cancelBuildJobForModelVersion', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
        ('version', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='version', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    * `version` (`Int!`)None
    '''

    cancel_job = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='cancelJob', args=sgqlc.types.ArgDict((
        ('job_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='jobId', default=None)),
))
    )
    '''Arguments:

    * `job_id` (`Int!`)None
    '''

    cancel_venv_build_job_for_model_version = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='cancelVenvBuildJobForModelVersion', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
        ('version', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='version', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    * `version` (`Int!`)None
    '''

    create_experiment = sgqlc.types.Field(sgqlc.types.non_null(Experiment), graphql_name='createExperiment', args=sgqlc.types.ArgDict((
        ('experiment_description', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='experimentDescription', default='')),
        ('experiment_name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='experimentName', default=None)),
        ('visibility', sgqlc.types.Arg(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility', default='PRIVATE')),
))
    )
    '''Arguments:

    * `experiment_description` (`String!`)None (default: `""`)
    * `experiment_name` (`String!`)None
    * `visibility` (`VisibilityOptions!`)None (default: `PRIVATE`)
    '''

    create_local_job = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='createLocalJob', args=sgqlc.types.ArgDict((
        ('experiment_params', sgqlc.types.Arg(ExperimentInput, graphql_name='experimentParams', default=None)),
        ('job_name', sgqlc.types.Arg(String, graphql_name='jobName', default=None)),
        ('visibility', sgqlc.types.Arg(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility', default=None)),
))
    )
    '''Arguments:

    * `experiment_params` (`ExperimentInput`)None (default: `null`)
    * `job_name` (`String`)None
    * `visibility` (`VisibilityOptions!`)None
    '''

    delete_experiment_tag = sgqlc.types.Field(sgqlc.types.non_null(Experiment), graphql_name='deleteExperimentTag', args=sgqlc.types.ArgDict((
        ('experiment_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='experimentId', default=None)),
        ('key', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='key', default=None)),
        ('value', sgqlc.types.Arg(String, graphql_name='value', default=None)),
))
    )
    '''Arguments:

    * `experiment_id` (`Int!`)None
    * `key` (`String!`)None
    * `value` (`String`)None (default: `null`)
    '''

    delete_finished_jobs = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='deleteFinishedJobs', args=sgqlc.types.ArgDict((
        ('job_ids', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Int))), graphql_name='jobIds', default=None)),
))
    )
    '''Arguments:

    * `job_ids` (`[Int!]!`)None
    '''

    delete_image = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='deleteImage', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
))
    )
    '''Arguments:

    * `name` (`String!`)None
    '''

    delete_object_tag = sgqlc.types.Field(sgqlc.types.non_null('ExecutorInfoModelInfoDatasetLoaderInfo'), graphql_name='deleteObjectTag', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
        ('key', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='key', default=None)),
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
        ('value', sgqlc.types.Arg(String, graphql_name='value', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    * `key` (`String!`)None
    * `model_type` (`ModelType!`)None
    * `value` (`String`)None (default: `null`)
    '''

    delete_object_version_tag = sgqlc.types.Field(sgqlc.types.non_null('DatasetLoaderVersionInfoModelVersionInfoExecutorVersionInfo'), graphql_name='deleteObjectVersionTag', args=sgqlc.types.ArgDict((
        ('key', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='key', default=None)),
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
        ('object_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionInput), graphql_name='objectVersion', default=None)),
        ('value', sgqlc.types.Arg(String, graphql_name='value', default=None)),
))
    )
    '''Arguments:

    * `key` (`String!`)None
    * `model_type` (`ModelType!`)None
    * `object_version` (`ObjectIdVersionInput!`)None
    * `value` (`String`)None (default: `null`)
    '''

    delete_object_versions = sgqlc.types.Field('DatasetLoaderInfoModelInfoExecutorInfo', graphql_name='deleteObjectVersions', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
        ('versions', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Int))), graphql_name='versions', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    * `model_type` (`ModelType!`)None
    * `versions` (`[Int!]!`)None
    '''

    delete_objects = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='deleteObjects', args=sgqlc.types.ArgDict((
        ('aggr_ids', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Int))), graphql_name='aggrIds', default=None)),
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
))
    )
    '''Arguments:

    * `aggr_ids` (`[Int!]!`)None
    * `model_type` (`ModelType!`)None
    '''

    log_metric = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='logMetric', args=sgqlc.types.ArgDict((
        ('metric', sgqlc.types.Arg(sgqlc.types.non_null(MetricInput), graphql_name='metric', default=None)),
        ('secret_uuid', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='secretUuid', default=None)),
))
    )
    '''Arguments:

    * `metric` (`MetricInput!`)None
    * `secret_uuid` (`String!`)None
    '''

    log_metrics = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='logMetrics', args=sgqlc.types.ArgDict((
        ('metrics', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(MetricInput))), graphql_name='metrics', default=None)),
        ('secret_uuid', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='secretUuid', default=None)),
))
    )
    '''Arguments:

    * `metrics` (`[MetricInput!]!`)None
    * `secret_uuid` (`String!`)None
    '''

    log_param = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='logParam', args=sgqlc.types.ArgDict((
        ('param', sgqlc.types.Arg(sgqlc.types.non_null(ParamInput), graphql_name='param', default=None)),
        ('secret_uuid', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='secretUuid', default=None)),
))
    )
    '''Arguments:

    * `param` (`ParamInput!`)None
    * `secret_uuid` (`String!`)None
    '''

    log_params = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='logParams', args=sgqlc.types.ArgDict((
        ('params', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ParamInput))), graphql_name='params', default=None)),
        ('secret_uuid', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='secretUuid', default=None)),
))
    )
    '''Arguments:

    * `params` (`[ParamInput!]!`)None
    * `secret_uuid` (`String!`)None
    '''

    rebuild_image = sgqlc.types.Field(sgqlc.types.non_null(CustomImage), graphql_name='rebuildImage', args=sgqlc.types.ArgDict((
        ('build_args', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(BuildArgInput)), graphql_name='buildArgs', default=None)),
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
))
    )
    '''Arguments:

    * `build_args` (`[BuildArgInput!]`)None (default: `null`)
    * `name` (`String!`)None
    '''

    rebuild_model_version_image = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='rebuildModelVersionImage', args=sgqlc.types.ArgDict((
        ('model_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionInput), graphql_name='modelVersion', default=None)),
))
    )
    '''Arguments:

    * `model_version` (`ObjectIdVersionInput!`)None
    '''

    rebuild_no_model_executor_version_image = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='rebuildNoModelExecutorVersionImage', args=sgqlc.types.ArgDict((
        ('executor_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionInput), graphql_name='executorVersion', default=None)),
))
    )
    '''Arguments:

    * `executor_version` (`ObjectIdVersionInput!`)None
    '''

    rename_experiment = sgqlc.types.Field(sgqlc.types.non_null(Experiment), graphql_name='renameExperiment', args=sgqlc.types.ArgDict((
        ('experiment_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='experimentId', default=None)),
        ('new_name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='newName', default=None)),
))
    )
    '''Arguments:

    * `experiment_id` (`Int!`)None
    * `new_name` (`String!`)None
    '''

    reset_experiment_tags = sgqlc.types.Field(sgqlc.types.non_null(Experiment), graphql_name='resetExperimentTags', args=sgqlc.types.ArgDict((
        ('experiment_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='experimentId', default=None)),
        ('key', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='key', default=None)),
        ('new_key', sgqlc.types.Arg(String, graphql_name='newKey', default=None)),
        ('values', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='values', default=None)),
))
    )
    '''Arguments:

    * `experiment_id` (`Int!`)None
    * `key` (`String!`)None
    * `new_key` (`String`)None (default: `null`)
    * `values` (`[String!]!`)None
    '''

    reset_object_tags = sgqlc.types.Field(sgqlc.types.non_null('ExecutorInfoModelInfoDatasetLoaderInfo'), graphql_name='resetObjectTags', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
        ('key', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='key', default=None)),
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
        ('new_key', sgqlc.types.Arg(String, graphql_name='newKey', default=None)),
        ('values', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='values', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    * `key` (`String!`)None
    * `model_type` (`ModelType!`)None
    * `new_key` (`String`)None (default: `null`)
    * `values` (`[String!]!`)None
    '''

    reset_object_version_tags = sgqlc.types.Field(sgqlc.types.non_null('DatasetLoaderVersionInfoModelVersionInfoExecutorVersionInfo'), graphql_name='resetObjectVersionTags', args=sgqlc.types.ArgDict((
        ('key', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='key', default=None)),
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
        ('new_key', sgqlc.types.Arg(String, graphql_name='newKey', default=None)),
        ('object_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionInput), graphql_name='objectVersion', default=None)),
        ('values', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='values', default=None)),
))
    )
    '''Arguments:

    * `key` (`String!`)None
    * `model_type` (`ModelType!`)None
    * `new_key` (`String`)None (default: `null`)
    * `object_version` (`ObjectIdVersionInput!`)None
    * `values` (`[String!]!`)None
    '''

    serve_model = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='serveModel', args=sgqlc.types.ArgDict((
        ('serving_parameters', sgqlc.types.Arg(sgqlc.types.non_null(ModelServingInput), graphql_name='servingParameters', default=None)),
))
    )
    '''Arguments:

    * `serving_parameters` (`ModelServingInput!`)None
    '''

    set_experiment_tags = sgqlc.types.Field(sgqlc.types.non_null(Experiment), graphql_name='setExperimentTags', args=sgqlc.types.ArgDict((
        ('experiment_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='experimentId', default=None)),
        ('key', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='key', default=None)),
        ('values', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='values', default=None)),
))
    )
    '''Arguments:

    * `experiment_id` (`Int!`)None
    * `key` (`String!`)None
    * `values` (`[String!]!`)None
    '''

    set_object_tags = sgqlc.types.Field(sgqlc.types.non_null('ExecutorInfoModelInfoDatasetLoaderInfo'), graphql_name='setObjectTags', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
        ('key', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='key', default=None)),
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
        ('values', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='values', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    * `key` (`String!`)None
    * `model_type` (`ModelType!`)None
    * `values` (`[String!]!`)None
    '''

    set_object_version_tags = sgqlc.types.Field(sgqlc.types.non_null('DatasetLoaderVersionInfoModelVersionInfoExecutorVersionInfo'), graphql_name='setObjectVersionTags', args=sgqlc.types.ArgDict((
        ('key', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='key', default=None)),
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
        ('object_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionInput), graphql_name='objectVersion', default=None)),
        ('values', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='values', default=None)),
))
    )
    '''Arguments:

    * `key` (`String!`)None
    * `model_type` (`ModelType!`)None
    * `object_version` (`ObjectIdVersionInput!`)None
    * `values` (`[String!]!`)None
    '''

    set_visibility_image = sgqlc.types.Field(sgqlc.types.non_null(CustomImage), graphql_name='setVisibilityImage', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
        ('visibility', sgqlc.types.Arg(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility', default=None)),
))
    )
    '''Arguments:

    * `name` (`String!`)None
    * `visibility` (`VisibilityOptions!`)None
    '''

    start_job = sgqlc.types.Field(sgqlc.types.non_null('CodeJobLocalJobMLMJob'), graphql_name='startJob', args=sgqlc.types.ArgDict((
        ('secret_uuid', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='secretUuid', default=None)),
))
    )
    '''Arguments:

    * `secret_uuid` (`String!`)None
    '''

    stop_job = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='stopJob', args=sgqlc.types.ArgDict((
        ('exception_traceback', sgqlc.types.Arg(String, graphql_name='exceptionTraceback', default=None)),
        ('message', sgqlc.types.Arg(String, graphql_name='message', default=None)),
        ('secret_uuid', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='secretUuid', default=None)),
        ('status', sgqlc.types.Arg(sgqlc.types.non_null(JobStatus), graphql_name='status', default='SUCCESSFUL')),
))
    )
    '''Arguments:

    * `exception_traceback` (`String`)None (default: `null`)
    * `message` (`String`)None (default: `null`)
    * `secret_uuid` (`String!`)None
    * `status` (`JobStatus!`)None (default: `SUCCESSFUL`)
    '''

    stop_model_serving = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='stopModelServing', args=sgqlc.types.ArgDict((
        ('model_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionInput), graphql_name='modelVersion', default=None)),
))
    )
    '''Arguments:

    * `model_version` (`ObjectIdVersionInput!`)None
    '''

    update_experiment = sgqlc.types.Field(sgqlc.types.non_null(Experiment), graphql_name='updateExperiment', args=sgqlc.types.ArgDict((
        ('experiment_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='experimentId', default=None)),
        ('update_experiment_form', sgqlc.types.Arg(sgqlc.types.non_null(UpdateObjectForm), graphql_name='updateExperimentForm', default=None)),
))
    )
    '''Arguments:

    * `experiment_id` (`Int!`)None
    * `update_experiment_form` (`UpdateObjectForm!`)None
    '''

    update_job = sgqlc.types.Field(sgqlc.types.non_null('CodeJobLocalJobMLMJob'), graphql_name='updateJob', args=sgqlc.types.ArgDict((
        ('job_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='jobId', default=None)),
        ('new_experiment_id', sgqlc.types.Arg(Int, graphql_name='newExperimentId', default=None)),
        ('new_name', sgqlc.types.Arg(String, graphql_name='newName', default=None)),
        ('visibility', sgqlc.types.Arg(VisibilityOptions, graphql_name='visibility', default=None)),
))
    )
    '''Arguments:

    * `job_id` (`Int!`)None
    * `new_experiment_id` (`Int`)None (default: `null`)
    * `new_name` (`String`)None (default: `null`)
    * `visibility` (`VisibilityOptions`)None (default: `null`)
    '''

    update_object = sgqlc.types.Field(sgqlc.types.non_null('ExecutorInfoModelInfoDatasetLoaderInfo'), graphql_name='updateObject', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
        ('update_object_form', sgqlc.types.Arg(sgqlc.types.non_null(UpdateObjectForm), graphql_name='updateObjectForm', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    * `model_type` (`ModelType!`)None
    * `update_object_form` (`UpdateObjectForm!`)None
    '''

    update_object_version = sgqlc.types.Field(sgqlc.types.non_null('DatasetLoaderVersionInfoModelVersionInfoExecutorVersionInfo'), graphql_name='updateObjectVersion', args=sgqlc.types.ArgDict((
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
        ('object_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionInput), graphql_name='objectVersion', default=None)),
        ('update_object_version_form', sgqlc.types.Arg(sgqlc.types.non_null(UpdateObjectVersionForm), graphql_name='updateObjectVersionForm', default=None)),
))
    )
    '''Arguments:

    * `model_type` (`ModelType!`)None
    * `object_version` (`ObjectIdVersionInput!`)None
    * `update_object_version_form` (`UpdateObjectVersionForm!`)None
    '''



class NothingType(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('visibility_options',)
    visibility_options = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptionsLower), graphql_name='visibilityOptions')



class ObjectVersion(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('aggr_id', 'name', 'version')
    aggr_id = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='aggrId')

    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')

    version = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='version')



class Param(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('key', 'value')
    key = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='key')

    value = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='value')



class Query(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('advanced_metric_groups', 'available_images', 'available_resources', 'dataset_loader_from_id', 'dataset_loader_from_name', 'dataset_loader_version_from_aggr_id_version', 'dataset_loader_version_from_name_version', 'dataset_loader_version_from_obj_uuid', 'executor_from_id', 'executor_from_name', 'executor_version_from_aggr_id_version', 'executor_version_from_name_version', 'executor_version_from_obj_uuid', 'experiment_from_id', 'experiment_from_name', 'get_all_images', 'get_code_with_hash', 'get_image', 'get_image_with_hash', 'get_objects_with_hash', 'is_distributed_job_supported', 'is_inference_model_ready', 'job_from_id', 'list_all_metric_names', 'list_artifacts_by_source_paths', 'list_build_job', 'list_dataset_loader', 'list_executor', 'list_experiment', 'list_initial_executor_version', 'list_initial_model_version', 'list_job', 'list_job_from_name', 'list_latest_metric_jobs_json', 'list_metric_jobs', 'list_model', 'model_from_id', 'model_from_name', 'model_version_from_aggr_id_version', 'model_version_from_name_version', 'model_version_from_obj_uuid', 'pagination_dataset_loader', 'pagination_executor', 'pagination_experiment', 'pagination_initial_executor_version', 'pagination_initial_model_version', 'pagination_job', 'pagination_metric_name', 'pagination_model')
    advanced_metric_groups = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(JSON))), graphql_name='advancedMetricGroups', args=sgqlc.types.ArgDict((
        ('axis_type', sgqlc.types.Arg(sgqlc.types.non_null(MetricAxis), graphql_name='axisType', default='timestamp')),
        ('interval', sgqlc.types.Arg(MetricInterval, graphql_name='interval', default=None)),
        ('job_to_metric_list', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(JobToMetricInput))), graphql_name='jobToMetricList', default=None)),
))
    )
    '''Arguments:

    * `axis_type` (`MetricAxis!`)None (default: `timestamp`)
    * `interval` (`MetricInterval`)None (default: `null`)
    * `job_to_metric_list` (`[JobToMetricInput!]!`)None
    '''

    available_images = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(CustomImage))), graphql_name='availableImages')

    available_resources = sgqlc.types.Field(sgqlc.types.non_null(AvailableResources), graphql_name='availableResources')

    dataset_loader_from_id = sgqlc.types.Field(sgqlc.types.non_null(DatasetLoaderInfo), graphql_name='datasetLoaderFromId', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    '''

    dataset_loader_from_name = sgqlc.types.Field(sgqlc.types.non_null(DatasetLoaderInfo), graphql_name='datasetLoaderFromName', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
))
    )
    '''Arguments:

    * `name` (`String!`)None
    '''

    dataset_loader_version_from_aggr_id_version = sgqlc.types.Field(sgqlc.types.non_null(DatasetLoaderVersionInfo), graphql_name='datasetLoaderVersionFromAggrIdVersion', args=sgqlc.types.ArgDict((
        ('dataset_loader_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionOptionalInput), graphql_name='datasetLoaderVersion', default=None)),
))
    )
    '''Arguments:

    * `dataset_loader_version` (`ObjectIdVersionOptionalInput!`)None
    '''

    dataset_loader_version_from_name_version = sgqlc.types.Field(sgqlc.types.non_null(DatasetLoaderVersionInfo), graphql_name='datasetLoaderVersionFromNameVersion', args=sgqlc.types.ArgDict((
        ('dataset_loader_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectVersionOptionalInput), graphql_name='datasetLoaderVersion', default=None)),
))
    )
    '''Arguments:

    * `dataset_loader_version` (`ObjectVersionOptionalInput!`)None
    '''

    dataset_loader_version_from_obj_uuid = sgqlc.types.Field(sgqlc.types.non_null(DatasetLoaderVersionInfo), graphql_name='datasetLoaderVersionFromObjUuid', args=sgqlc.types.ArgDict((
        ('obj_uuid', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='objUuid', default=None)),
))
    )
    '''Arguments:

    * `obj_uuid` (`String!`)None
    '''

    executor_from_id = sgqlc.types.Field(sgqlc.types.non_null(ExecutorInfo), graphql_name='executorFromId', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    '''

    executor_from_name = sgqlc.types.Field(sgqlc.types.non_null(ExecutorInfo), graphql_name='executorFromName', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
))
    )
    '''Arguments:

    * `name` (`String!`)None
    '''

    executor_version_from_aggr_id_version = sgqlc.types.Field(sgqlc.types.non_null(ExecutorVersionInfo), graphql_name='executorVersionFromAggrIdVersion', args=sgqlc.types.ArgDict((
        ('executor_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionOptionalInput), graphql_name='executorVersion', default=None)),
))
    )
    '''Arguments:

    * `executor_version` (`ObjectIdVersionOptionalInput!`)None
    '''

    executor_version_from_name_version = sgqlc.types.Field(sgqlc.types.non_null(ExecutorVersionInfo), graphql_name='executorVersionFromNameVersion', args=sgqlc.types.ArgDict((
        ('executor_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectVersionOptionalInput), graphql_name='executorVersion', default=None)),
))
    )
    '''Arguments:

    * `executor_version` (`ObjectVersionOptionalInput!`)None
    '''

    executor_version_from_obj_uuid = sgqlc.types.Field(sgqlc.types.non_null(ExecutorVersionInfo), graphql_name='executorVersionFromObjUuid', args=sgqlc.types.ArgDict((
        ('obj_uuid', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='objUuid', default=None)),
))
    )
    '''Arguments:

    * `obj_uuid` (`String!`)None
    '''

    experiment_from_id = sgqlc.types.Field(sgqlc.types.non_null(Experiment), graphql_name='experimentFromId', args=sgqlc.types.ArgDict((
        ('experiment_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='experimentId', default=None)),
))
    )
    '''Arguments:

    * `experiment_id` (`Int!`)None
    '''

    experiment_from_name = sgqlc.types.Field(sgqlc.types.non_null(Experiment), graphql_name='experimentFromName', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
))
    )
    '''Arguments:

    * `name` (`String!`)None
    '''

    get_all_images = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(CustomImage))), graphql_name='getAllImages')

    get_code_with_hash = sgqlc.types.Field(Int, graphql_name='getCodeWithHash', args=sgqlc.types.ArgDict((
        ('hash_code', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='hashCode', default=None)),
        ('visibility', sgqlc.types.Arg(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility', default=None)),
))
    )
    '''Arguments:

    * `hash_code` (`String!`)None
    * `visibility` (`VisibilityOptions!`)None
    '''

    get_image = sgqlc.types.Field(sgqlc.types.non_null(CustomImage), graphql_name='getImage', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
))
    )
    '''Arguments:

    * `name` (`String!`)None
    '''

    get_image_with_hash = sgqlc.types.Field(CustomImage, graphql_name='getImageWithHash', args=sgqlc.types.ArgDict((
        ('hash_data', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='hashData', default=None)),
        ('visibility', sgqlc.types.Arg(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility', default='PRIVATE')),
))
    )
    '''Arguments:

    * `hash_data` (`String!`)None
    * `visibility` (`VisibilityOptions!`)None (default: `PRIVATE`)
    '''

    get_objects_with_hash = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('DatasetLoaderVersionInfoModelVersionInfoExecutorVersionInfo'))), graphql_name='getObjectsWithHash', args=sgqlc.types.ArgDict((
        ('hash_artifacts', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='hashArtifacts', default=None)),
        ('model_type', sgqlc.types.Arg(sgqlc.types.non_null(ModelType), graphql_name='modelType', default=None)),
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
        ('visibility', sgqlc.types.Arg(sgqlc.types.non_null(VisibilityOptions), graphql_name='visibility', default=None)),
))
    )
    '''Arguments:

    * `hash_artifacts` (`String!`)None
    * `model_type` (`ModelType!`)None
    * `name` (`String!`)None
    * `visibility` (`VisibilityOptions!`)None
    '''

    is_distributed_job_supported = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isDistributedJobSupported')

    is_inference_model_ready = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isInferenceModelReady', args=sgqlc.types.ArgDict((
        ('model_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionInput), graphql_name='modelVersion', default=None)),
))
    )
    '''Arguments:

    * `model_version` (`ObjectIdVersionInput!`)None
    '''

    job_from_id = sgqlc.types.Field(sgqlc.types.non_null('CodeJobLocalJobMLMJob'), graphql_name='jobFromId', args=sgqlc.types.ArgDict((
        ('job_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='jobId', default=None)),
))
    )
    '''Arguments:

    * `job_id` (`Int!`)None
    '''

    list_all_metric_names = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='listAllMetricNames', args=sgqlc.types.ArgDict((
        ('job_ids', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Int))), graphql_name='jobIds', default=None)),
))
    )
    '''Arguments:

    * `job_ids` (`[Int!]!`)None
    '''

    list_artifacts_by_source_paths = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Artifacts))), graphql_name='listArtifactsBySourcePaths', args=sgqlc.types.ArgDict((
        ('source_paths', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='sourcePaths', default=None)),
))
    )
    '''Arguments:

    * `source_paths` (`[String!]!`)None
    '''

    list_build_job = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(BuildJob))), graphql_name='listBuildJob', args=sgqlc.types.ArgDict((
        ('ids', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Int))), graphql_name='ids', default=None)),
))
    )
    '''Arguments:

    * `ids` (`[Int!]!`)None
    '''

    list_dataset_loader = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(DatasetLoaderInfo))), graphql_name='listDatasetLoader', args=sgqlc.types.ArgDict((
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `sorting` (`[ObjectSortBySortingInput!]`)None (default: `null`)
    '''

    list_executor = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ExecutorInfo))), graphql_name='listExecutor', args=sgqlc.types.ArgDict((
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `sorting` (`[ObjectSortBySortingInput!]`)None (default: `null`)
    '''

    list_experiment = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Experiment))), graphql_name='listExperiment')

    list_initial_executor_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ExecutorVersionInfo))), graphql_name='listInitialExecutorVersion')

    list_initial_model_version = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ModelVersionInfo))), graphql_name='listInitialModelVersion')

    list_job = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('CodeJobLocalJobMLMJob'))), graphql_name='listJob')

    list_job_from_name = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('CodeJobLocalJobMLMJob'))), graphql_name='listJobFromName', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
))
    )
    '''Arguments:

    * `name` (`String!`)None
    '''

    list_latest_metric_jobs_json = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(MetricToJson))), graphql_name='listLatestMetricJobsJson', args=sgqlc.types.ArgDict((
        ('job_ids', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Int))), graphql_name='jobIds', default=None)),
))
    )
    '''Arguments:

    * `job_ids` (`[Int!]!`)None
    '''

    list_metric_jobs = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(JSON))), graphql_name='listMetricJobs', args=sgqlc.types.ArgDict((
        ('axis_type', sgqlc.types.Arg(sgqlc.types.non_null(MetricAxis), graphql_name='axisType', default='timestamp')),
        ('interval', sgqlc.types.Arg(MetricInterval, graphql_name='interval', default=None)),
        ('job_ids', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Int))), graphql_name='jobIds', default=None)),
        ('metric_name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='metricName', default=None)),
))
    )
    '''Arguments:

    * `axis_type` (`MetricAxis!`)None (default: `timestamp`)
    * `interval` (`MetricInterval`)None (default: `null`)
    * `job_ids` (`[Int!]!`)None
    * `metric_name` (`String!`)None
    '''

    list_model = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(ModelInfo))), graphql_name='listModel', args=sgqlc.types.ArgDict((
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `sorting` (`[ObjectSortBySortingInput!]`)None (default: `null`)
    '''

    model_from_id = sgqlc.types.Field(sgqlc.types.non_null(ModelInfo), graphql_name='modelFromId', args=sgqlc.types.ArgDict((
        ('aggr_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='aggrId', default=None)),
))
    )
    '''Arguments:

    * `aggr_id` (`Int!`)None
    '''

    model_from_name = sgqlc.types.Field(sgqlc.types.non_null(ModelInfo), graphql_name='modelFromName', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
))
    )
    '''Arguments:

    * `name` (`String!`)None
    '''

    model_version_from_aggr_id_version = sgqlc.types.Field(sgqlc.types.non_null(ModelVersionInfo), graphql_name='modelVersionFromAggrIdVersion', args=sgqlc.types.ArgDict((
        ('model_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectIdVersionOptionalInput), graphql_name='modelVersion', default=None)),
))
    )
    '''Arguments:

    * `model_version` (`ObjectIdVersionOptionalInput!`)None
    '''

    model_version_from_name_version = sgqlc.types.Field(sgqlc.types.non_null(ModelVersionInfo), graphql_name='modelVersionFromNameVersion', args=sgqlc.types.ArgDict((
        ('model_version', sgqlc.types.Arg(sgqlc.types.non_null(ObjectVersionOptionalInput), graphql_name='modelVersion', default=None)),
))
    )
    '''Arguments:

    * `model_version` (`ObjectVersionOptionalInput!`)None
    '''

    model_version_from_obj_uuid = sgqlc.types.Field(sgqlc.types.non_null(ModelVersionInfo), graphql_name='modelVersionFromObjUuid', args=sgqlc.types.ArgDict((
        ('obj_uuid', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='objUuid', default=None)),
))
    )
    '''Arguments:

    * `obj_uuid` (`String!`)None
    '''

    pagination_dataset_loader = sgqlc.types.Field(sgqlc.types.non_null(DatasetLoaderPagination), graphql_name='paginationDatasetLoader', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ObjectSortBySortingInput!]`)None (default: `null`)
    '''

    pagination_executor = sgqlc.types.Field(sgqlc.types.non_null(ExecutorPagination), graphql_name='paginationExecutor', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ObjectSortBySortingInput!]`)None (default: `null`)
    '''

    pagination_experiment = sgqlc.types.Field(sgqlc.types.non_null(ExperimentPagination), graphql_name='paginationExperiment', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ExperimentFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ExperimentSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ExperimentFilterSettings`)None (default:
      `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ExperimentSortBySortingInput!]`)None (default:
      `null`)
    '''

    pagination_initial_executor_version = sgqlc.types.Field(sgqlc.types.non_null(ExecutorVersionPagination), graphql_name='paginationInitialExecutorVersion', args=sgqlc.types.ArgDict((
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
))
    )
    '''Arguments:

    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    '''

    pagination_initial_model_version = sgqlc.types.Field(sgqlc.types.non_null(ModelVersionPagination), graphql_name='paginationInitialModelVersion', args=sgqlc.types.ArgDict((
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
))
    )
    '''Arguments:

    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    '''

    pagination_job = sgqlc.types.Field(sgqlc.types.non_null(JobPagination), graphql_name='paginationJob', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(JobFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(JobsSorting, graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`JobFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`JobsSorting`)None (default: `null`)
    '''

    pagination_metric_name = sgqlc.types.Field(sgqlc.types.non_null(MetricNamePagination), graphql_name='paginationMetricName', args=sgqlc.types.ArgDict((
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('metric_name', sgqlc.types.Arg(String, graphql_name='metricName', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
))
    )
    '''Arguments:

    * `limit` (`Int`)None (default: `null`)
    * `metric_name` (`String`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    '''

    pagination_model = sgqlc.types.Field(sgqlc.types.non_null(ModelPagination), graphql_name='paginationModel', args=sgqlc.types.ArgDict((
        ('filter_settings', sgqlc.types.Arg(ObjectFilterSettings, graphql_name='filterSettings', default=None)),
        ('limit', sgqlc.types.Arg(Int, graphql_name='limit', default=None)),
        ('offset', sgqlc.types.Arg(Int, graphql_name='offset', default=None)),
        ('sorting', sgqlc.types.Arg(sgqlc.types.list_of(sgqlc.types.non_null(ObjectSortBySortingInput)), graphql_name='sorting', default=None)),
))
    )
    '''Arguments:

    * `filter_settings` (`ObjectFilterSettings`)None (default: `null`)
    * `limit` (`Int`)None (default: `null`)
    * `offset` (`Int`)None (default: `null`)
    * `sorting` (`[ObjectSortBySortingInput!]`)None (default: `null`)
    '''



class ResourcesParams(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('cpus', 'gpu_number', 'gpu_type', 'memory_per_node')
    cpus = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='cpus')

    gpu_number = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='gpuNumber')

    gpu_type = sgqlc.types.Field(String, graphql_name='gpuType')

    memory_per_node = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='memoryPerNode')



class RoleDataParams(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('data_params', 'role')
    data_params = sgqlc.types.Field(sgqlc.types.non_null(DataParams), graphql_name='dataParams')

    role = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='role')



class RoleDatasetLoaderVersion(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('dataset_loader_version', 'role')
    dataset_loader_version = sgqlc.types.Field(sgqlc.types.non_null(DatasetLoaderVersionInfo), graphql_name='datasetLoaderVersion')

    role = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='role')



class RoleMethodSchema(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('list_method_schemas', 'role')
    list_method_schemas = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(MethodSchema))), graphql_name='listMethodSchemas')

    role = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='role')



class RoleModelParams(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('model_params', 'role', 'upload_params')
    model_params = sgqlc.types.Field(sgqlc.types.non_null(ModelParams), graphql_name='modelParams')

    role = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='role')

    upload_params = sgqlc.types.Field('UploadNewModelParams', graphql_name='uploadParams')



class RoleModelVersion(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('model_version', 'role')
    model_version = sgqlc.types.Field(sgqlc.types.non_null(ModelVersionInfo), graphql_name='modelVersion')

    role = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='role')



class Subscription(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('advanced_metric_groups', 'build_job_status', 'job_status', 'list_metric_jobs')
    advanced_metric_groups = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(JSON))), graphql_name='advancedMetricGroups', args=sgqlc.types.ArgDict((
        ('axis_type', sgqlc.types.Arg(sgqlc.types.non_null(MetricAxis), graphql_name='axisType', default='timestamp')),
        ('interval', sgqlc.types.Arg(MetricInterval, graphql_name='interval', default=None)),
        ('job_to_metric_list', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(JobToMetricInput))), graphql_name='jobToMetricList', default=None)),
))
    )
    '''Arguments:

    * `axis_type` (`MetricAxis!`)None (default: `timestamp`)
    * `interval` (`MetricInterval`)None (default: `null`)
    * `job_to_metric_list` (`[JobToMetricInput!]!`)None
    '''

    build_job_status = sgqlc.types.Field(sgqlc.types.non_null(JobInfoResponse), graphql_name='buildJobStatus', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='name', default=None)),
))
    )
    '''Arguments:

    * `name` (`String!`)None
    '''

    job_status = sgqlc.types.Field(sgqlc.types.non_null(JobInfoResponse), graphql_name='jobStatus', args=sgqlc.types.ArgDict((
        ('job_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='jobId', default=None)),
))
    )
    '''Arguments:

    * `job_id` (`Int!`)None
    '''

    list_metric_jobs = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(JSON))), graphql_name='listMetricJobs', args=sgqlc.types.ArgDict((
        ('axis_type', sgqlc.types.Arg(sgqlc.types.non_null(MetricAxis), graphql_name='axisType', default='timestamp')),
        ('interval', sgqlc.types.Arg(MetricInterval, graphql_name='interval', default=None)),
        ('job_ids', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(Int))), graphql_name='jobIds', default=None)),
        ('metric_name', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='metricName', default=None)),
))
    )
    '''Arguments:

    * `axis_type` (`MetricAxis!`)None (default: `timestamp`)
    * `interval` (`MetricInterval`)None (default: `null`)
    * `job_ids` (`[Int!]!`)None
    * `metric_name` (`String!`)None
    '''



class Tag(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('key', 'values')
    key = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='key')

    values = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(String))), graphql_name='values')



class UploadNewModelParams(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('description', 'new_model_name', 'new_model_visibility', 'prepare_new_model_inference', 'start_build_new_model_image', 'upload_model_mode')
    description = sgqlc.types.Field(String, graphql_name='description')

    new_model_name = sgqlc.types.Field(String, graphql_name='newModelName')

    new_model_visibility = sgqlc.types.Field(sgqlc.types.non_null(VisibilityOptions), graphql_name='newModelVisibility')

    prepare_new_model_inference = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='prepareNewModelInference')

    start_build_new_model_image = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='startBuildNewModelImage')

    upload_model_mode = sgqlc.types.Field(sgqlc.types.non_null(UploadModelMode), graphql_name='uploadModelMode')



class User(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('id',)
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')




########################################################################
# Unions
########################################################################
class CodeJobLocalJobMLMJob(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (CodeJob, LocalJob, MLMJob)


class DatasetLoaderInfoModelInfoExecutorInfo(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (DatasetLoaderInfo, ExecutorInfo, ModelInfo)


class DatasetLoaderVersionInfoModelVersionInfoExecutorVersionInfo(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (DatasetLoaderVersionInfo, ExecutorVersionInfo, ModelVersionInfo)


class ExecutorInfoModelInfoDatasetLoaderInfo(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (DatasetLoaderInfo, ExecutorInfo, ModelInfo)



########################################################################
# Schema Entry Points
########################################################################
schema.query_type = Query
schema.mutation_type = Mutation
schema.subscription_type = Subscription

