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
