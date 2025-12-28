r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-cognito-apigateway-lambda/README.adoc)
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

import aws_cdk.aws_apigateway as _aws_cdk_aws_apigateway_ceddda9d
import aws_cdk.aws_cognito as _aws_cdk_aws_cognito_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import constructs as _constructs_77d1e7e8


class CognitoToApiGatewayToLambda(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-cognito-apigateway-lambda.CognitoToApiGatewayToLambda",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        api_gateway_props: typing.Any = None,
        cognito_user_pool_client_props: typing.Any = None,
        cognito_user_pool_props: typing.Optional[typing.Union[_aws_cdk_aws_cognito_ceddda9d.UserPoolProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param api_gateway_props: Optional - user-provided props to override the default props for the API Gateway API. Default: - Default props are used
        :param cognito_user_pool_client_props: Optional user provided props to override the default props. Default: - Default props are used
        :param cognito_user_pool_props: Optional user provided props to override the default props. Default: - Default props are used
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the CognitoToApiGatewayToLambda class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9eaca7accdfc384e47b78f4c089044c219ba9c177cea63b6b40cb28e2ff24b16)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = CognitoToApiGatewayToLambdaProps(
            api_gateway_props=api_gateway_props,
            cognito_user_pool_client_props=cognito_user_pool_client_props,
            cognito_user_pool_props=cognito_user_pool_props,
            existing_lambda_obj=existing_lambda_obj,
            lambda_function_props=lambda_function_props,
            log_group_props=log_group_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="addAuthorizers")
    def add_authorizers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "addAuthorizers", []))

    @builtins.property
    @jsii.member(jsii_name="apiGateway")
    def api_gateway(self) -> _aws_cdk_aws_apigateway_ceddda9d.RestApi:
        return typing.cast(_aws_cdk_aws_apigateway_ceddda9d.RestApi, jsii.get(self, "apiGateway"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayAuthorizer")
    def api_gateway_authorizer(self) -> _aws_cdk_aws_apigateway_ceddda9d.CfnAuthorizer:
        return typing.cast(_aws_cdk_aws_apigateway_ceddda9d.CfnAuthorizer, jsii.get(self, "apiGatewayAuthorizer"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayLogGroup")
    def api_gateway_log_group(self) -> _aws_cdk_aws_logs_ceddda9d.LogGroup:
        return typing.cast(_aws_cdk_aws_logs_ceddda9d.LogGroup, jsii.get(self, "apiGatewayLogGroup"))

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="userPool")
    def user_pool(self) -> _aws_cdk_aws_cognito_ceddda9d.UserPool:
        return typing.cast(_aws_cdk_aws_cognito_ceddda9d.UserPool, jsii.get(self, "userPool"))

    @builtins.property
    @jsii.member(jsii_name="userPoolClient")
    def user_pool_client(self) -> _aws_cdk_aws_cognito_ceddda9d.UserPoolClient:
        return typing.cast(_aws_cdk_aws_cognito_ceddda9d.UserPoolClient, jsii.get(self, "userPoolClient"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayCloudWatchRole")
    def api_gateway_cloud_watch_role(
        self,
    ) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role]:
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role], jsii.get(self, "apiGatewayCloudWatchRole"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-cognito-apigateway-lambda.CognitoToApiGatewayToLambdaProps",
    jsii_struct_bases=[],
    name_mapping={
        "api_gateway_props": "apiGatewayProps",
        "cognito_user_pool_client_props": "cognitoUserPoolClientProps",
        "cognito_user_pool_props": "cognitoUserPoolProps",
        "existing_lambda_obj": "existingLambdaObj",
        "lambda_function_props": "lambdaFunctionProps",
        "log_group_props": "logGroupProps",
    },
)
class CognitoToApiGatewayToLambdaProps:
    def __init__(
        self,
        *,
        api_gateway_props: typing.Any = None,
        cognito_user_pool_client_props: typing.Any = None,
        cognito_user_pool_props: typing.Optional[typing.Union[_aws_cdk_aws_cognito_ceddda9d.UserPoolProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param api_gateway_props: Optional - user-provided props to override the default props for the API Gateway API. Default: - Default props are used
        :param cognito_user_pool_client_props: Optional user provided props to override the default props. Default: - Default props are used
        :param cognito_user_pool_props: Optional user provided props to override the default props. Default: - Default props are used
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used

        :summary: The properties for the CognitoToApiGatewayToLambda Construct
        '''
        if isinstance(cognito_user_pool_props, dict):
            cognito_user_pool_props = _aws_cdk_aws_cognito_ceddda9d.UserPoolProps(**cognito_user_pool_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8bfa34a711df2d1b926e3245de46541d8e27a3c36644ce41267003a58998b336)
            check_type(argname="argument api_gateway_props", value=api_gateway_props, expected_type=type_hints["api_gateway_props"])
            check_type(argname="argument cognito_user_pool_client_props", value=cognito_user_pool_client_props, expected_type=type_hints["cognito_user_pool_client_props"])
            check_type(argname="argument cognito_user_pool_props", value=cognito_user_pool_props, expected_type=type_hints["cognito_user_pool_props"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if api_gateway_props is not None:
            self._values["api_gateway_props"] = api_gateway_props
        if cognito_user_pool_client_props is not None:
            self._values["cognito_user_pool_client_props"] = cognito_user_pool_client_props
        if cognito_user_pool_props is not None:
            self._values["cognito_user_pool_props"] = cognito_user_pool_props
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props

    @builtins.property
    def api_gateway_props(self) -> typing.Any:
        '''Optional - user-provided props to override the default props for the API Gateway API.

        :default: - Default props are used
        '''
        result = self._values.get("api_gateway_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def cognito_user_pool_client_props(self) -> typing.Any:
        '''Optional user provided props to override the default props.

        :default: - Default props are used
        '''
        result = self._values.get("cognito_user_pool_client_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def cognito_user_pool_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_cognito_ceddda9d.UserPoolProps]:
        '''Optional user provided props to override the default props.

        :default: - Default props are used
        '''
        result = self._values.get("cognito_user_pool_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_cognito_ceddda9d.UserPoolProps], result)

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
    def log_group_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps]:
        '''User provided props to override the default props for the CloudWatchLogs LogGroup.

        :default: - Default props are used
        '''
        result = self._values.get("log_group_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CognitoToApiGatewayToLambdaProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "CognitoToApiGatewayToLambda",
    "CognitoToApiGatewayToLambdaProps",
]

publication.publish()

def _typecheckingstub__9eaca7accdfc384e47b78f4c089044c219ba9c177cea63b6b40cb28e2ff24b16(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    api_gateway_props: typing.Any = None,
    cognito_user_pool_client_props: typing.Any = None,
    cognito_user_pool_props: typing.Optional[typing.Union[_aws_cdk_aws_cognito_ceddda9d.UserPoolProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8bfa34a711df2d1b926e3245de46541d8e27a3c36644ce41267003a58998b336(
    *,
    api_gateway_props: typing.Any = None,
    cognito_user_pool_client_props: typing.Any = None,
    cognito_user_pool_props: typing.Optional[typing.Union[_aws_cdk_aws_cognito_ceddda9d.UserPoolProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
