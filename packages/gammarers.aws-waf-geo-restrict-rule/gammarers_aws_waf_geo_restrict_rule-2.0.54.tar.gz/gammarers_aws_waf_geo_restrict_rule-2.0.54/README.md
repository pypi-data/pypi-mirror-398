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
