# AWS Daily Cost Usage Report Stack

[![GitHub](https://img.shields.io/github/license/gammarers/aws-daily-cost-usage-report-stack?style=flat-square)](https://github.com/gammarers/aws-daily-cost-usage-report-stack/blob/main/LICENSE)
[![npm (scoped)](https://img.shields.io/npm/v/@gammarers/aws-daily-cost-usage-report-stack?style=flat-square)](https://www.npmjs.com/package/@gammarers/aws-daily-cost-usage-report-stack)
[![PyPI](https://img.shields.io/pypi/v/gammarers.aws-daily-cost-usage-report-stack?style=flat-square)](https://pypi.org/project/gammarers.aws-daily-cost-usage-report-stack/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/gammarers/aws-daily-cost-usage-report-stack/release.yml?branch=main&label=release&style=flat-square)](https://github.com/gammarers/aws-daily-cost-usage-report-stack/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/gammarers/aws-daily-cost-usage-report-stack?sort=semver&style=flat-square)](https://github.com/gammarers/aws-daily-cost-usage-report-stack/releases)

AWS Cost And Usage report to Slack on daily 09:01.

* Report type

  * Services

    * This is Cost by AWS Services.
  * Accounts

    * This is Cost by Linked Account (when organization master account)

## Resources

This construct creating resource list.

* Lambda function execution role
* Lambda function
* EventBridge Scheduler execution role
* EventBridge Scheduler

## Install

### TypeScript

#### use by npm

```shell
npm install @gammarers/aws-daily-cost-usage-report-stack
```

#### use by yarn

```shell
yarn add @gammarers/aws-daily-cost-usage-report-stack
```

### Python

```shell
pip install gammarers.aws-daily-cost-usage-report-stack
```

## Example

```shell
npm install @gammarers/aws-daily-cost-usage-report-stack
```

```python
import { CostGroupType, DailyCostUsageReportStack } from '@gammarer/aws-daily-cost-usage-report-stack';

new DailyCostUsageReportStack(app, 'DailyCostUsageReportStack', {
  slackToken: 'xoxb-11111111111-XXXXXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXX',
  slackChannel: 'example-channel',
  costGroupType: CostGroupType.SERVICES,
});
```

## License

This project is licensed under the Apache-2.0 License.
