r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-lambda-elasticsearch-kibana/README.adoc)
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
import aws_cdk.aws_cognito as _aws_cdk_aws_cognito_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_elasticsearch as _aws_cdk_aws_elasticsearch_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import constructs as _constructs_77d1e7e8


class LambdaToElasticSearchAndKibana(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-lambda-elasticsearch-kibana.LambdaToElasticSearchAndKibana",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        domain_name: builtins.str,
        cognito_domain_name: typing.Optional[builtins.str] = None,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        domain_endpoint_environment_variable_name: typing.Optional[builtins.str] = None,
        es_domain_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticsearch_ceddda9d.CfnDomainProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param domain_name: Cognito & ES Domain Name. Default: - None
        :param cognito_domain_name: Optional Cognito Domain Name, if provided it will be used for Cognito Domain, and domainName will be used for the Elasticsearch Domain. Default: - None
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. Default: - Alarms are created
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param domain_endpoint_environment_variable_name: Optional Name for the Lambda function environment variable set to the domain endpoint. Default: - DOMAIN_ENDPOINT
        :param es_domain_props: Optional user provided props to override the default props for the Elasticsearch Service. Default: - Default props are used
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case). Default: - None
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param vpc_props: Properties to override default properties if deployVpc is true. Default: - DefaultIsolatedVpcProps() in vpc-defaults.ts

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the LambdaToElasticSearchAndKibana class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__38bd0b5ffdf9ecc5034fa7a1869a0143c1ea3f5a4b7a0c562ef97a74f6a004f6)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = LambdaToElasticSearchAndKibanaProps(
            domain_name=domain_name,
            cognito_domain_name=cognito_domain_name,
            create_cloud_watch_alarms=create_cloud_watch_alarms,
            deploy_vpc=deploy_vpc,
            domain_endpoint_environment_variable_name=domain_endpoint_environment_variable_name,
            es_domain_props=es_domain_props,
            existing_lambda_obj=existing_lambda_obj,
            existing_vpc=existing_vpc,
            lambda_function_props=lambda_function_props,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="elasticsearchDomain")
    def elasticsearch_domain(self) -> _aws_cdk_aws_elasticsearch_ceddda9d.CfnDomain:
        return typing.cast(_aws_cdk_aws_elasticsearch_ceddda9d.CfnDomain, jsii.get(self, "elasticsearchDomain"))

    @builtins.property
    @jsii.member(jsii_name="elasticsearchRole")
    def elasticsearch_role(self) -> _aws_cdk_aws_iam_ceddda9d.Role:
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Role, jsii.get(self, "elasticsearchRole"))

    @builtins.property
    @jsii.member(jsii_name="identityPool")
    def identity_pool(self) -> _aws_cdk_aws_cognito_ceddda9d.CfnIdentityPool:
        return typing.cast(_aws_cdk_aws_cognito_ceddda9d.CfnIdentityPool, jsii.get(self, "identityPool"))

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
    jsii_type="@aws-solutions-constructs/aws-lambda-elasticsearch-kibana.LambdaToElasticSearchAndKibanaProps",
    jsii_struct_bases=[],
    name_mapping={
        "domain_name": "domainName",
        "cognito_domain_name": "cognitoDomainName",
        "create_cloud_watch_alarms": "createCloudWatchAlarms",
        "deploy_vpc": "deployVpc",
        "domain_endpoint_environment_variable_name": "domainEndpointEnvironmentVariableName",
        "es_domain_props": "esDomainProps",
        "existing_lambda_obj": "existingLambdaObj",
        "existing_vpc": "existingVpc",
        "lambda_function_props": "lambdaFunctionProps",
        "vpc_props": "vpcProps",
    },
)
class LambdaToElasticSearchAndKibanaProps:
    def __init__(
        self,
        *,
        domain_name: builtins.str,
        cognito_domain_name: typing.Optional[builtins.str] = None,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        domain_endpoint_environment_variable_name: typing.Optional[builtins.str] = None,
        es_domain_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticsearch_ceddda9d.CfnDomainProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param domain_name: Cognito & ES Domain Name. Default: - None
        :param cognito_domain_name: Optional Cognito Domain Name, if provided it will be used for Cognito Domain, and domainName will be used for the Elasticsearch Domain. Default: - None
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. Default: - Alarms are created
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param domain_endpoint_environment_variable_name: Optional Name for the Lambda function environment variable set to the domain endpoint. Default: - DOMAIN_ENDPOINT
        :param es_domain_props: Optional user provided props to override the default props for the Elasticsearch Service. Default: - Default props are used
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case). Default: - None
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param vpc_props: Properties to override default properties if deployVpc is true. Default: - DefaultIsolatedVpcProps() in vpc-defaults.ts

        :summary: The properties for the LambdaToElasticSearchAndKibana Construct
        '''
        if isinstance(es_domain_props, dict):
            es_domain_props = _aws_cdk_aws_elasticsearch_ceddda9d.CfnDomainProps(**es_domain_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a755489b8c5957595fd4ced6bb4b75a0e11da0b83fbaa4ce3696aba63d4b6499)
            check_type(argname="argument domain_name", value=domain_name, expected_type=type_hints["domain_name"])
            check_type(argname="argument cognito_domain_name", value=cognito_domain_name, expected_type=type_hints["cognito_domain_name"])
            check_type(argname="argument create_cloud_watch_alarms", value=create_cloud_watch_alarms, expected_type=type_hints["create_cloud_watch_alarms"])
            check_type(argname="argument deploy_vpc", value=deploy_vpc, expected_type=type_hints["deploy_vpc"])
            check_type(argname="argument domain_endpoint_environment_variable_name", value=domain_endpoint_environment_variable_name, expected_type=type_hints["domain_endpoint_environment_variable_name"])
            check_type(argname="argument es_domain_props", value=es_domain_props, expected_type=type_hints["es_domain_props"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "domain_name": domain_name,
        }
        if cognito_domain_name is not None:
            self._values["cognito_domain_name"] = cognito_domain_name
        if create_cloud_watch_alarms is not None:
            self._values["create_cloud_watch_alarms"] = create_cloud_watch_alarms
        if deploy_vpc is not None:
            self._values["deploy_vpc"] = deploy_vpc
        if domain_endpoint_environment_variable_name is not None:
            self._values["domain_endpoint_environment_variable_name"] = domain_endpoint_environment_variable_name
        if es_domain_props is not None:
            self._values["es_domain_props"] = es_domain_props
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def domain_name(self) -> builtins.str:
        '''Cognito & ES Domain Name.

        :default: - None
        '''
        result = self._values.get("domain_name")
        assert result is not None, "Required property 'domain_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def cognito_domain_name(self) -> typing.Optional[builtins.str]:
        '''Optional Cognito Domain Name, if provided it will be used for Cognito Domain, and domainName will be used for the Elasticsearch Domain.

        :default: - None
        '''
        result = self._values.get("cognito_domain_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def create_cloud_watch_alarms(self) -> typing.Optional[builtins.bool]:
        '''Whether to create recommended CloudWatch alarms.

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
    def domain_endpoint_environment_variable_name(
        self,
    ) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the domain endpoint.

        :default: - DOMAIN_ENDPOINT
        '''
        result = self._values.get("domain_endpoint_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def es_domain_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_elasticsearch_ceddda9d.CfnDomainProps]:
        '''Optional user provided props to override the default props for the Elasticsearch Service.

        :default: - Default props are used
        '''
        result = self._values.get("es_domain_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_elasticsearch_ceddda9d.CfnDomainProps], result)

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
    def vpc_props(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps]:
        '''Properties to override default properties if deployVpc is true.

        :default: - DefaultIsolatedVpcProps() in vpc-defaults.ts
        '''
        result = self._values.get("vpc_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LambdaToElasticSearchAndKibanaProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "LambdaToElasticSearchAndKibana",
    "LambdaToElasticSearchAndKibanaProps",
]

publication.publish()

def _typecheckingstub__38bd0b5ffdf9ecc5034fa7a1869a0143c1ea3f5a4b7a0c562ef97a74f6a004f6(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    domain_name: builtins.str,
    cognito_domain_name: typing.Optional[builtins.str] = None,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    domain_endpoint_environment_variable_name: typing.Optional[builtins.str] = None,
    es_domain_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticsearch_ceddda9d.CfnDomainProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a755489b8c5957595fd4ced6bb4b75a0e11da0b83fbaa4ce3696aba63d4b6499(
    *,
    domain_name: builtins.str,
    cognito_domain_name: typing.Optional[builtins.str] = None,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    domain_endpoint_environment_variable_name: typing.Optional[builtins.str] = None,
    es_domain_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticsearch_ceddda9d.CfnDomainProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
