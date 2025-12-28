r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-sqs-pipes-stepfunctions/README.adoc)
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *

import aws_cdk.aws_cloudwatch as _aws_cdk_aws_cloudwatch_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import aws_cdk.aws_pipes as _aws_cdk_aws_pipes_ceddda9d
import aws_cdk.aws_sqs as _aws_cdk_aws_sqs_ceddda9d
import aws_cdk.aws_stepfunctions as _aws_cdk_aws_stepfunctions_ceddda9d
import aws_solutions_constructs.core as _aws_solutions_constructs_core_ac4f6ab9
import constructs as _constructs_77d1e7e8


@jsii.enum(
    jsii_type="@aws-solutions-constructs/aws-sqs-pipes-stepfunctions.PipesLogLevel"
)
class PipesLogLevel(enum.Enum):
    OFF = "OFF"
    TRACE = "TRACE"
    INFO = "INFO"
    ERROR = "ERROR"


class SqsToPipesToStepfunctions(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-sqs-pipes-stepfunctions.SqsToPipesToStepfunctions",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        encrypt_queue_with_cmk: typing.Optional[builtins.bool] = None,
        enrichment_function: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        enrichment_state_machine: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
        existing_queue_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        existing_state_machine_obj: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_level: typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.PipesLogLevel] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        pipe_log_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        pipe_props: typing.Any = None,
        queue_encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        state_machine_props: typing.Optional[typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. default = true
        :param dead_letter_queue_props: Optional user-provided props to override the default props for the dead letter SQS queue.
        :param deploy_dead_letter_queue: Whether to create a secondary queue to be used as a dead letter queue. default = true.
        :param encrypt_queue_with_cmk: Whether to encrypt the Queue with a customer managed KMS key (CMK). This is the default behavior, and this property defaults to true - if it is explicitly set to false then the Queue is encrypted with an Amazon managed KMS key. For a completely unencrypted Queue (not recommended), create the Queue separately from the construct and pass it in using the existingQueueObject. Since SNS subscriptions do not currently support SQS queues with AWS managed encryption keys, setting this to false will always result in an error from the underlying CDK - we have still included this property for consistency with topics and to be ready if the services one day support this functionality.
        :param enrichment_function: Optional - Lambda function that the construct will configure to be called to enrich the message between source and target. The construct will configure the pipe IAM role to allow invoking the function (but will not affect the IArole assigned to the function). Specifying both this and enrichmentStateMachine is an error. Default - undefined
        :param enrichment_state_machine: Optional - Step Functions state machine that the construct will configure to be called to enrich the message between source and target. The construct will configure the pipe IAM role to allow executing the state machine (but will not affect the IAM role assigned to the state machine). Specifying both this and enrichmentStateMachine is an error. Enrichment is invoked synchronously, so this must be an EXPRESS state machin. Default - undefined
        :param existing_queue_encryption_key: An optional CMK that will be used by the construct to encrypt the new SQS queue.
        :param existing_queue_obj: An optional, existing SQS queue to be used instead of the default queue. Providing both this and queueProps will cause an error.
        :param existing_state_machine_obj: Optional existing state machine to incorporate into the construct.
        :param log_group_props: Optional user provided props to override the default props for for the CloudWatchLogs LogGroup.
        :param log_level: Threshold for what messages the new pipe sends to the log, PipesLogLevel.OFF, PipesLogLevel.ERROR, PipesLogLevel.INFO, PipesLogLevel.TRACE. The default is INFO. Setting the level to OFF will prevent any log group from being created. Providing pipeProps.logConfiguration will controls all aspects of logging and any construct provided log configuration is disabled. If pipeProps.logConfiguration is provided then specifying this or pipeLogProps is an error.
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead letter queue. Defaults to 15.
        :param pipe_log_props: Default behavior is for the this construct to create a new CloudWatch Logs log group for the pipe. These props are used to override defaults set by AWS or this construct. If there are concerns about the cost of log storage, this is where a client can specify a shorter retention duration (in days)
        :param pipe_props: Optional customer provided settings for the EventBridge pipe. source, target and roleArn are set by the construct and cannot be overriden. The construct will generate default sourceParameters, targetParameters and logConfiguration that can be overriden by populating those values in these props. If the client wants to implement enrichment or a filter, this is where that information can be provided. Any other props can be freely overridden.
        :param queue_encryption_key_props: An optional subset of key properties to override the default properties used by constructs (enableKeyRotation: true). These properties will be used in constructing the CMK used to encrypt the SQS queue.
        :param queue_props: Optional - user provided properties to override the default properties for the SQS queue. Providing both this and ``existingQueueObj`` will cause an error.
        :param state_machine_props: User provided props for the sfn.StateMachine. This or existingStateMachine is required.

        :access: public
        :summary: Constructs a new instance of the SqsToPipesToStepfunctions class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ceb1c3c4d051238d574ab5b99dbf3c5e745042f472b80f152d0f11b3d56c0c1b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = SqsToPipesToStepfunctionsProps(
            create_cloud_watch_alarms=create_cloud_watch_alarms,
            dead_letter_queue_props=dead_letter_queue_props,
            deploy_dead_letter_queue=deploy_dead_letter_queue,
            encrypt_queue_with_cmk=encrypt_queue_with_cmk,
            enrichment_function=enrichment_function,
            enrichment_state_machine=enrichment_state_machine,
            existing_queue_encryption_key=existing_queue_encryption_key,
            existing_queue_obj=existing_queue_obj,
            existing_state_machine_obj=existing_state_machine_obj,
            log_group_props=log_group_props,
            log_level=log_level,
            max_receive_count=max_receive_count,
            pipe_log_props=pipe_log_props,
            pipe_props=pipe_props,
            queue_encryption_key_props=queue_encryption_key_props,
            queue_props=queue_props,
            state_machine_props=state_machine_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="pipe")
    def pipe(self) -> _aws_cdk_aws_pipes_ceddda9d.CfnPipe:
        return typing.cast(_aws_cdk_aws_pipes_ceddda9d.CfnPipe, jsii.get(self, "pipe"))

    @builtins.property
    @jsii.member(jsii_name="pipeRole")
    def pipe_role(self) -> _aws_cdk_aws_iam_ceddda9d.Role:
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Role, jsii.get(self, "pipeRole"))

    @builtins.property
    @jsii.member(jsii_name="sqsQueue")
    def sqs_queue(self) -> _aws_cdk_aws_sqs_ceddda9d.Queue:
        return typing.cast(_aws_cdk_aws_sqs_ceddda9d.Queue, jsii.get(self, "sqsQueue"))

    @builtins.property
    @jsii.member(jsii_name="stateMachine")
    def state_machine(self) -> _aws_cdk_aws_stepfunctions_ceddda9d.StateMachine:
        return typing.cast(_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine, jsii.get(self, "stateMachine"))

    @builtins.property
    @jsii.member(jsii_name="cloudwatchAlarms")
    def cloudwatch_alarms(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_cloudwatch_ceddda9d.Alarm]]:
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_cloudwatch_ceddda9d.Alarm]], jsii.get(self, "cloudwatchAlarms"))

    @builtins.property
    @jsii.member(jsii_name="deadLetterQueue")
    def dead_letter_queue(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.DeadLetterQueue]:
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.DeadLetterQueue], jsii.get(self, "deadLetterQueue"))

    @builtins.property
    @jsii.member(jsii_name="encryptionKey")
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "encryptionKey"))

    @builtins.property
    @jsii.member(jsii_name="stateMachineLogGroup")
    def state_machine_log_group(
        self,
    ) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup]:
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup], jsii.get(self, "stateMachineLogGroup"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-sqs-pipes-stepfunctions.SqsToPipesToStepfunctionsProps",
    jsii_struct_bases=[],
    name_mapping={
        "create_cloud_watch_alarms": "createCloudWatchAlarms",
        "dead_letter_queue_props": "deadLetterQueueProps",
        "deploy_dead_letter_queue": "deployDeadLetterQueue",
        "encrypt_queue_with_cmk": "encryptQueueWithCmk",
        "enrichment_function": "enrichmentFunction",
        "enrichment_state_machine": "enrichmentStateMachine",
        "existing_queue_encryption_key": "existingQueueEncryptionKey",
        "existing_queue_obj": "existingQueueObj",
        "existing_state_machine_obj": "existingStateMachineObj",
        "log_group_props": "logGroupProps",
        "log_level": "logLevel",
        "max_receive_count": "maxReceiveCount",
        "pipe_log_props": "pipeLogProps",
        "pipe_props": "pipeProps",
        "queue_encryption_key_props": "queueEncryptionKeyProps",
        "queue_props": "queueProps",
        "state_machine_props": "stateMachineProps",
    },
)
class SqsToPipesToStepfunctionsProps:
    def __init__(
        self,
        *,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        encrypt_queue_with_cmk: typing.Optional[builtins.bool] = None,
        enrichment_function: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        enrichment_state_machine: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
        existing_queue_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        existing_state_machine_obj: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_level: typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.PipesLogLevel] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        pipe_log_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        pipe_props: typing.Any = None,
        queue_encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        state_machine_props: typing.Optional[typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. default = true
        :param dead_letter_queue_props: Optional user-provided props to override the default props for the dead letter SQS queue.
        :param deploy_dead_letter_queue: Whether to create a secondary queue to be used as a dead letter queue. default = true.
        :param encrypt_queue_with_cmk: Whether to encrypt the Queue with a customer managed KMS key (CMK). This is the default behavior, and this property defaults to true - if it is explicitly set to false then the Queue is encrypted with an Amazon managed KMS key. For a completely unencrypted Queue (not recommended), create the Queue separately from the construct and pass it in using the existingQueueObject. Since SNS subscriptions do not currently support SQS queues with AWS managed encryption keys, setting this to false will always result in an error from the underlying CDK - we have still included this property for consistency with topics and to be ready if the services one day support this functionality.
        :param enrichment_function: Optional - Lambda function that the construct will configure to be called to enrich the message between source and target. The construct will configure the pipe IAM role to allow invoking the function (but will not affect the IArole assigned to the function). Specifying both this and enrichmentStateMachine is an error. Default - undefined
        :param enrichment_state_machine: Optional - Step Functions state machine that the construct will configure to be called to enrich the message between source and target. The construct will configure the pipe IAM role to allow executing the state machine (but will not affect the IAM role assigned to the state machine). Specifying both this and enrichmentStateMachine is an error. Enrichment is invoked synchronously, so this must be an EXPRESS state machin. Default - undefined
        :param existing_queue_encryption_key: An optional CMK that will be used by the construct to encrypt the new SQS queue.
        :param existing_queue_obj: An optional, existing SQS queue to be used instead of the default queue. Providing both this and queueProps will cause an error.
        :param existing_state_machine_obj: Optional existing state machine to incorporate into the construct.
        :param log_group_props: Optional user provided props to override the default props for for the CloudWatchLogs LogGroup.
        :param log_level: Threshold for what messages the new pipe sends to the log, PipesLogLevel.OFF, PipesLogLevel.ERROR, PipesLogLevel.INFO, PipesLogLevel.TRACE. The default is INFO. Setting the level to OFF will prevent any log group from being created. Providing pipeProps.logConfiguration will controls all aspects of logging and any construct provided log configuration is disabled. If pipeProps.logConfiguration is provided then specifying this or pipeLogProps is an error.
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead letter queue. Defaults to 15.
        :param pipe_log_props: Default behavior is for the this construct to create a new CloudWatch Logs log group for the pipe. These props are used to override defaults set by AWS or this construct. If there are concerns about the cost of log storage, this is where a client can specify a shorter retention duration (in days)
        :param pipe_props: Optional customer provided settings for the EventBridge pipe. source, target and roleArn are set by the construct and cannot be overriden. The construct will generate default sourceParameters, targetParameters and logConfiguration that can be overriden by populating those values in these props. If the client wants to implement enrichment or a filter, this is where that information can be provided. Any other props can be freely overridden.
        :param queue_encryption_key_props: An optional subset of key properties to override the default properties used by constructs (enableKeyRotation: true). These properties will be used in constructing the CMK used to encrypt the SQS queue.
        :param queue_props: Optional - user provided properties to override the default properties for the SQS queue. Providing both this and ``existingQueueObj`` will cause an error.
        :param state_machine_props: User provided props for the sfn.StateMachine. This or existingStateMachine is required.

        :summary: The properties for the SnsToSqs class.
        '''
        if isinstance(dead_letter_queue_props, dict):
            dead_letter_queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**dead_letter_queue_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if isinstance(pipe_log_props, dict):
            pipe_log_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**pipe_log_props)
        if isinstance(queue_encryption_key_props, dict):
            queue_encryption_key_props = _aws_cdk_aws_kms_ceddda9d.KeyProps(**queue_encryption_key_props)
        if isinstance(queue_props, dict):
            queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**queue_props)
        if isinstance(state_machine_props, dict):
            state_machine_props = _aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps(**state_machine_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__194e6c5b4126faff541334ee4c6e09b0eb05d31358b8eba12e563e86b30c14c1)
            check_type(argname="argument create_cloud_watch_alarms", value=create_cloud_watch_alarms, expected_type=type_hints["create_cloud_watch_alarms"])
            check_type(argname="argument dead_letter_queue_props", value=dead_letter_queue_props, expected_type=type_hints["dead_letter_queue_props"])
            check_type(argname="argument deploy_dead_letter_queue", value=deploy_dead_letter_queue, expected_type=type_hints["deploy_dead_letter_queue"])
            check_type(argname="argument encrypt_queue_with_cmk", value=encrypt_queue_with_cmk, expected_type=type_hints["encrypt_queue_with_cmk"])
            check_type(argname="argument enrichment_function", value=enrichment_function, expected_type=type_hints["enrichment_function"])
            check_type(argname="argument enrichment_state_machine", value=enrichment_state_machine, expected_type=type_hints["enrichment_state_machine"])
            check_type(argname="argument existing_queue_encryption_key", value=existing_queue_encryption_key, expected_type=type_hints["existing_queue_encryption_key"])
            check_type(argname="argument existing_queue_obj", value=existing_queue_obj, expected_type=type_hints["existing_queue_obj"])
            check_type(argname="argument existing_state_machine_obj", value=existing_state_machine_obj, expected_type=type_hints["existing_state_machine_obj"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
            check_type(argname="argument log_level", value=log_level, expected_type=type_hints["log_level"])
            check_type(argname="argument max_receive_count", value=max_receive_count, expected_type=type_hints["max_receive_count"])
            check_type(argname="argument pipe_log_props", value=pipe_log_props, expected_type=type_hints["pipe_log_props"])
            check_type(argname="argument pipe_props", value=pipe_props, expected_type=type_hints["pipe_props"])
            check_type(argname="argument queue_encryption_key_props", value=queue_encryption_key_props, expected_type=type_hints["queue_encryption_key_props"])
            check_type(argname="argument queue_props", value=queue_props, expected_type=type_hints["queue_props"])
            check_type(argname="argument state_machine_props", value=state_machine_props, expected_type=type_hints["state_machine_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create_cloud_watch_alarms is not None:
            self._values["create_cloud_watch_alarms"] = create_cloud_watch_alarms
        if dead_letter_queue_props is not None:
            self._values["dead_letter_queue_props"] = dead_letter_queue_props
        if deploy_dead_letter_queue is not None:
            self._values["deploy_dead_letter_queue"] = deploy_dead_letter_queue
        if encrypt_queue_with_cmk is not None:
            self._values["encrypt_queue_with_cmk"] = encrypt_queue_with_cmk
        if enrichment_function is not None:
            self._values["enrichment_function"] = enrichment_function
        if enrichment_state_machine is not None:
            self._values["enrichment_state_machine"] = enrichment_state_machine
        if existing_queue_encryption_key is not None:
            self._values["existing_queue_encryption_key"] = existing_queue_encryption_key
        if existing_queue_obj is not None:
            self._values["existing_queue_obj"] = existing_queue_obj
        if existing_state_machine_obj is not None:
            self._values["existing_state_machine_obj"] = existing_state_machine_obj
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props
        if log_level is not None:
            self._values["log_level"] = log_level
        if max_receive_count is not None:
            self._values["max_receive_count"] = max_receive_count
        if pipe_log_props is not None:
            self._values["pipe_log_props"] = pipe_log_props
        if pipe_props is not None:
            self._values["pipe_props"] = pipe_props
        if queue_encryption_key_props is not None:
            self._values["queue_encryption_key_props"] = queue_encryption_key_props
        if queue_props is not None:
            self._values["queue_props"] = queue_props
        if state_machine_props is not None:
            self._values["state_machine_props"] = state_machine_props

    @builtins.property
    def create_cloud_watch_alarms(self) -> typing.Optional[builtins.bool]:
        '''Whether to create recommended CloudWatch alarms.

        default = true
        '''
        result = self._values.get("create_cloud_watch_alarms")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def dead_letter_queue_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''Optional user-provided props to override the default props for the dead letter SQS queue.'''
        result = self._values.get("dead_letter_queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

    @builtins.property
    def deploy_dead_letter_queue(self) -> typing.Optional[builtins.bool]:
        '''Whether to create a secondary queue to be used as a dead letter queue.

        default = true.
        '''
        result = self._values.get("deploy_dead_letter_queue")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def encrypt_queue_with_cmk(self) -> typing.Optional[builtins.bool]:
        '''Whether to encrypt the Queue with a customer managed KMS key (CMK).

        This is the default
        behavior, and this property defaults to true - if it is explicitly set to false then the Queue
        is encrypted with an Amazon managed KMS key. For a completely unencrypted Queue (not recommended),
        create the Queue separately from the construct and pass it in using the existingQueueObject. Since
        SNS subscriptions do not currently support SQS queues with AWS managed encryption keys, setting this
        to false will always result in an error from the underlying CDK - we have still included this property
        for consistency with topics and to be ready if the services one day support this functionality.
        '''
        result = self._values.get("encrypt_queue_with_cmk")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enrichment_function(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function]:
        '''Optional - Lambda function that the construct will configure to be called to enrich the message between source and target.

        The construct will configure the pipe IAM role to allow invoking the
        function (but will not affect the IArole assigned to the function). Specifying both this and
        enrichmentStateMachine is an error. Default - undefined
        '''
        result = self._values.get("enrichment_function")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function], result)

    @builtins.property
    def enrichment_state_machine(
        self,
    ) -> typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine]:
        '''Optional - Step Functions state machine that the construct will configure to be called to enrich the message between source and target.

        The construct will configure the pipe IAM role to allow executing the state
        machine (but will not affect the IAM role assigned to the state machine). Specifying both this and
        enrichmentStateMachine is an error. Enrichment is invoked synchronously, so this must be an EXPRESS
        state machin. Default - undefined
        '''
        result = self._values.get("enrichment_state_machine")
        return typing.cast(typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine], result)

    @builtins.property
    def existing_queue_encryption_key(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key]:
        '''An optional CMK that will be used by the construct to encrypt the new SQS queue.'''
        result = self._values.get("existing_queue_encryption_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def existing_queue_obj(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue]:
        '''An optional, existing SQS queue to be used instead of the default queue.

        Providing both this and queueProps will cause an error.
        '''
        result = self._values.get("existing_queue_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue], result)

    @builtins.property
    def existing_state_machine_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine]:
        '''Optional existing state machine to incorporate into the construct.'''
        result = self._values.get("existing_state_machine_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine], result)

    @builtins.property
    def log_group_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps]:
        '''Optional user provided props to override the default props for for the CloudWatchLogs LogGroup.'''
        result = self._values.get("log_group_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps], result)

    @builtins.property
    def log_level(
        self,
    ) -> typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.PipesLogLevel]:
        '''Threshold for what messages the new pipe sends to the log, PipesLogLevel.OFF, PipesLogLevel.ERROR, PipesLogLevel.INFO, PipesLogLevel.TRACE. The default is INFO. Setting the level to OFF will prevent any log group from being created. Providing pipeProps.logConfiguration will controls all aspects of logging and any construct provided log configuration is disabled. If pipeProps.logConfiguration is provided then specifying this or pipeLogProps is an error.'''
        result = self._values.get("log_level")
        return typing.cast(typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.PipesLogLevel], result)

    @builtins.property
    def max_receive_count(self) -> typing.Optional[jsii.Number]:
        '''The number of times a message can be unsuccessfully dequeued before being moved to the dead letter queue.

        Defaults to 15.
        '''
        result = self._values.get("max_receive_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def pipe_log_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps]:
        '''Default behavior is for the this construct to create a new CloudWatch Logs log group for the pipe.

        These props are used to override defaults set by AWS or this construct. If there are concerns about
        the cost of log storage, this is where a client can specify a shorter retention duration (in days)
        '''
        result = self._values.get("pipe_log_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps], result)

    @builtins.property
    def pipe_props(self) -> typing.Any:
        '''Optional customer provided settings for the EventBridge pipe.

        source, target and
        roleArn are set by the construct and cannot be overriden. The construct will generate
        default sourceParameters, targetParameters and logConfiguration that can be
        overriden by populating those values in these props. If the client wants to implement
        enrichment or a filter, this is where that information can be provided. Any other props
        can be freely overridden.
        '''
        result = self._values.get("pipe_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def queue_encryption_key_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps]:
        '''An optional subset of key properties to override the default properties used by constructs (enableKeyRotation: true).

        These properties will be used in constructing the CMK used to encrypt the SQS queue.
        '''
        result = self._values.get("queue_encryption_key_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps], result)

    @builtins.property
    def queue_props(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''Optional - user provided properties to override the default properties for the SQS queue.

        Providing both this and ``existingQueueObj`` will cause an error.
        '''
        result = self._values.get("queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

    @builtins.property
    def state_machine_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps]:
        '''User provided props for the sfn.StateMachine. This or existingStateMachine is required.'''
        result = self._values.get("state_machine_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SqsToPipesToStepfunctionsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "PipesLogLevel",
    "SqsToPipesToStepfunctions",
    "SqsToPipesToStepfunctionsProps",
]

publication.publish()

def _typecheckingstub__ceb1c3c4d051238d574ab5b99dbf3c5e745042f472b80f152d0f11b3d56c0c1b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    encrypt_queue_with_cmk: typing.Optional[builtins.bool] = None,
    enrichment_function: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    enrichment_state_machine: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
    existing_queue_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    existing_state_machine_obj: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_level: typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.PipesLogLevel] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    pipe_log_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    pipe_props: typing.Any = None,
    queue_encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    state_machine_props: typing.Optional[typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__194e6c5b4126faff541334ee4c6e09b0eb05d31358b8eba12e563e86b30c14c1(
    *,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    encrypt_queue_with_cmk: typing.Optional[builtins.bool] = None,
    enrichment_function: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    enrichment_state_machine: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
    existing_queue_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    existing_state_machine_obj: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_level: typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.PipesLogLevel] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    pipe_log_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    pipe_props: typing.Any = None,
    queue_encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    state_machine_props: typing.Optional[typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
