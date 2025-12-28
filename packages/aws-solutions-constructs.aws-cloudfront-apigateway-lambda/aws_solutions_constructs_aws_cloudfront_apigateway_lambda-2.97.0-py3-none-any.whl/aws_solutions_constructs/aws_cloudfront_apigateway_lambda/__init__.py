r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-cloudfront-apigateway-lambda/README.adoc)
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
import aws_cdk.aws_cloudfront as _aws_cdk_aws_cloudfront_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import constructs as _constructs_77d1e7e8


class CloudFrontToApiGatewayToLambda(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-cloudfront-apigateway-lambda.CloudFrontToApiGatewayToLambda",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        api_gateway_props: typing.Any,
        cloud_front_distribution_props: typing.Any = None,
        cloud_front_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        create_usage_plan: typing.Optional[builtins.bool] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        insert_http_security_headers: typing.Optional[builtins.bool] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        response_headers_policy_props: typing.Optional[typing.Union[_aws_cdk_aws_cloudfront_ceddda9d.ResponseHeadersPolicyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param api_gateway_props: User provided props to override the default props for the API Gateway. As of release 2.48.0, clients must include this property with defaultMethodOptions: { authorizationType: string } specified. See Issue1043 in the github repo https://github.com/awslabs/aws-solutions-constructs/issues/1043 Default: - defaultMethodOptions/authorizationType is required, for other, unspecified values the default props are used
        :param cloud_front_distribution_props: Optional user provided props to override the default props. Default: - Default props are used
        :param cloud_front_logging_bucket_props: Optional user provided props to override the default props for the CloudFront Logging Bucket. Default: - Default props are used
        :param create_usage_plan: Whether to create a Usage Plan attached to the API. Must be true if apiGatewayProps.defaultMethodOptions.apiKeyRequired is true Default: - true (to match legacy behavior)
        :param existing_lambda_obj: Existing instance of Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param insert_http_security_headers: Optional user provided props to turn on/off the automatic injection of best practice HTTP security headers in all responses from cloudfront. Turning this on will inject default headers and is mutually exclusive with passing custom security headers via the responseHeadersPolicyProps parameter. Default: - true
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param log_group_props: Optional user provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param response_headers_policy_props: Optional user provided configuration that cloudfront applies to all http responses. Can be used to pass a custom ResponseSecurityHeadersBehavior, ResponseCustomHeadersBehavior or ResponseHeadersCorsBehavior to the cloudfront distribution. Passing a custom ResponseSecurityHeadersBehavior is mutually exclusive with turning on the default security headers via ``insertHttpSecurityHeaders`` prop. Will throw an error if both ``insertHttpSecurityHeaders`` is set to ``true`` and ResponseSecurityHeadersBehavior is passed. Default: - undefined

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the CloudFrontToApiGatewayToLambda class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__461316ff0e3f859e7f9f591a5b92a85dedccc24c1704e2e7c328642bf2e9bc9f)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = CloudFrontToApiGatewayToLambdaProps(
            api_gateway_props=api_gateway_props,
            cloud_front_distribution_props=cloud_front_distribution_props,
            cloud_front_logging_bucket_props=cloud_front_logging_bucket_props,
            create_usage_plan=create_usage_plan,
            existing_lambda_obj=existing_lambda_obj,
            insert_http_security_headers=insert_http_security_headers,
            lambda_function_props=lambda_function_props,
            log_group_props=log_group_props,
            response_headers_policy_props=response_headers_policy_props,
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
    @jsii.member(jsii_name="cloudFrontWebDistribution")
    def cloud_front_web_distribution(
        self,
    ) -> _aws_cdk_aws_cloudfront_ceddda9d.Distribution:
        return typing.cast(_aws_cdk_aws_cloudfront_ceddda9d.Distribution, jsii.get(self, "cloudFrontWebDistribution"))

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayCloudWatchRole")
    def api_gateway_cloud_watch_role(
        self,
    ) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role]:
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role], jsii.get(self, "apiGatewayCloudWatchRole"))

    @builtins.property
    @jsii.member(jsii_name="cloudFrontFunction")
    def cloud_front_function(
        self,
    ) -> typing.Optional[_aws_cdk_aws_cloudfront_ceddda9d.Function]:
        return typing.cast(typing.Optional[_aws_cdk_aws_cloudfront_ceddda9d.Function], jsii.get(self, "cloudFrontFunction"))

    @builtins.property
    @jsii.member(jsii_name="cloudFrontLoggingBucket")
    def cloud_front_logging_bucket(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "cloudFrontLoggingBucket"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-cloudfront-apigateway-lambda.CloudFrontToApiGatewayToLambdaProps",
    jsii_struct_bases=[],
    name_mapping={
        "api_gateway_props": "apiGatewayProps",
        "cloud_front_distribution_props": "cloudFrontDistributionProps",
        "cloud_front_logging_bucket_props": "cloudFrontLoggingBucketProps",
        "create_usage_plan": "createUsagePlan",
        "existing_lambda_obj": "existingLambdaObj",
        "insert_http_security_headers": "insertHttpSecurityHeaders",
        "lambda_function_props": "lambdaFunctionProps",
        "log_group_props": "logGroupProps",
        "response_headers_policy_props": "responseHeadersPolicyProps",
    },
)
class CloudFrontToApiGatewayToLambdaProps:
    def __init__(
        self,
        *,
        api_gateway_props: typing.Any,
        cloud_front_distribution_props: typing.Any = None,
        cloud_front_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        create_usage_plan: typing.Optional[builtins.bool] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        insert_http_security_headers: typing.Optional[builtins.bool] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        response_headers_policy_props: typing.Optional[typing.Union[_aws_cdk_aws_cloudfront_ceddda9d.ResponseHeadersPolicyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param api_gateway_props: User provided props to override the default props for the API Gateway. As of release 2.48.0, clients must include this property with defaultMethodOptions: { authorizationType: string } specified. See Issue1043 in the github repo https://github.com/awslabs/aws-solutions-constructs/issues/1043 Default: - defaultMethodOptions/authorizationType is required, for other, unspecified values the default props are used
        :param cloud_front_distribution_props: Optional user provided props to override the default props. Default: - Default props are used
        :param cloud_front_logging_bucket_props: Optional user provided props to override the default props for the CloudFront Logging Bucket. Default: - Default props are used
        :param create_usage_plan: Whether to create a Usage Plan attached to the API. Must be true if apiGatewayProps.defaultMethodOptions.apiKeyRequired is true Default: - true (to match legacy behavior)
        :param existing_lambda_obj: Existing instance of Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param insert_http_security_headers: Optional user provided props to turn on/off the automatic injection of best practice HTTP security headers in all responses from cloudfront. Turning this on will inject default headers and is mutually exclusive with passing custom security headers via the responseHeadersPolicyProps parameter. Default: - true
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param log_group_props: Optional user provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param response_headers_policy_props: Optional user provided configuration that cloudfront applies to all http responses. Can be used to pass a custom ResponseSecurityHeadersBehavior, ResponseCustomHeadersBehavior or ResponseHeadersCorsBehavior to the cloudfront distribution. Passing a custom ResponseSecurityHeadersBehavior is mutually exclusive with turning on the default security headers via ``insertHttpSecurityHeaders`` prop. Will throw an error if both ``insertHttpSecurityHeaders`` is set to ``true`` and ResponseSecurityHeadersBehavior is passed. Default: - undefined

        :summary: The properties for the CloudFrontToApiGatewayToLambda Construct
        '''
        if isinstance(cloud_front_logging_bucket_props, dict):
            cloud_front_logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**cloud_front_logging_bucket_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if isinstance(response_headers_policy_props, dict):
            response_headers_policy_props = _aws_cdk_aws_cloudfront_ceddda9d.ResponseHeadersPolicyProps(**response_headers_policy_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ce72cd5951b6f82c649ba294f738b5af3f429f19b161a863f8dc35b18bc06462)
            check_type(argname="argument api_gateway_props", value=api_gateway_props, expected_type=type_hints["api_gateway_props"])
            check_type(argname="argument cloud_front_distribution_props", value=cloud_front_distribution_props, expected_type=type_hints["cloud_front_distribution_props"])
            check_type(argname="argument cloud_front_logging_bucket_props", value=cloud_front_logging_bucket_props, expected_type=type_hints["cloud_front_logging_bucket_props"])
            check_type(argname="argument create_usage_plan", value=create_usage_plan, expected_type=type_hints["create_usage_plan"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument insert_http_security_headers", value=insert_http_security_headers, expected_type=type_hints["insert_http_security_headers"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
            check_type(argname="argument response_headers_policy_props", value=response_headers_policy_props, expected_type=type_hints["response_headers_policy_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "api_gateway_props": api_gateway_props,
        }
        if cloud_front_distribution_props is not None:
            self._values["cloud_front_distribution_props"] = cloud_front_distribution_props
        if cloud_front_logging_bucket_props is not None:
            self._values["cloud_front_logging_bucket_props"] = cloud_front_logging_bucket_props
        if create_usage_plan is not None:
            self._values["create_usage_plan"] = create_usage_plan
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if insert_http_security_headers is not None:
            self._values["insert_http_security_headers"] = insert_http_security_headers
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props
        if response_headers_policy_props is not None:
            self._values["response_headers_policy_props"] = response_headers_policy_props

    @builtins.property
    def api_gateway_props(self) -> typing.Any:
        '''User provided props to override the default props for the API Gateway.

        As of release
        2.48.0, clients must include this property with defaultMethodOptions: { authorizationType: string } specified.
        See Issue1043 in the github repo https://github.com/awslabs/aws-solutions-constructs/issues/1043

        :default:

        - defaultMethodOptions/authorizationType is required, for other, unspecified values the
        default props are used
        '''
        result = self._values.get("api_gateway_props")
        assert result is not None, "Required property 'api_gateway_props' is missing"
        return typing.cast(typing.Any, result)

    @builtins.property
    def cloud_front_distribution_props(self) -> typing.Any:
        '''Optional user provided props to override the default props.

        :default: - Default props are used
        '''
        result = self._values.get("cloud_front_distribution_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def cloud_front_logging_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the CloudFront Logging Bucket.

        :default: - Default props are used
        '''
        result = self._values.get("cloud_front_logging_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

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
    def existing_lambda_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function]:
        '''Existing instance of Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_lambda_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function], result)

    @builtins.property
    def insert_http_security_headers(self) -> typing.Optional[builtins.bool]:
        '''Optional user provided props to turn on/off the automatic injection of best practice HTTP security headers in all responses from cloudfront.

        Turning this on will inject default headers and is mutually exclusive with passing custom security headers
        via the responseHeadersPolicyProps parameter.

        :default: - true
        '''
        result = self._values.get("insert_http_security_headers")
        return typing.cast(typing.Optional[builtins.bool], result)

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
        '''Optional user provided props to override the default props for the CloudWatchLogs LogGroup.

        :default: - Default props are used
        '''
        result = self._values.get("log_group_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps], result)

    @builtins.property
    def response_headers_policy_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_cloudfront_ceddda9d.ResponseHeadersPolicyProps]:
        '''Optional user provided configuration that cloudfront applies to all http responses.

        Can be used to pass a custom ResponseSecurityHeadersBehavior, ResponseCustomHeadersBehavior or
        ResponseHeadersCorsBehavior to the cloudfront distribution.

        Passing a custom ResponseSecurityHeadersBehavior is mutually exclusive with turning on the default security headers
        via ``insertHttpSecurityHeaders`` prop. Will throw an error if both ``insertHttpSecurityHeaders`` is set to ``true``
        and ResponseSecurityHeadersBehavior is passed.

        :default: - undefined
        '''
        result = self._values.get("response_headers_policy_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_cloudfront_ceddda9d.ResponseHeadersPolicyProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CloudFrontToApiGatewayToLambdaProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "CloudFrontToApiGatewayToLambda",
    "CloudFrontToApiGatewayToLambdaProps",
]

publication.publish()

def _typecheckingstub__461316ff0e3f859e7f9f591a5b92a85dedccc24c1704e2e7c328642bf2e9bc9f(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    api_gateway_props: typing.Any,
    cloud_front_distribution_props: typing.Any = None,
    cloud_front_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    create_usage_plan: typing.Optional[builtins.bool] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    insert_http_security_headers: typing.Optional[builtins.bool] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    response_headers_policy_props: typing.Optional[typing.Union[_aws_cdk_aws_cloudfront_ceddda9d.ResponseHeadersPolicyProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ce72cd5951b6f82c649ba294f738b5af3f429f19b161a863f8dc35b18bc06462(
    *,
    api_gateway_props: typing.Any,
    cloud_front_distribution_props: typing.Any = None,
    cloud_front_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    create_usage_plan: typing.Optional[builtins.bool] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    insert_http_security_headers: typing.Optional[builtins.bool] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    response_headers_policy_props: typing.Optional[typing.Union[_aws_cdk_aws_cloudfront_ceddda9d.ResponseHeadersPolicyProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
