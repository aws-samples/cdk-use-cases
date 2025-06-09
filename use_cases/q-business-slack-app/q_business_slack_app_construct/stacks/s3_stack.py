import hashlib

from aws_cdk import (
    aws_s3 as s3,
    NestedStack, RemovalPolicy,
    aws_s3_deployment as s3_deployment, Names
)
from constructs import Construct


class S3Stack(NestedStack):
    def __create_bucket(self, app_name):
        unique_suffix = Names.unique_id(self)
        hash_suffix = hashlib.sha256(unique_suffix.encode()).hexdigest()[:12]

        bucket = s3.Bucket(
            self, 'Bucket',
            bucket_name=f'{app_name.lower()}-{hash_suffix}',
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,

        )

        s3_deployment.BucketDeployment(
            self, 'BucketDeployment',
            destination_bucket=bucket,
            sources=[s3_deployment.Source.asset("q_business_slack_app_construct/assets/q_app_bucket_contents")]
        )

        return bucket

    def __init__(self, scope: Construct, construct_id: str, app_name: str) -> None:
        super().__init__(scope, construct_id)

        self.bucket = self.__create_bucket(app_name)
