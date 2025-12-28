r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-dynamodbstreams-lambda/README.adoc)
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

import aws_cdk.aws_dynamodb as _aws_cdk_aws_dynamodb_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_sqs as _aws_cdk_aws_sqs_ceddda9d
import constructs as _constructs_77d1e7e8


class DynamoDBStreamsToLambda(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-dynamodbstreams-lambda.DynamoDBStreamsToLambda",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        deploy_sqs_dlq_queue: typing.Optional[builtins.bool] = None,
        dynamo_event_source_props: typing.Any = None,
        dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        sqs_dlq_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param deploy_sqs_dlq_queue: Whether to deploy a SQS dead letter queue when a data record reaches the Maximum Retry Attempts or Maximum Record Age, its metadata like shard ID and stream ARN will be sent to an SQS queue. Default: - true.
        :param dynamo_event_source_props: Optional user provided props to override the default props. Default: - Default props are used
        :param dynamo_table_props: Optional user provided props to override the default props for the DynamoDB Table. Providing both this and ``existingTableInterface`` is an error. Default: - Partition key ID: string
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_table_interface: Optional - existing DynamoDB table, providing both this and ``dynamoTableProps`` will cause an error. Default: - None
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param sqs_dlq_queue_props: Optional user provided properties for the SQS dead letter queue. Default: - Default props are used

        :access: public
        :summary: Constructs a new instance of the LambdaToDynamoDB class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3c70d1c832501a8ca89dc559c7a2e0f4cc311e8b3ff7542ba16d41e65e7fde99)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = DynamoDBStreamsToLambdaProps(
            deploy_sqs_dlq_queue=deploy_sqs_dlq_queue,
            dynamo_event_source_props=dynamo_event_source_props,
            dynamo_table_props=dynamo_table_props,
            existing_lambda_obj=existing_lambda_obj,
            existing_table_interface=existing_table_interface,
            lambda_function_props=lambda_function_props,
            sqs_dlq_queue_props=sqs_dlq_queue_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="dynamoTableInterface")
    def dynamo_table_interface(self) -> _aws_cdk_aws_dynamodb_ceddda9d.ITable:
        return typing.cast(_aws_cdk_aws_dynamodb_ceddda9d.ITable, jsii.get(self, "dynamoTableInterface"))

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="dynamoTable")
    def dynamo_table(self) -> typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table]:
        return typing.cast(typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table], jsii.get(self, "dynamoTable"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-dynamodbstreams-lambda.DynamoDBStreamsToLambdaProps",
    jsii_struct_bases=[],
    name_mapping={
        "deploy_sqs_dlq_queue": "deploySqsDlqQueue",
        "dynamo_event_source_props": "dynamoEventSourceProps",
        "dynamo_table_props": "dynamoTableProps",
        "existing_lambda_obj": "existingLambdaObj",
        "existing_table_interface": "existingTableInterface",
        "lambda_function_props": "lambdaFunctionProps",
        "sqs_dlq_queue_props": "sqsDlqQueueProps",
    },
)
class DynamoDBStreamsToLambdaProps:
    def __init__(
        self,
        *,
        deploy_sqs_dlq_queue: typing.Optional[builtins.bool] = None,
        dynamo_event_source_props: typing.Any = None,
        dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        sqs_dlq_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param deploy_sqs_dlq_queue: Whether to deploy a SQS dead letter queue when a data record reaches the Maximum Retry Attempts or Maximum Record Age, its metadata like shard ID and stream ARN will be sent to an SQS queue. Default: - true.
        :param dynamo_event_source_props: Optional user provided props to override the default props. Default: - Default props are used
        :param dynamo_table_props: Optional user provided props to override the default props for the DynamoDB Table. Providing both this and ``existingTableInterface`` is an error. Default: - Partition key ID: string
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_table_interface: Optional - existing DynamoDB table, providing both this and ``dynamoTableProps`` will cause an error. Default: - None
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param sqs_dlq_queue_props: Optional user provided properties for the SQS dead letter queue. Default: - Default props are used

        :summary: The properties for the DynamoDBStreamsToLambda Construct
        '''
        if isinstance(dynamo_table_props, dict):
            dynamo_table_props = _aws_cdk_aws_dynamodb_ceddda9d.TableProps(**dynamo_table_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(sqs_dlq_queue_props, dict):
            sqs_dlq_queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**sqs_dlq_queue_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dc7e792539bcf7a63a525f59186a2dcbdebba6de562e1d1048e6c0075cd0ea97)
            check_type(argname="argument deploy_sqs_dlq_queue", value=deploy_sqs_dlq_queue, expected_type=type_hints["deploy_sqs_dlq_queue"])
            check_type(argname="argument dynamo_event_source_props", value=dynamo_event_source_props, expected_type=type_hints["dynamo_event_source_props"])
            check_type(argname="argument dynamo_table_props", value=dynamo_table_props, expected_type=type_hints["dynamo_table_props"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument existing_table_interface", value=existing_table_interface, expected_type=type_hints["existing_table_interface"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument sqs_dlq_queue_props", value=sqs_dlq_queue_props, expected_type=type_hints["sqs_dlq_queue_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if deploy_sqs_dlq_queue is not None:
            self._values["deploy_sqs_dlq_queue"] = deploy_sqs_dlq_queue
        if dynamo_event_source_props is not None:
            self._values["dynamo_event_source_props"] = dynamo_event_source_props
        if dynamo_table_props is not None:
            self._values["dynamo_table_props"] = dynamo_table_props
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if existing_table_interface is not None:
            self._values["existing_table_interface"] = existing_table_interface
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if sqs_dlq_queue_props is not None:
            self._values["sqs_dlq_queue_props"] = sqs_dlq_queue_props

    @builtins.property
    def deploy_sqs_dlq_queue(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a SQS dead letter queue when a data record reaches the Maximum Retry Attempts or Maximum Record Age, its metadata like shard ID and stream ARN will be sent to an SQS queue.

        :default: - true.
        '''
        result = self._values.get("deploy_sqs_dlq_queue")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def dynamo_event_source_props(self) -> typing.Any:
        '''Optional user provided props to override the default props.

        :default: - Default props are used
        '''
        result = self._values.get("dynamo_event_source_props")
        return typing.cast(typing.Any, result)

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
    def existing_lambda_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function]:
        '''Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_lambda_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function], result)

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
    def lambda_function_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps]:
        '''Optional - user provided props to override the default props for the Lambda function.

        Providing both this and ``existingLambdaObj`` is an error.

        :default: - Default props are used
        '''
        result = self._values.get("lambda_function_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps], result)

    @builtins.property
    def sqs_dlq_queue_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''Optional user provided properties for the SQS dead letter queue.

        :default: - Default props are used
        '''
        result = self._values.get("sqs_dlq_queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DynamoDBStreamsToLambdaProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "DynamoDBStreamsToLambda",
    "DynamoDBStreamsToLambdaProps",
]

publication.publish()

def _typecheckingstub__3c70d1c832501a8ca89dc559c7a2e0f4cc311e8b3ff7542ba16d41e65e7fde99(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    deploy_sqs_dlq_queue: typing.Optional[builtins.bool] = None,
    dynamo_event_source_props: typing.Any = None,
    dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    sqs_dlq_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dc7e792539bcf7a63a525f59186a2dcbdebba6de562e1d1048e6c0075cd0ea97(
    *,
    deploy_sqs_dlq_queue: typing.Optional[builtins.bool] = None,
    dynamo_event_source_props: typing.Any = None,
    dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    sqs_dlq_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
