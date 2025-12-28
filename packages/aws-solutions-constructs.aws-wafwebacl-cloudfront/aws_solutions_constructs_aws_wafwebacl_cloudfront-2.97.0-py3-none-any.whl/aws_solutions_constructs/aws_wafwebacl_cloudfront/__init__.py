r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-wafwebacl-cloudfront/README.adoc)
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

import aws_cdk.aws_cloudfront as _aws_cdk_aws_cloudfront_ceddda9d
import aws_cdk.aws_wafv2 as _aws_cdk_aws_wafv2_ceddda9d
import constructs as _constructs_77d1e7e8


class WafwebaclToCloudFront(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-wafwebacl-cloudfront.WafwebaclToCloudFront",
):
    '''
    :summary: The WafwebaclToCloudFront class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        existing_cloud_front_web_distribution: _aws_cdk_aws_cloudfront_ceddda9d.Distribution,
        existing_webacl_obj: typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL] = None,
        webacl_props: typing.Any = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param existing_cloud_front_web_distribution: The existing CloudFront instance that will be protected with the WAF web ACL. This construct changes the CloudFront distribution by directly manipulating the CloudFormation output, so this must be the Construct and cannot be changed to the Interface (IDistribution)
        :param existing_webacl_obj: Optional - existing instance of a WAF web ACL, providing both this and ``webaclProps`` is an error.
        :param webacl_props: Optional user-provided props to override the default props for the AWS WAF web ACL. Providing both this and existingWebaclObj is an error. To use a different collection of managed rule sets, specify a new rules property. Use our link:../core/lib/waf-defaults.ts[wrapManagedRuleSet(managedGroupName: string, vendorName: string, priority: number)] function from core to create an array entry from each desired managed rule set. Default: - Default properties are used.

        :access: public
        :summary: Constructs a new instance of the WafwebaclToCloudFront class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d5d8bd547f935ab6b8d3616094fcce5144f3e97e2b6bc2efff5fc3b86536057b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = WafwebaclToCloudFrontProps(
            existing_cloud_front_web_distribution=existing_cloud_front_web_distribution,
            existing_webacl_obj=existing_webacl_obj,
            webacl_props=webacl_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="cloudFrontWebDistribution")
    def cloud_front_web_distribution(
        self,
    ) -> _aws_cdk_aws_cloudfront_ceddda9d.Distribution:
        return typing.cast(_aws_cdk_aws_cloudfront_ceddda9d.Distribution, jsii.get(self, "cloudFrontWebDistribution"))

    @builtins.property
    @jsii.member(jsii_name="webacl")
    def webacl(self) -> _aws_cdk_aws_wafv2_ceddda9d.CfnWebACL:
        return typing.cast(_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL, jsii.get(self, "webacl"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-wafwebacl-cloudfront.WafwebaclToCloudFrontProps",
    jsii_struct_bases=[],
    name_mapping={
        "existing_cloud_front_web_distribution": "existingCloudFrontWebDistribution",
        "existing_webacl_obj": "existingWebaclObj",
        "webacl_props": "webaclProps",
    },
)
class WafwebaclToCloudFrontProps:
    def __init__(
        self,
        *,
        existing_cloud_front_web_distribution: _aws_cdk_aws_cloudfront_ceddda9d.Distribution,
        existing_webacl_obj: typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL] = None,
        webacl_props: typing.Any = None,
    ) -> None:
        '''
        :param existing_cloud_front_web_distribution: The existing CloudFront instance that will be protected with the WAF web ACL. This construct changes the CloudFront distribution by directly manipulating the CloudFormation output, so this must be the Construct and cannot be changed to the Interface (IDistribution)
        :param existing_webacl_obj: Optional - existing instance of a WAF web ACL, providing both this and ``webaclProps`` is an error.
        :param webacl_props: Optional user-provided props to override the default props for the AWS WAF web ACL. Providing both this and existingWebaclObj is an error. To use a different collection of managed rule sets, specify a new rules property. Use our link:../core/lib/waf-defaults.ts[wrapManagedRuleSet(managedGroupName: string, vendorName: string, priority: number)] function from core to create an array entry from each desired managed rule set. Default: - Default properties are used.

        :summary: The properties for the WafwebaclToCloudFront class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__40a0cf28e1b529b5efb8af1e8d3e34e9c89ef520a8810caf4b1ccce40fff2a84)
            check_type(argname="argument existing_cloud_front_web_distribution", value=existing_cloud_front_web_distribution, expected_type=type_hints["existing_cloud_front_web_distribution"])
            check_type(argname="argument existing_webacl_obj", value=existing_webacl_obj, expected_type=type_hints["existing_webacl_obj"])
            check_type(argname="argument webacl_props", value=webacl_props, expected_type=type_hints["webacl_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "existing_cloud_front_web_distribution": existing_cloud_front_web_distribution,
        }
        if existing_webacl_obj is not None:
            self._values["existing_webacl_obj"] = existing_webacl_obj
        if webacl_props is not None:
            self._values["webacl_props"] = webacl_props

    @builtins.property
    def existing_cloud_front_web_distribution(
        self,
    ) -> _aws_cdk_aws_cloudfront_ceddda9d.Distribution:
        '''The existing CloudFront instance that will be protected with the WAF web ACL.

        This construct changes the CloudFront distribution by directly manipulating
        the CloudFormation output, so this must be the Construct and cannot be
        changed to the Interface (IDistribution)
        '''
        result = self._values.get("existing_cloud_front_web_distribution")
        assert result is not None, "Required property 'existing_cloud_front_web_distribution' is missing"
        return typing.cast(_aws_cdk_aws_cloudfront_ceddda9d.Distribution, result)

    @builtins.property
    def existing_webacl_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL]:
        '''Optional - existing instance of a WAF web ACL, providing both this and ``webaclProps`` is an error.'''
        result = self._values.get("existing_webacl_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL], result)

    @builtins.property
    def webacl_props(self) -> typing.Any:
        '''Optional user-provided props to override the default props for the AWS WAF web ACL.

        Providing both this and
        existingWebaclObj is an error. To use a different collection of managed rule sets, specify a new rules
        property. Use our link:../core/lib/waf-defaults.ts[wrapManagedRuleSet(managedGroupName: string, vendorName:
        string, priority: number)] function from core to create an array entry from each desired managed rule set.

        :default: - Default properties are used.
        '''
        result = self._values.get("webacl_props")
        return typing.cast(typing.Any, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "WafwebaclToCloudFrontProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "WafwebaclToCloudFront",
    "WafwebaclToCloudFrontProps",
]

publication.publish()

def _typecheckingstub__d5d8bd547f935ab6b8d3616094fcce5144f3e97e2b6bc2efff5fc3b86536057b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    existing_cloud_front_web_distribution: _aws_cdk_aws_cloudfront_ceddda9d.Distribution,
    existing_webacl_obj: typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL] = None,
    webacl_props: typing.Any = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__40a0cf28e1b529b5efb8af1e8d3e34e9c89ef520a8810caf4b1ccce40fff2a84(
    *,
    existing_cloud_front_web_distribution: _aws_cdk_aws_cloudfront_ceddda9d.Distribution,
    existing_webacl_obj: typing.Optional[_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL] = None,
    webacl_props: typing.Any = None,
) -> None:
    """Type checking stubs"""
    pass
