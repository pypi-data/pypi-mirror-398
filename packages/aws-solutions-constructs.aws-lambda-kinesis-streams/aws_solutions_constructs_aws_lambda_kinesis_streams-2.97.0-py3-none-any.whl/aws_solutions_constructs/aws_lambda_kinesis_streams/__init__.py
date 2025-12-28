r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-lambda-kinesisstreams/README.adoc)
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
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_kinesis as _aws_cdk_aws_kinesis_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import constructs as _constructs_77d1e7e8


class LambdaToKinesisStreams(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-lambda-kinesisstreams.LambdaToKinesisStreams",
):
    '''
    :summary: The LambdaToKinesisStream class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        kinesis_stream_props: typing.Optional[typing.Union[_aws_cdk_aws_kinesis_ceddda9d.StreamProps, typing.Dict[builtins.str, typing.Any]]] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        stream_environment_variable_name: typing.Optional[builtins.str] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms for the Kinesis Stream. Default: - Alarms are created
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_stream_obj: Existing instance of Kinesis Stream, providing both this and ``kinesisStreamProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param kinesis_stream_props: Optional user-provided props to override the default props for the Kinesis stream. Default: - Default props are used.
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used.
        :param stream_environment_variable_name: Optional Name to override the Lambda Function default environment variable name that holds the Kinesis Data Stream name value. Default: - KINESIS_DATASTREAM_NAME
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the KinesisStreamsToLambda class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__67db5be410f2eb1981e9457be7006209df12c5478fd3b3f06299f8efbc047eb6)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = LambdaToKinesisStreamsProps(
            create_cloud_watch_alarms=create_cloud_watch_alarms,
            deploy_vpc=deploy_vpc,
            existing_lambda_obj=existing_lambda_obj,
            existing_stream_obj=existing_stream_obj,
            existing_vpc=existing_vpc,
            kinesis_stream_props=kinesis_stream_props,
            lambda_function_props=lambda_function_props,
            stream_environment_variable_name=stream_environment_variable_name,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="kinesisStream")
    def kinesis_stream(self) -> _aws_cdk_aws_kinesis_ceddda9d.Stream:
        return typing.cast(_aws_cdk_aws_kinesis_ceddda9d.Stream, jsii.get(self, "kinesisStream"))

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="cloudwatchAlarms")
    def cloudwatch_alarms(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_cloudwatch_ceddda9d.Alarm]]:
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_cloudwatch_ceddda9d.Alarm]], jsii.get(self, "cloudwatchAlarms"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-lambda-kinesisstreams.LambdaToKinesisStreamsProps",
    jsii_struct_bases=[],
    name_mapping={
        "create_cloud_watch_alarms": "createCloudWatchAlarms",
        "deploy_vpc": "deployVpc",
        "existing_lambda_obj": "existingLambdaObj",
        "existing_stream_obj": "existingStreamObj",
        "existing_vpc": "existingVpc",
        "kinesis_stream_props": "kinesisStreamProps",
        "lambda_function_props": "lambdaFunctionProps",
        "stream_environment_variable_name": "streamEnvironmentVariableName",
        "vpc_props": "vpcProps",
    },
)
class LambdaToKinesisStreamsProps:
    def __init__(
        self,
        *,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        kinesis_stream_props: typing.Optional[typing.Union[_aws_cdk_aws_kinesis_ceddda9d.StreamProps, typing.Dict[builtins.str, typing.Any]]] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        stream_environment_variable_name: typing.Optional[builtins.str] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''The properties for the LambdaToKinesisStreams class.

        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms for the Kinesis Stream. Default: - Alarms are created
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_stream_obj: Existing instance of Kinesis Stream, providing both this and ``kinesisStreamProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param kinesis_stream_props: Optional user-provided props to override the default props for the Kinesis stream. Default: - Default props are used.
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used.
        :param stream_environment_variable_name: Optional Name to override the Lambda Function default environment variable name that holds the Kinesis Data Stream name value. Default: - KINESIS_DATASTREAM_NAME
        :param vpc_props: Properties to override default properties if deployVpc is true.
        '''
        if isinstance(kinesis_stream_props, dict):
            kinesis_stream_props = _aws_cdk_aws_kinesis_ceddda9d.StreamProps(**kinesis_stream_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fb9026f620d0f1877fecfd16d8264bd0472521b09f79bf8872c5ff227eabc595)
            check_type(argname="argument create_cloud_watch_alarms", value=create_cloud_watch_alarms, expected_type=type_hints["create_cloud_watch_alarms"])
            check_type(argname="argument deploy_vpc", value=deploy_vpc, expected_type=type_hints["deploy_vpc"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument existing_stream_obj", value=existing_stream_obj, expected_type=type_hints["existing_stream_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument kinesis_stream_props", value=kinesis_stream_props, expected_type=type_hints["kinesis_stream_props"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument stream_environment_variable_name", value=stream_environment_variable_name, expected_type=type_hints["stream_environment_variable_name"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create_cloud_watch_alarms is not None:
            self._values["create_cloud_watch_alarms"] = create_cloud_watch_alarms
        if deploy_vpc is not None:
            self._values["deploy_vpc"] = deploy_vpc
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if existing_stream_obj is not None:
            self._values["existing_stream_obj"] = existing_stream_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if kinesis_stream_props is not None:
            self._values["kinesis_stream_props"] = kinesis_stream_props
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if stream_environment_variable_name is not None:
            self._values["stream_environment_variable_name"] = stream_environment_variable_name
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def create_cloud_watch_alarms(self) -> typing.Optional[builtins.bool]:
        '''Whether to create recommended CloudWatch alarms for the Kinesis Stream.

        :default: - Alarms are created
        '''
        result = self._values.get("create_cloud_watch_alarms")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def deploy_vpc(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a new VPC.

        :default: - false
        '''
        result = self._values.get("deploy_vpc")
        return typing.cast(typing.Optional[builtins.bool], result)

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
    def existing_stream_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream]:
        '''Existing instance of Kinesis Stream, providing both this and ``kinesisStreamProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_stream_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream], result)

    @builtins.property
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC for the construct to use (construct will NOT create a new VPC in this case).'''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def kinesis_stream_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.StreamProps]:
        '''Optional user-provided props to override the default props for the Kinesis stream.

        :default: - Default props are used.
        '''
        result = self._values.get("kinesis_stream_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.StreamProps], result)

    @builtins.property
    def lambda_function_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps]:
        '''Optional - user provided props to override the default props for the Lambda function.

        Providing both this and ``existingLambdaObj`` is an error.

        :default: - Default props are used.
        '''
        result = self._values.get("lambda_function_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps], result)

    @builtins.property
    def stream_environment_variable_name(self) -> typing.Optional[builtins.str]:
        '''Optional Name to override the Lambda Function default environment variable name that holds the Kinesis Data Stream name value.

        :default: - KINESIS_DATASTREAM_NAME
        '''
        result = self._values.get("stream_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

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
        return "LambdaToKinesisStreamsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "LambdaToKinesisStreams",
    "LambdaToKinesisStreamsProps",
]

publication.publish()

def _typecheckingstub__67db5be410f2eb1981e9457be7006209df12c5478fd3b3f06299f8efbc047eb6(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    kinesis_stream_props: typing.Optional[typing.Union[_aws_cdk_aws_kinesis_ceddda9d.StreamProps, typing.Dict[builtins.str, typing.Any]]] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    stream_environment_variable_name: typing.Optional[builtins.str] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fb9026f620d0f1877fecfd16d8264bd0472521b09f79bf8872c5ff227eabc595(
    *,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    kinesis_stream_props: typing.Optional[typing.Union[_aws_cdk_aws_kinesis_ceddda9d.StreamProps, typing.Dict[builtins.str, typing.Any]]] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    stream_environment_variable_name: typing.Optional[builtins.str] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
