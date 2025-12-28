r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-iot-kinesisfirehose-s3/README.adoc)
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
import aws_cdk.aws_kinesisfirehose as _aws_cdk_aws_kinesisfirehose_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import constructs as _constructs_77d1e7e8


class IotToKinesisFirehoseToS3(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-iot-kinesisfirehose-s3.IotToKinesisFirehoseToS3",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        iot_topic_rule_props: typing.Union[_aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps, typing.Dict[builtins.str, typing.Any]],
        bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        kinesis_firehose_props: typing.Any = None,
        logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_s3_access_logs: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param iot_topic_rule_props: User provided CfnTopicRuleProps to override the defaults. Default: - Default props are used
        :param bucket_props: Optional user provided props to override the default props for the S3 Bucket, providing both this and ``existingBucketObj`` will cause an error. Default: - Default props are used
        :param existing_bucket_obj: Optional - existing instance of S3 Bucket. If this is provided, then also providing bucketProps is an error. Default: - None
        :param kinesis_firehose_props: Optional user provided props to override the default props. Default: - Default props are used
        :param logging_bucket_props: Optional user provided props to override the default props for the S3 Logging Bucket. Default: - Default props are used
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param log_s3_access_logs: Whether to turn on Access Logs for the S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the IotToKinesisFirehoseToS3 class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5ca2d486fca2a9e92559aff5f96b20ad515d136c3cf94df60a63e059854571b5)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = IotToKinesisFirehoseToS3Props(
            iot_topic_rule_props=iot_topic_rule_props,
            bucket_props=bucket_props,
            existing_bucket_obj=existing_bucket_obj,
            kinesis_firehose_props=kinesis_firehose_props,
            logging_bucket_props=logging_bucket_props,
            log_group_props=log_group_props,
            log_s3_access_logs=log_s3_access_logs,
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
    @jsii.member(jsii_name="kinesisFirehose")
    def kinesis_firehose(
        self,
    ) -> _aws_cdk_aws_kinesisfirehose_ceddda9d.CfnDeliveryStream:
        return typing.cast(_aws_cdk_aws_kinesisfirehose_ceddda9d.CfnDeliveryStream, jsii.get(self, "kinesisFirehose"))

    @builtins.property
    @jsii.member(jsii_name="kinesisFirehoseLogGroup")
    def kinesis_firehose_log_group(self) -> _aws_cdk_aws_logs_ceddda9d.LogGroup:
        return typing.cast(_aws_cdk_aws_logs_ceddda9d.LogGroup, jsii.get(self, "kinesisFirehoseLogGroup"))

    @builtins.property
    @jsii.member(jsii_name="kinesisFirehoseRole")
    def kinesis_firehose_role(self) -> _aws_cdk_aws_iam_ceddda9d.Role:
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Role, jsii.get(self, "kinesisFirehoseRole"))

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
    jsii_type="@aws-solutions-constructs/aws-iot-kinesisfirehose-s3.IotToKinesisFirehoseToS3Props",
    jsii_struct_bases=[],
    name_mapping={
        "iot_topic_rule_props": "iotTopicRuleProps",
        "bucket_props": "bucketProps",
        "existing_bucket_obj": "existingBucketObj",
        "kinesis_firehose_props": "kinesisFirehoseProps",
        "logging_bucket_props": "loggingBucketProps",
        "log_group_props": "logGroupProps",
        "log_s3_access_logs": "logS3AccessLogs",
    },
)
class IotToKinesisFirehoseToS3Props:
    def __init__(
        self,
        *,
        iot_topic_rule_props: typing.Union[_aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps, typing.Dict[builtins.str, typing.Any]],
        bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        kinesis_firehose_props: typing.Any = None,
        logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_s3_access_logs: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''
        :param iot_topic_rule_props: User provided CfnTopicRuleProps to override the defaults. Default: - Default props are used
        :param bucket_props: Optional user provided props to override the default props for the S3 Bucket, providing both this and ``existingBucketObj`` will cause an error. Default: - Default props are used
        :param existing_bucket_obj: Optional - existing instance of S3 Bucket. If this is provided, then also providing bucketProps is an error. Default: - None
        :param kinesis_firehose_props: Optional user provided props to override the default props. Default: - Default props are used
        :param logging_bucket_props: Optional user provided props to override the default props for the S3 Logging Bucket. Default: - Default props are used
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param log_s3_access_logs: Whether to turn on Access Logs for the S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true

        :summary: The properties for the IotToKinesisFirehoseToS3 Construct
        '''
        if isinstance(iot_topic_rule_props, dict):
            iot_topic_rule_props = _aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps(**iot_topic_rule_props)
        if isinstance(bucket_props, dict):
            bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**bucket_props)
        if isinstance(logging_bucket_props, dict):
            logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**logging_bucket_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__40546083b5db3b8bee937f75b074c31aac3d1f7f6e3cd4fb3584471c7da08e90)
            check_type(argname="argument iot_topic_rule_props", value=iot_topic_rule_props, expected_type=type_hints["iot_topic_rule_props"])
            check_type(argname="argument bucket_props", value=bucket_props, expected_type=type_hints["bucket_props"])
            check_type(argname="argument existing_bucket_obj", value=existing_bucket_obj, expected_type=type_hints["existing_bucket_obj"])
            check_type(argname="argument kinesis_firehose_props", value=kinesis_firehose_props, expected_type=type_hints["kinesis_firehose_props"])
            check_type(argname="argument logging_bucket_props", value=logging_bucket_props, expected_type=type_hints["logging_bucket_props"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
            check_type(argname="argument log_s3_access_logs", value=log_s3_access_logs, expected_type=type_hints["log_s3_access_logs"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "iot_topic_rule_props": iot_topic_rule_props,
        }
        if bucket_props is not None:
            self._values["bucket_props"] = bucket_props
        if existing_bucket_obj is not None:
            self._values["existing_bucket_obj"] = existing_bucket_obj
        if kinesis_firehose_props is not None:
            self._values["kinesis_firehose_props"] = kinesis_firehose_props
        if logging_bucket_props is not None:
            self._values["logging_bucket_props"] = logging_bucket_props
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props
        if log_s3_access_logs is not None:
            self._values["log_s3_access_logs"] = log_s3_access_logs

    @builtins.property
    def iot_topic_rule_props(self) -> _aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps:
        '''User provided CfnTopicRuleProps to override the defaults.

        :default: - Default props are used
        '''
        result = self._values.get("iot_topic_rule_props")
        assert result is not None, "Required property 'iot_topic_rule_props' is missing"
        return typing.cast(_aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps, result)

    @builtins.property
    def bucket_props(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the S3 Bucket, providing both this and ``existingBucketObj`` will cause an error.

        :default: - Default props are used
        '''
        result = self._values.get("bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def existing_bucket_obj(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        '''Optional - existing instance of S3 Bucket.

        If this is provided, then also providing bucketProps is an error.

        :default: - None
        '''
        result = self._values.get("existing_bucket_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], result)

    @builtins.property
    def kinesis_firehose_props(self) -> typing.Any:
        '''Optional user provided props to override the default props.

        :default: - Default props are used
        '''
        result = self._values.get("kinesis_firehose_props")
        return typing.cast(typing.Any, result)

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
        '''User provided props to override the default props for the CloudWatchLogs LogGroup.

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
        return "IotToKinesisFirehoseToS3Props(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "IotToKinesisFirehoseToS3",
    "IotToKinesisFirehoseToS3Props",
]

publication.publish()

def _typecheckingstub__5ca2d486fca2a9e92559aff5f96b20ad515d136c3cf94df60a63e059854571b5(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    iot_topic_rule_props: typing.Union[_aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps, typing.Dict[builtins.str, typing.Any]],
    bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    kinesis_firehose_props: typing.Any = None,
    logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_s3_access_logs: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__40546083b5db3b8bee937f75b074c31aac3d1f7f6e3cd4fb3584471c7da08e90(
    *,
    iot_topic_rule_props: typing.Union[_aws_cdk_aws_iot_ceddda9d.CfnTopicRuleProps, typing.Dict[builtins.str, typing.Any]],
    bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    kinesis_firehose_props: typing.Any = None,
    logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_s3_access_logs: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass
