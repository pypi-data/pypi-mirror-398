r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-dynamodbstreams-pipes-stepfunctions/README.adoc)
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
import aws_cdk.aws_dynamodb as _aws_cdk_aws_dynamodb_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import aws_cdk.aws_pipes as _aws_cdk_aws_pipes_ceddda9d
import aws_cdk.aws_sqs as _aws_cdk_aws_sqs_ceddda9d
import aws_cdk.aws_stepfunctions as _aws_cdk_aws_stepfunctions_ceddda9d
import aws_solutions_constructs.core as _aws_solutions_constructs_core_ac4f6ab9
import constructs as _constructs_77d1e7e8


class DynamoDBStreamsToPipesToStepfunctions(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-dynamodbstreams-pipes-stepfunctions.DynamoDBStreamsToPipesToStepfunctions",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        deploy_sqs_dlq_queue: typing.Optional[builtins.bool] = None,
        dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
        enrichment_function: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        enrichment_state_machine: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
        existing_state_machine_obj: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
        existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_level: typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.PipesLogLevel] = None,
        pipe_log_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        pipe_props: typing.Any = None,
        sqs_dlq_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        state_machine_props: typing.Optional[typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. default = true
        :param deploy_sqs_dlq_queue: Whether to deploy a SQS dead letter queue when a data record reaches the Maximum Retry Attempts or Maximum Record Age, its metadata like shard ID and stream ARN will be sent to an SQS queue. The construct will create and configure the DLQ with a default maximumRetryAttempts of 2. To customize this, you should set maximumRecordAgeInSeconds and/or maximumRetryAttempts attempts in pipeProps.sourceParameters.dynamoDbStreamParameters. Default - deploy queue, MaximumRetryAttempts is set to 3, and maximumRecordAge is left to default (-1, or infinite) Default: - true.
        :param dynamo_table_props: Optional user provided props to override the default props for the DynamoDB Table. Providing both this and ``existingTableInterface`` is an error. Default: - Partition key ID: string
        :param enrichment_function: Optional - Lambda function that the construct will configure to be called to enrich the message between source and target. The construct will configure the pipe IAM role to allow invoking the function (but will not affect the IArole assigned to the function). Specifying both this and enrichmentStateMachine is an error. Default - undefined
        :param enrichment_state_machine: Optional - Step Functions state machine that the construct will configure to be called to enrich the message between source and target. The construct will configure the pipe IAM role to allow executing the state machine (but will not affect the IAM role assigned to the state machine). Specifying both this and enrichmentStateMachine is an error. Enrichment is invoked synchronously, so this must be an EXPRESS state machin. Default - undefined
        :param existing_state_machine_obj: Optional existing state machine to incorporate into the construct.
        :param existing_table_interface: Optional - existing DynamoDB table, providing both this and ``dynamoTableProps`` will cause an error. Default: - None
        :param log_group_props: Optional user provided props to override the default props for for the CloudWatchLogs LogGroup.
        :param log_level: Threshold for what messages the new pipe sends to the log, PipesLogLevel.OFF, PipesLogLevel.ERROR, PipesLogLevel.INFO, PipesLogLevel.TRACE. The default is INFO. Setting the level to OFF will prevent any log group from being created. Providing pipeProps.logConfiguration will controls all aspects of logging and any construct provided log configuration is disabled. If pipeProps.logConfiguration is provided then specifying this or pipeLogProps is an error.
        :param pipe_log_props: Default behavior is for the this construct to create a new CloudWatch Logs log group for the pipe. These props are used to override defaults set by AWS or this construct. If there are concerns about the cost of log storage, this is where a client can specify a shorter retention duration (in days)
        :param pipe_props: Optional customer provided settings for the EventBridge pipe. source, target and roleArn are set by the construct and cannot be overriden. The construct will generate default sourceParameters, targetParameters and logConfiguration that can be overriden by populating those values in these props. If the client wants to implement enrichment or a filter, this is where that information can be provided. Any other props can be freely overridden. To control aspects of the Streams feed (e.g. batchSize, startingPosition), do that here under sourceParameters.dynamoDbStreamParameters.
        :param sqs_dlq_queue_props: Optional user provided properties for the SQS dead letter queue. Default: - Default props are used
        :param state_machine_props: User provided props for the sfn.StateMachine. This or existingStateMachine is required.

        :access: public
        :summary: Constructs a new instance of the DynamoDBStreamsToPipesToStepfunctions class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__da63fc90b96e824cc2b5f32e45c97ba7f1076efbc492bd8ce92b253d0a95f5ac)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = DynamoDBStreamsToPipesToStepfunctionsProps(
            create_cloud_watch_alarms=create_cloud_watch_alarms,
            deploy_sqs_dlq_queue=deploy_sqs_dlq_queue,
            dynamo_table_props=dynamo_table_props,
            enrichment_function=enrichment_function,
            enrichment_state_machine=enrichment_state_machine,
            existing_state_machine_obj=existing_state_machine_obj,
            existing_table_interface=existing_table_interface,
            log_group_props=log_group_props,
            log_level=log_level,
            pipe_log_props=pipe_log_props,
            pipe_props=pipe_props,
            sqs_dlq_queue_props=sqs_dlq_queue_props,
            state_machine_props=state_machine_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="dynamoTableInterface")
    def dynamo_table_interface(self) -> _aws_cdk_aws_dynamodb_ceddda9d.ITable:
        return typing.cast(_aws_cdk_aws_dynamodb_ceddda9d.ITable, jsii.get(self, "dynamoTableInterface"))

    @builtins.property
    @jsii.member(jsii_name="pipe")
    def pipe(self) -> _aws_cdk_aws_pipes_ceddda9d.CfnPipe:
        return typing.cast(_aws_cdk_aws_pipes_ceddda9d.CfnPipe, jsii.get(self, "pipe"))

    @builtins.property
    @jsii.member(jsii_name="pipeRole")
    def pipe_role(self) -> _aws_cdk_aws_iam_ceddda9d.Role:
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Role, jsii.get(self, "pipeRole"))

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
    @jsii.member(jsii_name="dlq")
    def dlq(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue]:
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue], jsii.get(self, "dlq"))

    @builtins.property
    @jsii.member(jsii_name="dynamoTable")
    def dynamo_table(self) -> typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table]:
        return typing.cast(typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table], jsii.get(self, "dynamoTable"))

    @builtins.property
    @jsii.member(jsii_name="stateMachineLogGroup")
    def state_machine_log_group(
        self,
    ) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup]:
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup], jsii.get(self, "stateMachineLogGroup"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-dynamodbstreams-pipes-stepfunctions.DynamoDBStreamsToPipesToStepfunctionsProps",
    jsii_struct_bases=[],
    name_mapping={
        "create_cloud_watch_alarms": "createCloudWatchAlarms",
        "deploy_sqs_dlq_queue": "deploySqsDlqQueue",
        "dynamo_table_props": "dynamoTableProps",
        "enrichment_function": "enrichmentFunction",
        "enrichment_state_machine": "enrichmentStateMachine",
        "existing_state_machine_obj": "existingStateMachineObj",
        "existing_table_interface": "existingTableInterface",
        "log_group_props": "logGroupProps",
        "log_level": "logLevel",
        "pipe_log_props": "pipeLogProps",
        "pipe_props": "pipeProps",
        "sqs_dlq_queue_props": "sqsDlqQueueProps",
        "state_machine_props": "stateMachineProps",
    },
)
class DynamoDBStreamsToPipesToStepfunctionsProps:
    def __init__(
        self,
        *,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        deploy_sqs_dlq_queue: typing.Optional[builtins.bool] = None,
        dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
        enrichment_function: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        enrichment_state_machine: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
        existing_state_machine_obj: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
        existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_level: typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.PipesLogLevel] = None,
        pipe_log_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        pipe_props: typing.Any = None,
        sqs_dlq_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        state_machine_props: typing.Optional[typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. default = true
        :param deploy_sqs_dlq_queue: Whether to deploy a SQS dead letter queue when a data record reaches the Maximum Retry Attempts or Maximum Record Age, its metadata like shard ID and stream ARN will be sent to an SQS queue. The construct will create and configure the DLQ with a default maximumRetryAttempts of 2. To customize this, you should set maximumRecordAgeInSeconds and/or maximumRetryAttempts attempts in pipeProps.sourceParameters.dynamoDbStreamParameters. Default - deploy queue, MaximumRetryAttempts is set to 3, and maximumRecordAge is left to default (-1, or infinite) Default: - true.
        :param dynamo_table_props: Optional user provided props to override the default props for the DynamoDB Table. Providing both this and ``existingTableInterface`` is an error. Default: - Partition key ID: string
        :param enrichment_function: Optional - Lambda function that the construct will configure to be called to enrich the message between source and target. The construct will configure the pipe IAM role to allow invoking the function (but will not affect the IArole assigned to the function). Specifying both this and enrichmentStateMachine is an error. Default - undefined
        :param enrichment_state_machine: Optional - Step Functions state machine that the construct will configure to be called to enrich the message between source and target. The construct will configure the pipe IAM role to allow executing the state machine (but will not affect the IAM role assigned to the state machine). Specifying both this and enrichmentStateMachine is an error. Enrichment is invoked synchronously, so this must be an EXPRESS state machin. Default - undefined
        :param existing_state_machine_obj: Optional existing state machine to incorporate into the construct.
        :param existing_table_interface: Optional - existing DynamoDB table, providing both this and ``dynamoTableProps`` will cause an error. Default: - None
        :param log_group_props: Optional user provided props to override the default props for for the CloudWatchLogs LogGroup.
        :param log_level: Threshold for what messages the new pipe sends to the log, PipesLogLevel.OFF, PipesLogLevel.ERROR, PipesLogLevel.INFO, PipesLogLevel.TRACE. The default is INFO. Setting the level to OFF will prevent any log group from being created. Providing pipeProps.logConfiguration will controls all aspects of logging and any construct provided log configuration is disabled. If pipeProps.logConfiguration is provided then specifying this or pipeLogProps is an error.
        :param pipe_log_props: Default behavior is for the this construct to create a new CloudWatch Logs log group for the pipe. These props are used to override defaults set by AWS or this construct. If there are concerns about the cost of log storage, this is where a client can specify a shorter retention duration (in days)
        :param pipe_props: Optional customer provided settings for the EventBridge pipe. source, target and roleArn are set by the construct and cannot be overriden. The construct will generate default sourceParameters, targetParameters and logConfiguration that can be overriden by populating those values in these props. If the client wants to implement enrichment or a filter, this is where that information can be provided. Any other props can be freely overridden. To control aspects of the Streams feed (e.g. batchSize, startingPosition), do that here under sourceParameters.dynamoDbStreamParameters.
        :param sqs_dlq_queue_props: Optional user provided properties for the SQS dead letter queue. Default: - Default props are used
        :param state_machine_props: User provided props for the sfn.StateMachine. This or existingStateMachine is required.
        '''
        if isinstance(dynamo_table_props, dict):
            dynamo_table_props = _aws_cdk_aws_dynamodb_ceddda9d.TableProps(**dynamo_table_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if isinstance(pipe_log_props, dict):
            pipe_log_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**pipe_log_props)
        if isinstance(sqs_dlq_queue_props, dict):
            sqs_dlq_queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**sqs_dlq_queue_props)
        if isinstance(state_machine_props, dict):
            state_machine_props = _aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps(**state_machine_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__baa7c9f98f5295187f469d3c73109aef618163bfccf1eaa6b521f6483f92c07b)
            check_type(argname="argument create_cloud_watch_alarms", value=create_cloud_watch_alarms, expected_type=type_hints["create_cloud_watch_alarms"])
            check_type(argname="argument deploy_sqs_dlq_queue", value=deploy_sqs_dlq_queue, expected_type=type_hints["deploy_sqs_dlq_queue"])
            check_type(argname="argument dynamo_table_props", value=dynamo_table_props, expected_type=type_hints["dynamo_table_props"])
            check_type(argname="argument enrichment_function", value=enrichment_function, expected_type=type_hints["enrichment_function"])
            check_type(argname="argument enrichment_state_machine", value=enrichment_state_machine, expected_type=type_hints["enrichment_state_machine"])
            check_type(argname="argument existing_state_machine_obj", value=existing_state_machine_obj, expected_type=type_hints["existing_state_machine_obj"])
            check_type(argname="argument existing_table_interface", value=existing_table_interface, expected_type=type_hints["existing_table_interface"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
            check_type(argname="argument log_level", value=log_level, expected_type=type_hints["log_level"])
            check_type(argname="argument pipe_log_props", value=pipe_log_props, expected_type=type_hints["pipe_log_props"])
            check_type(argname="argument pipe_props", value=pipe_props, expected_type=type_hints["pipe_props"])
            check_type(argname="argument sqs_dlq_queue_props", value=sqs_dlq_queue_props, expected_type=type_hints["sqs_dlq_queue_props"])
            check_type(argname="argument state_machine_props", value=state_machine_props, expected_type=type_hints["state_machine_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create_cloud_watch_alarms is not None:
            self._values["create_cloud_watch_alarms"] = create_cloud_watch_alarms
        if deploy_sqs_dlq_queue is not None:
            self._values["deploy_sqs_dlq_queue"] = deploy_sqs_dlq_queue
        if dynamo_table_props is not None:
            self._values["dynamo_table_props"] = dynamo_table_props
        if enrichment_function is not None:
            self._values["enrichment_function"] = enrichment_function
        if enrichment_state_machine is not None:
            self._values["enrichment_state_machine"] = enrichment_state_machine
        if existing_state_machine_obj is not None:
            self._values["existing_state_machine_obj"] = existing_state_machine_obj
        if existing_table_interface is not None:
            self._values["existing_table_interface"] = existing_table_interface
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props
        if log_level is not None:
            self._values["log_level"] = log_level
        if pipe_log_props is not None:
            self._values["pipe_log_props"] = pipe_log_props
        if pipe_props is not None:
            self._values["pipe_props"] = pipe_props
        if sqs_dlq_queue_props is not None:
            self._values["sqs_dlq_queue_props"] = sqs_dlq_queue_props
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
    def deploy_sqs_dlq_queue(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a SQS dead letter queue when a data record reaches the Maximum Retry Attempts or Maximum Record Age, its metadata like shard ID and stream ARN will be sent to an SQS queue.

        The construct will create and configure the DLQ
        with a default maximumRetryAttempts of 2. To customize this, you should set maximumRecordAgeInSeconds and/or
        maximumRetryAttempts attempts in pipeProps.sourceParameters.dynamoDbStreamParameters. Default - deploy queue,
        MaximumRetryAttempts is set to 3, and maximumRecordAge is left to default (-1, or infinite)

        :default: - true.
        '''
        result = self._values.get("deploy_sqs_dlq_queue")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def dynamo_table_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.TableProps]:
        '''Optional user provided props to override the default props for the DynamoDB Table.

        Providing both this and
        ``existingTableInterface`` is an error.

        :default: - Partition key ID: string
        '''
        result = self._values.get("dynamo_table_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.TableProps], result)

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
    def existing_state_machine_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine]:
        '''Optional existing state machine to incorporate into the construct.'''
        result = self._values.get("existing_state_machine_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine], result)

    @builtins.property
    def existing_table_interface(
        self,
    ) -> typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable]:
        '''Optional - existing DynamoDB table, providing both this and ``dynamoTableProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_table_interface")
        return typing.cast(typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable], result)

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
        can be freely overridden. To control aspects of the Streams feed (e.g. batchSize, startingPosition),
        do that here under sourceParameters.dynamoDbStreamParameters.
        '''
        result = self._values.get("pipe_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def sqs_dlq_queue_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''Optional user provided properties for the SQS dead letter queue.

        :default: - Default props are used
        '''
        result = self._values.get("sqs_dlq_queue_props")
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
        return "DynamoDBStreamsToPipesToStepfunctionsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(
    jsii_type="@aws-solutions-constructs/aws-dynamodbstreams-pipes-stepfunctions.PipesLogLevel"
)
class PipesLogLevel(enum.Enum):
    OFF = "OFF"
    TRACE = "TRACE"
    INFO = "INFO"
    ERROR = "ERROR"


__all__ = [
    "DynamoDBStreamsToPipesToStepfunctions",
    "DynamoDBStreamsToPipesToStepfunctionsProps",
    "PipesLogLevel",
]

publication.publish()

def _typecheckingstub__da63fc90b96e824cc2b5f32e45c97ba7f1076efbc492bd8ce92b253d0a95f5ac(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    deploy_sqs_dlq_queue: typing.Optional[builtins.bool] = None,
    dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
    enrichment_function: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    enrichment_state_machine: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
    existing_state_machine_obj: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
    existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_level: typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.PipesLogLevel] = None,
    pipe_log_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    pipe_props: typing.Any = None,
    sqs_dlq_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    state_machine_props: typing.Optional[typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__baa7c9f98f5295187f469d3c73109aef618163bfccf1eaa6b521f6483f92c07b(
    *,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    deploy_sqs_dlq_queue: typing.Optional[builtins.bool] = None,
    dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
    enrichment_function: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    enrichment_state_machine: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
    existing_state_machine_obj: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine] = None,
    existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_level: typing.Optional[_aws_solutions_constructs_core_ac4f6ab9.PipesLogLevel] = None,
    pipe_log_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    pipe_props: typing.Any = None,
    sqs_dlq_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    state_machine_props: typing.Optional[typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
