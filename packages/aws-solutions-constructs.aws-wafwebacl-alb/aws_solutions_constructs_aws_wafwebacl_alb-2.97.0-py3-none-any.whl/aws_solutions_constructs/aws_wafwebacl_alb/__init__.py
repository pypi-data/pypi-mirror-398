r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-wafwebacl-alb/README.adoc)
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

import aws_cdk.aws_elasticloadbalancingv2 as _aws_cdk_aws_elasticloadbalancingv2_ceddda9d
import aws_cdk.aws_wafv2 as _aws_cdk_aws_wafv2_ceddda9d
import constructs as _constructs_77d1e7e8


class WafwebaclToAlb(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-wafwebacl-alb.WafwebaclToAlb",
):
    '''
    :summary: The WafwebaclToAlb class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        existing_load_balancer_obj: _aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer,
        existing_webacl_obj: typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL] = None,
        webacl_props: typing.Optional[typing.Union[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACLProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param existing_load_balancer_obj: The existing Application Load Balancer instance that will be protected with the WAF web ACL.
        :param existing_webacl_obj: Optional - existing instance of a WAF web ACL, providing both this and ``webaclProps`` is an error.
        :param webacl_props: Optional user-provided props to override the default props for the AWS WAF web ACL. Default: - Default properties are used.

        :access: public
        :summary: Constructs a new instance of the WafwebaclToAlb class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5d9fca27bcf4884f10024231360c0b181b1f48549a906f3c155e7e36081db71a)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = WafwebaclToAlbProps(
            existing_load_balancer_obj=existing_load_balancer_obj,
            existing_webacl_obj=existing_webacl_obj,
            webacl_props=webacl_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="loadBalancer")
    def load_balancer(
        self,
    ) -> _aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer:
        return typing.cast(_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer, jsii.get(self, "loadBalancer"))

    @builtins.property
    @jsii.member(jsii_name="webacl")
    def webacl(self) -> _aws_cdk_aws_wafv2_ceddda9d.CfnWebACL:
        return typing.cast(_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL, jsii.get(self, "webacl"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-wafwebacl-alb.WafwebaclToAlbProps",
    jsii_struct_bases=[],
    name_mapping={
        "existing_load_balancer_obj": "existingLoadBalancerObj",
        "existing_webacl_obj": "existingWebaclObj",
        "webacl_props": "webaclProps",
    },
)
class WafwebaclToAlbProps:
    def __init__(
        self,
        *,
        existing_load_balancer_obj: _aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer,
        existing_webacl_obj: typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL] = None,
        webacl_props: typing.Optional[typing.Union[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACLProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param existing_load_balancer_obj: The existing Application Load Balancer instance that will be protected with the WAF web ACL.
        :param existing_webacl_obj: Optional - existing instance of a WAF web ACL, providing both this and ``webaclProps`` is an error.
        :param webacl_props: Optional user-provided props to override the default props for the AWS WAF web ACL. Default: - Default properties are used.

        :summary: The properties for the WafwebaclToAlb class.
        '''
        if isinstance(webacl_props, dict):
            webacl_props = _aws_cdk_aws_wafv2_ceddda9d.CfnWebACLProps(**webacl_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__483e9f36d71d5f09cdd48df668e867c0366bcd28db3938702f119e674b261393)
            check_type(argname="argument existing_load_balancer_obj", value=existing_load_balancer_obj, expected_type=type_hints["existing_load_balancer_obj"])
            check_type(argname="argument existing_webacl_obj", value=existing_webacl_obj, expected_type=type_hints["existing_webacl_obj"])
            check_type(argname="argument webacl_props", value=webacl_props, expected_type=type_hints["webacl_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "existing_load_balancer_obj": existing_load_balancer_obj,
        }
        if existing_webacl_obj is not None:
            self._values["existing_webacl_obj"] = existing_webacl_obj
        if webacl_props is not None:
            self._values["webacl_props"] = webacl_props

    @builtins.property
    def existing_load_balancer_obj(
        self,
    ) -> _aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer:
        '''The existing Application Load Balancer instance that will be protected with the WAF web ACL.'''
        result = self._values.get("existing_load_balancer_obj")
        assert result is not None, "Required property 'existing_load_balancer_obj' is missing"
        return typing.cast(_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer, result)

    @builtins.property
    def existing_webacl_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL]:
        '''Optional - existing instance of a WAF web ACL, providing both this and ``webaclProps`` is an error.'''
        result = self._values.get("existing_webacl_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL], result)

    @builtins.property
    def webacl_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACLProps]:
        '''Optional user-provided props to override the default props for the AWS WAF web ACL.

        :default: - Default properties are used.
        '''
        result = self._values.get("webacl_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACLProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "WafwebaclToAlbProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "WafwebaclToAlb",
    "WafwebaclToAlbProps",
]

publication.publish()

def _typecheckingstub__5d9fca27bcf4884f10024231360c0b181b1f48549a906f3c155e7e36081db71a(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    existing_load_balancer_obj: _aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer,
    existing_webacl_obj: typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL] = None,
    webacl_props: typing.Optional[typing.Union[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACLProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__483e9f36d71d5f09cdd48df668e867c0366bcd28db3938702f119e674b261393(
    *,
    existing_load_balancer_obj: _aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer,
    existing_webacl_obj: typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL] = None,
    webacl_props: typing.Optional[typing.Union[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACLProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
