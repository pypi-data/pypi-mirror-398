r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-lambda-elasticachememcached/README.adoc)
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
import aws_cdk.aws_elasticache as _aws_cdk_aws_elasticache_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import constructs as _constructs_77d1e7e8


class LambdaToElasticachememcached(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-lambda-elasticachememcached.LambdaToElasticachememcached",
):
    '''
    :summary: The LambdaToElasticachememcached class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        cache_endpoint_environment_variable_name: typing.Optional[builtins.str] = None,
        cache_props: typing.Any = None,
        existing_cache: typing.Optional[_aws_cdk_aws_elasticache_ceddda9d.CfnCacheCluster] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param cache_endpoint_environment_variable_name: Optional Name for the Lambda function environment variable set to the cache endpoint. Default: - CACHE_ENDPOINT
        :param cache_props: Optional user provided props to override the default props for the Elasticache cache. Providing both this and ``existingCache`` will cause an error. If you provide this, you must provide the associated VPC in existingVpc. Default: - Default properties are used (core/lib/elasticacahe-defaults.ts)
        :param existing_cache: Existing instance of Elasticache Cluster object, providing both this and ``cacheProps`` will cause an error. Default: - none
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case). Default: - none
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default properties are used.
        :param vpc_props: Properties to override default properties if deployVpc is true. Default: - DefaultIsolatedVpcProps() in vpc-defaults.ts

        :access: public
        :summary: Constructs a new instance of the LambdaToElasticachememcached class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9839f737b99fce32b9fe35e48df7f778fd78cb8ea7d9d44af8828e8277cdfed4)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = LambdaToElasticachememcachedProps(
            cache_endpoint_environment_variable_name=cache_endpoint_environment_variable_name,
            cache_props=cache_props,
            existing_cache=existing_cache,
            existing_lambda_obj=existing_lambda_obj,
            existing_vpc=existing_vpc,
            lambda_function_props=lambda_function_props,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="cache")
    def cache(self) -> _aws_cdk_aws_elasticache_ceddda9d.CfnCacheCluster:
        return typing.cast(_aws_cdk_aws_elasticache_ceddda9d.CfnCacheCluster, jsii.get(self, "cache"))

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-lambda-elasticachememcached.LambdaToElasticachememcachedProps",
    jsii_struct_bases=[],
    name_mapping={
        "cache_endpoint_environment_variable_name": "cacheEndpointEnvironmentVariableName",
        "cache_props": "cacheProps",
        "existing_cache": "existingCache",
        "existing_lambda_obj": "existingLambdaObj",
        "existing_vpc": "existingVpc",
        "lambda_function_props": "lambdaFunctionProps",
        "vpc_props": "vpcProps",
    },
)
class LambdaToElasticachememcachedProps:
    def __init__(
        self,
        *,
        cache_endpoint_environment_variable_name: typing.Optional[builtins.str] = None,
        cache_props: typing.Any = None,
        existing_cache: typing.Optional[_aws_cdk_aws_elasticache_ceddda9d.CfnCacheCluster] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param cache_endpoint_environment_variable_name: Optional Name for the Lambda function environment variable set to the cache endpoint. Default: - CACHE_ENDPOINT
        :param cache_props: Optional user provided props to override the default props for the Elasticache cache. Providing both this and ``existingCache`` will cause an error. If you provide this, you must provide the associated VPC in existingVpc. Default: - Default properties are used (core/lib/elasticacahe-defaults.ts)
        :param existing_cache: Existing instance of Elasticache Cluster object, providing both this and ``cacheProps`` will cause an error. Default: - none
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case). Default: - none
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default properties are used.
        :param vpc_props: Properties to override default properties if deployVpc is true. Default: - DefaultIsolatedVpcProps() in vpc-defaults.ts

        :summary: The properties for the LambdaToElasticachememcached class.
        '''
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__be5112c9f409f0761d2af51f178f83dc585cee7d02815e1150d8a47e9df3b4da)
            check_type(argname="argument cache_endpoint_environment_variable_name", value=cache_endpoint_environment_variable_name, expected_type=type_hints["cache_endpoint_environment_variable_name"])
            check_type(argname="argument cache_props", value=cache_props, expected_type=type_hints["cache_props"])
            check_type(argname="argument existing_cache", value=existing_cache, expected_type=type_hints["existing_cache"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if cache_endpoint_environment_variable_name is not None:
            self._values["cache_endpoint_environment_variable_name"] = cache_endpoint_environment_variable_name
        if cache_props is not None:
            self._values["cache_props"] = cache_props
        if existing_cache is not None:
            self._values["existing_cache"] = existing_cache
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def cache_endpoint_environment_variable_name(self) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the cache endpoint.

        :default: - CACHE_ENDPOINT
        '''
        result = self._values.get("cache_endpoint_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def cache_props(self) -> typing.Any:
        '''Optional user provided props to override the default props for the Elasticache cache.

        Providing both this and ``existingCache`` will cause an error.  If you provide this,
        you must provide the associated VPC in existingVpc.

        :default: - Default properties are used (core/lib/elasticacahe-defaults.ts)
        '''
        result = self._values.get("cache_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def existing_cache(
        self,
    ) -> typing.Optional[_aws_cdk_aws_elasticache_ceddda9d.CfnCacheCluster]:
        '''Existing instance of Elasticache Cluster object, providing both this and ``cacheProps`` will cause an error.

        :default: - none
        '''
        result = self._values.get("existing_cache")
        return typing.cast(typing.Optional[_aws_cdk_aws_elasticache_ceddda9d.CfnCacheCluster], result)

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

        :default: - none
        '''
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
        return "LambdaToElasticachememcachedProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "LambdaToElasticachememcached",
    "LambdaToElasticachememcachedProps",
]

publication.publish()

def _typecheckingstub__9839f737b99fce32b9fe35e48df7f778fd78cb8ea7d9d44af8828e8277cdfed4(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    cache_endpoint_environment_variable_name: typing.Optional[builtins.str] = None,
    cache_props: typing.Any = None,
    existing_cache: typing.Optional[_aws_cdk_aws_elasticache_ceddda9d.CfnCacheCluster] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__be5112c9f409f0761d2af51f178f83dc585cee7d02815e1150d8a47e9df3b4da(
    *,
    cache_endpoint_environment_variable_name: typing.Optional[builtins.str] = None,
    cache_props: typing.Any = None,
    existing_cache: typing.Optional[_aws_cdk_aws_elasticache_ceddda9d.CfnCacheCluster] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
