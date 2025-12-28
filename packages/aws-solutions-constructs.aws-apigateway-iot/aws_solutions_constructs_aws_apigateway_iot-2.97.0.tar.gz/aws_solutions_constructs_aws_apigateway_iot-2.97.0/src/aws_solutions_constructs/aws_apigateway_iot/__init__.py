r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-apigateway-iot/README.adoc)
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
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import constructs as _constructs_77d1e7e8


class ApiGatewayToIot(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-apigateway-iot.ApiGatewayToIot",
):
    '''
    :summary: The ApiGatewayIot class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        iot_endpoint: builtins.str,
        api_gateway_create_api_key: typing.Optional[builtins.bool] = None,
        api_gateway_execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
        create_usage_plan: typing.Optional[builtins.bool] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param iot_endpoint: The AWS IoT endpoint subdomain to integrate the API Gateway with (e.g ab123cdefghij4l-ats). Added as AWS Subdomain to the Integration Request. Note that this must reference the ATS endpoint to avoid SSL certificate trust issues. Default: - None.
        :param api_gateway_create_api_key: Creates an api key and associates to usage plan if set to true. Default: - false
        :param api_gateway_execution_role: The IAM role that is used by API Gateway to publish messages to IoT topics and Thing shadows. Default: - An IAM role with iot:Publish access to all topics (topic/*) and iot:UpdateThingShadow access to all things (thing/*) is created.
        :param api_gateway_props: Optional user-provided props to override the default props for the API. Default: - Default props are used.
        :param create_usage_plan: Whether to create a Usage Plan attached to the API. Must be true if apiGatewayProps.defaultMethodOptions.apiKeyRequired is true Default: - true (to match legacy behavior)
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the ApiGatewayIot class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2e924fb0cf81b109b48a204074c76b3f0589533998633acfa966ff106a85324c)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ApiGatewayToIotProps(
            iot_endpoint=iot_endpoint,
            api_gateway_create_api_key=api_gateway_create_api_key,
            api_gateway_execution_role=api_gateway_execution_role,
            api_gateway_props=api_gateway_props,
            create_usage_plan=create_usage_plan,
            log_group_props=log_group_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="apiGateway")
    def api_gateway(self) -> _aws_cdk_aws_apigateway_ceddda9d.RestApi:
        return typing.cast(_aws_cdk_aws_apigateway_ceddda9d.RestApi, jsii.get(self, "apiGateway"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayLogGroup")
    def api_gateway_log_group(self) -> _aws_cdk_aws_logs_ceddda9d.LogGroup:
        return typing.cast(_aws_cdk_aws_logs_ceddda9d.LogGroup, jsii.get(self, "apiGatewayLogGroup"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayRole")
    def api_gateway_role(self) -> _aws_cdk_aws_iam_ceddda9d.IRole:
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.IRole, jsii.get(self, "apiGatewayRole"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayCloudWatchRole")
    def api_gateway_cloud_watch_role(
        self,
    ) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role]:
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role], jsii.get(self, "apiGatewayCloudWatchRole"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-apigateway-iot.ApiGatewayToIotProps",
    jsii_struct_bases=[],
    name_mapping={
        "iot_endpoint": "iotEndpoint",
        "api_gateway_create_api_key": "apiGatewayCreateApiKey",
        "api_gateway_execution_role": "apiGatewayExecutionRole",
        "api_gateway_props": "apiGatewayProps",
        "create_usage_plan": "createUsagePlan",
        "log_group_props": "logGroupProps",
    },
)
class ApiGatewayToIotProps:
    def __init__(
        self,
        *,
        iot_endpoint: builtins.str,
        api_gateway_create_api_key: typing.Optional[builtins.bool] = None,
        api_gateway_execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
        api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
        create_usage_plan: typing.Optional[builtins.bool] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''The properties for the ApiGatewayIot class.

        :param iot_endpoint: The AWS IoT endpoint subdomain to integrate the API Gateway with (e.g ab123cdefghij4l-ats). Added as AWS Subdomain to the Integration Request. Note that this must reference the ATS endpoint to avoid SSL certificate trust issues. Default: - None.
        :param api_gateway_create_api_key: Creates an api key and associates to usage plan if set to true. Default: - false
        :param api_gateway_execution_role: The IAM role that is used by API Gateway to publish messages to IoT topics and Thing shadows. Default: - An IAM role with iot:Publish access to all topics (topic/*) and iot:UpdateThingShadow access to all things (thing/*) is created.
        :param api_gateway_props: Optional user-provided props to override the default props for the API. Default: - Default props are used.
        :param create_usage_plan: Whether to create a Usage Plan attached to the API. Must be true if apiGatewayProps.defaultMethodOptions.apiKeyRequired is true Default: - true (to match legacy behavior)
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        '''
        if isinstance(api_gateway_props, dict):
            api_gateway_props = _aws_cdk_aws_apigateway_ceddda9d.RestApiProps(**api_gateway_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8700595a6a6afd7bc80184c79201387ce9c5cc241bfb91bc3cf126abc3e944c8)
            check_type(argname="argument iot_endpoint", value=iot_endpoint, expected_type=type_hints["iot_endpoint"])
            check_type(argname="argument api_gateway_create_api_key", value=api_gateway_create_api_key, expected_type=type_hints["api_gateway_create_api_key"])
            check_type(argname="argument api_gateway_execution_role", value=api_gateway_execution_role, expected_type=type_hints["api_gateway_execution_role"])
            check_type(argname="argument api_gateway_props", value=api_gateway_props, expected_type=type_hints["api_gateway_props"])
            check_type(argname="argument create_usage_plan", value=create_usage_plan, expected_type=type_hints["create_usage_plan"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "iot_endpoint": iot_endpoint,
        }
        if api_gateway_create_api_key is not None:
            self._values["api_gateway_create_api_key"] = api_gateway_create_api_key
        if api_gateway_execution_role is not None:
            self._values["api_gateway_execution_role"] = api_gateway_execution_role
        if api_gateway_props is not None:
            self._values["api_gateway_props"] = api_gateway_props
        if create_usage_plan is not None:
            self._values["create_usage_plan"] = create_usage_plan
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props

    @builtins.property
    def iot_endpoint(self) -> builtins.str:
        '''The AWS IoT endpoint subdomain to integrate the API Gateway with (e.g ab123cdefghij4l-ats). Added as AWS Subdomain to the Integration Request. Note that this must reference the ATS endpoint to avoid SSL certificate trust issues.

        :default: - None.
        '''
        result = self._values.get("iot_endpoint")
        assert result is not None, "Required property 'iot_endpoint' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def api_gateway_create_api_key(self) -> typing.Optional[builtins.bool]:
        '''Creates an api key and associates to usage plan if set to true.

        :default: - false
        '''
        result = self._values.get("api_gateway_create_api_key")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def api_gateway_execution_role(
        self,
    ) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole]:
        '''The IAM role that is used by API Gateway to publish messages to IoT topics and Thing shadows.

        :default: - An IAM role with iot:Publish access to all topics (topic/*) and iot:UpdateThingShadow access to all things (thing/*) is created.
        '''
        result = self._values.get("api_gateway_execution_role")
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole], result)

    @builtins.property
    def api_gateway_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps]:
        '''Optional user-provided props to override the default props for the API.

        :default: - Default props are used.
        '''
        result = self._values.get("api_gateway_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps], result)

    @builtins.property
    def create_usage_plan(self) -> typing.Optional[builtins.bool]:
        '''Whether to create a Usage Plan attached to the API.

        Must be true if
        apiGatewayProps.defaultMethodOptions.apiKeyRequired is true

        :default: - true (to match legacy behavior)
        '''
        result = self._values.get("create_usage_plan")
        return typing.cast(typing.Optional[builtins.bool], result)

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
        return "ApiGatewayToIotProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "ApiGatewayToIot",
    "ApiGatewayToIotProps",
]

publication.publish()

def _typecheckingstub__2e924fb0cf81b109b48a204074c76b3f0589533998633acfa966ff106a85324c(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    iot_endpoint: builtins.str,
    api_gateway_create_api_key: typing.Optional[builtins.bool] = None,
    api_gateway_execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
    create_usage_plan: typing.Optional[builtins.bool] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8700595a6a6afd7bc80184c79201387ce9c5cc241bfb91bc3cf126abc3e944c8(
    *,
    iot_endpoint: builtins.str,
    api_gateway_create_api_key: typing.Optional[builtins.bool] = None,
    api_gateway_execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
    create_usage_plan: typing.Optional[builtins.bool] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
