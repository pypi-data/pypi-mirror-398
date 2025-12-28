r'''
# aws-lambda-transcribe module

<!--BEGIN STABILITY BANNER-->---


![Stability: Experimental](https://img.shields.io/badge/stability-Experimental-important.svg?style=for-the-badge)

---
<!--END STABILITY BANNER-->

| **Reference Documentation**:| <span style="font-weight: normal">https://docs.aws.amazon.com/solutions/latest/constructs/</span>|
|:-------------|:-------------|

<div style="height:8px"></div>

| **Language**     | **Package**        |
|:-------------|-----------------|
|![Python Logo](https://docs.aws.amazon.com/cdk/api/latest/img/python32.png) Python|`aws_solutions_constructs.aws_lambda_transcribe`|
|![Typescript Logo](https://docs.aws.amazon.com/cdk/api/latest/img/typescript32.png) Typescript|`@aws-solutions-constructs/aws-lambda-transcribe`|
|![Java Logo](https://docs.aws.amazon.com/cdk/api/latest/img/java32.png) Java|`software.amazon.awsconstructs.services.lambdatranscribe`|

## Overview

This AWS Solutions Construct implements an AWS Lambda function connected to Amazon S3 buckets for use with Amazon Transcribe.

Here is a minimal deployable pattern definition:

Typescript

```python
import { Construct } from 'constructs';
import { Stack, StackProps } from 'aws-cdk-lib';
import { LambdaToTranscribe } from '@aws-solutions-constructs/aws-lambda-transcribe';
import * as lambda from 'aws-cdk-lib/aws-lambda';

new LambdaToTranscribe(this, 'LambdaToTranscribePattern', {
    lambdaFunctionProps: {
        runtime: lambda.Runtime.NODEJS_22_X,
        handler: 'index.handler',
        code: lambda.Code.fromAsset(`lambda`)
    }
});
```

Python

```python
from aws_solutions_constructs.aws_lambda_transcribe import LambdaToTranscribe
from aws_cdk import (
    aws_lambda as _lambda,
    Stack
)
from constructs import Construct

LambdaToTranscribe(self, 'LambdaToTranscribePattern',
        lambda_function_props=_lambda.FunctionProps(
            code=_lambda.Code.from_asset('lambda'),
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler='index.handler'
        )
        )
```

Java

```java
import software.constructs.Construct;

import software.amazon.awscdk.Stack;
import software.amazon.awscdk.StackProps;
import software.amazon.awscdk.services.lambda.*;
import software.amazon.awscdk.services.lambda.Runtime;
import software.amazon.awsconstructs.services.lambdatranscribe.*;

new LambdaToTranscribe(this, "LambdaToTranscribePattern", new LambdaToTranscribeProps.Builder()
        .lambdaFunctionProps(new FunctionProps.Builder()
                .runtime(Runtime.NODEJS_22_X)
                .code(Code.fromAsset("lambda"))
                .handler("index.handler")
                .build())
        .build());
```

## Pattern Construct Props

| **Name**     | **Type**        | **Description** |
|:-------------|:----------------|-----------------|
|existingLambdaObj?|[`lambda.Function`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda.Function.html)|Existing instance of Lambda Function object, providing both this and `lambdaFunctionProps` will cause an error.|
|lambdaFunctionProps?|[`lambda.FunctionProps`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda.FunctionProps.html)|Optional user provided props to override the default props for the Lambda function.|
|existingSourceBucketObj?|[`s3.IBucket`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_s3.IBucket.html)|Existing instance of S3 Bucket object for source audio files.|
|sourceBucketProps?|[`s3.BucketProps`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_s3.BucketProps.html)|Optional user provided props to override the default props for the source S3 Bucket.|
|existingDestinationBucketObj?|[`s3.IBucket`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_s3.IBucket.html)|Existing instance of S3 Bucket object for transcription results.|
|destinationBucketProps?|[`s3.BucketProps`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_s3.BucketProps.html)|Optional user provided props to override the default props for the destination S3 Bucket.|
|useSameBucket?|`boolean`|Whether to use the same S3 bucket for both source and destination files. Default: false|

## Pattern Properties

| **Name**     | **Type**        | **Description** |
|:-------------|:----------------|-----------------|
|lambdaFunction|[`lambda.Function`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda.Function.html)|Returns an instance of the Lambda function created by the pattern.|
|sourceBucket?|[`s3.Bucket`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_s3.Bucket.html)|Returns an instance of the source S3 bucket created by the pattern.|
|destinationBucket?|[`s3.Bucket`](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_s3.Bucket.html)|Returns an instance of the destination S3 bucket created by the pattern.|

## Default settings

Out of the box implementation of the Construct without any override will set the following defaults:

### AWS Lambda Function

* Configure limited privilege access IAM role for Lambda function
* Enable reusing connections with Keep-Alive for NodeJs Lambda function
* Enable X-Ray Tracing
* Set Environment Variables

  * SOURCE_BUCKET_NAME
  * DESTINATION_BUCKET_NAME
  * AWS_NODEJS_CONNECTION_REUSE_ENABLED (for Node 10.x and higher functions)
* Grant permissions to use Amazon Transcribe service, write to source bucket, and read from destination bucket

### Amazon S3 Buckets

* Configure Access logging for both S3 Buckets
* Enable server-side encryption for both S3 Buckets using AWS managed KMS Key
* Enforce encryption of data in transit
* Turn on the versioning for both S3 Buckets
* Don't allow public access for both S3 Buckets
* Retain the S3 Buckets when deleting the CloudFormation stack

### Amazon Transcribe Service

* The Transcribe service will have read access to the source bucket and write permissions to the destination bucket
* Lambda function will have permissions to start transcription jobs, get job status, and list transcription jobs

## Architecture

![Architecture Diagram](architecture.png)

---


© Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import constructs as _constructs_77d1e7e8


class LambdaToTranscribe(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-lambda-transcribe.LambdaToTranscribe",
):
    '''
    :summary: The LambdaToTranscribe class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        destination_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
        destination_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        destination_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_destination_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_source_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_destination_s3_access_logs: typing.Optional[builtins.bool] = None,
        log_source_s3_access_logs: typing.Optional[builtins.bool] = None,
        source_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
        source_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        source_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        use_same_bucket: typing.Optional[builtins.bool] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param destination_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the destination bucket. Default: - DESTINATION_BUCKET_NAME
        :param destination_bucket_props: Optional user provided props to override the default props for the destination S3 Bucket. Default: - Default props are used
        :param destination_logging_bucket_props: Optional user provided props to override the default props for the destination S3 Logging Bucket. Default: - Default props are used
        :param existing_destination_bucket_obj: Existing instance of S3 Bucket object for transcription results, providing both this and ``destinationBucketProps`` will cause an error. Default: - None
        :param existing_lambda_obj: Existing instance of Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_source_bucket_obj: Existing instance of S3 Bucket object for source audio files, providing both this and ``sourceBucketProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default properties are used.
        :param log_destination_s3_access_logs: Whether to turn on Access Logs for the destination S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param log_source_s3_access_logs: Whether to turn on Access Logs for the source S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param source_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the source bucket. Default: - SOURCE_BUCKET_NAME
        :param source_bucket_props: Optional user provided props to override the default props for the source S3 Bucket. Default: - Default props are used
        :param source_logging_bucket_props: Optional user provided props to override the default props for the source S3 Logging Bucket. Default: - Default props are used
        :param use_same_bucket: Whether to use the same S3 bucket for both source and destination files. Default: - false
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :access: public
        :summary: Constructs a new instance of the LambdaToTranscribe class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bb0670a21928ee2853f7f2fe6000bf5d058c4375bd032f00f8ca27e78c1b1c70)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = LambdaToTranscribeProps(
            deploy_vpc=deploy_vpc,
            destination_bucket_environment_variable_name=destination_bucket_environment_variable_name,
            destination_bucket_props=destination_bucket_props,
            destination_logging_bucket_props=destination_logging_bucket_props,
            existing_destination_bucket_obj=existing_destination_bucket_obj,
            existing_lambda_obj=existing_lambda_obj,
            existing_source_bucket_obj=existing_source_bucket_obj,
            existing_vpc=existing_vpc,
            lambda_function_props=lambda_function_props,
            log_destination_s3_access_logs=log_destination_s3_access_logs,
            log_source_s3_access_logs=log_source_s3_access_logs,
            source_bucket_environment_variable_name=source_bucket_environment_variable_name,
            source_bucket_props=source_bucket_props,
            source_logging_bucket_props=source_logging_bucket_props,
            use_same_bucket=use_same_bucket,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="destinationBucketInterface")
    def destination_bucket_interface(self) -> _aws_cdk_aws_s3_ceddda9d.IBucket:
        return typing.cast(_aws_cdk_aws_s3_ceddda9d.IBucket, jsii.get(self, "destinationBucketInterface"))

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="sourceBucketInterface")
    def source_bucket_interface(self) -> _aws_cdk_aws_s3_ceddda9d.IBucket:
        return typing.cast(_aws_cdk_aws_s3_ceddda9d.IBucket, jsii.get(self, "sourceBucketInterface"))

    @builtins.property
    @jsii.member(jsii_name="destinationBucket")
    def destination_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "destinationBucket"))

    @builtins.property
    @jsii.member(jsii_name="destinationLoggingBucket")
    def destination_logging_bucket(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "destinationLoggingBucket"))

    @builtins.property
    @jsii.member(jsii_name="sourceBucket")
    def source_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "sourceBucket"))

    @builtins.property
    @jsii.member(jsii_name="sourceLoggingBucket")
    def source_logging_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "sourceLoggingBucket"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-lambda-transcribe.LambdaToTranscribeProps",
    jsii_struct_bases=[],
    name_mapping={
        "deploy_vpc": "deployVpc",
        "destination_bucket_environment_variable_name": "destinationBucketEnvironmentVariableName",
        "destination_bucket_props": "destinationBucketProps",
        "destination_logging_bucket_props": "destinationLoggingBucketProps",
        "existing_destination_bucket_obj": "existingDestinationBucketObj",
        "existing_lambda_obj": "existingLambdaObj",
        "existing_source_bucket_obj": "existingSourceBucketObj",
        "existing_vpc": "existingVpc",
        "lambda_function_props": "lambdaFunctionProps",
        "log_destination_s3_access_logs": "logDestinationS3AccessLogs",
        "log_source_s3_access_logs": "logSourceS3AccessLogs",
        "source_bucket_environment_variable_name": "sourceBucketEnvironmentVariableName",
        "source_bucket_props": "sourceBucketProps",
        "source_logging_bucket_props": "sourceLoggingBucketProps",
        "use_same_bucket": "useSameBucket",
        "vpc_props": "vpcProps",
    },
)
class LambdaToTranscribeProps:
    def __init__(
        self,
        *,
        deploy_vpc: typing.Optional[builtins.bool] = None,
        destination_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
        destination_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        destination_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_destination_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_source_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_destination_s3_access_logs: typing.Optional[builtins.bool] = None,
        log_source_s3_access_logs: typing.Optional[builtins.bool] = None,
        source_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
        source_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        source_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        use_same_bucket: typing.Optional[builtins.bool] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param destination_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the destination bucket. Default: - DESTINATION_BUCKET_NAME
        :param destination_bucket_props: Optional user provided props to override the default props for the destination S3 Bucket. Default: - Default props are used
        :param destination_logging_bucket_props: Optional user provided props to override the default props for the destination S3 Logging Bucket. Default: - Default props are used
        :param existing_destination_bucket_obj: Existing instance of S3 Bucket object for transcription results, providing both this and ``destinationBucketProps`` will cause an error. Default: - None
        :param existing_lambda_obj: Existing instance of Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_source_bucket_obj: Existing instance of S3 Bucket object for source audio files, providing both this and ``sourceBucketProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default properties are used.
        :param log_destination_s3_access_logs: Whether to turn on Access Logs for the destination S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param log_source_s3_access_logs: Whether to turn on Access Logs for the source S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param source_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the source bucket. Default: - SOURCE_BUCKET_NAME
        :param source_bucket_props: Optional user provided props to override the default props for the source S3 Bucket. Default: - Default props are used
        :param source_logging_bucket_props: Optional user provided props to override the default props for the source S3 Logging Bucket. Default: - Default props are used
        :param use_same_bucket: Whether to use the same S3 bucket for both source and destination files. Default: - false
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :summary: The properties for the LambdaToTranscribe class.
        '''
        if isinstance(destination_bucket_props, dict):
            destination_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**destination_bucket_props)
        if isinstance(destination_logging_bucket_props, dict):
            destination_logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**destination_logging_bucket_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(source_bucket_props, dict):
            source_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**source_bucket_props)
        if isinstance(source_logging_bucket_props, dict):
            source_logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**source_logging_bucket_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0231621833b3a9d9d0f5a4a367f1d87af322de6fa51cc5ff03818555bd27958f)
            check_type(argname="argument deploy_vpc", value=deploy_vpc, expected_type=type_hints["deploy_vpc"])
            check_type(argname="argument destination_bucket_environment_variable_name", value=destination_bucket_environment_variable_name, expected_type=type_hints["destination_bucket_environment_variable_name"])
            check_type(argname="argument destination_bucket_props", value=destination_bucket_props, expected_type=type_hints["destination_bucket_props"])
            check_type(argname="argument destination_logging_bucket_props", value=destination_logging_bucket_props, expected_type=type_hints["destination_logging_bucket_props"])
            check_type(argname="argument existing_destination_bucket_obj", value=existing_destination_bucket_obj, expected_type=type_hints["existing_destination_bucket_obj"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument existing_source_bucket_obj", value=existing_source_bucket_obj, expected_type=type_hints["existing_source_bucket_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument log_destination_s3_access_logs", value=log_destination_s3_access_logs, expected_type=type_hints["log_destination_s3_access_logs"])
            check_type(argname="argument log_source_s3_access_logs", value=log_source_s3_access_logs, expected_type=type_hints["log_source_s3_access_logs"])
            check_type(argname="argument source_bucket_environment_variable_name", value=source_bucket_environment_variable_name, expected_type=type_hints["source_bucket_environment_variable_name"])
            check_type(argname="argument source_bucket_props", value=source_bucket_props, expected_type=type_hints["source_bucket_props"])
            check_type(argname="argument source_logging_bucket_props", value=source_logging_bucket_props, expected_type=type_hints["source_logging_bucket_props"])
            check_type(argname="argument use_same_bucket", value=use_same_bucket, expected_type=type_hints["use_same_bucket"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if deploy_vpc is not None:
            self._values["deploy_vpc"] = deploy_vpc
        if destination_bucket_environment_variable_name is not None:
            self._values["destination_bucket_environment_variable_name"] = destination_bucket_environment_variable_name
        if destination_bucket_props is not None:
            self._values["destination_bucket_props"] = destination_bucket_props
        if destination_logging_bucket_props is not None:
            self._values["destination_logging_bucket_props"] = destination_logging_bucket_props
        if existing_destination_bucket_obj is not None:
            self._values["existing_destination_bucket_obj"] = existing_destination_bucket_obj
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if existing_source_bucket_obj is not None:
            self._values["existing_source_bucket_obj"] = existing_source_bucket_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if log_destination_s3_access_logs is not None:
            self._values["log_destination_s3_access_logs"] = log_destination_s3_access_logs
        if log_source_s3_access_logs is not None:
            self._values["log_source_s3_access_logs"] = log_source_s3_access_logs
        if source_bucket_environment_variable_name is not None:
            self._values["source_bucket_environment_variable_name"] = source_bucket_environment_variable_name
        if source_bucket_props is not None:
            self._values["source_bucket_props"] = source_bucket_props
        if source_logging_bucket_props is not None:
            self._values["source_logging_bucket_props"] = source_logging_bucket_props
        if use_same_bucket is not None:
            self._values["use_same_bucket"] = use_same_bucket
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def deploy_vpc(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a new VPC.

        :default: - false
        '''
        result = self._values.get("deploy_vpc")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def destination_bucket_environment_variable_name(
        self,
    ) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the name of the destination bucket.

        :default: - DESTINATION_BUCKET_NAME
        '''
        result = self._values.get("destination_bucket_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def destination_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the destination S3 Bucket.

        :default: - Default props are used
        '''
        result = self._values.get("destination_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def destination_logging_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the destination S3 Logging Bucket.

        :default: - Default props are used
        '''
        result = self._values.get("destination_logging_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def existing_destination_bucket_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        '''Existing instance of S3 Bucket object for transcription results, providing both this and ``destinationBucketProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_destination_bucket_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], result)

    @builtins.property
    def existing_lambda_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function]:
        '''Existing instance of Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_lambda_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function], result)

    @builtins.property
    def existing_source_bucket_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        '''Existing instance of S3 Bucket object for source audio files, providing both this and ``sourceBucketProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_source_bucket_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], result)

    @builtins.property
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC for the construct to use (construct will NOT create a new VPC in this case).'''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def lambda_function_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps]:
        '''Optional - user provided props to override the default props for the Lambda function.

        Providing both this and ``existingLambdaObj`` is an error.

        :default: - Default properties are used.
        '''
        result = self._values.get("lambda_function_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps], result)

    @builtins.property
    def log_destination_s3_access_logs(self) -> typing.Optional[builtins.bool]:
        '''Whether to turn on Access Logs for the destination S3 bucket with the associated storage costs.

        Enabling Access Logging is a best practice.

        :default: - true
        '''
        result = self._values.get("log_destination_s3_access_logs")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def log_source_s3_access_logs(self) -> typing.Optional[builtins.bool]:
        '''Whether to turn on Access Logs for the source S3 bucket with the associated storage costs.

        Enabling Access Logging is a best practice.

        :default: - true
        '''
        result = self._values.get("log_source_s3_access_logs")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def source_bucket_environment_variable_name(self) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the name of the source bucket.

        :default: - SOURCE_BUCKET_NAME
        '''
        result = self._values.get("source_bucket_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def source_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the source S3 Bucket.

        :default: - Default props are used
        '''
        result = self._values.get("source_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def source_logging_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the source S3 Logging Bucket.

        :default: - Default props are used
        '''
        result = self._values.get("source_logging_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def use_same_bucket(self) -> typing.Optional[builtins.bool]:
        '''Whether to use the same S3 bucket for both source and destination files.

        :default: - false
        '''
        result = self._values.get("use_same_bucket")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def vpc_props(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps]:
        '''Properties to override default properties if deployVpc is true.'''
        result = self._values.get("vpc_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LambdaToTranscribeProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "LambdaToTranscribe",
    "LambdaToTranscribeProps",
]

publication.publish()

def _typecheckingstub__bb0670a21928ee2853f7f2fe6000bf5d058c4375bd032f00f8ca27e78c1b1c70(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    destination_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
    destination_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    destination_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_destination_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_source_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_destination_s3_access_logs: typing.Optional[builtins.bool] = None,
    log_source_s3_access_logs: typing.Optional[builtins.bool] = None,
    source_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
    source_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    source_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    use_same_bucket: typing.Optional[builtins.bool] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0231621833b3a9d9d0f5a4a367f1d87af322de6fa51cc5ff03818555bd27958f(
    *,
    deploy_vpc: typing.Optional[builtins.bool] = None,
    destination_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
    destination_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    destination_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_destination_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_source_bucket_obj: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_destination_s3_access_logs: typing.Optional[builtins.bool] = None,
    log_source_s3_access_logs: typing.Optional[builtins.bool] = None,
    source_bucket_environment_variable_name: typing.Optional[builtins.str] = None,
    source_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    source_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    use_same_bucket: typing.Optional[builtins.bool] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
