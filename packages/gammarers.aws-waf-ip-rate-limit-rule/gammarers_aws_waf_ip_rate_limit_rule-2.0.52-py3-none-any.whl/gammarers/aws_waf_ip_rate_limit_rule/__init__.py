r'''
# AWS WAF(V2) IP Rete Limit Rule

[![GitHub](https://img.shields.io/github/license/gammarers/aws-waf-ip-rate-limit-rule?style=flat-square)](https://github.com/gammarers/aws-waf-ip-rate-limit-rule/blob/main/LICENSE)
[![npm (scoped)](https://img.shields.io/npm/v/@gammarers/aws-waf-ip-rate-limit-rule?style=flat-square)](https://www.npmjs.com/package/@gammarers/aws-waf-ip-rate-limit-rule)
[![PyPI](https://img.shields.io/pypi/v/gammarers.aws-waf-ip-rate-limit-rule?style=flat-square)](https://pypi.org/project/gammarers.aws-waf-ip-rate-limit-rule/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/gammarers/aws-waf-ip-rate-limit-rule/release.yml?branch=main&label=release&style=flat-square)](https://github.com/gammarers/aws-waf-ip-rate-limit-rule/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/gammarers/aws-waf-ip-rate-limit-rule?sort=semver&style=flat-square)](https://github.com/gammarers/aws-waf-ip-rate-limit-rule/releases)

[![View on Construct Hub](https://constructs.dev/badge?package=@gammarers/aws-waf-ip-rate-limit-rule)](https://constructs.dev/packages/@gammarers/aws-waf-ip-rate-limit-rule)

This is an AWS CDK WAF IP Rate Limit Rule

## Resources

This construct creating resource list.

* WAF V2 RuleGroup

## Install

### TypeScript

#### install by npm

```shell
npm install @gammarers/aws-waf-ip-rate-limit-rule
```

#### install by yarn

```shell
yarn add @gammarers/aws-waf-ip-rate-limit-rule
```

### Python

```shell
pip install gammarers.aws-waf-ip-rate-limit-rule
```

## Example

```python
import { WAFIPRateLimitRule } from '@gammarers/aws-waf-ip-rate-limit-rule';

const ipRateLimitRule = new WAFIPRateLimitRule({
  rateLimit: 100,
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
    ipRateLimitRule.blockRule({
      priority: 1,
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
    jsii_type="@gammarers/aws-waf-ip-rate-limit-rule.RuleConfig",
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
            type_hints = typing.get_type_hints(_typecheckingstub__35c1f7da2efbcd797bfac49d55496bf87903529ce22c8942c8abdb03627d02e8)
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


class WAFIPRateLimitRule(
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-waf-ip-rate-limit-rule.WAFIPRateLimitRule",
):
    def __init__(self, *, rate_limit: jsii.Number) -> None:
        '''
        :param rate_limit: 
        '''
        props = WAFIPRateLimitRuleProps(rate_limit=rate_limit)

        jsii.create(self.__class__, self, [props])

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
    jsii_type="@gammarers/aws-waf-ip-rate-limit-rule.WAFIPRateLimitRuleProps",
    jsii_struct_bases=[],
    name_mapping={"rate_limit": "rateLimit"},
)
class WAFIPRateLimitRuleProps:
    def __init__(self, *, rate_limit: jsii.Number) -> None:
        '''
        :param rate_limit: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__21c859ac6052a64fbed028880cafa9671873bb796a9cb974e3a9ddb052e8808a)
            check_type(argname="argument rate_limit", value=rate_limit, expected_type=type_hints["rate_limit"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "rate_limit": rate_limit,
        }

    @builtins.property
    def rate_limit(self) -> jsii.Number:
        result = self._values.get("rate_limit")
        assert result is not None, "Required property 'rate_limit' is missing"
        return typing.cast(jsii.Number, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "WAFIPRateLimitRuleProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "RuleConfig",
    "WAFIPRateLimitRule",
    "WAFIPRateLimitRuleProps",
]

publication.publish()

def _typecheckingstub__35c1f7da2efbcd797bfac49d55496bf87903529ce22c8942c8abdb03627d02e8(
    *,
    priority: jsii.Number,
    cloud_watch_metrics_name: typing.Optional[builtins.str] = None,
    rule_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__21c859ac6052a64fbed028880cafa9671873bb796a9cb974e3a9ddb052e8808a(
    *,
    rate_limit: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass
