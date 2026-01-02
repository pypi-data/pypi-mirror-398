# @robhan-cdk-lib/aws_mwaa

AWS Cloud Development Kit (CDK) constructs for Amazon Managed Workflows for Apache Airflow (MWAA).

In [aws-cdk-lib.aws_mwaa](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_mwaa-readme.html), there currently only exist L1 constructs for Amazon Managed Workflows for Apache Airflow (MWAA).

While helpful, they miss convenience like:

* advanced parameter checking (min/max number values, string lengths, array lengths...) before CloudFormation deployment
* proper parameter typing, e.g. enum values instead of strings
* simply referencing other constructs instead of e.g. ARN strings

Those features are implemented here.

The CDK maintainers explain that [publishing your own package](https://github.com/aws/aws-cdk/blob/main/CONTRIBUTING.md#publishing-your-own-package) is "by far the strongest signal you can give to the CDK team that a feature should be included within the core aws-cdk packages".

This project aims to develop aws_mwaa constructs to a maturity that can potentially be accepted to the CDK core.

It is not supported by AWS and is not endorsed by them. Please file issues in the [GitHub repository](https://github.com/robert-hanuschke/cdk-aws_mwaa/issues) if you find any.

## Example use

```python
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import {
  AirflowVersion,
  Environment,
  EnvironmentClass,
} from "@robhan-cdk-lib/aws_mwaa";

export class AwsMwaaCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const environment = new Environment(this, "Environment", {
      airflowConfigurationOptions: {
        key: "value",
      },
      name: "myEnvironment",
      airflowVersion: AirflowVersion.V3_0_6,
      environmentClass: EnvironmentClass.MW1_MEDIUM,
      minWebservers: 2,
      maxWebservers: 4,
      minWorkers: 2,
      maxWorkers: 4,
    });
  }
}
```

## License

MIT
