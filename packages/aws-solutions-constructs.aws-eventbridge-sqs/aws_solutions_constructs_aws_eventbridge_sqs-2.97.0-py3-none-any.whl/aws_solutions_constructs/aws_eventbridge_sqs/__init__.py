r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-eventbridge-sqs/README.adoc)
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

import aws_cdk.aws_events as _aws_cdk_aws_events_ceddda9d
import aws_cdk.aws_events_targets as _aws_cdk_aws_events_targets_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_sqs as _aws_cdk_aws_sqs_ceddda9d
import constructs as _constructs_77d1e7e8


class EventbridgeToSqs(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-eventbridge-sqs.EventbridgeToSqs",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        event_rule_props: typing.Union[_aws_cdk_aws_events_ceddda9d.RuleProps, typing.Dict[builtins.str, typing.Any]],
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        deploy_event_rule_dlq: typing.Optional[builtins.bool] = None,
        enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        enable_queue_purging: typing.Optional[builtins.bool] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        event_bus_props: typing.Optional[typing.Union[_aws_cdk_aws_events_ceddda9d.EventBusProps, typing.Dict[builtins.str, typing.Any]]] = None,
        event_rule_dlq_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_event_bus_interface: typing.Optional[_aws_cdk_aws_events_ceddda9d.IEventBus] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        target_props: typing.Optional[typing.Union[_aws_cdk_aws_events_targets_ceddda9d.SqsQueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param event_rule_props: User provided eventRuleProps to override the defaults. Default: - None
        :param dead_letter_queue_props: Optional user provided properties for the dead letter queue. Default: - Default props are used
        :param deploy_dead_letter_queue: Whether to deploy a secondary queue to be used as a dead letter queue. Default: - true.
        :param deploy_event_rule_dlq: Whether to deploy a DLQ for the Event Rule. If set to ``true``, this DLQ will receive any messages that can't be delivered to the target SQS queue. Default: - false
        :param enable_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps. Default: - True if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
        :param enable_queue_purging: Whether to grant additional permissions to the Lambda function enabling it to purge the SQS queue. Default: - "false", disabled by default.
        :param encryption_key: An optional, imported encryption key to encrypt the SQS queue with. Default: - None
        :param encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SQS queue with. Default: - None
        :param event_bus_props: Optional - user provided properties to override the default properties when creating a custom EventBus. Setting this value to ``{}`` will create a custom EventBus using all default properties. If neither this nor ``existingEventBusInterface`` is provided the construct will use the default EventBus. Providing both this and ``existingEventBusInterface`` results an error. Default: - None
        :param event_rule_dlq_key_props: Properties to define the key created to protect the ruleDlq Only valid if deployEventRuleDlq is set to true. Default: - default props are used
        :param existing_event_bus_interface: Optional - user provided custom event bus for this construct to use. Providing both this and ``eventBusProps`` is an error. Default: - None
        :param existing_queue_obj: Existing instance of SQS queue object, providing both this and queueProps will cause an error. Default: - None
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue. Default: - required field if deployDeadLetterQueue=true.
        :param queue_props: User provided props to override the default props for the SQS queue. Default: - Default props are used
        :param target_props: Optional user provided properties to define the SQS target on the Event Rule. If you specify a deadLetterQueue for the rule here, you are responsible for adding a resource policy to the queue allowing events.amazonaws.com permission to SendMessage, GetQueueUrl and GetQueueAttributes. You cannot send a DLQ in this property and set deployRuleDlq to true Default: - undefined (all default values are used)

        :access: public
        :since: 1.62.0
        :summary: Constructs a new instance of the EventbridgeToSqs class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ab22dc4bf8e02d8d1c6e2c647a426482c782898bff2f352481aeb8f2cbe01b9a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = EventbridgeToSqsProps(
            event_rule_props=event_rule_props,
            dead_letter_queue_props=dead_letter_queue_props,
            deploy_dead_letter_queue=deploy_dead_letter_queue,
            deploy_event_rule_dlq=deploy_event_rule_dlq,
            enable_encryption_with_customer_managed_key=enable_encryption_with_customer_managed_key,
            enable_queue_purging=enable_queue_purging,
            encryption_key=encryption_key,
            encryption_key_props=encryption_key_props,
            event_bus_props=event_bus_props,
            event_rule_dlq_key_props=event_rule_dlq_key_props,
            existing_event_bus_interface=existing_event_bus_interface,
            existing_queue_obj=existing_queue_obj,
            max_receive_count=max_receive_count,
            queue_props=queue_props,
            target_props=target_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="eventsRule")
    def events_rule(self) -> _aws_cdk_aws_events_ceddda9d.Rule:
        return typing.cast(_aws_cdk_aws_events_ceddda9d.Rule, jsii.get(self, "eventsRule"))

    @builtins.property
    @jsii.member(jsii_name="sqsQueue")
    def sqs_queue(self) -> _aws_cdk_aws_sqs_ceddda9d.Queue:
        return typing.cast(_aws_cdk_aws_sqs_ceddda9d.Queue, jsii.get(self, "sqsQueue"))

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
    @jsii.member(jsii_name="eventBus")
    def event_bus(self) -> typing.Optional[_aws_cdk_aws_events_ceddda9d.IEventBus]:
        return typing.cast(typing.Optional[_aws_cdk_aws_events_ceddda9d.IEventBus], jsii.get(self, "eventBus"))

    @builtins.property
    @jsii.member(jsii_name="eventRuleDlq")
    def event_rule_dlq(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue]:
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue], jsii.get(self, "eventRuleDlq"))

    @builtins.property
    @jsii.member(jsii_name="eventRuleDlqKey")
    def event_rule_dlq_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey]:
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey], jsii.get(self, "eventRuleDlqKey"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-eventbridge-sqs.EventbridgeToSqsProps",
    jsii_struct_bases=[],
    name_mapping={
        "event_rule_props": "eventRuleProps",
        "dead_letter_queue_props": "deadLetterQueueProps",
        "deploy_dead_letter_queue": "deployDeadLetterQueue",
        "deploy_event_rule_dlq": "deployEventRuleDlq",
        "enable_encryption_with_customer_managed_key": "enableEncryptionWithCustomerManagedKey",
        "enable_queue_purging": "enableQueuePurging",
        "encryption_key": "encryptionKey",
        "encryption_key_props": "encryptionKeyProps",
        "event_bus_props": "eventBusProps",
        "event_rule_dlq_key_props": "eventRuleDlqKeyProps",
        "existing_event_bus_interface": "existingEventBusInterface",
        "existing_queue_obj": "existingQueueObj",
        "max_receive_count": "maxReceiveCount",
        "queue_props": "queueProps",
        "target_props": "targetProps",
    },
)
class EventbridgeToSqsProps:
    def __init__(
        self,
        *,
        event_rule_props: typing.Union[_aws_cdk_aws_events_ceddda9d.RuleProps, typing.Dict[builtins.str, typing.Any]],
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        deploy_event_rule_dlq: typing.Optional[builtins.bool] = None,
        enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        enable_queue_purging: typing.Optional[builtins.bool] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        event_bus_props: typing.Optional[typing.Union[_aws_cdk_aws_events_ceddda9d.EventBusProps, typing.Dict[builtins.str, typing.Any]]] = None,
        event_rule_dlq_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_event_bus_interface: typing.Optional[_aws_cdk_aws_events_ceddda9d.IEventBus] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        target_props: typing.Optional[typing.Union[_aws_cdk_aws_events_targets_ceddda9d.SqsQueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param event_rule_props: User provided eventRuleProps to override the defaults. Default: - None
        :param dead_letter_queue_props: Optional user provided properties for the dead letter queue. Default: - Default props are used
        :param deploy_dead_letter_queue: Whether to deploy a secondary queue to be used as a dead letter queue. Default: - true.
        :param deploy_event_rule_dlq: Whether to deploy a DLQ for the Event Rule. If set to ``true``, this DLQ will receive any messages that can't be delivered to the target SQS queue. Default: - false
        :param enable_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps. Default: - True if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
        :param enable_queue_purging: Whether to grant additional permissions to the Lambda function enabling it to purge the SQS queue. Default: - "false", disabled by default.
        :param encryption_key: An optional, imported encryption key to encrypt the SQS queue with. Default: - None
        :param encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SQS queue with. Default: - None
        :param event_bus_props: Optional - user provided properties to override the default properties when creating a custom EventBus. Setting this value to ``{}`` will create a custom EventBus using all default properties. If neither this nor ``existingEventBusInterface`` is provided the construct will use the default EventBus. Providing both this and ``existingEventBusInterface`` results an error. Default: - None
        :param event_rule_dlq_key_props: Properties to define the key created to protect the ruleDlq Only valid if deployEventRuleDlq is set to true. Default: - default props are used
        :param existing_event_bus_interface: Optional - user provided custom event bus for this construct to use. Providing both this and ``eventBusProps`` is an error. Default: - None
        :param existing_queue_obj: Existing instance of SQS queue object, providing both this and queueProps will cause an error. Default: - None
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue. Default: - required field if deployDeadLetterQueue=true.
        :param queue_props: User provided props to override the default props for the SQS queue. Default: - Default props are used
        :param target_props: Optional user provided properties to define the SQS target on the Event Rule. If you specify a deadLetterQueue for the rule here, you are responsible for adding a resource policy to the queue allowing events.amazonaws.com permission to SendMessage, GetQueueUrl and GetQueueAttributes. You cannot send a DLQ in this property and set deployRuleDlq to true Default: - undefined (all default values are used)

        :summary: The properties for the EventbridgeToSqs Construct
        '''
        if isinstance(event_rule_props, dict):
            event_rule_props = _aws_cdk_aws_events_ceddda9d.RuleProps(**event_rule_props)
        if isinstance(dead_letter_queue_props, dict):
            dead_letter_queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**dead_letter_queue_props)
        if isinstance(encryption_key_props, dict):
            encryption_key_props = _aws_cdk_aws_kms_ceddda9d.KeyProps(**encryption_key_props)
        if isinstance(event_bus_props, dict):
            event_bus_props = _aws_cdk_aws_events_ceddda9d.EventBusProps(**event_bus_props)
        if isinstance(event_rule_dlq_key_props, dict):
            event_rule_dlq_key_props = _aws_cdk_aws_kms_ceddda9d.KeyProps(**event_rule_dlq_key_props)
        if isinstance(queue_props, dict):
            queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**queue_props)
        if isinstance(target_props, dict):
            target_props = _aws_cdk_aws_events_targets_ceddda9d.SqsQueueProps(**target_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ed059501b695f8a8c855e7f9a3d09a62a5ad5886525d65986cb9392bc18de3ce)
            check_type(argname="argument event_rule_props", value=event_rule_props, expected_type=type_hints["event_rule_props"])
            check_type(argname="argument dead_letter_queue_props", value=dead_letter_queue_props, expected_type=type_hints["dead_letter_queue_props"])
            check_type(argname="argument deploy_dead_letter_queue", value=deploy_dead_letter_queue, expected_type=type_hints["deploy_dead_letter_queue"])
            check_type(argname="argument deploy_event_rule_dlq", value=deploy_event_rule_dlq, expected_type=type_hints["deploy_event_rule_dlq"])
            check_type(argname="argument enable_encryption_with_customer_managed_key", value=enable_encryption_with_customer_managed_key, expected_type=type_hints["enable_encryption_with_customer_managed_key"])
            check_type(argname="argument enable_queue_purging", value=enable_queue_purging, expected_type=type_hints["enable_queue_purging"])
            check_type(argname="argument encryption_key", value=encryption_key, expected_type=type_hints["encryption_key"])
            check_type(argname="argument encryption_key_props", value=encryption_key_props, expected_type=type_hints["encryption_key_props"])
            check_type(argname="argument event_bus_props", value=event_bus_props, expected_type=type_hints["event_bus_props"])
            check_type(argname="argument event_rule_dlq_key_props", value=event_rule_dlq_key_props, expected_type=type_hints["event_rule_dlq_key_props"])
            check_type(argname="argument existing_event_bus_interface", value=existing_event_bus_interface, expected_type=type_hints["existing_event_bus_interface"])
            check_type(argname="argument existing_queue_obj", value=existing_queue_obj, expected_type=type_hints["existing_queue_obj"])
            check_type(argname="argument max_receive_count", value=max_receive_count, expected_type=type_hints["max_receive_count"])
            check_type(argname="argument queue_props", value=queue_props, expected_type=type_hints["queue_props"])
            check_type(argname="argument target_props", value=target_props, expected_type=type_hints["target_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "event_rule_props": event_rule_props,
        }
        if dead_letter_queue_props is not None:
            self._values["dead_letter_queue_props"] = dead_letter_queue_props
        if deploy_dead_letter_queue is not None:
            self._values["deploy_dead_letter_queue"] = deploy_dead_letter_queue
        if deploy_event_rule_dlq is not None:
            self._values["deploy_event_rule_dlq"] = deploy_event_rule_dlq
        if enable_encryption_with_customer_managed_key is not None:
            self._values["enable_encryption_with_customer_managed_key"] = enable_encryption_with_customer_managed_key
        if enable_queue_purging is not None:
            self._values["enable_queue_purging"] = enable_queue_purging
        if encryption_key is not None:
            self._values["encryption_key"] = encryption_key
        if encryption_key_props is not None:
            self._values["encryption_key_props"] = encryption_key_props
        if event_bus_props is not None:
            self._values["event_bus_props"] = event_bus_props
        if event_rule_dlq_key_props is not None:
            self._values["event_rule_dlq_key_props"] = event_rule_dlq_key_props
        if existing_event_bus_interface is not None:
            self._values["existing_event_bus_interface"] = existing_event_bus_interface
        if existing_queue_obj is not None:
            self._values["existing_queue_obj"] = existing_queue_obj
        if max_receive_count is not None:
            self._values["max_receive_count"] = max_receive_count
        if queue_props is not None:
            self._values["queue_props"] = queue_props
        if target_props is not None:
            self._values["target_props"] = target_props

    @builtins.property
    def event_rule_props(self) -> _aws_cdk_aws_events_ceddda9d.RuleProps:
        '''User provided eventRuleProps to override the defaults.

        :default: - None
        '''
        result = self._values.get("event_rule_props")
        assert result is not None, "Required property 'event_rule_props' is missing"
        return typing.cast(_aws_cdk_aws_events_ceddda9d.RuleProps, result)

    @builtins.property
    def dead_letter_queue_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''Optional user provided properties for the dead letter queue.

        :default: - Default props are used
        '''
        result = self._values.get("dead_letter_queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

    @builtins.property
    def deploy_dead_letter_queue(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a secondary queue to be used as a dead letter queue.

        :default: - true.
        '''
        result = self._values.get("deploy_dead_letter_queue")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def deploy_event_rule_dlq(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a DLQ for the Event Rule.

        If set to ``true``, this DLQ will
        receive any messages that can't be delivered to the target SQS queue.

        :default: - false
        '''
        result = self._values.get("deploy_event_rule_dlq")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_encryption_with_customer_managed_key(
        self,
    ) -> typing.Optional[builtins.bool]:
        '''If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key.

        This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps.

        :default: - True if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
        '''
        result = self._values.get("enable_encryption_with_customer_managed_key")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_queue_purging(self) -> typing.Optional[builtins.bool]:
        '''Whether to grant additional permissions to the Lambda function enabling it to purge the SQS queue.

        :default: - "false", disabled by default.
        '''
        result = self._values.get("enable_queue_purging")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key]:
        '''An optional, imported encryption key to encrypt the SQS queue with.

        :default: - None
        '''
        result = self._values.get("encryption_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def encryption_key_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps]:
        '''Optional user provided properties to override the default properties for the KMS encryption key used to  encrypt the SQS queue with.

        :default: - None
        '''
        result = self._values.get("encryption_key_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps], result)

    @builtins.property
    def event_bus_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_events_ceddda9d.EventBusProps]:
        '''Optional - user provided properties to override the default properties when creating a custom EventBus.

        Setting
        this value to ``{}`` will create a custom EventBus using all default properties. If neither this nor
        ``existingEventBusInterface`` is provided the construct will use the default EventBus. Providing both this and
        ``existingEventBusInterface`` results an error.

        :default: - None
        '''
        result = self._values.get("event_bus_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_events_ceddda9d.EventBusProps], result)

    @builtins.property
    def event_rule_dlq_key_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps]:
        '''Properties to define the key created to protect the ruleDlq Only valid if deployEventRuleDlq is set to true.

        :default: - default props are used
        '''
        result = self._values.get("event_rule_dlq_key_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps], result)

    @builtins.property
    def existing_event_bus_interface(
        self,
    ) -> typing.Optional[_aws_cdk_aws_events_ceddda9d.IEventBus]:
        '''Optional - user provided custom event bus for this construct to use.

        Providing both this and ``eventBusProps`` is
        an error.

        :default: - None
        '''
        result = self._values.get("existing_event_bus_interface")
        return typing.cast(typing.Optional[_aws_cdk_aws_events_ceddda9d.IEventBus], result)

    @builtins.property
    def existing_queue_obj(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue]:
        '''Existing instance of SQS queue object, providing both this and queueProps will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_queue_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue], result)

    @builtins.property
    def max_receive_count(self) -> typing.Optional[jsii.Number]:
        '''The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue.

        :default: - required field if deployDeadLetterQueue=true.
        '''
        result = self._values.get("max_receive_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def queue_props(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''User provided props to override the default props for the SQS queue.

        :default: - Default props are used
        '''
        result = self._values.get("queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

    @builtins.property
    def target_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_events_targets_ceddda9d.SqsQueueProps]:
        '''Optional user provided properties to define the SQS target on the Event Rule.

        If you specify a deadLetterQueue for the rule here, you are responsible for adding a resource policy
        to the queue allowing events.amazonaws.com permission to SendMessage, GetQueueUrl and GetQueueAttributes. You
        cannot send a DLQ in this property and set deployRuleDlq to true

        :default: - undefined (all default values are used)
        '''
        result = self._values.get("target_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_events_targets_ceddda9d.SqsQueueProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EventbridgeToSqsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "EventbridgeToSqs",
    "EventbridgeToSqsProps",
]

publication.publish()

def _typecheckingstub__ab22dc4bf8e02d8d1c6e2c647a426482c782898bff2f352481aeb8f2cbe01b9a(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    event_rule_props: typing.Union[_aws_cdk_aws_events_ceddda9d.RuleProps, typing.Dict[builtins.str, typing.Any]],
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    deploy_event_rule_dlq: typing.Optional[builtins.bool] = None,
    enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    enable_queue_purging: typing.Optional[builtins.bool] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    event_bus_props: typing.Optional[typing.Union[_aws_cdk_aws_events_ceddda9d.EventBusProps, typing.Dict[builtins.str, typing.Any]]] = None,
    event_rule_dlq_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_event_bus_interface: typing.Optional[_aws_cdk_aws_events_ceddda9d.IEventBus] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    target_props: typing.Optional[typing.Union[_aws_cdk_aws_events_targets_ceddda9d.SqsQueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ed059501b695f8a8c855e7f9a3d09a62a5ad5886525d65986cb9392bc18de3ce(
    *,
    event_rule_props: typing.Union[_aws_cdk_aws_events_ceddda9d.RuleProps, typing.Dict[builtins.str, typing.Any]],
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    deploy_event_rule_dlq: typing.Optional[builtins.bool] = None,
    enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    enable_queue_purging: typing.Optional[builtins.bool] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    event_bus_props: typing.Optional[typing.Union[_aws_cdk_aws_events_ceddda9d.EventBusProps, typing.Dict[builtins.str, typing.Any]]] = None,
    event_rule_dlq_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_event_bus_interface: typing.Optional[_aws_cdk_aws_events_ceddda9d.IEventBus] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    target_props: typing.Optional[typing.Union[_aws_cdk_aws_events_targets_ceddda9d.SqsQueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
