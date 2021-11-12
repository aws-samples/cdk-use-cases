import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as cloud9 from '@aws-cdk/aws-cloud9';
import * as ssm from '@aws-cdk/aws-ssm';
import * as lambda from '@aws-cdk/aws-lambda';
import * as iam from '@aws-cdk/aws-iam';

const yaml = require('yaml')
const fs   = require('fs')


export interface CustomCloud9SsmProps {
    readonly ssmDocumentProps?: ssm.CfnDocumentProps
    readonly cloud9Ec2Props?: cloud9.Ec2EnvironmentProps
}

export class CustomCloud9Ssm extends cdk.Construct {
    private static readonly DEFAULT_EBS_SIZE = 100
    private static readonly DEFAULT_DOCUMENT_FILE_NAME = `${__dirname}/assets/default_document.yml`
    private static readonly RESIZE_STEP_FILE_NAME = `${__dirname}/assets/resize_ebs_step.yml`
    private static readonly ATTACH_PROFILE_FILE_NAME = `${__dirname}/assets/profile_attach.py`
    private static readonly DEFAULT_DOCUMENT_NAME = 'CustomCloudSsm-SsmDocument'

    private document: ssm.CfnDocument
    public readonly ec2Role: iam.Role


    public addDocumentSteps(steps: string): void {
        // Add the mainSteps section if it doesn't exist
        if (!('mainSteps' in this.document.content)) {
            this.document.content['mainSteps'] = []
        }

        // Add the new step
        this.document.content['mainSteps'].push(...yaml.parse(steps))
    }

    public addDocumentParameters(parameters: string): void {
        // Add the parameters section if it doesn't exist
        if (!('parameters' in this.document.content)) {
            this.document.content['parameters'] = {}
        }

        // Add the new parameter
        this.document.content['parameters'] = Object.assign({}, this.document.content['parameters'], yaml.parse(parameters))
    }

    public resizeEBSTo(size: number): void {
        let steps: string = fs.readFileSync(CustomCloud9Ssm.RESIZE_STEP_FILE_NAME, 'utf8')
        steps.replace('{{ size }}', String(size))

        // Add the resizing step
        this.addDocumentSteps(steps)

        // Grant permission to the EC2 instance to execute the statements included in the SSM Document
        this.ec2Role.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
                'ec2:DescribeInstances',
                'ec2:ModifyVolume'
            ],
            resources: ['*']
        }))
    }

    constructor(scope: cdk.Construct, id: string, props: CustomCloud9SsmProps) {
        super(scope, id)

        let cloud9Env: cloud9.Ec2Environment

        // Create the Cloud9 environment using the default configuration
        if (!props.cloud9Ec2Props) {
            cloud9Env = new cloud9.Ec2Environment(this, 'Cloud9Ec2Environment', {
                vpc: new ec2.Vpc(this, 'VPC', {
                    maxAzs: 2
                })
            })
        }
        // Create the Cloud9 environment using the received props
        else {
            cloud9Env = new cloud9.Ec2Environment(this, 'Cloud9Ec2Environment', props.cloud9Ec2Props)
        }

        // Create a Role for the EC2 instance and an instance profile with it
        this.ec2Role = new iam.Role(this,'Ec2Role', {
            assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
            roleName: 'CustomCloud9SsmEc2Role',
            managedPolicies: [
                iam.ManagedPolicy.fromManagedPolicyArn(
                    this,
                    'SsmManagedPolicy',
                    'arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore'
                )
            ]
        })
        const instanceProfile = new iam.CfnInstanceProfile(this, 'Ec2InstanceProfile', {
            roles: [this.ec2Role.roleName]
        })

        // Create the SSM Document using the default configuration
        if (!props.ssmDocumentProps) {
            let content: string = fs.readFileSync(CustomCloud9Ssm.DEFAULT_DOCUMENT_FILE_NAME, 'utf8')

            const ssmDocumentProps = {
                documentType: 'Command',
                content: yaml.parse(content)
            }

            this.document = new ssm.CfnDocument(this, 'SsmDocument', ssmDocumentProps)
            this.resizeEBSTo(CustomCloud9Ssm.DEFAULT_EBS_SIZE)
        }
        // Create the SSM Document using the received props
        else {
            this.document = new ssm.CfnDocument(this, 'SsmDocument', props.ssmDocumentProps)
        }

        // Create an SSM Association to apply the document configuration
        new ssm.CfnAssociation(this, 'SsmAssociation', {
            name: this.document.name? this.document.name : CustomCloud9Ssm.DEFAULT_DOCUMENT_NAME,
            targets: [
                {
                    key: 'tag:aws:cloud9:environment',
                    values: [cloud9Env.environmentId]
                }
            ]
        })

        // Create the Lambda function that attaches the instance profile to the EC2 instance
        let code: string = fs.readFileSync(CustomCloud9Ssm.ATTACH_PROFILE_FILE_NAME, 'utf8')

        const lambdaFunction = new lambda.Function(this, 'LambdaFunction', {
            runtime: lambda.Runtime.PYTHON_3_6,
            code: lambda.Code.fromInline(code),
            handler: 'index.handler',
            timeout: cdk.Duration.seconds(60)
        })

        // Create the Custom Resource that invokes the Lambda function
        new cdk.CustomResource(this, 'CustomResource', {
            serviceToken: lambdaFunction.functionArn,
            properties: {
                cloud9_env_id: cloud9Env.environmentId,
                profile_arn: instanceProfile.attrArn
            }
        })
    }
}
