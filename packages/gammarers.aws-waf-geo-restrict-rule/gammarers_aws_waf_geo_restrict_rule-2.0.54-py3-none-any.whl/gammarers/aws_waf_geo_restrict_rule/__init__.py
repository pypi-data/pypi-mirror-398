r'''
# AWS WAF(v2) GEO Restrict Rule

[![GitHub](https://img.shields.io/github/license/gammarers/aws-waf-geo-restrict-rule?style=flat-square)](https://github.com/gammarers/aws-waf-geo-restrict-rule/blob/main/LICENSE)
[![npm (scoped)](https://img.shields.io/npm/v/@gammarers/aws-waf-geo-restrict-rule?style=flat-square)](https://www.npmjs.com/package/@gammarers/aws-waf-geo-restrict-rule)
[![PyPI](https://img.shields.io/pypi/v/gammarers.aws-waf-geo-restrict-rule?style=flat-square)](https://pypi.org/project/gammarers.aws-waf-geo-restrict-rule/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/gammarers/aws-waf-geo-restrict-rule/release.yml?branch=main&label=release&style=flat-square)](https://github.com/gammarers/aws-waf-geo-restrict-rule/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/gammarers/aws-waf-geo-restrict-rule?sort=semver&style=flat-square)](https://github.com/gammarers/aws-waf-geo-restrict-rule/releases)

[![View on Construct Hub](https://constructs.dev/badge?package=@gammarers/aws-waf-geo-restrict-rule)](https://constructs.dev/packages/@gammarers/aws-waf-geo-restrict-rule)

This is an AWS CDK WAF Geo Restrict Rule on WAF V2

## Install

### TypeScript

#### install by npm

```shell
npm install @gammarers/aws-waf-geo-restrict-rule
```

#### install by yarn

```shell
yarn add @gammarers/aws-waf-geo-restrict-rule
```

### Python

```shell
pip install gammarers.aws-waf-geo-restrict-rule
```

## Example

```python
import { WAFGeoRestrictRule } from '@gammarers/aws-waf-geo-restrict-rule';

const geoRestrictRule = new WAFGeoRestrictRule({
  allowCountries: ['JP'],
});

new wafv2.CfnWebACL(stack, 'WebACL', {
  defaultAction: { allow: {} },
  scope: 'CLOUD_FRONT',
  name: 'WebAclWithCustomRules',
  visibilityConfig: {
    cloudWatchMetricsEnabled: true,
    metricName: 'WebAclMetric',
    sampledRequestsEnabled: true,
  },
  rules: [
    geoRestrictRule.allowRule({
      priority: 1,
    }),
    geoRestrictRule.blockRule({
      priority: 2,
    }),
  ],
});
```

## License

This project is licensed under the Apache-2.0 License.
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

import aws_cdk.aws_wafv2 as _aws_cdk_aws_wafv2_ceddda9d


@jsii.data_type(
    jsii_type="@gammarers/aws-waf-geo-restrict-rule.RuleConfig",
    jsii_struct_bases=[],
    name_mapping={
        "priority": "priority",
        "cloud_watch_metrics_name": "cloudWatchMetricsName",
        "rule_name": "ruleName",
    },
)
class RuleConfig:
    def __init__(
        self,
        *,
        priority: jsii.Number,
        cloud_watch_metrics_name: typing.Optional[builtins.str] = None,
        rule_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param priority: 
        :param cloud_watch_metrics_name: 
        :param rule_name: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0070bef32d51311d47895c9197806c9f416031e4b6db5e3bcc48c1a9da468aed)
            check_type(argname="argument priority", value=priority, expected_type=type_hints["priority"])
            check_type(argname="argument cloud_watch_metrics_name", value=cloud_watch_metrics_name, expected_type=type_hints["cloud_watch_metrics_name"])
            check_type(argname="argument rule_name", value=rule_name, expected_type=type_hints["rule_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "priority": priority,
        }
        if cloud_watch_metrics_name is not None:
            self._values["cloud_watch_metrics_name"] = cloud_watch_metrics_name
        if rule_name is not None:
            self._values["rule_name"] = rule_name

    @builtins.property
    def priority(self) -> jsii.Number:
        result = self._values.get("priority")
        assert result is not None, "Required property 'priority' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def cloud_watch_metrics_name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("cloud_watch_metrics_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def rule_name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("rule_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RuleConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class WAFGeoRestrictRule(
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-waf-geo-restrict-rule.WAFGeoRestrictRule",
):
    def __init__(self, *, allow_countries: typing.Sequence[builtins.str]) -> None:
        '''
        :param allow_countries: 
        '''
        props = WAFGeoRestrictRuleProps(allow_countries=allow_countries)

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="allowRule")
    def allow_rule(
        self,
        *,
        priority: jsii.Number,
        cloud_watch_metrics_name: typing.Optional[builtins.str] = None,
        rule_name: typing.Optional[builtins.str] = None,
    ) -> "_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL.RuleProperty":
        '''
        :param priority: 
        :param cloud_watch_metrics_name: 
        :param rule_name: 
        '''
        config = RuleConfig(
            priority=priority,
            cloud_watch_metrics_name=cloud_watch_metrics_name,
            rule_name=rule_name,
        )

        return typing.cast("_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL.RuleProperty", jsii.invoke(self, "allowRule", [config]))

    @jsii.member(jsii_name="blockRule")
    def block_rule(
        self,
        *,
        priority: jsii.Number,
        cloud_watch_metrics_name: typing.Optional[builtins.str] = None,
        rule_name: typing.Optional[builtins.str] = None,
    ) -> "_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL.RuleProperty":
        '''
        :param priority: 
        :param cloud_watch_metrics_name: 
        :param rule_name: 
        '''
        config = RuleConfig(
            priority=priority,
            cloud_watch_metrics_name=cloud_watch_metrics_name,
            rule_name=rule_name,
        )

        return typing.cast("_aws_cdk_aws_wafv2_ceddda9d.CfnWebACL.RuleProperty", jsii.invoke(self, "blockRule", [config]))


@jsii.data_type(
    jsii_type="@gammarers/aws-waf-geo-restrict-rule.WAFGeoRestrictRuleProps",
    jsii_struct_bases=[],
    name_mapping={"allow_countries": "allowCountries"},
)
class WAFGeoRestrictRuleProps:
    def __init__(self, *, allow_countries: typing.Sequence[builtins.str]) -> None:
        '''
        :param allow_countries: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__556cb1206803c4b0c266a98f089217eb97b55bef033c5a8c474890058ccae035)
            check_type(argname="argument allow_countries", value=allow_countries, expected_type=type_hints["allow_countries"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "allow_countries": allow_countries,
        }

    @builtins.property
    def allow_countries(self) -> typing.List[builtins.str]:
        result = self._values.get("allow_countries")
        assert result is not None, "Required property 'allow_countries' is missing"
        return typing.cast(typing.List[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "WAFGeoRestrictRuleProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "RuleConfig",
    "WAFGeoRestrictRule",
    "WAFGeoRestrictRuleProps",
]

publication.publish()

def _typecheckingstub__0070bef32d51311d47895c9197806c9f416031e4b6db5e3bcc48c1a9da468aed(
    *,
    priority: jsii.Number,
    cloud_watch_metrics_name: typing.Optional[builtins.str] = None,
    rule_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__556cb1206803c4b0c266a98f089217eb97b55bef033c5a8c474890058ccae035(
    *,
    allow_countries: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass
