r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-lambda-sagemakerendpoint/README.adoc)
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
import aws_cdk.aws_sagemaker as _aws_cdk_aws_sagemaker_ceddda9d
import constructs as _constructs_77d1e7e8


class LambdaToSagemakerEndpoint(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-lambda-sagemakerendpoint.LambdaToSagemakerEndpoint",
):
    '''
    :summary: The LambdaToSagemakerEndpoint class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        endpoint_config_props: typing.Optional[typing.Union[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointConfigProps, typing.Dict[builtins.str, typing.Any]]] = None,
        endpoint_props: typing.Optional[typing.Union[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_sagemaker_endpoint_obj: typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpoint] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        model_props: typing.Any = None,
        sagemaker_environment_variable_name: typing.Optional[builtins.str] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a scope-unique id.
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param endpoint_config_props: User provided props to create SageMaker Endpoint Configuration. Default: - Default props are used
        :param endpoint_props: User provided props to create SageMaker Endpoint. Default: - Default props are used
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_sagemaker_endpoint_obj: Existing SageMaker Endpoint object, providing both this and endpointProps will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case). Default: - None
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param model_props: User provided props to create SageMaker Model. Default: - None
        :param sagemaker_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the SageMaker endpoint. Default: - SAGEMAKER_ENDPOINT_NAME
        :param vpc_props: Properties to override default properties if deployVpc is true. Default: - None

        :access: public
        :since: 1.87.1
        :summary: Constructs a new instance of the LambdaToSagemakerEndpoint class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bf9d2e0463ae174b142d99fe4bd598445b64467b76ddd95c55778c856c79d69e)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = LambdaToSagemakerEndpointProps(
            deploy_vpc=deploy_vpc,
            endpoint_config_props=endpoint_config_props,
            endpoint_props=endpoint_props,
            existing_lambda_obj=existing_lambda_obj,
            existing_sagemaker_endpoint_obj=existing_sagemaker_endpoint_obj,
            existing_vpc=existing_vpc,
            lambda_function_props=lambda_function_props,
            model_props=model_props,
            sagemaker_environment_variable_name=sagemaker_environment_variable_name,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="sagemakerEndpoint")
    def sagemaker_endpoint(self) -> _aws_cdk_aws_sagemaker_ceddda9d.CfnEndpoint:
        return typing.cast(_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpoint, jsii.get(self, "sagemakerEndpoint"))

    @builtins.property
    @jsii.member(jsii_name="sagemakerEndpointConfig")
    def sagemaker_endpoint_config(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointConfig]:
        return typing.cast(typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointConfig], jsii.get(self, "sagemakerEndpointConfig"))

    @builtins.property
    @jsii.member(jsii_name="sagemakerModel")
    def sagemaker_model(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnModel]:
        return typing.cast(typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnModel], jsii.get(self, "sagemakerModel"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-lambda-sagemakerendpoint.LambdaToSagemakerEndpointProps",
    jsii_struct_bases=[],
    name_mapping={
        "deploy_vpc": "deployVpc",
        "endpoint_config_props": "endpointConfigProps",
        "endpoint_props": "endpointProps",
        "existing_lambda_obj": "existingLambdaObj",
        "existing_sagemaker_endpoint_obj": "existingSagemakerEndpointObj",
        "existing_vpc": "existingVpc",
        "lambda_function_props": "lambdaFunctionProps",
        "model_props": "modelProps",
        "sagemaker_environment_variable_name": "sagemakerEnvironmentVariableName",
        "vpc_props": "vpcProps",
    },
)
class LambdaToSagemakerEndpointProps:
    def __init__(
        self,
        *,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        endpoint_config_props: typing.Optional[typing.Union[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointConfigProps, typing.Dict[builtins.str, typing.Any]]] = None,
        endpoint_props: typing.Optional[typing.Union[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_sagemaker_endpoint_obj: typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpoint] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        model_props: typing.Any = None,
        sagemaker_environment_variable_name: typing.Optional[builtins.str] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param endpoint_config_props: User provided props to create SageMaker Endpoint Configuration. Default: - Default props are used
        :param endpoint_props: User provided props to create SageMaker Endpoint. Default: - Default props are used
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_sagemaker_endpoint_obj: Existing SageMaker Endpoint object, providing both this and endpointProps will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case). Default: - None
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param model_props: User provided props to create SageMaker Model. Default: - None
        :param sagemaker_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the SageMaker endpoint. Default: - SAGEMAKER_ENDPOINT_NAME
        :param vpc_props: Properties to override default properties if deployVpc is true. Default: - None

        :summary: The properties for the LambdaToSagemakerEndpoint class
        '''
        if isinstance(endpoint_config_props, dict):
            endpoint_config_props = _aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointConfigProps(**endpoint_config_props)
        if isinstance(endpoint_props, dict):
            endpoint_props = _aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointProps(**endpoint_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c5f786655886d43fcb2a8501f8efcb38e4abc0e7d4540e404b9963c489d4d8ac)
            check_type(argname="argument deploy_vpc", value=deploy_vpc, expected_type=type_hints["deploy_vpc"])
            check_type(argname="argument endpoint_config_props", value=endpoint_config_props, expected_type=type_hints["endpoint_config_props"])
            check_type(argname="argument endpoint_props", value=endpoint_props, expected_type=type_hints["endpoint_props"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument existing_sagemaker_endpoint_obj", value=existing_sagemaker_endpoint_obj, expected_type=type_hints["existing_sagemaker_endpoint_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument model_props", value=model_props, expected_type=type_hints["model_props"])
            check_type(argname="argument sagemaker_environment_variable_name", value=sagemaker_environment_variable_name, expected_type=type_hints["sagemaker_environment_variable_name"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if deploy_vpc is not None:
            self._values["deploy_vpc"] = deploy_vpc
        if endpoint_config_props is not None:
            self._values["endpoint_config_props"] = endpoint_config_props
        if endpoint_props is not None:
            self._values["endpoint_props"] = endpoint_props
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if existing_sagemaker_endpoint_obj is not None:
            self._values["existing_sagemaker_endpoint_obj"] = existing_sagemaker_endpoint_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if model_props is not None:
            self._values["model_props"] = model_props
        if sagemaker_environment_variable_name is not None:
            self._values["sagemaker_environment_variable_name"] = sagemaker_environment_variable_name
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def deploy_vpc(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a new VPC.

        :default: - false
        '''
        result = self._values.get("deploy_vpc")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def endpoint_config_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointConfigProps]:
        '''User provided props to create SageMaker Endpoint Configuration.

        :default: - Default props are used
        '''
        result = self._values.get("endpoint_config_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointConfigProps], result)

    @builtins.property
    def endpoint_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointProps]:
        '''User provided props to create SageMaker Endpoint.

        :default: - Default props are used
        '''
        result = self._values.get("endpoint_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointProps], result)

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
    def existing_sagemaker_endpoint_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpoint]:
        '''Existing SageMaker Endpoint object, providing both this and endpointProps will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_sagemaker_endpoint_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpoint], result)

    @builtins.property
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC for the construct to use (construct will NOT create a new VPC in this case).

        :default: - None
        '''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

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
    def model_props(self) -> typing.Any:
        '''User provided props to create SageMaker Model.

        :default: - None
        '''
        result = self._values.get("model_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def sagemaker_environment_variable_name(self) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the name of the SageMaker endpoint.

        :default: - SAGEMAKER_ENDPOINT_NAME
        '''
        result = self._values.get("sagemaker_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vpc_props(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps]:
        '''Properties to override default properties if deployVpc is true.

        :default: - None
        '''
        result = self._values.get("vpc_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LambdaToSagemakerEndpointProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "LambdaToSagemakerEndpoint",
    "LambdaToSagemakerEndpointProps",
]

publication.publish()

def _typecheckingstub__bf9d2e0463ae174b142d99fe4bd598445b64467b76ddd95c55778c856c79d69e(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    endpoint_config_props: typing.Optional[typing.Union[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointConfigProps, typing.Dict[builtins.str, typing.Any]]] = None,
    endpoint_props: typing.Optional[typing.Union[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_sagemaker_endpoint_obj: typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpoint] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    model_props: typing.Any = None,
    sagemaker_environment_variable_name: typing.Optional[builtins.str] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c5f786655886d43fcb2a8501f8efcb38e4abc0e7d4540e404b9963c489d4d8ac(
    *,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    endpoint_config_props: typing.Optional[typing.Union[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointConfigProps, typing.Dict[builtins.str, typing.Any]]] = None,
    endpoint_props: typing.Optional[typing.Union[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpointProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_sagemaker_endpoint_obj: typing.Optional[_aws_cdk_aws_sagemaker_ceddda9d.CfnEndpoint] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    model_props: typing.Any = None,
    sagemaker_environment_variable_name: typing.Optional[builtins.str] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
