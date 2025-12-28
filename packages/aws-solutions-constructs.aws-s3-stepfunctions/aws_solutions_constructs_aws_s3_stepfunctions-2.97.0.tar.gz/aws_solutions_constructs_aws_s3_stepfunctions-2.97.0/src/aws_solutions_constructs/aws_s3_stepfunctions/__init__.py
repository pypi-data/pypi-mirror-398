r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-s3-stepfunctions/README.adoc)
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
import aws_cdk.aws_events as _aws_cdk_aws_events_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import aws_cdk.aws_stepfunctions as _aws_cdk_aws_stepfunctions_ceddda9d
import constructs as _constructs_77d1e7e8


class S3ToStepfunctions(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-s3-stepfunctions.S3ToStepfunctions",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        state_machine_props: typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]],
        bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        deploy_cloud_trail: typing.Optional[builtins.bool] = None,
        event_rule_props: typing.Optional[typing.Union[_aws_cdk_aws_events_ceddda9d.RuleProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_s3_access_logs: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param state_machine_props: User provided StateMachineProps to override the defaults. Default: - None
        :param bucket_props: Optional user provided props to override the default props for the S3 Bucket, providing both this and ``existingBucketObj`` will cause an error. Default: - Default props are used
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. Default: - Alarms are created
        :param deploy_cloud_trail: Whether to deploy a Trail in AWS CloudTrail to log API events in Amazon S3. Default: - true
        :param event_rule_props: Optional user provided eventRuleProps to override the defaults. Default: - None
        :param existing_bucket_obj: Optional - existing instance of S3 Bucket. If this is provided, then also providing bucketProps is an error. The Amazon EventBridge property must be enabled in the existing bucket for the construct to work. Default: - None
        :param logging_bucket_props: Optional user provided props to override the default props for the S3 Logging Bucket. Default: - Default props are used
        :param log_group_props: Optional user provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param log_s3_access_logs: Whether to turn on Access Logs for the S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true

        :access: public
        :summary: Constructs a new instance of the S3ToStepfunctions class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bd75686908c6c6a7c90aeb7241a2eadcf5032086698a0d52c96244f42413eec3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = S3ToStepfunctionsProps(
            state_machine_props=state_machine_props,
            bucket_props=bucket_props,
            create_cloud_watch_alarms=create_cloud_watch_alarms,
            deploy_cloud_trail=deploy_cloud_trail,
            event_rule_props=event_rule_props,
            existing_bucket_obj=existing_bucket_obj,
            logging_bucket_props=logging_bucket_props,
            log_group_props=log_group_props,
            log_s3_access_logs=log_s3_access_logs,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="s3BucketInterface")
    def s3_bucket_interface(self) -> _aws_cdk_aws_s3_ceddda9d.IBucket:
        return typing.cast(_aws_cdk_aws_s3_ceddda9d.IBucket, jsii.get(self, "s3BucketInterface"))

    @builtins.property
    @jsii.member(jsii_name="stateMachine")
    def state_machine(self) -> _aws_cdk_aws_stepfunctions_ceddda9d.StateMachine:
        return typing.cast(_aws_cdk_aws_stepfunctions_ceddda9d.StateMachine, jsii.get(self, "stateMachine"))

    @builtins.property
    @jsii.member(jsii_name="stateMachineLogGroup")
    def state_machine_log_group(self) -> _aws_cdk_aws_logs_ceddda9d.ILogGroup:
        return typing.cast(_aws_cdk_aws_logs_ceddda9d.ILogGroup, jsii.get(self, "stateMachineLogGroup"))

    @builtins.property
    @jsii.member(jsii_name="cloudwatchAlarms")
    def cloudwatch_alarms(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_cloudwatch_ceddda9d.Alarm]]:
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_cloudwatch_ceddda9d.Alarm]], jsii.get(self, "cloudwatchAlarms"))

    @builtins.property
    @jsii.member(jsii_name="s3Bucket")
    def s3_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "s3Bucket"))

    @builtins.property
    @jsii.member(jsii_name="s3LoggingBucket")
    def s3_logging_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "s3LoggingBucket"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-s3-stepfunctions.S3ToStepfunctionsProps",
    jsii_struct_bases=[],
    name_mapping={
        "state_machine_props": "stateMachineProps",
        "bucket_props": "bucketProps",
        "create_cloud_watch_alarms": "createCloudWatchAlarms",
        "deploy_cloud_trail": "deployCloudTrail",
        "event_rule_props": "eventRuleProps",
        "existing_bucket_obj": "existingBucketObj",
        "logging_bucket_props": "loggingBucketProps",
        "log_group_props": "logGroupProps",
        "log_s3_access_logs": "logS3AccessLogs",
    },
)
class S3ToStepfunctionsProps:
    def __init__(
        self,
        *,
        state_machine_props: typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]],
        bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        deploy_cloud_trail: typing.Optional[builtins.bool] = None,
        event_rule_props: typing.Optional[typing.Union[_aws_cdk_aws_events_ceddda9d.RuleProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_s3_access_logs: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''
        :param state_machine_props: User provided StateMachineProps to override the defaults. Default: - None
        :param bucket_props: Optional user provided props to override the default props for the S3 Bucket, providing both this and ``existingBucketObj`` will cause an error. Default: - Default props are used
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. Default: - Alarms are created
        :param deploy_cloud_trail: Whether to deploy a Trail in AWS CloudTrail to log API events in Amazon S3. Default: - true
        :param event_rule_props: Optional user provided eventRuleProps to override the defaults. Default: - None
        :param existing_bucket_obj: Optional - existing instance of S3 Bucket. If this is provided, then also providing bucketProps is an error. The Amazon EventBridge property must be enabled in the existing bucket for the construct to work. Default: - None
        :param logging_bucket_props: Optional user provided props to override the default props for the S3 Logging Bucket. Default: - Default props are used
        :param log_group_props: Optional user provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param log_s3_access_logs: Whether to turn on Access Logs for the S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true

        :summary: The properties for the S3ToStepfunctions Construct
        '''
        if isinstance(state_machine_props, dict):
            state_machine_props = _aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps(**state_machine_props)
        if isinstance(bucket_props, dict):
            bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**bucket_props)
        if isinstance(event_rule_props, dict):
            event_rule_props = _aws_cdk_aws_events_ceddda9d.RuleProps(**event_rule_props)
        if isinstance(logging_bucket_props, dict):
            logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**logging_bucket_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3edf24cb56b383ec8f3f1d2f8b5b271ffc85ec3c7fab6b62d9a77b3a552920c5)
            check_type(argname="argument state_machine_props", value=state_machine_props, expected_type=type_hints["state_machine_props"])
            check_type(argname="argument bucket_props", value=bucket_props, expected_type=type_hints["bucket_props"])
            check_type(argname="argument create_cloud_watch_alarms", value=create_cloud_watch_alarms, expected_type=type_hints["create_cloud_watch_alarms"])
            check_type(argname="argument deploy_cloud_trail", value=deploy_cloud_trail, expected_type=type_hints["deploy_cloud_trail"])
            check_type(argname="argument event_rule_props", value=event_rule_props, expected_type=type_hints["event_rule_props"])
            check_type(argname="argument existing_bucket_obj", value=existing_bucket_obj, expected_type=type_hints["existing_bucket_obj"])
            check_type(argname="argument logging_bucket_props", value=logging_bucket_props, expected_type=type_hints["logging_bucket_props"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
            check_type(argname="argument log_s3_access_logs", value=log_s3_access_logs, expected_type=type_hints["log_s3_access_logs"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "state_machine_props": state_machine_props,
        }
        if bucket_props is not None:
            self._values["bucket_props"] = bucket_props
        if create_cloud_watch_alarms is not None:
            self._values["create_cloud_watch_alarms"] = create_cloud_watch_alarms
        if deploy_cloud_trail is not None:
            self._values["deploy_cloud_trail"] = deploy_cloud_trail
        if event_rule_props is not None:
            self._values["event_rule_props"] = event_rule_props
        if existing_bucket_obj is not None:
            self._values["existing_bucket_obj"] = existing_bucket_obj
        if logging_bucket_props is not None:
            self._values["logging_bucket_props"] = logging_bucket_props
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props
        if log_s3_access_logs is not None:
            self._values["log_s3_access_logs"] = log_s3_access_logs

    @builtins.property
    def state_machine_props(
        self,
    ) -> _aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps:
        '''User provided StateMachineProps to override the defaults.

        :default: - None
        '''
        result = self._values.get("state_machine_props")
        assert result is not None, "Required property 'state_machine_props' is missing"
        return typing.cast(_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, result)

    @builtins.property
    def bucket_props(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the S3 Bucket, providing both this and ``existingBucketObj`` will cause an error.

        :default: - Default props are used
        '''
        result = self._values.get("bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def create_cloud_watch_alarms(self) -> typing.Optional[builtins.bool]:
        '''Whether to create recommended CloudWatch alarms.

        :default: - Alarms are created
        '''
        result = self._values.get("create_cloud_watch_alarms")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def deploy_cloud_trail(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a Trail in AWS CloudTrail to log API events in Amazon S3.

        :default: - true
        '''
        result = self._values.get("deploy_cloud_trail")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def event_rule_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_events_ceddda9d.RuleProps]:
        '''Optional user provided eventRuleProps to override the defaults.

        :default: - None
        '''
        result = self._values.get("event_rule_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_events_ceddda9d.RuleProps], result)

    @builtins.property
    def existing_bucket_obj(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        '''Optional - existing instance of S3 Bucket.

        If this is provided, then also providing bucketProps is an error.
        The Amazon EventBridge property must be enabled in the existing bucket for the construct to work.

        :default: - None
        '''
        result = self._values.get("existing_bucket_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], result)

    @builtins.property
    def logging_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the S3 Logging Bucket.

        :default: - Default props are used
        '''
        result = self._values.get("logging_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def log_group_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps]:
        '''Optional user provided props to override the default props for the CloudWatchLogs LogGroup.

        :default: - Default props are used
        '''
        result = self._values.get("log_group_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps], result)

    @builtins.property
    def log_s3_access_logs(self) -> typing.Optional[builtins.bool]:
        '''Whether to turn on Access Logs for the S3 bucket with the associated storage costs.

        Enabling Access Logging is a best practice.

        :default: - true
        '''
        result = self._values.get("log_s3_access_logs")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "S3ToStepfunctionsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "S3ToStepfunctions",
    "S3ToStepfunctionsProps",
]

publication.publish()

def _typecheckingstub__bd75686908c6c6a7c90aeb7241a2eadcf5032086698a0d52c96244f42413eec3(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    state_machine_props: typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]],
    bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    deploy_cloud_trail: typing.Optional[builtins.bool] = None,
    event_rule_props: typing.Optional[typing.Union[_aws_cdk_aws_events_ceddda9d.RuleProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_s3_access_logs: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3edf24cb56b383ec8f3f1d2f8b5b271ffc85ec3c7fab6b62d9a77b3a552920c5(
    *,
    state_machine_props: typing.Union[_aws_cdk_aws_stepfunctions_ceddda9d.StateMachineProps, typing.Dict[builtins.str, typing.Any]],
    bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    deploy_cloud_trail: typing.Optional[builtins.bool] = None,
    event_rule_props: typing.Optional[typing.Union[_aws_cdk_aws_events_ceddda9d.RuleProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_s3_access_logs: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass
