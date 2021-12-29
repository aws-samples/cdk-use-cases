import {CustomResource, Duration, Tags} from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cloud9 from 'aws-cdk-lib/aws-cloud9';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as iam from 'aws-cdk-lib/aws-iam';

const yaml = require('yaml')
const fs   = require('fs')

export interface CustomCloud9SsmProps {
    /**
     * Optional configuration for the SSM Document.
     *
     * @default: none
     */
    readonly ssmDocumentProps?: ssm.CfnDocumentProps

    /**
     * Optional configuration for the Cloud9 EC2 environment.
     *
     * @default: none
     */
    readonly cloud9Ec2Props?: cloud9.CfnEnvironmentEC2Props
}

export class CustomCloud9Ssm extends Construct {
    private static readonly DEFAULT_EBS_SIZE = 100
    private static readonly DEFAULT_DOCUMENT_FILE_NAME = `${__dirname}/assets/default_document.yml`
    private static readonly RESIZE_STEP_FILE_NAME = `${__dirname}/assets/resize_ebs_step.yml`
    private static readonly ATTACH_PROFILE_FILE_NAME = `${__dirname}/assets/profile_attach.py`
    private static readonly DEFAULT_DOCUMENT_NAME = 'CustomCloudSsm-SsmDocument'

    private readonly document: ssm.CfnDocument

    /**
     * The IAM Role that is attached to the EC2 instance launched with the Cloud9 environment to grant it permissions to execute the statements in the SSM Document.
     */
    public readonly ec2Role: iam.Role

    /**
     * Adds one or more steps to the content of the SSM Document.
     * @param steps: YAML formatted string containing one or more steps to be added to the mainSteps section of the SSM Document.
     */
    public addDocumentSteps(steps: string): void {
        // Add the mainSteps section if it doesn't exist
        if (!('mainSteps' in this.document.content)) {
            this.document.content['mainSteps'] = []
        }

        // Add the new step
        this.document.content['mainSteps'].push(...yaml.parse(steps))
    }

    /**
     * Adds one or more parameters to the content of the SSM Document.
     * @param parameters: YAML formatted string containing one or more parameters to be added to the parameters section of the SSM Document.
     */
    public addDocumentParameters(parameters: string): void {
        // Add the parameters section if it doesn't exist
        if (!('parameters' in this.document.content)) {
            this.document.content['parameters'] = {}
        }

        // Add the new parameter
        this.document.content['parameters'] = Object.assign({}, this.document.content['parameters'], yaml.parse(parameters))
    }

    /**
     * Adds a step to the SSM Document content that resizes the EBS volume of the EC2 instance. Attaches the required policies to ec2Role.
     * @param size: size in GiB to resize the EBS volume to.
     */
    public resizeEBSTo(size: number): void {
        let steps: string = fs.readFileSync(CustomCloud9Ssm.RESIZE_STEP_FILE_NAME, 'utf8')
        steps = steps.replace('{{ size }}', String(size))

        // Add the resizing step
        this.addDocumentSteps(steps)

        // Grant permission to the EC2 instance to execute the statements included in the SSM Document
        this.ec2Role.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
                'ec2:DescribeInstances',
                'ec2:ModifyVolume',
                'ec2:DescribeVolumesModifications'
            ],
            resources: ['*']
        }))
    }

    constructor(scope: Construct, id: string, props: CustomCloud9SsmProps = {}) {
        super(scope, id);

        let cloud9Env: cloud9.CfnEnvironmentEC2
        let ssmAssociation: ssm.CfnAssociation
        let customResource: CustomResource

        // Create the Cloud9 environment using the default configuration
        if (!props.cloud9Ec2Props) {
            cloud9Env = new cloud9.CfnEnvironmentEC2(this,'Cloud9Ec2Environment', {instanceType: "t3.large"})
        }
        // Create the Cloud9 environment using the received props
        else {
            cloud9Env = new cloud9.CfnEnvironmentEC2(this,'Cloud9Ec2Environment', props.cloud9Ec2Props)
        }

        // Create a Role for the EC2 instance and an instance profile with it
        this.ec2Role = new iam.Role(this,'Ec2Role', {
            assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
            roleName: id + '-CustomCloud9SsmEc2Role',
            managedPolicies: [
                iam.ManagedPolicy.fromManagedPolicyArn(
                    this,
                    id + '-SsmManagedPolicy',
                    'arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore'
                )
            ]
        })
        const instanceProfile = new iam.CfnInstanceProfile(this,'Ec2InstanceProfile', {
            roles: [this.ec2Role.roleName]
        })

        // Create the SSM Document using the default configuration
        if (!props.ssmDocumentProps) {
            let content: string = fs.readFileSync(CustomCloud9Ssm.DEFAULT_DOCUMENT_FILE_NAME, 'utf8')

            const ssmDocumentProps = {
                documentType: 'Command',
                content: yaml.parse(content),
                name: id + '-' + CustomCloud9Ssm.DEFAULT_DOCUMENT_NAME
            }

            this.document = new ssm.CfnDocument(this,'SsmDocument', ssmDocumentProps)
            this.resizeEBSTo(CustomCloud9Ssm.DEFAULT_EBS_SIZE)
        }
        // Create the SSM Document using the received props
        else {
            if (!props.ssmDocumentProps.name) {
                throw new Error("The document name must be specified.")
            }

            this.document = new ssm.CfnDocument(this,'SsmDocument', props.ssmDocumentProps)
        }

        // Add the name of the document as a tag to the EC2 instance to identify it as a target of the SSM Association
        Tags.of(cloud9Env).add("SSMConfiguration", this.document.name as string)

        // Create an SSM Association to apply the document configuration
        ssmAssociation = new ssm.CfnAssociation(this,'SsmAssociation', {
            name: this.document.name as string,
            targets: [
                {
                    key: 'tag:SSMConfiguration',
                    values: [this.document.name as string]
                }
            ]
        })

        // Create the Lambda function that attaches the instance profile to the EC2 instance
        let code: string = fs.readFileSync(CustomCloud9Ssm.ATTACH_PROFILE_FILE_NAME, 'utf8')

        const lambdaFunction = new lambda.Function(this,'ProfileAttachLambdaFunction', {
            runtime: lambda.Runtime.PYTHON_3_6,
            code: lambda.Code.fromInline(code),
            handler: 'index.handler',
            timeout: Duration.seconds(800)
        })

        // Give permissions to the function to execute some APIs
        lambdaFunction.addToRolePolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
                'ec2:DescribeInstances',
                'ec2:AssociateIamInstanceProfile',
                'ec2:ReplaceIamInstanceProfileAssociation',
                'ec2:RebootInstances',
                'iam:ListInstanceProfiles',
                'iam:PassRole',
                'ssm:DescribeAssociationExecutions',
                'ssm:DescribeAssociationExecutionTargets'
            ],
            resources: ['*']
        }))

        // Create the Custom Resource that invokes the Lambda function
        customResource = new CustomResource(this, 'CustomResource', {
            serviceToken: lambdaFunction.functionArn,
            properties: {
                document_name: this.document.name as string,
                profile_arn: instanceProfile.attrArn,
                association_id: ssmAssociation.attrAssociationId
            }
        })

        // Add resource dependencies
        instanceProfile.node.addDependency(this.ec2Role)

        ssmAssociation.node.addDependency(cloud9Env)
        ssmAssociation.node.addDependency(this.document)

        customResource.node.addDependency(instanceProfile)
        customResource.node.addDependency(ssmAssociation)
    }
}
