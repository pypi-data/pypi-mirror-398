r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-iot-s3/README.adoc)
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

import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_iot as _aws_cdk_aws_iot_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import constructs as _constructs_77d1e7e8


class IotToS3(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-iot-s3.IotToS3",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        iot_topic_rule_props: typing.Union[_aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps, typing.Dict[builtins.str, typing.Any]],
        bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_bucket_interface: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_s3_access_logs: typing.Optional[builtins.bool] = None,
        s3_key: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param iot_topic_rule_props: User provided CfnTopicRuleProps to override the defaults. Default: - Default props are used. S3ActionProperty with S3 Key '${topic()}/${timestamp()}' is used.
        :param bucket_props: User provided props to override the default props for the S3 Bucket. Default: - Default props are used.
        :param existing_bucket_interface: Existing S3 Bucket interface, providing both this and ``bucketProps`` will cause an error. Default: - None
        :param logging_bucket_props: Optional user provided props to override the default props for the S3 Logging Bucket. Default: - Default props are used
        :param log_s3_access_logs: Whether to turn on Access Logs for the S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param s3_key: Optional user provided value to override the default S3Key for IoTRule S3 Action. Default: - Default value '${topic()}/${timestamp()}' is used

        :access: public
        :summary: Constructs a new instance of the IotToSqs class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__309b13fbc5013f774a12aeeeb762ce28de1108a9e1e13e31303391bd5d07bfb3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = IotToS3Props(
            iot_topic_rule_props=iot_topic_rule_props,
            bucket_props=bucket_props,
            existing_bucket_interface=existing_bucket_interface,
            logging_bucket_props=logging_bucket_props,
            log_s3_access_logs=log_s3_access_logs,
            s3_key=s3_key,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="iotActionsRole")
    def iot_actions_role(self) -> _aws_cdk_aws_iam_ceddda9d.Role:
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Role, jsii.get(self, "iotActionsRole"))

    @builtins.property
    @jsii.member(jsii_name="iotTopicRule")
    def iot_topic_rule(self) -> _aws_cdk_aws_iot_ceddda9d.CfnTopicRule:
        return typing.cast(_aws_cdk_aws_iot_ceddda9d.CfnTopicRule, jsii.get(self, "iotTopicRule"))

    @builtins.property
    @jsii.member(jsii_name="s3BucketInterface")
    def s3_bucket_interface(self) -> _aws_cdk_aws_s3_ceddda9d.IBucket:
        return typing.cast(_aws_cdk_aws_s3_ceddda9d.IBucket, jsii.get(self, "s3BucketInterface"))

    @builtins.property
    @jsii.member(jsii_name="s3Bucket")
    def s3_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "s3Bucket"))

    @builtins.property
    @jsii.member(jsii_name="s3LoggingBucket")
    def s3_logging_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "s3LoggingBucket"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-iot-s3.IotToS3Props",
    jsii_struct_bases=[],
    name_mapping={
        "iot_topic_rule_props": "iotTopicRuleProps",
        "bucket_props": "bucketProps",
        "existing_bucket_interface": "existingBucketInterface",
        "logging_bucket_props": "loggingBucketProps",
        "log_s3_access_logs": "logS3AccessLogs",
        "s3_key": "s3Key",
    },
)
class IotToS3Props:
    def __init__(
        self,
        *,
        iot_topic_rule_props: typing.Union[_aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps, typing.Dict[builtins.str, typing.Any]],
        bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_bucket_interface: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_s3_access_logs: typing.Optional[builtins.bool] = None,
        s3_key: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param iot_topic_rule_props: User provided CfnTopicRuleProps to override the defaults. Default: - Default props are used. S3ActionProperty with S3 Key '${topic()}/${timestamp()}' is used.
        :param bucket_props: User provided props to override the default props for the S3 Bucket. Default: - Default props are used.
        :param existing_bucket_interface: Existing S3 Bucket interface, providing both this and ``bucketProps`` will cause an error. Default: - None
        :param logging_bucket_props: Optional user provided props to override the default props for the S3 Logging Bucket. Default: - Default props are used
        :param log_s3_access_logs: Whether to turn on Access Logs for the S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param s3_key: Optional user provided value to override the default S3Key for IoTRule S3 Action. Default: - Default value '${topic()}/${timestamp()}' is used

        :summary: The properties for the IotToS3 class.
        '''
        if isinstance(iot_topic_rule_props, dict):
            iot_topic_rule_props = _aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps(**iot_topic_rule_props)
        if isinstance(bucket_props, dict):
            bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**bucket_props)
        if isinstance(logging_bucket_props, dict):
            logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**logging_bucket_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d3012513e464959c0a3c43e16f684aabcfd5eac021081cdba86321999d6acde7)
            check_type(argname="argument iot_topic_rule_props", value=iot_topic_rule_props, expected_type=type_hints["iot_topic_rule_props"])
            check_type(argname="argument bucket_props", value=bucket_props, expected_type=type_hints["bucket_props"])
            check_type(argname="argument existing_bucket_interface", value=existing_bucket_interface, expected_type=type_hints["existing_bucket_interface"])
            check_type(argname="argument logging_bucket_props", value=logging_bucket_props, expected_type=type_hints["logging_bucket_props"])
            check_type(argname="argument log_s3_access_logs", value=log_s3_access_logs, expected_type=type_hints["log_s3_access_logs"])
            check_type(argname="argument s3_key", value=s3_key, expected_type=type_hints["s3_key"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "iot_topic_rule_props": iot_topic_rule_props,
        }
        if bucket_props is not None:
            self._values["bucket_props"] = bucket_props
        if existing_bucket_interface is not None:
            self._values["existing_bucket_interface"] = existing_bucket_interface
        if logging_bucket_props is not None:
            self._values["logging_bucket_props"] = logging_bucket_props
        if log_s3_access_logs is not None:
            self._values["log_s3_access_logs"] = log_s3_access_logs
        if s3_key is not None:
            self._values["s3_key"] = s3_key

    @builtins.property
    def iot_topic_rule_props(self) -> _aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps:
        '''User provided CfnTopicRuleProps to override the defaults.

        :default: - Default props are used. S3ActionProperty with S3 Key '${topic()}/${timestamp()}' is used.
        '''
        result = self._values.get("iot_topic_rule_props")
        assert result is not None, "Required property 'iot_topic_rule_props' is missing"
        return typing.cast(_aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps, result)

    @builtins.property
    def bucket_props(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''User provided props to override the default props for the S3 Bucket.

        :default: - Default props are used.
        '''
        result = self._values.get("bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def existing_bucket_interface(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        '''Existing S3 Bucket interface, providing both this and ``bucketProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_bucket_interface")
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
    def log_s3_access_logs(self) -> typing.Optional[builtins.bool]:
        '''Whether to turn on Access Logs for the S3 bucket with the associated storage costs.

        Enabling Access Logging is a best practice.

        :default: - true
        '''
        result = self._values.get("log_s3_access_logs")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def s3_key(self) -> typing.Optional[builtins.str]:
        '''Optional user provided value to override the default S3Key for IoTRule S3 Action.

        :default: - Default value '${topic()}/${timestamp()}' is used
        '''
        result = self._values.get("s3_key")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IotToS3Props(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "IotToS3",
    "IotToS3Props",
]

publication.publish()

def _typecheckingstub__309b13fbc5013f774a12aeeeb762ce28de1108a9e1e13e31303391bd5d07bfb3(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    iot_topic_rule_props: typing.Union[_aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps, typing.Dict[builtins.str, typing.Any]],
    bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_bucket_interface: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_s3_access_logs: typing.Optional[builtins.bool] = None,
    s3_key: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d3012513e464959c0a3c43e16f684aabcfd5eac021081cdba86321999d6acde7(
    *,
    iot_topic_rule_props: typing.Union[_aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps, typing.Dict[builtins.str, typing.Any]],
    bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_bucket_interface: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_s3_access_logs: typing.Optional[builtins.bool] = None,
    s3_key: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
