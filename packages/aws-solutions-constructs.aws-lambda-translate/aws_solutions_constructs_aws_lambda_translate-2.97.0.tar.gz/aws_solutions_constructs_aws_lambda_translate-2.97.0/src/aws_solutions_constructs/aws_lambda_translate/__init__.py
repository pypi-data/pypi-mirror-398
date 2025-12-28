r'''
# aws-lambda-translate module

<!--BEGIN STABILITY BANNER-->---


![Stability: Experimental](https://img.shields.io/badge/stability-Experimental-important.svg?style=for-the-badge)

---
<!--END STABILITY BANNER-->

| **Reference Documentation**:| <span style="font-weight: normal">https://docs.aws.amazon.com/solutions/latest/constructs/</span>|
|:-------------|:-------------|

<div style="height:8px"></div>

| Language | Package |
|:---------|---------|
|![Python Logo](https://docs.aws.amazon.com/cdk/api/latest/img/python32.png) Python|`aws_solutions_constructs.aws_lambda_translate`|
|![Typescript Logo](https://docs.aws.amazon.com/cdk/api/latest/img/typescript32.png) Typescript|`@aws-solutions-constructs/aws-lambda-translate`|
|![Java Logo](https://docs.aws.amazon.com/cdk/api/latest/img/java32.png) Java|`software.amazon.awsconstructs.services.lambdatranslate`|

## Overview

This AWS Solutions Construct implements an AWS Lambda function connected to Amazon Translate service. For asynchronous translation jobs, the construct can optionally create source and destination S3 buckets with appropriate IAM permissions for the Lambda function to interact with both buckets and Amazon Translate service.

For full documentation, see the [README.adoc](README.adoc) file.

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


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-lambda-translate.EnvironmentVariableDefinition",
    jsii_struct_bases=[],
    name_mapping={
        "default_name": "defaultName",
        "value": "value",
        "client_name_override": "clientNameOverride",
    },
)
class EnvironmentVariableDefinition:
    def __init__(
        self,
        *,
        default_name: builtins.str,
        value: builtins.str,
        client_name_override: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param default_name: -
        :param value: -
        :param client_name_override: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dc5a40d076159233aade7b920615f7e0bce19512833c729b9fc0c54d3cbd0f53)
            check_type(argname="argument default_name", value=default_name, expected_type=type_hints["default_name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
            check_type(argname="argument client_name_override", value=client_name_override, expected_type=type_hints["client_name_override"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "default_name": default_name,
            "value": value,
        }
        if client_name_override is not None:
            self._values["client_name_override"] = client_name_override

    @builtins.property
    def default_name(self) -> builtins.str:
        result = self._values.get("default_name")
        assert result is not None, "Required property 'default_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def value(self) -> builtins.str:
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def client_name_override(self) -> typing.Optional[builtins.str]:
        result = self._values.get("client_name_override")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EnvironmentVariableDefinition(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class LambdaToTranslate(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-lambda-translate.LambdaToTranslate",
):
    '''
    :summary: The LambdaToTranslate class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        additional_permissions: typing.Optional[typing.Sequence[builtins.str]] = None,
        async_jobs: typing.Optional[builtins.bool] = None,
        data_access_role_arn_environment_variable_name: typing.Optional[builtins.str] = None,
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
        :param additional_permissions: Optional array of additional IAM permissions to grant to the Lambda function for Amazon Translate. Default: - ['translate:TranslateText', 'translate:TranslateDocument']
        :param async_jobs: Whether to enable asynchronous translation jobs. When true, source and destination S3 buckets will be created and the Lambda function will be granted permissions to start and stop translation jobs. Default: - false
        :param data_access_role_arn_environment_variable_name: Optional Name for the role to pass to Batch translate jobs. Only set if asyncJobs is true Default: - DATA_ACCESS_ROLE_ARN
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param destination_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the destination bucket. Only valid when asyncJobs is true. Default: - DESTINATION_BUCKET_NAME
        :param destination_bucket_props: Optional user provided props to override the default props for the destination S3 Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param destination_logging_bucket_props: Optional user provided props to override the default props for the destination S3 Logging Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param existing_destination_bucket_obj: Existing instance of S3 Bucket object for translation results, providing both this and ``destinationBucketProps`` will cause an error. Only valid when asyncJobs is true. Default: - None
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_source_bucket_obj: Existing instance of S3 Bucket object for source files, providing both this and ``sourceBucketProps`` will cause an error. Only valid when asyncJobs is true. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default properties are used.
        :param log_destination_s3_access_logs: Whether to turn on Access Logs for the destination S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Only valid when asyncJobs is true. Default: - true
        :param log_source_s3_access_logs: Whether to turn on Access Logs for the source S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Only valid when asyncJobs is true. Default: - true
        :param source_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the source bucket. Only valid when asyncJobs is true. Default: - SOURCE_BUCKET_NAME
        :param source_bucket_props: Optional user provided props to override the default props for the source S3 Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param source_logging_bucket_props: Optional user provided props to override the default props for the source S3 Logging Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param use_same_bucket: Whether to use the same S3 bucket for both source and destination files. When true, only the source bucket will be created and used for both purposes. Only valid when asyncJobs is true. Default: - false
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :access: public
        :summary: Constructs a new instance of the LambdaToTranslate class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ff2b7e413dbe2f595e0e589c92c275ff183790ccc23a5dd58d64b056e50a8304)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = LambdaToTranslateProps(
            additional_permissions=additional_permissions,
            async_jobs=async_jobs,
            data_access_role_arn_environment_variable_name=data_access_role_arn_environment_variable_name,
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
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="destinationBucket")
    def destination_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "destinationBucket"))

    @builtins.property
    @jsii.member(jsii_name="destinationBucketInterface")
    def destination_bucket_interface(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], jsii.get(self, "destinationBucketInterface"))

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
    @jsii.member(jsii_name="sourceBucketInterface")
    def source_bucket_interface(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], jsii.get(self, "sourceBucketInterface"))

    @builtins.property
    @jsii.member(jsii_name="sourceLoggingBucket")
    def source_logging_bucket(self) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket]:
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.Bucket], jsii.get(self, "sourceLoggingBucket"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-lambda-translate.LambdaToTranslateProps",
    jsii_struct_bases=[],
    name_mapping={
        "additional_permissions": "additionalPermissions",
        "async_jobs": "asyncJobs",
        "data_access_role_arn_environment_variable_name": "dataAccessRoleArnEnvironmentVariableName",
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
class LambdaToTranslateProps:
    def __init__(
        self,
        *,
        additional_permissions: typing.Optional[typing.Sequence[builtins.str]] = None,
        async_jobs: typing.Optional[builtins.bool] = None,
        data_access_role_arn_environment_variable_name: typing.Optional[builtins.str] = None,
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
        :param additional_permissions: Optional array of additional IAM permissions to grant to the Lambda function for Amazon Translate. Default: - ['translate:TranslateText', 'translate:TranslateDocument']
        :param async_jobs: Whether to enable asynchronous translation jobs. When true, source and destination S3 buckets will be created and the Lambda function will be granted permissions to start and stop translation jobs. Default: - false
        :param data_access_role_arn_environment_variable_name: Optional Name for the role to pass to Batch translate jobs. Only set if asyncJobs is true Default: - DATA_ACCESS_ROLE_ARN
        :param deploy_vpc: Whether to deploy a new VPC. Default: - false
        :param destination_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the destination bucket. Only valid when asyncJobs is true. Default: - DESTINATION_BUCKET_NAME
        :param destination_bucket_props: Optional user provided props to override the default props for the destination S3 Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param destination_logging_bucket_props: Optional user provided props to override the default props for the destination S3 Logging Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param existing_destination_bucket_obj: Existing instance of S3 Bucket object for translation results, providing both this and ``destinationBucketProps`` will cause an error. Only valid when asyncJobs is true. Default: - None
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_source_bucket_obj: Existing instance of S3 Bucket object for source files, providing both this and ``sourceBucketProps`` will cause an error. Only valid when asyncJobs is true. Default: - None
        :param existing_vpc: An existing VPC for the construct to use (construct will NOT create a new VPC in this case).
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default properties are used.
        :param log_destination_s3_access_logs: Whether to turn on Access Logs for the destination S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Only valid when asyncJobs is true. Default: - true
        :param log_source_s3_access_logs: Whether to turn on Access Logs for the source S3 bucket with the associated storage costs. Enabling Access Logging is a best practice. Only valid when asyncJobs is true. Default: - true
        :param source_bucket_environment_variable_name: Optional Name for the Lambda function environment variable set to the name of the source bucket. Only valid when asyncJobs is true. Default: - SOURCE_BUCKET_NAME
        :param source_bucket_props: Optional user provided props to override the default props for the source S3 Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param source_logging_bucket_props: Optional user provided props to override the default props for the source S3 Logging Bucket. Only valid when asyncJobs is true. Default: - Default props are used
        :param use_same_bucket: Whether to use the same S3 bucket for both source and destination files. When true, only the source bucket will be created and used for both purposes. Only valid when asyncJobs is true. Default: - false
        :param vpc_props: Properties to override default properties if deployVpc is true.

        :summary: The properties for the LambdaToTranslate class.
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
            type_hints = typing.get_type_hints(_typecheckingstub__d794e98bbaa9ed3fefea9ba9e3b6b743e2531613a7d37bca86f4df7e9b6111c6)
            check_type(argname="argument additional_permissions", value=additional_permissions, expected_type=type_hints["additional_permissions"])
            check_type(argname="argument async_jobs", value=async_jobs, expected_type=type_hints["async_jobs"])
            check_type(argname="argument data_access_role_arn_environment_variable_name", value=data_access_role_arn_environment_variable_name, expected_type=type_hints["data_access_role_arn_environment_variable_name"])
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
        if additional_permissions is not None:
            self._values["additional_permissions"] = additional_permissions
        if async_jobs is not None:
            self._values["async_jobs"] = async_jobs
        if data_access_role_arn_environment_variable_name is not None:
            self._values["data_access_role_arn_environment_variable_name"] = data_access_role_arn_environment_variable_name
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
    def additional_permissions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Optional array of additional IAM permissions to grant to the Lambda function for Amazon Translate.

        :default: - ['translate:TranslateText', 'translate:TranslateDocument']
        '''
        result = self._values.get("additional_permissions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def async_jobs(self) -> typing.Optional[builtins.bool]:
        '''Whether to enable asynchronous translation jobs.

        When true, source and destination S3 buckets will be created and the Lambda function
        will be granted permissions to start and stop translation jobs.

        :default: - false
        '''
        result = self._values.get("async_jobs")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def data_access_role_arn_environment_variable_name(
        self,
    ) -> typing.Optional[builtins.str]:
        '''Optional Name for the role to pass to Batch translate jobs.

        Only set if asyncJobs is true

        :default: - DATA_ACCESS_ROLE_ARN
        '''
        result = self._values.get("data_access_role_arn_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

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

        Only valid when asyncJobs is true.

        :default: - DESTINATION_BUCKET_NAME
        '''
        result = self._values.get("destination_bucket_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def destination_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the destination S3 Bucket.

        Only valid when asyncJobs is true.

        :default: - Default props are used
        '''
        result = self._values.get("destination_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def destination_logging_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the destination S3 Logging Bucket.

        Only valid when asyncJobs is true.

        :default: - Default props are used
        '''
        result = self._values.get("destination_logging_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def existing_destination_bucket_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        '''Existing instance of S3 Bucket object for translation results, providing both this and ``destinationBucketProps`` will cause an error.

        Only valid when asyncJobs is true.

        :default: - None
        '''
        result = self._values.get("existing_destination_bucket_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket], result)

    @builtins.property
    def existing_lambda_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function]:
        '''Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_lambda_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function], result)

    @builtins.property
    def existing_source_bucket_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket]:
        '''Existing instance of S3 Bucket object for source files, providing both this and ``sourceBucketProps`` will cause an error.

        Only valid when asyncJobs is true.

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
        Only valid when asyncJobs is true.

        :default: - true
        '''
        result = self._values.get("log_destination_s3_access_logs")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def log_source_s3_access_logs(self) -> typing.Optional[builtins.bool]:
        '''Whether to turn on Access Logs for the source S3 bucket with the associated storage costs.

        Enabling Access Logging is a best practice.
        Only valid when asyncJobs is true.

        :default: - true
        '''
        result = self._values.get("log_source_s3_access_logs")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def source_bucket_environment_variable_name(self) -> typing.Optional[builtins.str]:
        '''Optional Name for the Lambda function environment variable set to the name of the source bucket.

        Only valid when asyncJobs is true.

        :default: - SOURCE_BUCKET_NAME
        '''
        result = self._values.get("source_bucket_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def source_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the source S3 Bucket.

        Only valid when asyncJobs is true.

        :default: - Default props are used
        '''
        result = self._values.get("source_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def source_logging_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional user provided props to override the default props for the source S3 Logging Bucket.

        Only valid when asyncJobs is true.

        :default: - Default props are used
        '''
        result = self._values.get("source_logging_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

    @builtins.property
    def use_same_bucket(self) -> typing.Optional[builtins.bool]:
        '''Whether to use the same S3 bucket for both source and destination files.

        When true, only the source bucket will be created and used
        for both purposes. Only valid when asyncJobs is true.

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
        return "LambdaToTranslateProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "EnvironmentVariableDefinition",
    "LambdaToTranslate",
    "LambdaToTranslateProps",
]

publication.publish()

def _typecheckingstub__dc5a40d076159233aade7b920615f7e0bce19512833c729b9fc0c54d3cbd0f53(
    *,
    default_name: builtins.str,
    value: builtins.str,
    client_name_override: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ff2b7e413dbe2f595e0e589c92c275ff183790ccc23a5dd58d64b056e50a8304(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    additional_permissions: typing.Optional[typing.Sequence[builtins.str]] = None,
    async_jobs: typing.Optional[builtins.bool] = None,
    data_access_role_arn_environment_variable_name: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__d794e98bbaa9ed3fefea9ba9e3b6b743e2531613a7d37bca86f4df7e9b6111c6(
    *,
    additional_permissions: typing.Optional[typing.Sequence[builtins.str]] = None,
    async_jobs: typing.Optional[builtins.bool] = None,
    data_access_role_arn_environment_variable_name: typing.Optional[builtins.str] = None,
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
