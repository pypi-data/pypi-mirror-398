r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-lambda-sqs-lambda/README.adoc)
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

import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_lambda_event_sources as _aws_cdk_aws_lambda_event_sources_ceddda9d
import aws_cdk.aws_sqs as _aws_cdk_aws_sqs_ceddda9d
import constructs as _constructs_77d1e7e8


class LambdaToSqsToLambda(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-lambda-sqs-lambda.LambdaToSqsToLambda",
):
    '''
    :summary: The LambdaToSqsToLambda class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        consumer_lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        existing_consumer_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_producer_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        producer_lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        queue_environment_variable_name: typing.Optional[builtins.str] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        sqs_event_source_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_event_sources_ceddda9d.SqsEventSourceProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param consumer_lambda_function_props: Optional - user provided props to override the default props for the consumer Lambda function. Providing both this and ``existingConsumerLambdaObj`` is an error. Default: - Default properties are used.
        :param dead_letter_queue_props: Optional user-provided props to override the default props for the dead letter queue. Only used if the ``deployDeadLetterQueue`` property is set to true. Default: - Default props are used.
        :param deploy_dead_letter_queue: Whether to create a secondary queue to be used as a dead letter queue. Defaults to ``true``. Default: - true.
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param existing_consumer_lambda_obj: An optional, existing Lambda function to be used instead of the default function for receiving/consuming messages from the queue. Providing both this and ``consumerLambdaFunctionProps`` will cause an error. Default: - None.
        :param existing_producer_lambda_obj: An optional, existing Lambda function to be used instead of the default function for sending messages to the queue. Providing both this and ``producerLambdaFunctionProps`` property will cause an error. Default: - None.
        :param existing_queue_obj: An optional, existing SQS queue to be used instead of the default queue. Providing both this and ``queueProps`` will cause an error. Default: - None.
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead letter queue. Defaults to ``15``. Default: - 15.
        :param producer_lambda_function_props: Optional - user provided props to override the default props for the producer Lambda function. Providing both this and ``existingProducerLambdaObj`` is an error. Default: - Default properties are used.
        :param queue_environment_variable_name: Optional Name for the Lambda function environment variable set to the URL of the queue. Default: - SQS_QUEUE_URL
        :param queue_props: Optional - user provided properties to override the default properties for the SQS queue. Providing both this and ``existingQueueObj`` will cause an error. Default: - Default props are used.
        :param sqs_event_source_props: Optional user provided properties for the queue event source. Default: - Default props are used
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :access: public
        :summary: Constructs a new instance of the LambdaToSqsToLambda class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4dcac242d39b60acc1536a4e2dca319a038d2c2c5381764f0b31c2314148ec91)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = LambdaToSqsToLambdaProps(
            consumer_lambda_function_props=consumer_lambda_function_props,
            dead_letter_queue_props=dead_letter_queue_props,
            deploy_dead_letter_queue=deploy_dead_letter_queue,
            deploy_vpc=deploy_vpc,
            existing_consumer_lambda_obj=existing_consumer_lambda_obj,
            existing_producer_lambda_obj=existing_producer_lambda_obj,
            existing_queue_obj=existing_queue_obj,
            existing_vpc=existing_vpc,
            max_receive_count=max_receive_count,
            producer_lambda_function_props=producer_lambda_function_props,
            queue_environment_variable_name=queue_environment_variable_name,
            queue_props=queue_props,
            sqs_event_source_props=sqs_event_source_props,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="consumerLambdaFunction")
    def consumer_lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "consumerLambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="producerLambdaFunction")
    def producer_lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "producerLambdaFunction"))

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
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-lambda-sqs-lambda.LambdaToSqsToLambdaProps",
    jsii_struct_bases=[],
    name_mapping={
        "consumer_lambda_function_props": "consumerLambdaFunctionProps",
        "dead_letter_queue_props": "deadLetterQueueProps",
        "deploy_dead_letter_queue": "deployDeadLetterQueue",
        "deploy_vpc": "deployVpc",
        "existing_consumer_lambda_obj": "existingConsumerLambdaObj",
        "existing_producer_lambda_obj": "existingProducerLambdaObj",
        "existing_queue_obj": "existingQueueObj",
        "existing_vpc": "existingVpc",
        "max_receive_count": "maxReceiveCount",
        "producer_lambda_function_props": "producerLambdaFunctionProps",
        "queue_environment_variable_name": "queueEnvironmentVariableName",
        "queue_props": "queueProps",
        "sqs_event_source_props": "sqsEventSourceProps",
        "vpc_props": "vpcProps",
    },
)
class LambdaToSqsToLambdaProps:
    def __init__(
        self,
        *,
        consumer_lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        existing_consumer_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_producer_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        producer_lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        queue_environment_variable_name: typing.Optional[builtins.str] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        sqs_event_source_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_event_sources_ceddda9d.SqsEventSourceProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param consumer_lambda_function_props: Optional - user provided props to override the default props for the consumer Lambda function. Providing both this and ``existingConsumerLambdaObj`` is an error. Default: - Default properties are used.
        :param dead_letter_queue_props: Optional user-provided props to override the default props for the dead letter queue. Only used if the ``deployDeadLetterQueue`` property is set to true. Default: - Default props are used.
        :param deploy_dead_letter_queue: Whether to create a secondary queue to be used as a dead letter queue. Defaults to ``true``. Default: - true.
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param existing_consumer_lambda_obj: An optional, existing Lambda function to be used instead of the default function for receiving/consuming messages from the queue. Providing both this and ``consumerLambdaFunctionProps`` will cause an error. Default: - None.
        :param existing_producer_lambda_obj: An optional, existing Lambda function to be used instead of the default function for sending messages to the queue. Providing both this and ``producerLambdaFunctionProps`` property will cause an error. Default: - None.
        :param existing_queue_obj: An optional, existing SQS queue to be used instead of the default queue. Providing both this and ``queueProps`` will cause an error. Default: - None.
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead letter queue. Defaults to ``15``. Default: - 15.
        :param producer_lambda_function_props: Optional - user provided props to override the default props for the producer Lambda function. Providing both this and ``existingProducerLambdaObj`` is an error. Default: - Default properties are used.
        :param queue_environment_variable_name: Optional Name for the Lambda function environment variable set to the URL of the queue. Default: - SQS_QUEUE_URL
        :param queue_props: Optional - user provided properties to override the default properties for the SQS queue. Providing both this and ``existingQueueObj`` will cause an error. Default: - Default props are used.
        :param sqs_event_source_props: Optional user provided properties for the queue event source. Default: - Default props are used
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :summary: The properties for the LambdaToSqsToLambda class.
        '''
        if isinstance(consumer_lambda_function_props, dict):
            consumer_lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**consumer_lambda_function_props)
        if isinstance(dead_letter_queue_props, dict):
            dead_letter_queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**dead_letter_queue_props)
        if isinstance(producer_lambda_function_props, dict):
            producer_lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**producer_lambda_function_props)
        if isinstance(queue_props, dict):
            queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**queue_props)
        if isinstance(sqs_event_source_props, dict):
            sqs_event_source_props = _aws_cdk_aws_lambda_event_sources_ceddda9d.SqsEventSourceProps(**sqs_event_source_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__35d74c84b8d1f96157035ad48360aa4c6ddbfdc76eaf72f6fd4cf24fec06f8bf)
            check_type(argname="argument consumer_lambda_function_props", value=consumer_lambda_function_props, expected_type=type_hints["consumer_lambda_function_props"])
            check_type(argname="argument dead_letter_queue_props", value=dead_letter_queue_props, expected_type=type_hints["dead_letter_queue_props"])
            check_type(argname="argument deploy_dead_letter_queue", value=deploy_dead_letter_queue, expected_type=type_hints["deploy_dead_letter_queue"])
            check_type(argname="argument deploy_vpc", value=deploy_vpc, expected_type=type_hints["deploy_vpc"])
            check_type(argname="argument existing_consumer_lambda_obj", value=existing_consumer_lambda_obj, expected_type=type_hints["existing_consumer_lambda_obj"])
            check_type(argname="argument existing_producer_lambda_obj", value=existing_producer_lambda_obj, expected_type=type_hints["existing_producer_lambda_obj"])
            check_type(argname="argument existing_queue_obj", value=existing_queue_obj, expected_type=type_hints["existing_queue_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument max_receive_count", value=max_receive_count, expected_type=type_hints["max_receive_count"])
            check_type(argname="argument producer_lambda_function_props", value=producer_lambda_function_props, expected_type=type_hints["producer_lambda_function_props"])
            check_type(argname="argument queue_environment_variable_name", value=queue_environment_variable_name, expected_type=type_hints["queue_environment_variable_name"])
            check_type(argname="argument queue_props", value=queue_props, expected_type=type_hints["queue_props"])
            check_type(argname="argument sqs_event_source_props", value=sqs_event_source_props, expected_type=type_hints["sqs_event_source_props"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if consumer_lambda_function_props is not None:
            self._values["consumer_lambda_function_props"] = consumer_lambda_function_props
        if dead_letter_queue_props is not None:
            self._values["dead_letter_queue_props"] = dead_letter_queue_props
        if deploy_dead_letter_queue is not None:
            self._values["deploy_dead_letter_queue"] = deploy_dead_letter_queue
        if deploy_vpc is not None:
            self._values["deploy_vpc"] = deploy_vpc
        if existing_consumer_lambda_obj is not None:
            self._values["existing_consumer_lambda_obj"] = existing_consumer_lambda_obj
        if existing_producer_lambda_obj is not None:
            self._values["existing_producer_lambda_obj"] = existing_producer_lambda_obj
        if existing_queue_obj is not None:
            self._values["existing_queue_obj"] = existing_queue_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if max_receive_count is not None:
            self._values["max_receive_count"] = max_receive_count
        if producer_lambda_function_props is not None:
            self._values["producer_lambda_function_props"] = producer_lambda_function_props
        if queue_environment_variable_name is not None:
            self._values["queue_environment_variable_name"] = queue_environment_variable_name
        if queue_props is not None:
            self._values["queue_props"] = queue_props
        if sqs_event_source_props is not None:
            self._values["sqs_event_source_props"] = sqs_event_source_props
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def consumer_lambda_function_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps]:
        '''Optional - user provided props to override the default props for the consumer Lambda function.

        Providing both this and ``existingConsumerLambdaObj`` is an error.

        :default: - Default properties are used.
        '''
        result = self._values.get("consumer_lambda_function_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps], result)

    @builtins.property
    def dead_letter_queue_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''Optional user-provided props to override the default props for the dead letter queue.

        Only used if the
        ``deployDeadLetterQueue`` property is set to true.

        :default: - Default props are used.
        '''
        result = self._values.get("dead_letter_queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

    @builtins.property
    def deploy_dead_letter_queue(self) -> typing.Optional[builtins.bool]:
        '''Whether to create a secondary queue to be used as a dead letter queue.

        Defaults to ``true``.

        :default: - true.
        '''
        result = self._values.get("deploy_dead_letter_queue")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def deploy_vpc(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a new VPC.

        :default: - false
        '''
        result = self._values.get("deploy_vpc")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def existing_consumer_lambda_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function]:
        '''An optional, existing Lambda function to be used instead of the default function for receiving/consuming messages from the queue.

        Providing both this and ``consumerLambdaFunctionProps`` will cause an error.

        :default: - None.
        '''
        result = self._values.get("existing_consumer_lambda_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function], result)

    @builtins.property
    def existing_producer_lambda_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function]:
        '''An optional, existing Lambda function to be used instead of the default function for sending messages to the queue.

        Providing both this and ``producerLambdaFunctionProps`` property will cause an error.

        :default: - None.
        '''
        result = self._values.get("existing_producer_lambda_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function], result)

    @builtins.property
    def existing_queue_obj(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue]:
        '''An optional, existing SQS queue to be used instead of the default queue.

        Providing both this and ``queueProps``
        will cause an error.

        :default: - None.
        '''
        result = self._values.get("existing_queue_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue], result)

    @builtins.property
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC for the construct to use (construct will NOT create a new VPC in this case).'''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def max_receive_count(self) -> typing.Optional[jsii.Number]:
        '''The number of times a message can be unsuccessfully dequeued before being moved to the dead letter queue.

        Defaults to ``15``.

        :default:

        -
        15.
        '''
        result = self._values.get("max_receive_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def producer_lambda_function_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps]:
        '''Optional - user provided props to override the default props for the producer Lambda function.

        Providing
        both this and ``existingProducerLambdaObj`` is an error.

        :default: - Default properties are used.
        '''
        result = self._values.get("producer_lambda_function_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps], result)

    @builtins.property
    def queue_environment_variable_name(self) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the URL of the queue.

        :default: - SQS_QUEUE_URL
        '''
        result = self._values.get("queue_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def queue_props(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''Optional - user provided properties to override the default properties for the SQS queue.

        Providing both this and ``existingQueueObj`` will cause an error.

        :default: - Default props are used.
        '''
        result = self._values.get("queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

    @builtins.property
    def sqs_event_source_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_event_sources_ceddda9d.SqsEventSourceProps]:
        '''Optional user provided properties for the queue event source.

        :default: - Default props are used
        '''
        result = self._values.get("sqs_event_source_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_event_sources_ceddda9d.SqsEventSourceProps], result)

    @builtins.property
    def vpc_props(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps]:
        '''Properties to override default properties if deployVpc is true.'''
        result = self._values.get("vpc_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LambdaToSqsToLambdaProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "LambdaToSqsToLambda",
    "LambdaToSqsToLambdaProps",
]

publication.publish()

def _typecheckingstub__4dcac242d39b60acc1536a4e2dca319a038d2c2c5381764f0b31c2314148ec91(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    consumer_lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    existing_consumer_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_producer_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    producer_lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    queue_environment_variable_name: typing.Optional[builtins.str] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    sqs_event_source_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_event_sources_ceddda9d.SqsEventSourceProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__35d74c84b8d1f96157035ad48360aa4c6ddbfdc76eaf72f6fd4cf24fec06f8bf(
    *,
    consumer_lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    existing_consumer_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_producer_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    producer_lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    queue_environment_variable_name: typing.Optional[builtins.str] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    sqs_event_source_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_event_sources_ceddda9d.SqsEventSourceProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
