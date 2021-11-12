# custom-cloud9-ssm
<!--BEGIN STABILITY BANNER-->

---

![Stability: Experimental](https://img.shields.io/badge/stability-Experimental-important.svg?style=for-the-badge)

> All classes are under active development and subject to non-backward compatible changes or removal in any
> future version. These are not subject to the [Semantic Versioning](https://semver.org/) model.
> This means that while you may use them, you may need to update your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

| **Language**     | **Package**        |
|:-------------|-----------------|
|![Python Logo](https://docs.aws.amazon.com/cdk/api/latest/img/python32.png) Python|`cdk_use_cases.custom_cloud9_ssm`|
|![Typescript Logo](https://docs.aws.amazon.com/cdk/api/latest/img/typescript32.png) Typescript|`@cdk-use-cases/custom-cloud9-ssm`|
|![Java Logo](https://docs.aws.amazon.com/cdk/api/latest/img/java32.png) Java|`software.amazon.cdkusecases.customcloud9ssm`|

This pattern implements a Cloud9 EC2 environment, applying an initial configuration to the EC2 instance using an SSM Document. It includes helper methods to add steps and parameters to the SSM Document and to resize the EBS volume of the EC2 instance to a given size.

Here is a minimal deployable pattern definition in Typescript:

``` typescript
new CustomCloud9Ssm(stack, 'CustomCloud9Ssm', {});
```

## Initializer

``` typescript
new CustomCloud9Ssm(scope: Construct, id: string, props: CustomCloud9SsmProps);
```

_Parameters_
    
* scope [`Construct`](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_core.Construct.html)
* id `string`
* props [`CustomCloud9SsmProps`](#pattern-construct-props)

## Pattern Construct Props

| **Name**     | **Type**        | **Description** |
|:-------------|:----------------|-----------------|
| ssmDocumentProps? | [ssm.CfnDocumentProps](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-ssm.CfnDocumentProps.html) | Optional configuration for the SSM Document. |
| cloud9Ec2Props? | [cloud9.Ec2EnvironmentProps](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-cloud9.Ec2EnvironmentProps.html) | Optional configuration for the Cloud9 EC2 environment. |

## Pattern Properties

| **Name**     | **Type**        | **Description** |
|:-------------|:----------------|-----------------|
| ec2Role | [iam.Role](https://docs.aws.amazon.com/cdk/api/latest/docs/@aws-cdk_aws-iam.Role.html) | The IAM Role that is attached to the EC2 instance launched with the Cloud9 environment to grant it permissions to execute the statements in the SSM Document. |

## Pattern Methods

``` typescript
public addDocumentSteps(steps: string): void
```

_Description_

Adds one or more steps to the content of the SSM Document.

_Parameters_

* steps `string`: YAML formatted string containing one or more steps to be added to the `mainSteps` section of the SSM Document.

``` typescript
public addDocumentParameters(parameters: string): void
```

_Description_

Adds one or more parameters to the content of the SSM Document.

_Parameters_

* parameters `string`: YAML formatted string containing one or more parameters to be added to the `parameters` section of the SSM Document.

``` typescript
public resizeEBSTo(size: number): void
```

_Description_

Adds a step to the SSM Document content that resizes the EBS volume of the EC2 instance. Attaches the required policies to `ec2Role`.

_Parameters_

* size `number`: size to resize the EBS volume to.


## Default settings

Out of the box implementation of the Construct without any override will set the following defaults:

### Cloud9 EC2 environment
* Creates a Cloud9 EC2 environment with:
    * New VPC that spans 2 AZs and has one public and private subnet per AZ.
    * T2.micro instance type.

### SSM Document
* Creates an SSM Document with:
    * A step that installs jq and boto3.
    * A step that resizes the EBS volume of the EC2 instance to 100GB.

## Architecture
![Architecture Diagram](architecture.png)

***
&copy; Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
