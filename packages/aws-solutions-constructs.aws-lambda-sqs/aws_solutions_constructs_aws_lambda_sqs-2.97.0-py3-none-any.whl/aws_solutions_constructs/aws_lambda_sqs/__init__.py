r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-lambda-sqs/README.adoc)
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
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_sqs as _aws_cdk_aws_sqs_ceddda9d
import constructs as _constructs_77d1e7e8


class LambdaToSqs(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-lambda-sqs.LambdaToSqs",
):
    '''
    :summary: The LambdaToSqs class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        enable_queue_purging: typing.Optional[builtins.bool] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        queue_environment_variable_name: typing.Optional[builtins.str] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param dead_letter_queue_props: Optional user provided properties for the dead letter queue. Default: - Default props are used
        :param deploy_dead_letter_queue: Whether to deploy a secondary queue to be used as a dead letter queue. Default: - true.
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param enable_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps. Default: - False if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
        :param enable_queue_purging: Whether to grant additional permissions to the Lambda function enabling it to purge the SQS queue. Default: - "false", disabled by default.
        :param encryption_key: An optional, imported encryption key to encrypt the SQS Queue with. Default: - None
        :param encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SQS Queue with. Default: - None
        :param existing_lambda_obj: Existing instance of Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_queue_obj: Existing instance of SQS queue object, Providing both this and queueProps will cause an error. Default: - Default props are used
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default properties are used.
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue. Default: - required field if deployDeadLetterQueue=true.
        :param queue_environment_variable_name: Optional Name for the Lambda function environment variable set to the URL of the queue. Default: - SQS_QUEUE_URL
        :param queue_props: Optional - user provided properties to override the default properties for the SQS queue. Providing both this and ``existingQueueObj`` will cause an error. Default: - Default props are used
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :access: public
        :since: 1.49.0
        :summary: Constructs a new instance of the LambdaToSqs class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8032b7329efd1b110a0387bc7e9520f50d964e7d4cdac06ac35ef023d2167602)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = LambdaToSqsProps(
            dead_letter_queue_props=dead_letter_queue_props,
            deploy_dead_letter_queue=deploy_dead_letter_queue,
            deploy_vpc=deploy_vpc,
            enable_encryption_with_customer_managed_key=enable_encryption_with_customer_managed_key,
            enable_queue_purging=enable_queue_purging,
            encryption_key=encryption_key,
            encryption_key_props=encryption_key_props,
            existing_lambda_obj=existing_lambda_obj,
            existing_queue_obj=existing_queue_obj,
            existing_vpc=existing_vpc,
            lambda_function_props=lambda_function_props,
            max_receive_count=max_receive_count,
            queue_environment_variable_name=queue_environment_variable_name,
            queue_props=queue_props,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

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
    jsii_type="@aws-solutions-constructs/aws-lambda-sqs.LambdaToSqsProps",
    jsii_struct_bases=[],
    name_mapping={
        "dead_letter_queue_props": "deadLetterQueueProps",
        "deploy_dead_letter_queue": "deployDeadLetterQueue",
        "deploy_vpc": "deployVpc",
        "enable_encryption_with_customer_managed_key": "enableEncryptionWithCustomerManagedKey",
        "enable_queue_purging": "enableQueuePurging",
        "encryption_key": "encryptionKey",
        "encryption_key_props": "encryptionKeyProps",
        "existing_lambda_obj": "existingLambdaObj",
        "existing_queue_obj": "existingQueueObj",
        "existing_vpc": "existingVpc",
        "lambda_function_props": "lambdaFunctionProps",
        "max_receive_count": "maxReceiveCount",
        "queue_environment_variable_name": "queueEnvironmentVariableName",
        "queue_props": "queueProps",
        "vpc_props": "vpcProps",
    },
)
class LambdaToSqsProps:
    def __init__(
        self,
        *,
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        enable_queue_purging: typing.Optional[builtins.bool] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        queue_environment_variable_name: typing.Optional[builtins.str] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param dead_letter_queue_props: Optional user provided properties for the dead letter queue. Default: - Default props are used
        :param deploy_dead_letter_queue: Whether to deploy a secondary queue to be used as a dead letter queue. Default: - true.
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param enable_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps. Default: - False if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
        :param enable_queue_purging: Whether to grant additional permissions to the Lambda function enabling it to purge the SQS queue. Default: - "false", disabled by default.
        :param encryption_key: An optional, imported encryption key to encrypt the SQS Queue with. Default: - None
        :param encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SQS Queue with. Default: - None
        :param existing_lambda_obj: Existing instance of Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_queue_obj: Existing instance of SQS queue object, Providing both this and queueProps will cause an error. Default: - Default props are used
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default properties are used.
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue. Default: - required field if deployDeadLetterQueue=true.
        :param queue_environment_variable_name: Optional Name for the Lambda function environment variable set to the URL of the queue. Default: - SQS_QUEUE_URL
        :param queue_props: Optional - user provided properties to override the default properties for the SQS queue. Providing both this and ``existingQueueObj`` will cause an error. Default: - Default props are used
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :summary: The properties for the LambdaToSqs class.
        '''
        if isinstance(dead_letter_queue_props, dict):
            dead_letter_queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**dead_letter_queue_props)
        if isinstance(encryption_key_props, dict):
            encryption_key_props = _aws_cdk_aws_kms_ceddda9d.KeyProps(**encryption_key_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(queue_props, dict):
            queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**queue_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ff64244bddffdd380ea8d41dc1da7270c0c024aeb05fdb5a9b5c2a56c18f7d01)
            check_type(argname="argument dead_letter_queue_props", value=dead_letter_queue_props, expected_type=type_hints["dead_letter_queue_props"])
            check_type(argname="argument deploy_dead_letter_queue", value=deploy_dead_letter_queue, expected_type=type_hints["deploy_dead_letter_queue"])
            check_type(argname="argument deploy_vpc", value=deploy_vpc, expected_type=type_hints["deploy_vpc"])
            check_type(argname="argument enable_encryption_with_customer_managed_key", value=enable_encryption_with_customer_managed_key, expected_type=type_hints["enable_encryption_with_customer_managed_key"])
            check_type(argname="argument enable_queue_purging", value=enable_queue_purging, expected_type=type_hints["enable_queue_purging"])
            check_type(argname="argument encryption_key", value=encryption_key, expected_type=type_hints["encryption_key"])
            check_type(argname="argument encryption_key_props", value=encryption_key_props, expected_type=type_hints["encryption_key_props"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument existing_queue_obj", value=existing_queue_obj, expected_type=type_hints["existing_queue_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument max_receive_count", value=max_receive_count, expected_type=type_hints["max_receive_count"])
            check_type(argname="argument queue_environment_variable_name", value=queue_environment_variable_name, expected_type=type_hints["queue_environment_variable_name"])
            check_type(argname="argument queue_props", value=queue_props, expected_type=type_hints["queue_props"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if dead_letter_queue_props is not None:
            self._values["dead_letter_queue_props"] = dead_letter_queue_props
        if deploy_dead_letter_queue is not None:
            self._values["deploy_dead_letter_queue"] = deploy_dead_letter_queue
        if deploy_vpc is not None:
            self._values["deploy_vpc"] = deploy_vpc
        if enable_encryption_with_customer_managed_key is not None:
            self._values["enable_encryption_with_customer_managed_key"] = enable_encryption_with_customer_managed_key
        if enable_queue_purging is not None:
            self._values["enable_queue_purging"] = enable_queue_purging
        if encryption_key is not None:
            self._values["encryption_key"] = encryption_key
        if encryption_key_props is not None:
            self._values["encryption_key_props"] = encryption_key_props
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if existing_queue_obj is not None:
            self._values["existing_queue_obj"] = existing_queue_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if max_receive_count is not None:
            self._values["max_receive_count"] = max_receive_count
        if queue_environment_variable_name is not None:
            self._values["queue_environment_variable_name"] = queue_environment_variable_name
        if queue_props is not None:
            self._values["queue_props"] = queue_props
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

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
    def deploy_vpc(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a new VPC.

        :default: - false
        '''
        result = self._values.get("deploy_vpc")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_encryption_with_customer_managed_key(
        self,
    ) -> typing.Optional[builtins.bool]:
        '''If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key.

        This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps.

        :default: - False if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
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
        '''An optional, imported encryption key to encrypt the SQS Queue with.

        :default: - None
        '''
        result = self._values.get("encryption_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def encryption_key_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps]:
        '''Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SQS Queue with.

        :default: - None
        '''
        result = self._values.get("encryption_key_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps], result)

    @builtins.property
    def existing_lambda_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function]:
        '''Existing instance of Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_lambda_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function], result)

    @builtins.property
    def existing_queue_obj(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue]:
        '''Existing instance of SQS queue object, Providing both this and queueProps will cause an error.

        :default: - Default props are used
        '''
        result = self._values.get("existing_queue_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue], result)

    @builtins.property
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC for the construct to use (construct will NOT create a new VPC in this case).'''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def lambda_function_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps]:
        '''Optional - user provided props to override the default props for the Lambda function.

        Providing both this and ``existingLambdaObj`` is an error.

        :default: - Default properties are used.
        '''
        result = self._values.get("lambda_function_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps], result)

    @builtins.property
    def max_receive_count(self) -> typing.Optional[jsii.Number]:
        '''The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue.

        :default: - required field if deployDeadLetterQueue=true.
        '''
        result = self._values.get("max_receive_count")
        return typing.cast(typing.Optional[jsii.Number], result)

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

        :default: - Default props are used
        '''
        result = self._values.get("queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

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
        return "LambdaToSqsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "LambdaToSqs",
    "LambdaToSqsProps",
]

publication.publish()

def _typecheckingstub__8032b7329efd1b110a0387bc7e9520f50d964e7d4cdac06ac35ef023d2167602(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    enable_queue_purging: typing.Optional[builtins.bool] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    queue_environment_variable_name: typing.Optional[builtins.str] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ff64244bddffdd380ea8d41dc1da7270c0c024aeb05fdb5a9b5c2a56c18f7d01(
    *,
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    enable_queue_purging: typing.Optional[builtins.bool] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    queue_environment_variable_name: typing.Optional[builtins.str] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
