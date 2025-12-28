r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-s3-sns/README.adoc)
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

import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import aws_cdk.aws_sns as _aws_cdk_aws_sns_ceddda9d
import constructs as _constructs_77d1e7e8


class S3ToSns(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-s3-sns.S3ToSns",
):
    '''
    :summary: The S3ToSns class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket] = None,
        existing_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        existing_topic_obj: typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic] = None,
        logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_s3_access_logs: typing.Optional[builtins.bool] = None,
        s3_event_filters: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_s3_ceddda9d.NotificationKeyFilter, typing.Dict[builtins.str, typing.Any]]]] = None,
        s3_event_types: typing.Optional[typing.Sequence[_aws_cdk_aws_s3_ceddda9d.EventType]] = None,
        topic_props: typing.Optional[typing.Union[_aws_cdk_aws_sns_ceddda9d.TopicProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param bucket_props: Optional user provided props to override the default props for the S3 Bucket. Default: - Default props are used
        :param enable_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the topic is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: topicProps.masterKey, encryptionKey or encryptionKeyProps. Default: - False if topicProps.masterKey, encryptionKey, and encryptionKeyProps are all undefined.
        :param encryption_key: An optional, imported encryption key to encrypt the SNS Topic with. Default: - None
        :param encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SNS Topic with. Default: - None
        :param existing_bucket_obj: Optional - existing instance of S3 Bucket. If this is provided, then also providing bucketProps is an error. Default: - None
        :param existing_topic_encryption_key: If an existing topic is provided in the ``existingTopicObj`` property, and that topic is encrypted with a Customer-Managed KMS key, this property also needs to be set with same key. Default: - None
        :param existing_topic_obj: An optional, existing SNS topic to be used instead of the default topic. Providing both this and ``topicProps`` will cause an error. Optional - existing instance of SNS topic object, providing both this and ``topicProps`` will cause an error. If the SNS Topic is encrypted with a Customer-Managed KMS Key, the key must be specified in the ``existingTopicEncryptionKey`` property. Default: - Default props are used
        :param logging_bucket_props: Optional user provided props to override the default props for the S3 Logging Bucket. Default: - Default props are used
        :param log_s3_access_logs: Whether to turn on Access Logs for the S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param s3_event_filters: S3 object key filter rules to determine which objects trigger this event. Default: - If not specified no filter rules will be applied.
        :param s3_event_types: The S3 event types that will trigger the notification. Default: - If not specified the s3.EventType.OBJECT_CREATED event will trigger the notification.
        :param topic_props: Optional - user provided properties to override the default properties for the SNS topic. Providing both this and ``existingTopicObj`` is an error. Default: - Default props are used

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the S3ToSns class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b99c77422c893c6fa5655a87b4c9c2e30b782cc960cda222c26f427eefb1ab53)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = S3ToSnsProps(
            bucket_props=bucket_props,
            enable_encryption_with_customer_managed_key=enable_encryption_with_customer_managed_key,
            encryption_key=encryption_key,
            encryption_key_props=encryption_key_props,
            existing_bucket_obj=existing_bucket_obj,
            existing_topic_encryption_key=existing_topic_encryption_key,
            existing_topic_obj=existing_topic_obj,
            logging_bucket_props=logging_bucket_props,
            log_s3_access_logs=log_s3_access_logs,
            s3_event_filters=s3_event_filters,
            s3_event_types=s3_event_types,
            topic_props=topic_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="s3BucketInterface")
    def s3_bucket_interface(self) -> _aws_cdk_aws_s3_ceddda9d.IBucket:
        return typing.cast(_aws_cdk_aws_s3_ceddda9d.IBucket, jsii.get(self, "s3BucketInterface"))

    @builtins.property
    @jsii.member(jsii_name="snsTopic")
    def sns_topic(self) -> _aws_cdk_aws_sns_ceddda9d.Topic:
        return typing.cast(_aws_cdk_aws_sns_ceddda9d.Topic, jsii.get(self, "snsTopic"))

    @builtins.property
    @jsii.member(jsii_name="encryptionKey")
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "encryptionKey"))

    @builtins.property
    @jsii.member(jsii_name="s3Bucket")
    def s3_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "s3Bucket"))

    @builtins.property
    @jsii.member(jsii_name="s3LoggingBucket")
    def s3_logging_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "s3LoggingBucket"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-s3-sns.S3ToSnsProps",
    jsii_struct_bases=[],
    name_mapping={
        "bucket_props": "bucketProps",
        "enable_encryption_with_customer_managed_key": "enableEncryptionWithCustomerManagedKey",
        "encryption_key": "encryptionKey",
        "encryption_key_props": "encryptionKeyProps",
        "existing_bucket_obj": "existingBucketObj",
        "existing_topic_encryption_key": "existingTopicEncryptionKey",
        "existing_topic_obj": "existingTopicObj",
        "logging_bucket_props": "loggingBucketProps",
        "log_s3_access_logs": "logS3AccessLogs",
        "s3_event_filters": "s3EventFilters",
        "s3_event_types": "s3EventTypes",
        "topic_props": "topicProps",
    },
)
class S3ToSnsProps:
    def __init__(
        self,
        *,
        bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket] = None,
        existing_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        existing_topic_obj: typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic] = None,
        logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_s3_access_logs: typing.Optional[builtins.bool] = None,
        s3_event_filters: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_s3_ceddda9d.NotificationKeyFilter, typing.Dict[builtins.str, typing.Any]]]] = None,
        s3_event_types: typing.Optional[typing.Sequence[_aws_cdk_aws_s3_ceddda9d.EventType]] = None,
        topic_props: typing.Optional[typing.Union[_aws_cdk_aws_sns_ceddda9d.TopicProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param bucket_props: Optional user provided props to override the default props for the S3 Bucket. Default: - Default props are used
        :param enable_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the topic is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: topicProps.masterKey, encryptionKey or encryptionKeyProps. Default: - False if topicProps.masterKey, encryptionKey, and encryptionKeyProps are all undefined.
        :param encryption_key: An optional, imported encryption key to encrypt the SNS Topic with. Default: - None
        :param encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SNS Topic with. Default: - None
        :param existing_bucket_obj: Optional - existing instance of S3 Bucket. If this is provided, then also providing bucketProps is an error. Default: - None
        :param existing_topic_encryption_key: If an existing topic is provided in the ``existingTopicObj`` property, and that topic is encrypted with a Customer-Managed KMS key, this property also needs to be set with same key. Default: - None
        :param existing_topic_obj: An optional, existing SNS topic to be used instead of the default topic. Providing both this and ``topicProps`` will cause an error. Optional - existing instance of SNS topic object, providing both this and ``topicProps`` will cause an error. If the SNS Topic is encrypted with a Customer-Managed KMS Key, the key must be specified in the ``existingTopicEncryptionKey`` property. Default: - Default props are used
        :param logging_bucket_props: Optional user provided props to override the default props for the S3 Logging Bucket. Default: - Default props are used
        :param log_s3_access_logs: Whether to turn on Access Logs for the S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param s3_event_filters: S3 object key filter rules to determine which objects trigger this event. Default: - If not specified no filter rules will be applied.
        :param s3_event_types: The S3 event types that will trigger the notification. Default: - If not specified the s3.EventType.OBJECT_CREATED event will trigger the notification.
        :param topic_props: Optional - user provided properties to override the default properties for the SNS topic. Providing both this and ``existingTopicObj`` is an error. Default: - Default props are used

        :summary: The properties for the S3ToSns class.
        '''
        if isinstance(bucket_props, dict):
            bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**bucket_props)
        if isinstance(encryption_key_props, dict):
            encryption_key_props = _aws_cdk_aws_kms_ceddda9d.KeyProps(**encryption_key_props)
        if isinstance(logging_bucket_props, dict):
            logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**logging_bucket_props)
        if isinstance(topic_props, dict):
            topic_props = _aws_cdk_aws_sns_ceddda9d.TopicProps(**topic_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cdc9c4755ec4db8685e2f828ed0068b2d1401be1d5628b29f1e7abfe03efb54e)
            check_type(argname="argument bucket_props", value=bucket_props, expected_type=type_hints["bucket_props"])
            check_type(argname="argument enable_encryption_with_customer_managed_key", value=enable_encryption_with_customer_managed_key, expected_type=type_hints["enable_encryption_with_customer_managed_key"])
            check_type(argname="argument encryption_key", value=encryption_key, expected_type=type_hints["encryption_key"])
            check_type(argname="argument encryption_key_props", value=encryption_key_props, expected_type=type_hints["encryption_key_props"])
            check_type(argname="argument existing_bucket_obj", value=existing_bucket_obj, expected_type=type_hints["existing_bucket_obj"])
            check_type(argname="argument existing_topic_encryption_key", value=existing_topic_encryption_key, expected_type=type_hints["existing_topic_encryption_key"])
            check_type(argname="argument existing_topic_obj", value=existing_topic_obj, expected_type=type_hints["existing_topic_obj"])
            check_type(argname="argument logging_bucket_props", value=logging_bucket_props, expected_type=type_hints["logging_bucket_props"])
            check_type(argname="argument log_s3_access_logs", value=log_s3_access_logs, expected_type=type_hints["log_s3_access_logs"])
            check_type(argname="argument s3_event_filters", value=s3_event_filters, expected_type=type_hints["s3_event_filters"])
            check_type(argname="argument s3_event_types", value=s3_event_types, expected_type=type_hints["s3_event_types"])
            check_type(argname="argument topic_props", value=topic_props, expected_type=type_hints["topic_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if bucket_props is not None:
            self._values["bucket_props"] = bucket_props
        if enable_encryption_with_customer_managed_key is not None:
            self._values["enable_encryption_with_customer_managed_key"] = enable_encryption_with_customer_managed_key
        if encryption_key is not None:
            self._values["encryption_key"] = encryption_key
        if encryption_key_props is not None:
            self._values["encryption_key_props"] = encryption_key_props
        if existing_bucket_obj is not None:
            self._values["existing_bucket_obj"] = existing_bucket_obj
        if existing_topic_encryption_key is not None:
            self._values["existing_topic_encryption_key"] = existing_topic_encryption_key
        if existing_topic_obj is not None:
            self._values["existing_topic_obj"] = existing_topic_obj
        if logging_bucket_props is not None:
            self._values["logging_bucket_props"] = logging_bucket_props
        if log_s3_access_logs is not None:
            self._values["log_s3_access_logs"] = log_s3_access_logs
        if s3_event_filters is not None:
            self._values["s3_event_filters"] = s3_event_filters
        if s3_event_types is not None:
            self._values["s3_event_types"] = s3_event_types
        if topic_props is not None:
            self._values["topic_props"] = topic_props

    @builtins.property
    def bucket_props(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the S3 Bucket.

        :default: - Default props are used
        '''
        result = self._values.get("bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def enable_encryption_with_customer_managed_key(
        self,
    ) -> typing.Optional[builtins.bool]:
        '''If no key is provided, this flag determines whether the topic is encrypted with a new CMK or an AWS managed key.

        This flag is ignored if any of the following are defined: topicProps.masterKey, encryptionKey or encryptionKeyProps.

        :default: - False if topicProps.masterKey, encryptionKey, and encryptionKeyProps are all undefined.
        '''
        result = self._values.get("enable_encryption_with_customer_managed_key")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key]:
        '''An optional, imported encryption key to encrypt the SNS Topic with.

        :default: - None
        '''
        result = self._values.get("encryption_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def encryption_key_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps]:
        '''Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SNS Topic with.

        :default: - None
        '''
        result = self._values.get("encryption_key_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps], result)

    @builtins.property
    def existing_bucket_obj(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        '''Optional - existing instance of S3 Bucket.

        If this is provided, then also providing bucketProps is an error.

        :default: - None
        '''
        result = self._values.get("existing_bucket_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], result)

    @builtins.property
    def existing_topic_encryption_key(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key]:
        '''If an existing topic is provided in the ``existingTopicObj`` property, and that topic is encrypted with a Customer-Managed KMS key, this property also needs to be set with same key.

        :default: - None
        '''
        result = self._values.get("existing_topic_encryption_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def existing_topic_obj(self) -> typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic]:
        '''An optional, existing SNS topic to be used instead of the default topic.

        Providing both this and ``topicProps`` will cause an error.
        Optional - existing instance of SNS topic object, providing both this and ``topicProps`` will cause an error. If the SNS Topic is encrypted
        with a Customer-Managed KMS Key, the key must be specified in the ``existingTopicEncryptionKey`` property.

        :default: - Default props are used
        '''
        result = self._values.get("existing_topic_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic], result)

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
    def s3_event_filters(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_s3_ceddda9d.NotificationKeyFilter]]:
        '''S3 object key filter rules to determine which objects trigger this event.

        :default: - If not specified no filter rules will be applied.
        '''
        result = self._values.get("s3_event_filters")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_s3_ceddda9d.NotificationKeyFilter]], result)

    @builtins.property
    def s3_event_types(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_s3_ceddda9d.EventType]]:
        '''The S3 event types that will trigger the notification.

        :default: - If not specified the s3.EventType.OBJECT_CREATED event will trigger the notification.
        '''
        result = self._values.get("s3_event_types")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_s3_ceddda9d.EventType]], result)

    @builtins.property
    def topic_props(self) -> typing.Optional[_aws_cdk_aws_sns_ceddda9d.TopicProps]:
        '''Optional - user provided properties to override the default properties for the SNS topic.

        Providing both this and
        ``existingTopicObj`` is an error.

        :default: - Default props are used
        '''
        result = self._values.get("topic_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sns_ceddda9d.TopicProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "S3ToSnsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "S3ToSns",
    "S3ToSnsProps",
]

publication.publish()

def _typecheckingstub__b99c77422c893c6fa5655a87b4c9c2e30b782cc960cda222c26f427eefb1ab53(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket] = None,
    existing_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    existing_topic_obj: typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic] = None,
    logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_s3_access_logs: typing.Optional[builtins.bool] = None,
    s3_event_filters: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_s3_ceddda9d.NotificationKeyFilter, typing.Dict[builtins.str, typing.Any]]]] = None,
    s3_event_types: typing.Optional[typing.Sequence[_aws_cdk_aws_s3_ceddda9d.EventType]] = None,
    topic_props: typing.Optional[typing.Union[_aws_cdk_aws_sns_ceddda9d.TopicProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cdc9c4755ec4db8685e2f828ed0068b2d1401be1d5628b29f1e7abfe03efb54e(
    *,
    bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket] = None,
    existing_topic_encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    existing_topic_obj: typing.Optional[_aws_cdk_aws_sns_ceddda9d.Topic] = None,
    logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_s3_access_logs: typing.Optional[builtins.bool] = None,
    s3_event_filters: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_s3_ceddda9d.NotificationKeyFilter, typing.Dict[builtins.str, typing.Any]]]] = None,
    s3_event_types: typing.Optional[typing.Sequence[_aws_cdk_aws_s3_ceddda9d.EventType]] = None,
    topic_props: typing.Optional[typing.Union[_aws_cdk_aws_sns_ceddda9d.TopicProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
