r'''
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

import aws_cdk as _aws_cdk_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import constructs as _constructs_77d1e7e8


@jsii.enum(jsii_type="@robhan-cdk-lib/aws_mwaa.AirflowVersion")
class AirflowVersion(enum.Enum):
    V2_7_2 = "V2_7_2"
    V2_8_1 = "V2_8_1"
    V2_9_2 = "V2_9_2"
    V2_10_1 = "V2_10_1"
    V2_10_3 = "V2_10_3"
    V3_0_6 = "V3_0_6"


@jsii.enum(jsii_type="@robhan-cdk-lib/aws_mwaa.EndpointManagement")
class EndpointManagement(enum.Enum):
    CUSTOMER = "CUSTOMER"
    SERVICE = "SERVICE"


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_mwaa.EnvironmentAttributes",
    jsii_struct_bases=[],
    name_mapping={
        "airflow_configuration_options": "airflowConfigurationOptions",
        "environment_arn": "environmentArn",
        "name": "name",
        "airflow_version": "airflowVersion",
        "celery_executor_queue": "celeryExecutorQueue",
        "dag_s3_path": "dagS3Path",
        "database_vpc_endpoint_service": "databaseVpcEndpointService",
        "endpoint_management": "endpointManagement",
        "environment_class": "environmentClass",
        "execution_role": "executionRole",
        "kms_key": "kmsKey",
        "logging_configuration": "loggingConfiguration",
        "logging_configuration_dag_processing_logs_cloud_watch_log_group_arn": "loggingConfigurationDagProcessingLogsCloudWatchLogGroupArn",
        "logging_configuration_scheduler_logs_cloud_watch_log_group_arn": "loggingConfigurationSchedulerLogsCloudWatchLogGroupArn",
        "logging_configuration_task_logs_cloud_watch_log_group_arn": "loggingConfigurationTaskLogsCloudWatchLogGroupArn",
        "logging_configuration_webserver_logs_cloud_watch_log_group_arn": "loggingConfigurationWebserverLogsCloudWatchLogGroupArn",
        "logging_configuration_worker_logs_cloud_watch_log_group_arn": "loggingConfigurationWorkerLogsCloudWatchLogGroupArn",
        "max_webservers": "maxWebservers",
        "max_workers": "maxWorkers",
        "min_webservers": "minWebservers",
        "min_workers": "minWorkers",
        "network_configuration": "networkConfiguration",
        "plugins_s3_object_version": "pluginsS3ObjectVersion",
        "plugins_s3_path": "pluginsS3Path",
        "requirements_s3_object_version": "requirementsS3ObjectVersion",
        "requirements_s3_path": "requirementsS3Path",
        "schedulers": "schedulers",
        "source_bucket": "sourceBucket",
        "startup_script_s3_object_version": "startupScriptS3ObjectVersion",
        "startup_script_s3_path": "startupScriptS3Path",
        "webserver_access_mode": "webserverAccessMode",
        "webserver_url": "webserverUrl",
        "webserver_vpc_endpoint_service": "webserverVpcEndpointService",
        "weekly_maintenance_window_start": "weeklyMaintenanceWindowStart",
    },
)
class EnvironmentAttributes:
    def __init__(
        self,
        *,
        airflow_configuration_options: typing.Mapping[builtins.str, builtins.str],
        environment_arn: builtins.str,
        name: builtins.str,
        airflow_version: typing.Optional["AirflowVersion"] = None,
        celery_executor_queue: typing.Optional[builtins.str] = None,
        dag_s3_path: typing.Optional[builtins.str] = None,
        database_vpc_endpoint_service: typing.Optional[builtins.str] = None,
        endpoint_management: typing.Optional["EndpointManagement"] = None,
        environment_class: typing.Optional["EnvironmentClass"] = None,
        execution_role: typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"] = None,
        kms_key: typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"] = None,
        logging_configuration: typing.Optional[typing.Union["LoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        logging_configuration_dag_processing_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
        logging_configuration_scheduler_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
        logging_configuration_task_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
        logging_configuration_webserver_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
        logging_configuration_worker_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
        max_webservers: typing.Optional[jsii.Number] = None,
        max_workers: typing.Optional[jsii.Number] = None,
        min_webservers: typing.Optional[jsii.Number] = None,
        min_workers: typing.Optional[jsii.Number] = None,
        network_configuration: typing.Optional[typing.Union["NetworkConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        plugins_s3_object_version: typing.Optional[builtins.str] = None,
        plugins_s3_path: typing.Optional[builtins.str] = None,
        requirements_s3_object_version: typing.Optional[builtins.str] = None,
        requirements_s3_path: typing.Optional[builtins.str] = None,
        schedulers: typing.Optional[jsii.Number] = None,
        source_bucket: typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"] = None,
        startup_script_s3_object_version: typing.Optional[builtins.str] = None,
        startup_script_s3_path: typing.Optional[builtins.str] = None,
        webserver_access_mode: typing.Optional["WebserverAccessMode"] = None,
        webserver_url: typing.Optional[builtins.str] = None,
        webserver_vpc_endpoint_service: typing.Optional[builtins.str] = None,
        weekly_maintenance_window_start: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for importing an Amazon Managed Workflows for Apache Airflow Environment.

        :param airflow_configuration_options: A list of key-value pairs containing the Airflow configuration options for your environment. For example, core.default_timezone: utc.
        :param environment_arn: The ARN for the Amazon MWAA environment.
        :param name: The name of your Amazon MWAA environment.
        :param airflow_version: The version of Apache Airflow to use for the environment. If no value is specified, defaults to the latest version. If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        :param celery_executor_queue: The queue ARN for the environment's Celery Executor. Amazon MWAA uses a Celery Executor to distribute tasks across multiple workers. When you create an environment in a shared VPC, you must provide access to the Celery Executor queue from your VPC.
        :param dag_s3_path: The relative path to the DAGs folder on your Amazon S3 bucket. For example, dags.
        :param database_vpc_endpoint_service: The VPC endpoint for the environment's Amazon RDS database.
        :param endpoint_management: Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA. If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC. If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        :param environment_class: The environment class type.
        :param execution_role: The execution role in IAM that allows MWAA to access AWS resources in your environment.
        :param kms_key: The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment. You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        :param logging_configuration: The Apache Airflow logs being sent to CloudWatch Logs.
        :param logging_configuration_dag_processing_logs_cloud_watch_log_group_arn: The ARN for the CloudWatch Logs group where the Apache Airflow DAG processing logs are published.
        :param logging_configuration_scheduler_logs_cloud_watch_log_group_arn: The ARN for the CloudWatch Logs group where the Apache Airflow Scheduler logs are published.
        :param logging_configuration_task_logs_cloud_watch_log_group_arn: The ARN for the CloudWatch Logs group where the Apache Airflow task logs are published.
        :param logging_configuration_webserver_logs_cloud_watch_log_group_arn: The ARN for the CloudWatch Logs group where the Apache Airflow Web server logs are published.
        :param logging_configuration_worker_logs_cloud_watch_log_group_arn: The ARN for the CloudWatch Logs group where the Apache Airflow Worker logs are published.
        :param max_webservers: The maximum number of web servers that you want to run in your environment. Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers. Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        :param max_workers: The maximum number of workers that you want to run in your environment. MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or the number you specify in MinWorkers.
        :param min_webservers: The minimum number of web servers that you want to run in your environment. Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load, decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers. Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        :param min_workers: The minimum number of workers that you want to run in your environment. MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the worker count you specify in the MinWorkers field. For example, 2.
        :param network_configuration: The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.
        :param plugins_s3_object_version: The version of the plugins.zip file on your Amazon S3 bucket.
        :param plugins_s3_path: The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.
        :param requirements_s3_object_version: The version of the requirements.txt file on your Amazon S3 bucket.
        :param requirements_s3_path: The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.
        :param schedulers: The number of schedulers that you want to run in your environment. Valid values: v2 - For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1. v1 - Accepts 1.
        :param source_bucket: The Amazon S3 bucket where your DAG code and supporting files are stored.
        :param startup_script_s3_object_version: The version of the startup shell script in your Amazon S3 bucket. You must specify the version ID that Amazon S3 assigns to the file every time you update the script. Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long. The following is an example: 3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        :param startup_script_s3_path: The relative path to the startup shell script in your Amazon S3 bucket. For example, s3://mwaa-environment/startup.sh. Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process. You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        :param webserver_access_mode: The Apache Airflow Web server access mode.
        :param webserver_url: The URL of your Apache Airflow UI.
        :param webserver_vpc_endpoint_service: The VPC endpoint for the environment's web server.
        :param weekly_maintenance_window_start: The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM. For example: TUE:03:30. You can specify a start time in 30 minute increments only. Supported input includes the following: MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        if isinstance(logging_configuration, dict):
            logging_configuration = LoggingConfiguration(**logging_configuration)
        if isinstance(network_configuration, dict):
            network_configuration = NetworkConfiguration(**network_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d75f091b184b8fb2d88550b01b5b1291a3af0d350440b3c1dadc6631ec062c57)
            check_type(argname="argument airflow_configuration_options", value=airflow_configuration_options, expected_type=type_hints["airflow_configuration_options"])
            check_type(argname="argument environment_arn", value=environment_arn, expected_type=type_hints["environment_arn"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument airflow_version", value=airflow_version, expected_type=type_hints["airflow_version"])
            check_type(argname="argument celery_executor_queue", value=celery_executor_queue, expected_type=type_hints["celery_executor_queue"])
            check_type(argname="argument dag_s3_path", value=dag_s3_path, expected_type=type_hints["dag_s3_path"])
            check_type(argname="argument database_vpc_endpoint_service", value=database_vpc_endpoint_service, expected_type=type_hints["database_vpc_endpoint_service"])
            check_type(argname="argument endpoint_management", value=endpoint_management, expected_type=type_hints["endpoint_management"])
            check_type(argname="argument environment_class", value=environment_class, expected_type=type_hints["environment_class"])
            check_type(argname="argument execution_role", value=execution_role, expected_type=type_hints["execution_role"])
            check_type(argname="argument kms_key", value=kms_key, expected_type=type_hints["kms_key"])
            check_type(argname="argument logging_configuration", value=logging_configuration, expected_type=type_hints["logging_configuration"])
            check_type(argname="argument logging_configuration_dag_processing_logs_cloud_watch_log_group_arn", value=logging_configuration_dag_processing_logs_cloud_watch_log_group_arn, expected_type=type_hints["logging_configuration_dag_processing_logs_cloud_watch_log_group_arn"])
            check_type(argname="argument logging_configuration_scheduler_logs_cloud_watch_log_group_arn", value=logging_configuration_scheduler_logs_cloud_watch_log_group_arn, expected_type=type_hints["logging_configuration_scheduler_logs_cloud_watch_log_group_arn"])
            check_type(argname="argument logging_configuration_task_logs_cloud_watch_log_group_arn", value=logging_configuration_task_logs_cloud_watch_log_group_arn, expected_type=type_hints["logging_configuration_task_logs_cloud_watch_log_group_arn"])
            check_type(argname="argument logging_configuration_webserver_logs_cloud_watch_log_group_arn", value=logging_configuration_webserver_logs_cloud_watch_log_group_arn, expected_type=type_hints["logging_configuration_webserver_logs_cloud_watch_log_group_arn"])
            check_type(argname="argument logging_configuration_worker_logs_cloud_watch_log_group_arn", value=logging_configuration_worker_logs_cloud_watch_log_group_arn, expected_type=type_hints["logging_configuration_worker_logs_cloud_watch_log_group_arn"])
            check_type(argname="argument max_webservers", value=max_webservers, expected_type=type_hints["max_webservers"])
            check_type(argname="argument max_workers", value=max_workers, expected_type=type_hints["max_workers"])
            check_type(argname="argument min_webservers", value=min_webservers, expected_type=type_hints["min_webservers"])
            check_type(argname="argument min_workers", value=min_workers, expected_type=type_hints["min_workers"])
            check_type(argname="argument network_configuration", value=network_configuration, expected_type=type_hints["network_configuration"])
            check_type(argname="argument plugins_s3_object_version", value=plugins_s3_object_version, expected_type=type_hints["plugins_s3_object_version"])
            check_type(argname="argument plugins_s3_path", value=plugins_s3_path, expected_type=type_hints["plugins_s3_path"])
            check_type(argname="argument requirements_s3_object_version", value=requirements_s3_object_version, expected_type=type_hints["requirements_s3_object_version"])
            check_type(argname="argument requirements_s3_path", value=requirements_s3_path, expected_type=type_hints["requirements_s3_path"])
            check_type(argname="argument schedulers", value=schedulers, expected_type=type_hints["schedulers"])
            check_type(argname="argument source_bucket", value=source_bucket, expected_type=type_hints["source_bucket"])
            check_type(argname="argument startup_script_s3_object_version", value=startup_script_s3_object_version, expected_type=type_hints["startup_script_s3_object_version"])
            check_type(argname="argument startup_script_s3_path", value=startup_script_s3_path, expected_type=type_hints["startup_script_s3_path"])
            check_type(argname="argument webserver_access_mode", value=webserver_access_mode, expected_type=type_hints["webserver_access_mode"])
            check_type(argname="argument webserver_url", value=webserver_url, expected_type=type_hints["webserver_url"])
            check_type(argname="argument webserver_vpc_endpoint_service", value=webserver_vpc_endpoint_service, expected_type=type_hints["webserver_vpc_endpoint_service"])
            check_type(argname="argument weekly_maintenance_window_start", value=weekly_maintenance_window_start, expected_type=type_hints["weekly_maintenance_window_start"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "airflow_configuration_options": airflow_configuration_options,
            "environment_arn": environment_arn,
            "name": name,
        }
        if airflow_version is not None:
            self._values["airflow_version"] = airflow_version
        if celery_executor_queue is not None:
            self._values["celery_executor_queue"] = celery_executor_queue
        if dag_s3_path is not None:
            self._values["dag_s3_path"] = dag_s3_path
        if database_vpc_endpoint_service is not None:
            self._values["database_vpc_endpoint_service"] = database_vpc_endpoint_service
        if endpoint_management is not None:
            self._values["endpoint_management"] = endpoint_management
        if environment_class is not None:
            self._values["environment_class"] = environment_class
        if execution_role is not None:
            self._values["execution_role"] = execution_role
        if kms_key is not None:
            self._values["kms_key"] = kms_key
        if logging_configuration is not None:
            self._values["logging_configuration"] = logging_configuration
        if logging_configuration_dag_processing_logs_cloud_watch_log_group_arn is not None:
            self._values["logging_configuration_dag_processing_logs_cloud_watch_log_group_arn"] = logging_configuration_dag_processing_logs_cloud_watch_log_group_arn
        if logging_configuration_scheduler_logs_cloud_watch_log_group_arn is not None:
            self._values["logging_configuration_scheduler_logs_cloud_watch_log_group_arn"] = logging_configuration_scheduler_logs_cloud_watch_log_group_arn
        if logging_configuration_task_logs_cloud_watch_log_group_arn is not None:
            self._values["logging_configuration_task_logs_cloud_watch_log_group_arn"] = logging_configuration_task_logs_cloud_watch_log_group_arn
        if logging_configuration_webserver_logs_cloud_watch_log_group_arn is not None:
            self._values["logging_configuration_webserver_logs_cloud_watch_log_group_arn"] = logging_configuration_webserver_logs_cloud_watch_log_group_arn
        if logging_configuration_worker_logs_cloud_watch_log_group_arn is not None:
            self._values["logging_configuration_worker_logs_cloud_watch_log_group_arn"] = logging_configuration_worker_logs_cloud_watch_log_group_arn
        if max_webservers is not None:
            self._values["max_webservers"] = max_webservers
        if max_workers is not None:
            self._values["max_workers"] = max_workers
        if min_webservers is not None:
            self._values["min_webservers"] = min_webservers
        if min_workers is not None:
            self._values["min_workers"] = min_workers
        if network_configuration is not None:
            self._values["network_configuration"] = network_configuration
        if plugins_s3_object_version is not None:
            self._values["plugins_s3_object_version"] = plugins_s3_object_version
        if plugins_s3_path is not None:
            self._values["plugins_s3_path"] = plugins_s3_path
        if requirements_s3_object_version is not None:
            self._values["requirements_s3_object_version"] = requirements_s3_object_version
        if requirements_s3_path is not None:
            self._values["requirements_s3_path"] = requirements_s3_path
        if schedulers is not None:
            self._values["schedulers"] = schedulers
        if source_bucket is not None:
            self._values["source_bucket"] = source_bucket
        if startup_script_s3_object_version is not None:
            self._values["startup_script_s3_object_version"] = startup_script_s3_object_version
        if startup_script_s3_path is not None:
            self._values["startup_script_s3_path"] = startup_script_s3_path
        if webserver_access_mode is not None:
            self._values["webserver_access_mode"] = webserver_access_mode
        if webserver_url is not None:
            self._values["webserver_url"] = webserver_url
        if webserver_vpc_endpoint_service is not None:
            self._values["webserver_vpc_endpoint_service"] = webserver_vpc_endpoint_service
        if weekly_maintenance_window_start is not None:
            self._values["weekly_maintenance_window_start"] = weekly_maintenance_window_start

    @builtins.property
    def airflow_configuration_options(
        self,
    ) -> typing.Mapping[builtins.str, builtins.str]:
        '''A list of key-value pairs containing the Airflow configuration options for your environment.

        For example, core.default_timezone: utc.
        '''
        result = self._values.get("airflow_configuration_options")
        assert result is not None, "Required property 'airflow_configuration_options' is missing"
        return typing.cast(typing.Mapping[builtins.str, builtins.str], result)

    @builtins.property
    def environment_arn(self) -> builtins.str:
        '''The ARN for the Amazon MWAA environment.'''
        result = self._values.get("environment_arn")
        assert result is not None, "Required property 'environment_arn' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of your Amazon MWAA environment.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def airflow_version(self) -> typing.Optional["AirflowVersion"]:
        '''The version of Apache Airflow to use for the environment.

        If no value is specified, defaults to the latest version.

        If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        '''
        result = self._values.get("airflow_version")
        return typing.cast(typing.Optional["AirflowVersion"], result)

    @builtins.property
    def celery_executor_queue(self) -> typing.Optional[builtins.str]:
        '''The queue ARN for the environment's Celery Executor.

        Amazon MWAA uses a Celery Executor to distribute tasks across multiple workers.
        When you create an environment in a shared VPC, you must provide access to the Celery Executor queue from your VPC.
        '''
        result = self._values.get("celery_executor_queue")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def dag_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the DAGs folder on your Amazon S3 bucket.

        For example, dags.
        '''
        result = self._values.get("dag_s3_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def database_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's Amazon RDS database.'''
        result = self._values.get("database_vpc_endpoint_service")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def endpoint_management(self) -> typing.Optional["EndpointManagement"]:
        '''Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA.

        If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC.
        If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        '''
        result = self._values.get("endpoint_management")
        return typing.cast(typing.Optional["EndpointManagement"], result)

    @builtins.property
    def environment_class(self) -> typing.Optional["EnvironmentClass"]:
        '''The environment class type.'''
        result = self._values.get("environment_class")
        return typing.cast(typing.Optional["EnvironmentClass"], result)

    @builtins.property
    def execution_role(self) -> typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"]:
        '''The execution role in IAM that allows MWAA to access AWS resources in your environment.'''
        result = self._values.get("execution_role")
        return typing.cast(typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"], result)

    @builtins.property
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment.

        You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        '''
        result = self._values.get("kms_key")
        return typing.cast(typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"], result)

    @builtins.property
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''The Apache Airflow logs being sent to CloudWatch Logs.'''
        result = self._values.get("logging_configuration")
        return typing.cast(typing.Optional["LoggingConfiguration"], result)

    @builtins.property
    def logging_configuration_dag_processing_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow DAG processing logs are published.'''
        result = self._values.get("logging_configuration_dag_processing_logs_cloud_watch_log_group_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def logging_configuration_scheduler_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Scheduler logs are published.'''
        result = self._values.get("logging_configuration_scheduler_logs_cloud_watch_log_group_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def logging_configuration_task_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow task logs are published.'''
        result = self._values.get("logging_configuration_task_logs_cloud_watch_log_group_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def logging_configuration_webserver_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Web server logs are published.'''
        result = self._values.get("logging_configuration_webserver_logs_cloud_watch_log_group_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def logging_configuration_worker_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Worker logs are published.'''
        result = self._values.get("logging_configuration_worker_logs_cloud_watch_log_group_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def max_webservers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network
        calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to
        the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in
        MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        result = self._values.get("max_webservers")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_workers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more
        tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or
        the number you specify in MinWorkers.
        '''
        result = self._values.get("max_workers")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def min_webservers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load,
        decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        result = self._values.get("min_webservers")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def min_workers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you
        specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving
        the worker count you specify in the MinWorkers field. For example, 2.
        '''
        result = self._values.get("min_workers")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def network_configuration(self) -> typing.Optional["NetworkConfiguration"]:
        '''The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.'''
        result = self._values.get("network_configuration")
        return typing.cast(typing.Optional["NetworkConfiguration"], result)

    @builtins.property
    def plugins_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the plugins.zip file on your Amazon S3 bucket.'''
        result = self._values.get("plugins_s3_object_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def plugins_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.'''
        result = self._values.get("plugins_s3_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def requirements_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the requirements.txt file on your Amazon S3 bucket.'''
        result = self._values.get("requirements_s3_object_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def requirements_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.'''
        result = self._values.get("requirements_s3_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def schedulers(self) -> typing.Optional[jsii.Number]:
        '''The number of schedulers that you want to run in your environment.

        Valid values:
        v2 - For environments larger than mw1.micro, accepts values from 2 to 5.
        Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        v1 - Accepts 1.
        '''
        result = self._values.get("schedulers")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def source_bucket(self) -> typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"]:
        '''The Amazon S3 bucket where your DAG code and supporting files are stored.'''
        result = self._values.get("source_bucket")
        return typing.cast(typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"], result)

    @builtins.property
    def startup_script_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the startup shell script in your Amazon S3 bucket.

        You must specify the version ID that Amazon S3 assigns to the file every time you update the script.
        Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long.

        The following is an example:
        3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        '''
        result = self._values.get("startup_script_s3_object_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def startup_script_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the startup shell script in your Amazon S3 bucket.

        For example, s3://mwaa-environment/startup.sh.
        Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process.
        You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        '''
        result = self._values.get("startup_script_s3_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def webserver_access_mode(self) -> typing.Optional["WebserverAccessMode"]:
        '''The Apache Airflow Web server access mode.'''
        result = self._values.get("webserver_access_mode")
        return typing.cast(typing.Optional["WebserverAccessMode"], result)

    @builtins.property
    def webserver_url(self) -> typing.Optional[builtins.str]:
        '''The URL of your Apache Airflow UI.'''
        result = self._values.get("webserver_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def webserver_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's web server.'''
        result = self._values.get("webserver_vpc_endpoint_service")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def weekly_maintenance_window_start(self) -> typing.Optional[builtins.str]:
        '''The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM.

        For example: TUE:03:30. You can specify a start time in 30 minute increments only.

        Supported input includes the following:
        MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        result = self._values.get("weekly_maintenance_window_start")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EnvironmentAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(jsii_type="@robhan-cdk-lib/aws_mwaa.EnvironmentClass")
class EnvironmentClass(enum.Enum):
    MW1_MICRO = "MW1_MICRO"
    MW1_SMALL = "MW1_SMALL"
    MW1_MEDIUM = "MW1_MEDIUM"
    MW1_LARGE = "MW1_LARGE"
    MW1_1LARGE = "MW1_1LARGE"
    MW1_2LARGE = "MW1_2LARGE"


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_mwaa.EnvironmentProps",
    jsii_struct_bases=[],
    name_mapping={
        "airflow_configuration_options": "airflowConfigurationOptions",
        "name": "name",
        "airflow_version": "airflowVersion",
        "dag_s3_path": "dagS3Path",
        "endpoint_management": "endpointManagement",
        "environment_class": "environmentClass",
        "execution_role": "executionRole",
        "kms_key": "kmsKey",
        "logging_configuration": "loggingConfiguration",
        "max_webservers": "maxWebservers",
        "max_workers": "maxWorkers",
        "min_webservers": "minWebservers",
        "min_workers": "minWorkers",
        "network_configuration": "networkConfiguration",
        "plugins_s3_object_version": "pluginsS3ObjectVersion",
        "plugins_s3_path": "pluginsS3Path",
        "requirements_s3_object_version": "requirementsS3ObjectVersion",
        "requirements_s3_path": "requirementsS3Path",
        "schedulers": "schedulers",
        "source_bucket": "sourceBucket",
        "startup_script_s3_object_version": "startupScriptS3ObjectVersion",
        "startup_script_s3_path": "startupScriptS3Path",
        "webserver_access_mode": "webserverAccessMode",
        "weekly_maintenance_window_start": "weeklyMaintenanceWindowStart",
    },
)
class EnvironmentProps:
    def __init__(
        self,
        *,
        airflow_configuration_options: typing.Mapping[builtins.str, builtins.str],
        name: builtins.str,
        airflow_version: typing.Optional["AirflowVersion"] = None,
        dag_s3_path: typing.Optional[builtins.str] = None,
        endpoint_management: typing.Optional["EndpointManagement"] = None,
        environment_class: typing.Optional["EnvironmentClass"] = None,
        execution_role: typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"] = None,
        kms_key: typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"] = None,
        logging_configuration: typing.Optional[typing.Union["LoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        max_webservers: typing.Optional[jsii.Number] = None,
        max_workers: typing.Optional[jsii.Number] = None,
        min_webservers: typing.Optional[jsii.Number] = None,
        min_workers: typing.Optional[jsii.Number] = None,
        network_configuration: typing.Optional[typing.Union["NetworkConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        plugins_s3_object_version: typing.Optional[builtins.str] = None,
        plugins_s3_path: typing.Optional[builtins.str] = None,
        requirements_s3_object_version: typing.Optional[builtins.str] = None,
        requirements_s3_path: typing.Optional[builtins.str] = None,
        schedulers: typing.Optional[jsii.Number] = None,
        source_bucket: typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"] = None,
        startup_script_s3_object_version: typing.Optional[builtins.str] = None,
        startup_script_s3_path: typing.Optional[builtins.str] = None,
        webserver_access_mode: typing.Optional["WebserverAccessMode"] = None,
        weekly_maintenance_window_start: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for creating an Amazon Managed Workflows for Apache Airflow Environment.

        :param airflow_configuration_options: A list of key-value pairs containing the Airflow configuration options for your environment. For example, core.default_timezone: utc.
        :param name: The name of your Amazon MWAA environment.
        :param airflow_version: The version of Apache Airflow to use for the environment. If no value is specified, defaults to the latest version. If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        :param dag_s3_path: The relative path to the DAGs folder on your Amazon S3 bucket. For example, dags.
        :param endpoint_management: Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA. If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC. If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        :param environment_class: The environment class type.
        :param execution_role: The execution role in IAM that allows MWAA to access AWS resources in your environment.
        :param kms_key: The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment. You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        :param logging_configuration: The Apache Airflow logs being sent to CloudWatch Logs.
        :param max_webservers: The maximum number of web servers that you want to run in your environment. Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers. Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        :param max_workers: The maximum number of workers that you want to run in your environment. MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or the number you specify in MinWorkers.
        :param min_webservers: The minimum number of web servers that you want to run in your environment. Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load, decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers. Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        :param min_workers: The minimum number of workers that you want to run in your environment. MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the worker count you specify in the MinWorkers field. For example, 2.
        :param network_configuration: The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.
        :param plugins_s3_object_version: The version of the plugins.zip file on your Amazon S3 bucket.
        :param plugins_s3_path: The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.
        :param requirements_s3_object_version: The version of the requirements.txt file on your Amazon S3 bucket.
        :param requirements_s3_path: The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.
        :param schedulers: The number of schedulers that you want to run in your environment. Valid values: v2 - For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1. v1 - Accepts 1.
        :param source_bucket: The Amazon S3 bucket where your DAG code and supporting files are stored.
        :param startup_script_s3_object_version: The version of the startup shell script in your Amazon S3 bucket. You must specify the version ID that Amazon S3 assigns to the file every time you update the script. Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long. The following is an example: 3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        :param startup_script_s3_path: The relative path to the startup shell script in your Amazon S3 bucket. For example, s3://mwaa-environment/startup.sh. Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process. You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        :param webserver_access_mode: The Apache Airflow Web server access mode.
        :param weekly_maintenance_window_start: The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM. For example: TUE:03:30. You can specify a start time in 30 minute increments only. Supported input includes the following: MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        if isinstance(logging_configuration, dict):
            logging_configuration = LoggingConfiguration(**logging_configuration)
        if isinstance(network_configuration, dict):
            network_configuration = NetworkConfiguration(**network_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__adae2e01428b106a0a65893828e0f65d1e96376eb6556581f26b272553f74e81)
            check_type(argname="argument airflow_configuration_options", value=airflow_configuration_options, expected_type=type_hints["airflow_configuration_options"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument airflow_version", value=airflow_version, expected_type=type_hints["airflow_version"])
            check_type(argname="argument dag_s3_path", value=dag_s3_path, expected_type=type_hints["dag_s3_path"])
            check_type(argname="argument endpoint_management", value=endpoint_management, expected_type=type_hints["endpoint_management"])
            check_type(argname="argument environment_class", value=environment_class, expected_type=type_hints["environment_class"])
            check_type(argname="argument execution_role", value=execution_role, expected_type=type_hints["execution_role"])
            check_type(argname="argument kms_key", value=kms_key, expected_type=type_hints["kms_key"])
            check_type(argname="argument logging_configuration", value=logging_configuration, expected_type=type_hints["logging_configuration"])
            check_type(argname="argument max_webservers", value=max_webservers, expected_type=type_hints["max_webservers"])
            check_type(argname="argument max_workers", value=max_workers, expected_type=type_hints["max_workers"])
            check_type(argname="argument min_webservers", value=min_webservers, expected_type=type_hints["min_webservers"])
            check_type(argname="argument min_workers", value=min_workers, expected_type=type_hints["min_workers"])
            check_type(argname="argument network_configuration", value=network_configuration, expected_type=type_hints["network_configuration"])
            check_type(argname="argument plugins_s3_object_version", value=plugins_s3_object_version, expected_type=type_hints["plugins_s3_object_version"])
            check_type(argname="argument plugins_s3_path", value=plugins_s3_path, expected_type=type_hints["plugins_s3_path"])
            check_type(argname="argument requirements_s3_object_version", value=requirements_s3_object_version, expected_type=type_hints["requirements_s3_object_version"])
            check_type(argname="argument requirements_s3_path", value=requirements_s3_path, expected_type=type_hints["requirements_s3_path"])
            check_type(argname="argument schedulers", value=schedulers, expected_type=type_hints["schedulers"])
            check_type(argname="argument source_bucket", value=source_bucket, expected_type=type_hints["source_bucket"])
            check_type(argname="argument startup_script_s3_object_version", value=startup_script_s3_object_version, expected_type=type_hints["startup_script_s3_object_version"])
            check_type(argname="argument startup_script_s3_path", value=startup_script_s3_path, expected_type=type_hints["startup_script_s3_path"])
            check_type(argname="argument webserver_access_mode", value=webserver_access_mode, expected_type=type_hints["webserver_access_mode"])
            check_type(argname="argument weekly_maintenance_window_start", value=weekly_maintenance_window_start, expected_type=type_hints["weekly_maintenance_window_start"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "airflow_configuration_options": airflow_configuration_options,
            "name": name,
        }
        if airflow_version is not None:
            self._values["airflow_version"] = airflow_version
        if dag_s3_path is not None:
            self._values["dag_s3_path"] = dag_s3_path
        if endpoint_management is not None:
            self._values["endpoint_management"] = endpoint_management
        if environment_class is not None:
            self._values["environment_class"] = environment_class
        if execution_role is not None:
            self._values["execution_role"] = execution_role
        if kms_key is not None:
            self._values["kms_key"] = kms_key
        if logging_configuration is not None:
            self._values["logging_configuration"] = logging_configuration
        if max_webservers is not None:
            self._values["max_webservers"] = max_webservers
        if max_workers is not None:
            self._values["max_workers"] = max_workers
        if min_webservers is not None:
            self._values["min_webservers"] = min_webservers
        if min_workers is not None:
            self._values["min_workers"] = min_workers
        if network_configuration is not None:
            self._values["network_configuration"] = network_configuration
        if plugins_s3_object_version is not None:
            self._values["plugins_s3_object_version"] = plugins_s3_object_version
        if plugins_s3_path is not None:
            self._values["plugins_s3_path"] = plugins_s3_path
        if requirements_s3_object_version is not None:
            self._values["requirements_s3_object_version"] = requirements_s3_object_version
        if requirements_s3_path is not None:
            self._values["requirements_s3_path"] = requirements_s3_path
        if schedulers is not None:
            self._values["schedulers"] = schedulers
        if source_bucket is not None:
            self._values["source_bucket"] = source_bucket
        if startup_script_s3_object_version is not None:
            self._values["startup_script_s3_object_version"] = startup_script_s3_object_version
        if startup_script_s3_path is not None:
            self._values["startup_script_s3_path"] = startup_script_s3_path
        if webserver_access_mode is not None:
            self._values["webserver_access_mode"] = webserver_access_mode
        if weekly_maintenance_window_start is not None:
            self._values["weekly_maintenance_window_start"] = weekly_maintenance_window_start

    @builtins.property
    def airflow_configuration_options(
        self,
    ) -> typing.Mapping[builtins.str, builtins.str]:
        '''A list of key-value pairs containing the Airflow configuration options for your environment.

        For example, core.default_timezone: utc.
        '''
        result = self._values.get("airflow_configuration_options")
        assert result is not None, "Required property 'airflow_configuration_options' is missing"
        return typing.cast(typing.Mapping[builtins.str, builtins.str], result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of your Amazon MWAA environment.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def airflow_version(self) -> typing.Optional["AirflowVersion"]:
        '''The version of Apache Airflow to use for the environment.

        If no value is specified, defaults to the latest version.

        If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        '''
        result = self._values.get("airflow_version")
        return typing.cast(typing.Optional["AirflowVersion"], result)

    @builtins.property
    def dag_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the DAGs folder on your Amazon S3 bucket.

        For example, dags.
        '''
        result = self._values.get("dag_s3_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def endpoint_management(self) -> typing.Optional["EndpointManagement"]:
        '''Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA.

        If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC.
        If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        '''
        result = self._values.get("endpoint_management")
        return typing.cast(typing.Optional["EndpointManagement"], result)

    @builtins.property
    def environment_class(self) -> typing.Optional["EnvironmentClass"]:
        '''The environment class type.'''
        result = self._values.get("environment_class")
        return typing.cast(typing.Optional["EnvironmentClass"], result)

    @builtins.property
    def execution_role(self) -> typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"]:
        '''The execution role in IAM that allows MWAA to access AWS resources in your environment.'''
        result = self._values.get("execution_role")
        return typing.cast(typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"], result)

    @builtins.property
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment.

        You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        '''
        result = self._values.get("kms_key")
        return typing.cast(typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"], result)

    @builtins.property
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''The Apache Airflow logs being sent to CloudWatch Logs.'''
        result = self._values.get("logging_configuration")
        return typing.cast(typing.Optional["LoggingConfiguration"], result)

    @builtins.property
    def max_webservers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network
        calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to
        the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in
        MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        result = self._values.get("max_webservers")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_workers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more
        tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or
        the number you specify in MinWorkers.
        '''
        result = self._values.get("max_workers")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def min_webservers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load,
        decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        result = self._values.get("min_webservers")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def min_workers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you
        specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving
        the worker count you specify in the MinWorkers field. For example, 2.
        '''
        result = self._values.get("min_workers")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def network_configuration(self) -> typing.Optional["NetworkConfiguration"]:
        '''The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.'''
        result = self._values.get("network_configuration")
        return typing.cast(typing.Optional["NetworkConfiguration"], result)

    @builtins.property
    def plugins_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the plugins.zip file on your Amazon S3 bucket.'''
        result = self._values.get("plugins_s3_object_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def plugins_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.'''
        result = self._values.get("plugins_s3_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def requirements_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the requirements.txt file on your Amazon S3 bucket.'''
        result = self._values.get("requirements_s3_object_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def requirements_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.'''
        result = self._values.get("requirements_s3_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def schedulers(self) -> typing.Optional[jsii.Number]:
        '''The number of schedulers that you want to run in your environment.

        Valid values:
        v2 - For environments larger than mw1.micro, accepts values from 2 to 5.
        Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        v1 - Accepts 1.
        '''
        result = self._values.get("schedulers")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def source_bucket(self) -> typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"]:
        '''The Amazon S3 bucket where your DAG code and supporting files are stored.'''
        result = self._values.get("source_bucket")
        return typing.cast(typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"], result)

    @builtins.property
    def startup_script_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the startup shell script in your Amazon S3 bucket.

        You must specify the version ID that Amazon S3 assigns to the file every time you update the script.
        Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long.

        The following is an example:
        3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        '''
        result = self._values.get("startup_script_s3_object_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def startup_script_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the startup shell script in your Amazon S3 bucket.

        For example, s3://mwaa-environment/startup.sh.
        Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process.
        You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        '''
        result = self._values.get("startup_script_s3_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def webserver_access_mode(self) -> typing.Optional["WebserverAccessMode"]:
        '''The Apache Airflow Web server access mode.'''
        result = self._values.get("webserver_access_mode")
        return typing.cast(typing.Optional["WebserverAccessMode"], result)

    @builtins.property
    def weekly_maintenance_window_start(self) -> typing.Optional[builtins.str]:
        '''The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM.

        For example: TUE:03:30. You can specify a start time in 30 minute increments only.

        Supported input includes the following:
        MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        result = self._values.get("weekly_maintenance_window_start")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EnvironmentProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.interface(jsii_type="@robhan-cdk-lib/aws_mwaa.IEnvironment")
class IEnvironment(_aws_cdk_ceddda9d.IResource, typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="airflowConfigurationOptions")
    def airflow_configuration_options(
        self,
    ) -> typing.Mapping[builtins.str, builtins.str]:
        '''A list of key-value pairs containing the Airflow configuration options for your environment.

        For example, core.default_timezone: utc.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="environmentArn")
    def environment_arn(self) -> builtins.str:
        '''The ARN for the Amazon MWAA environment.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''The name of your Amazon MWAA environment.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="airflowVersion")
    def airflow_version(self) -> typing.Optional["AirflowVersion"]:
        '''The version of Apache Airflow to use for the environment.

        If no value is specified, defaults to the latest version.

        If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="celeryExecutorQueue")
    def celery_executor_queue(self) -> typing.Optional[builtins.str]:
        '''The queue ARN for the environment's Celery Executor.

        Amazon MWAA uses a Celery Executor to distribute tasks across multiple workers.
        When you create an environment in a shared VPC, you must provide access to the Celery Executor queue from your VPC.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="dagS3Path")
    def dag_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the DAGs folder on your Amazon S3 bucket.

        For example, dags.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="databaseVpcEndpointService")
    def database_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's Amazon RDS database.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="endpointManagement")
    def endpoint_management(self) -> typing.Optional["EndpointManagement"]:
        '''Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA.

        If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC.
        If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="environmentClass")
    def environment_class(self) -> typing.Optional["EnvironmentClass"]:
        '''The environment class type.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"]:
        '''The execution role in IAM that allows MWAA to access AWS resources in your environment.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment.

        You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfiguration")
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''The Apache Airflow logs being sent to CloudWatch Logs.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationDagProcessingLogsCloudWatchLogGroupArn")
    def logging_configuration_dag_processing_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow DAG processing logs are published.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationSchedulerLogsCloudWatchLogGroupArn")
    def logging_configuration_scheduler_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Scheduler logs are published.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationTaskLogsCloudWatchLogGroupArn")
    def logging_configuration_task_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow task logs are published.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationWebserverLogsCloudWatchLogGroupArn")
    def logging_configuration_webserver_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Web server logs are published.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationWorkerLogsCloudWatchLogGroupArn")
    def logging_configuration_worker_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Worker logs are published.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="maxWebservers")
    def max_webservers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network
        calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to
        the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in
        MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="maxWorkers")
    def max_workers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more
        tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or
        the number you specify in MinWorkers.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="minWebservers")
    def min_webservers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load,
        decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="minWorkers")
    def min_workers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you
        specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving
        the worker count you specify in the MinWorkers field. For example, 2.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="networkConfiguration")
    def network_configuration(self) -> typing.Optional["NetworkConfiguration"]:
        '''The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="pluginsS3ObjectVersion")
    def plugins_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the plugins.zip file on your Amazon S3 bucket.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="pluginsS3Path")
    def plugins_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="requirementsS3ObjectVersion")
    def requirements_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the requirements.txt file on your Amazon S3 bucket.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="requirementsS3Path")
    def requirements_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="schedulers")
    def schedulers(self) -> typing.Optional[jsii.Number]:
        '''The number of schedulers that you want to run in your environment.

        Valid values:
        v2 - For environments larger than mw1.micro, accepts values from 2 to 5.
        Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        v1 - Accepts 1.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="sourceBucket")
    def source_bucket(self) -> typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"]:
        '''The Amazon S3 bucket where your DAG code and supporting files are stored.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="startupScriptS3ObjectVersion")
    def startup_script_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the startup shell script in your Amazon S3 bucket.

        You must specify the version ID that Amazon S3 assigns to the file every time you update the script.
        Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long.

        The following is an example:
        3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="startupScriptS3Path")
    def startup_script_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the startup shell script in your Amazon S3 bucket.

        For example, s3://mwaa-environment/startup.sh.
        Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process.
        You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="webserverAccessMode")
    def webserver_access_mode(self) -> typing.Optional["WebserverAccessMode"]:
        '''The Apache Airflow Web server access mode.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="webserverUrl")
    def webserver_url(self) -> typing.Optional[builtins.str]:
        '''The URL of your Apache Airflow UI.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="webserverVpcEndpointService")
    def webserver_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's web server.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="weeklyMaintenanceWindowStart")
    def weekly_maintenance_window_start(self) -> typing.Optional[builtins.str]:
        '''The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM.

        For example: TUE:03:30. You can specify a start time in 30 minute increments only.

        Supported input includes the following:
        MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        ...


class _IEnvironmentProxy(
    jsii.proxy_for(_aws_cdk_ceddda9d.IResource), # type: ignore[misc]
):
    __jsii_type__: typing.ClassVar[str] = "@robhan-cdk-lib/aws_mwaa.IEnvironment"

    @builtins.property
    @jsii.member(jsii_name="airflowConfigurationOptions")
    def airflow_configuration_options(
        self,
    ) -> typing.Mapping[builtins.str, builtins.str]:
        '''A list of key-value pairs containing the Airflow configuration options for your environment.

        For example, core.default_timezone: utc.
        '''
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "airflowConfigurationOptions"))

    @builtins.property
    @jsii.member(jsii_name="environmentArn")
    def environment_arn(self) -> builtins.str:
        '''The ARN for the Amazon MWAA environment.'''
        return typing.cast(builtins.str, jsii.get(self, "environmentArn"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''The name of your Amazon MWAA environment.'''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="airflowVersion")
    def airflow_version(self) -> typing.Optional["AirflowVersion"]:
        '''The version of Apache Airflow to use for the environment.

        If no value is specified, defaults to the latest version.

        If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        '''
        return typing.cast(typing.Optional["AirflowVersion"], jsii.get(self, "airflowVersion"))

    @builtins.property
    @jsii.member(jsii_name="celeryExecutorQueue")
    def celery_executor_queue(self) -> typing.Optional[builtins.str]:
        '''The queue ARN for the environment's Celery Executor.

        Amazon MWAA uses a Celery Executor to distribute tasks across multiple workers.
        When you create an environment in a shared VPC, you must provide access to the Celery Executor queue from your VPC.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "celeryExecutorQueue"))

    @builtins.property
    @jsii.member(jsii_name="dagS3Path")
    def dag_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the DAGs folder on your Amazon S3 bucket.

        For example, dags.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "dagS3Path"))

    @builtins.property
    @jsii.member(jsii_name="databaseVpcEndpointService")
    def database_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's Amazon RDS database.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "databaseVpcEndpointService"))

    @builtins.property
    @jsii.member(jsii_name="endpointManagement")
    def endpoint_management(self) -> typing.Optional["EndpointManagement"]:
        '''Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA.

        If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC.
        If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        '''
        return typing.cast(typing.Optional["EndpointManagement"], jsii.get(self, "endpointManagement"))

    @builtins.property
    @jsii.member(jsii_name="environmentClass")
    def environment_class(self) -> typing.Optional["EnvironmentClass"]:
        '''The environment class type.'''
        return typing.cast(typing.Optional["EnvironmentClass"], jsii.get(self, "environmentClass"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"]:
        '''The execution role in IAM that allows MWAA to access AWS resources in your environment.'''
        return typing.cast(typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"], jsii.get(self, "executionRole"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment.

        You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        '''
        return typing.cast(typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"], jsii.get(self, "kmsKey"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfiguration")
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''The Apache Airflow logs being sent to CloudWatch Logs.'''
        return typing.cast(typing.Optional["LoggingConfiguration"], jsii.get(self, "loggingConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationDagProcessingLogsCloudWatchLogGroupArn")
    def logging_configuration_dag_processing_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow DAG processing logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationDagProcessingLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationSchedulerLogsCloudWatchLogGroupArn")
    def logging_configuration_scheduler_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Scheduler logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationSchedulerLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationTaskLogsCloudWatchLogGroupArn")
    def logging_configuration_task_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow task logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationTaskLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationWebserverLogsCloudWatchLogGroupArn")
    def logging_configuration_webserver_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Web server logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationWebserverLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationWorkerLogsCloudWatchLogGroupArn")
    def logging_configuration_worker_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Worker logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationWorkerLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="maxWebservers")
    def max_webservers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network
        calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to
        the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in
        MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxWebservers"))

    @builtins.property
    @jsii.member(jsii_name="maxWorkers")
    def max_workers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more
        tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or
        the number you specify in MinWorkers.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxWorkers"))

    @builtins.property
    @jsii.member(jsii_name="minWebservers")
    def min_webservers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load,
        decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "minWebservers"))

    @builtins.property
    @jsii.member(jsii_name="minWorkers")
    def min_workers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you
        specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving
        the worker count you specify in the MinWorkers field. For example, 2.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "minWorkers"))

    @builtins.property
    @jsii.member(jsii_name="networkConfiguration")
    def network_configuration(self) -> typing.Optional["NetworkConfiguration"]:
        '''The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.'''
        return typing.cast(typing.Optional["NetworkConfiguration"], jsii.get(self, "networkConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="pluginsS3ObjectVersion")
    def plugins_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the plugins.zip file on your Amazon S3 bucket.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "pluginsS3ObjectVersion"))

    @builtins.property
    @jsii.member(jsii_name="pluginsS3Path")
    def plugins_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "pluginsS3Path"))

    @builtins.property
    @jsii.member(jsii_name="requirementsS3ObjectVersion")
    def requirements_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the requirements.txt file on your Amazon S3 bucket.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "requirementsS3ObjectVersion"))

    @builtins.property
    @jsii.member(jsii_name="requirementsS3Path")
    def requirements_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "requirementsS3Path"))

    @builtins.property
    @jsii.member(jsii_name="schedulers")
    def schedulers(self) -> typing.Optional[jsii.Number]:
        '''The number of schedulers that you want to run in your environment.

        Valid values:
        v2 - For environments larger than mw1.micro, accepts values from 2 to 5.
        Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        v1 - Accepts 1.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "schedulers"))

    @builtins.property
    @jsii.member(jsii_name="sourceBucket")
    def source_bucket(self) -> typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"]:
        '''The Amazon S3 bucket where your DAG code and supporting files are stored.'''
        return typing.cast(typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"], jsii.get(self, "sourceBucket"))

    @builtins.property
    @jsii.member(jsii_name="startupScriptS3ObjectVersion")
    def startup_script_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the startup shell script in your Amazon S3 bucket.

        You must specify the version ID that Amazon S3 assigns to the file every time you update the script.
        Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long.

        The following is an example:
        3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "startupScriptS3ObjectVersion"))

    @builtins.property
    @jsii.member(jsii_name="startupScriptS3Path")
    def startup_script_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the startup shell script in your Amazon S3 bucket.

        For example, s3://mwaa-environment/startup.sh.
        Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process.
        You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "startupScriptS3Path"))

    @builtins.property
    @jsii.member(jsii_name="webserverAccessMode")
    def webserver_access_mode(self) -> typing.Optional["WebserverAccessMode"]:
        '''The Apache Airflow Web server access mode.'''
        return typing.cast(typing.Optional["WebserverAccessMode"], jsii.get(self, "webserverAccessMode"))

    @builtins.property
    @jsii.member(jsii_name="webserverUrl")
    def webserver_url(self) -> typing.Optional[builtins.str]:
        '''The URL of your Apache Airflow UI.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "webserverUrl"))

    @builtins.property
    @jsii.member(jsii_name="webserverVpcEndpointService")
    def webserver_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's web server.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "webserverVpcEndpointService"))

    @builtins.property
    @jsii.member(jsii_name="weeklyMaintenanceWindowStart")
    def weekly_maintenance_window_start(self) -> typing.Optional[builtins.str]:
        '''The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM.

        For example: TUE:03:30. You can specify a start time in 30 minute increments only.

        Supported input includes the following:
        MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "weeklyMaintenanceWindowStart"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IEnvironment).__jsii_proxy_class__ = lambda : _IEnvironmentProxy


@jsii.enum(jsii_type="@robhan-cdk-lib/aws_mwaa.LogLevel")
class LogLevel(enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_mwaa.LoggingConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "dag_processing_logs": "dagProcessingLogs",
        "scheduler_logs": "schedulerLogs",
        "task_logs": "taskLogs",
        "web_server_logs": "webServerLogs",
        "worker_logs": "workerLogs",
    },
)
class LoggingConfiguration:
    def __init__(
        self,
        *,
        dag_processing_logs: typing.Optional[typing.Union["ModuleLoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        scheduler_logs: typing.Optional[typing.Union["ModuleLoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        task_logs: typing.Optional[typing.Union["ModuleLoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        web_server_logs: typing.Optional[typing.Union["ModuleLoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        worker_logs: typing.Optional[typing.Union["ModuleLoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''The type of Apache Airflow logs to send to CloudWatch Logs.

        :param dag_processing_logs: Defines the processing logs sent to CloudWatch Logs and the logging level to send.
        :param scheduler_logs: Defines the scheduler logs sent to CloudWatch Logs and the logging level to send.
        :param task_logs: Defines the task logs sent to CloudWatch Logs and the logging level to send.
        :param web_server_logs: Defines the web server logs sent to CloudWatch Logs and the logging level to send.
        :param worker_logs: Defines the worker logs sent to CloudWatch Logs and the logging level to send.
        '''
        if isinstance(dag_processing_logs, dict):
            dag_processing_logs = ModuleLoggingConfiguration(**dag_processing_logs)
        if isinstance(scheduler_logs, dict):
            scheduler_logs = ModuleLoggingConfiguration(**scheduler_logs)
        if isinstance(task_logs, dict):
            task_logs = ModuleLoggingConfiguration(**task_logs)
        if isinstance(web_server_logs, dict):
            web_server_logs = ModuleLoggingConfiguration(**web_server_logs)
        if isinstance(worker_logs, dict):
            worker_logs = ModuleLoggingConfiguration(**worker_logs)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__587e90c0429a944bc98095249fe5cd300a90dcf33089932ed503e117deb58614)
            check_type(argname="argument dag_processing_logs", value=dag_processing_logs, expected_type=type_hints["dag_processing_logs"])
            check_type(argname="argument scheduler_logs", value=scheduler_logs, expected_type=type_hints["scheduler_logs"])
            check_type(argname="argument task_logs", value=task_logs, expected_type=type_hints["task_logs"])
            check_type(argname="argument web_server_logs", value=web_server_logs, expected_type=type_hints["web_server_logs"])
            check_type(argname="argument worker_logs", value=worker_logs, expected_type=type_hints["worker_logs"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if dag_processing_logs is not None:
            self._values["dag_processing_logs"] = dag_processing_logs
        if scheduler_logs is not None:
            self._values["scheduler_logs"] = scheduler_logs
        if task_logs is not None:
            self._values["task_logs"] = task_logs
        if web_server_logs is not None:
            self._values["web_server_logs"] = web_server_logs
        if worker_logs is not None:
            self._values["worker_logs"] = worker_logs

    @builtins.property
    def dag_processing_logs(self) -> typing.Optional["ModuleLoggingConfiguration"]:
        '''Defines the processing logs sent to CloudWatch Logs and the logging level to send.'''
        result = self._values.get("dag_processing_logs")
        return typing.cast(typing.Optional["ModuleLoggingConfiguration"], result)

    @builtins.property
    def scheduler_logs(self) -> typing.Optional["ModuleLoggingConfiguration"]:
        '''Defines the scheduler logs sent to CloudWatch Logs and the logging level to send.'''
        result = self._values.get("scheduler_logs")
        return typing.cast(typing.Optional["ModuleLoggingConfiguration"], result)

    @builtins.property
    def task_logs(self) -> typing.Optional["ModuleLoggingConfiguration"]:
        '''Defines the task logs sent to CloudWatch Logs and the logging level to send.'''
        result = self._values.get("task_logs")
        return typing.cast(typing.Optional["ModuleLoggingConfiguration"], result)

    @builtins.property
    def web_server_logs(self) -> typing.Optional["ModuleLoggingConfiguration"]:
        '''Defines the web server logs sent to CloudWatch Logs and the logging level to send.'''
        result = self._values.get("web_server_logs")
        return typing.cast(typing.Optional["ModuleLoggingConfiguration"], result)

    @builtins.property
    def worker_logs(self) -> typing.Optional["ModuleLoggingConfiguration"]:
        '''Defines the worker logs sent to CloudWatch Logs and the logging level to send.'''
        result = self._values.get("worker_logs")
        return typing.cast(typing.Optional["ModuleLoggingConfiguration"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LoggingConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_mwaa.ModuleLoggingConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "cloud_watch_log_group": "cloudWatchLogGroup",
        "enabled": "enabled",
        "log_level": "logLevel",
    },
)
class ModuleLoggingConfiguration:
    def __init__(
        self,
        *,
        cloud_watch_log_group: typing.Optional["_aws_cdk_aws_logs_ceddda9d.ILogGroup"] = None,
        enabled: typing.Optional[builtins.bool] = None,
        log_level: typing.Optional["LogLevel"] = None,
    ) -> None:
        '''Defines the type of logs to send for the Apache Airflow log type (e.g. DagProcessingLogs).

        :param cloud_watch_log_group: The CloudWatch Logs log group for each type ofApache Airflow log type that you have enabled.
        :param enabled: Indicates whether to enable the Apache Airflow log type (e.g. DagProcessingLogs) in CloudWatch Logs.
        :param log_level: Defines the Apache Airflow logs to send for the log type (e.g. DagProcessingLogs) to CloudWatch Logs.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7b6b5c584242899ae7800864118420958302bf2568da5e2d6f5a683e345399aa)
            check_type(argname="argument cloud_watch_log_group", value=cloud_watch_log_group, expected_type=type_hints["cloud_watch_log_group"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument log_level", value=log_level, expected_type=type_hints["log_level"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if cloud_watch_log_group is not None:
            self._values["cloud_watch_log_group"] = cloud_watch_log_group
        if enabled is not None:
            self._values["enabled"] = enabled
        if log_level is not None:
            self._values["log_level"] = log_level

    @builtins.property
    def cloud_watch_log_group(
        self,
    ) -> typing.Optional["_aws_cdk_aws_logs_ceddda9d.ILogGroup"]:
        '''The CloudWatch Logs log group for each type ofApache Airflow log type that you have enabled.'''
        result = self._values.get("cloud_watch_log_group")
        return typing.cast(typing.Optional["_aws_cdk_aws_logs_ceddda9d.ILogGroup"], result)

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        '''Indicates whether to enable the Apache Airflow log type (e.g. DagProcessingLogs) in CloudWatch Logs.'''
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def log_level(self) -> typing.Optional["LogLevel"]:
        '''Defines the Apache Airflow logs to send for the log type (e.g. DagProcessingLogs) to CloudWatch Logs.'''
        result = self._values.get("log_level")
        return typing.cast(typing.Optional["LogLevel"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ModuleLoggingConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@robhan-cdk-lib/aws_mwaa.NetworkConfiguration",
    jsii_struct_bases=[],
    name_mapping={"security_groups": "securityGroups", "subnets": "subnets"},
)
class NetworkConfiguration:
    def __init__(
        self,
        *,
        security_groups: typing.Optional[typing.Sequence["_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup"]] = None,
        subnets: typing.Optional[typing.Sequence["_aws_cdk_aws_ec2_ceddda9d.ISubnet"]] = None,
    ) -> None:
        '''The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.

        :param security_groups: A list of one or more security groups. Accepts up to 5 security groups. A security group must be attached to the same VPC as the subnets.
        :param subnets: A list of subnets. Required to create an environment. Must be private subnets in two different availability zones. A subnet must be attached to the same VPC as the security group.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__66a8db1008fda8f8cf9a9e9d41de07bde3dc8b894d4a91cd243e4e3057ff04ae)
            check_type(argname="argument security_groups", value=security_groups, expected_type=type_hints["security_groups"])
            check_type(argname="argument subnets", value=subnets, expected_type=type_hints["subnets"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if security_groups is not None:
            self._values["security_groups"] = security_groups
        if subnets is not None:
            self._values["subnets"] = subnets

    @builtins.property
    def security_groups(
        self,
    ) -> typing.Optional[typing.List["_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup"]]:
        '''A list of one or more security groups.

        Accepts up to 5 security groups. A security group must be attached to the same VPC as the subnets.
        '''
        result = self._values.get("security_groups")
        return typing.cast(typing.Optional[typing.List["_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup"]], result)

    @builtins.property
    def subnets(
        self,
    ) -> typing.Optional[typing.List["_aws_cdk_aws_ec2_ceddda9d.ISubnet"]]:
        '''A list of subnets.

        Required to create an environment. Must be private subnets in two different availability zones.
        A subnet must be attached to the same VPC as the security group.
        '''
        result = self._values.get("subnets")
        return typing.cast(typing.Optional[typing.List["_aws_cdk_aws_ec2_ceddda9d.ISubnet"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(jsii_type="@robhan-cdk-lib/aws_mwaa.WebserverAccessMode")
class WebserverAccessMode(enum.Enum):
    PRIVATE_ONLY = "PRIVATE_ONLY"
    PUBLIC_ONLY = "PUBLIC_ONLY"


@jsii.enum(jsii_type="@robhan-cdk-lib/aws_mwaa.WorkerReplacementStrategy")
class WorkerReplacementStrategy(enum.Enum):
    FORCED = "FORCED"
    GRACEFUL = "GRACEFUL"


@jsii.implements(IEnvironment)
class EnvironmentBase(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@robhan-cdk-lib/aws_mwaa.EnvironmentBase",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        account: typing.Optional[builtins.str] = None,
        environment_from_arn: typing.Optional[builtins.str] = None,
        physical_name: typing.Optional[builtins.str] = None,
        region: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param account: The AWS account ID this resource belongs to. Default: - the resource is in the same account as the stack it belongs to
        :param environment_from_arn: ARN to deduce region and account from. The ARN is parsed and the account and region are taken from the ARN. This should be used for imported resources. Cannot be supplied together with either ``account`` or ``region``. Default: - take environment from ``account``, ``region`` parameters, or use Stack environment.
        :param physical_name: The value passed in by users to the physical name prop of the resource. - ``undefined`` implies that a physical name will be allocated by CloudFormation during deployment. - a concrete value implies a specific physical name - ``PhysicalName.GENERATE_IF_NEEDED`` is a marker that indicates that a physical will only be generated by the CDK if it is needed for cross-environment references. Otherwise, it will be allocated by CloudFormation. Default: - The physical name will be allocated by CloudFormation at deployment time
        :param region: The AWS region this resource belongs to. Default: - the resource is in the same region as the stack it belongs to
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ad5873da45b6688f4c218055f06ff0d6a531da884f4fbcf05c463ed354d7521f)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = _aws_cdk_ceddda9d.ResourceProps(
            account=account,
            environment_from_arn=environment_from_arn,
            physical_name=physical_name,
            region=region,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="airflowConfigurationOptions")
    @abc.abstractmethod
    def airflow_configuration_options(
        self,
    ) -> typing.Mapping[builtins.str, builtins.str]:
        '''A list of key-value pairs containing the Airflow configuration options for your environment.

        For example, core.default_timezone: utc.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="environmentArn")
    @abc.abstractmethod
    def environment_arn(self) -> builtins.str:
        '''The ARN for the Amazon MWAA environment.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="name")
    @abc.abstractmethod
    def name(self) -> builtins.str:
        '''The name of your Amazon MWAA environment.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="airflowVersion")
    @abc.abstractmethod
    def airflow_version(self) -> typing.Optional["AirflowVersion"]:
        '''The version of Apache Airflow to use for the environment.

        If no value is specified, defaults to the latest version.

        If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="celeryExecutorQueue")
    @abc.abstractmethod
    def celery_executor_queue(self) -> typing.Optional[builtins.str]:
        '''The queue ARN for the environment's Celery Executor.

        Amazon MWAA uses a Celery Executor to distribute tasks across multiple workers.
        When you create an environment in a shared VPC, you must provide access to the Celery Executor queue from your VPC.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="dagS3Path")
    @abc.abstractmethod
    def dag_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the DAGs folder on your Amazon S3 bucket.

        For example, dags.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="databaseVpcEndpointService")
    @abc.abstractmethod
    def database_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's Amazon RDS database.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="endpointManagement")
    @abc.abstractmethod
    def endpoint_management(self) -> typing.Optional["EndpointManagement"]:
        '''Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA.

        If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC.
        If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="environmentClass")
    @abc.abstractmethod
    def environment_class(self) -> typing.Optional["EnvironmentClass"]:
        '''The environment class type.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    @abc.abstractmethod
    def execution_role(self) -> typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"]:
        '''The execution role in IAM that allows MWAA to access AWS resources in your environment.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    @abc.abstractmethod
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment.

        You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfiguration")
    @abc.abstractmethod
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''The Apache Airflow logs being sent to CloudWatch Logs.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationDagProcessingLogsCloudWatchLogGroupArn")
    @abc.abstractmethod
    def logging_configuration_dag_processing_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow DAG processing logs are published.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationSchedulerLogsCloudWatchLogGroupArn")
    @abc.abstractmethod
    def logging_configuration_scheduler_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Scheduler logs are published.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationTaskLogsCloudWatchLogGroupArn")
    @abc.abstractmethod
    def logging_configuration_task_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow task logs are published.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationWebserverLogsCloudWatchLogGroupArn")
    @abc.abstractmethod
    def logging_configuration_webserver_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Web server logs are published.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationWorkerLogsCloudWatchLogGroupArn")
    @abc.abstractmethod
    def logging_configuration_worker_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Worker logs are published.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="maxWebservers")
    @abc.abstractmethod
    def max_webservers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network
        calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to
        the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in
        MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="maxWorkers")
    @abc.abstractmethod
    def max_workers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more
        tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or
        the number you specify in MinWorkers.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="minWebservers")
    @abc.abstractmethod
    def min_webservers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load,
        decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="minWorkers")
    @abc.abstractmethod
    def min_workers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you
        specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving
        the worker count you specify in the MinWorkers field. For example, 2.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="networkConfiguration")
    @abc.abstractmethod
    def network_configuration(self) -> typing.Optional["NetworkConfiguration"]:
        '''The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="pluginsS3ObjectVersion")
    @abc.abstractmethod
    def plugins_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the plugins.zip file on your Amazon S3 bucket.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="pluginsS3Path")
    @abc.abstractmethod
    def plugins_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="requirementsS3ObjectVersion")
    @abc.abstractmethod
    def requirements_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the requirements.txt file on your Amazon S3 bucket.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="requirementsS3Path")
    @abc.abstractmethod
    def requirements_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="schedulers")
    @abc.abstractmethod
    def schedulers(self) -> typing.Optional[jsii.Number]:
        '''The number of schedulers that you want to run in your environment.

        Valid values:
        v2 - For environments larger than mw1.micro, accepts values from 2 to 5.
        Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        v1 - Accepts 1.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="sourceBucket")
    @abc.abstractmethod
    def source_bucket(self) -> typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"]:
        '''The Amazon S3 bucket where your DAG code and supporting files are stored.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="startupScriptS3ObjectVersion")
    @abc.abstractmethod
    def startup_script_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the startup shell script in your Amazon S3 bucket.

        You must specify the version ID that Amazon S3 assigns to the file every time you update the script.
        Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long.

        The following is an example:
        3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="startupScriptS3Path")
    @abc.abstractmethod
    def startup_script_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the startup shell script in your Amazon S3 bucket.

        For example, s3://mwaa-environment/startup.sh.
        Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process.
        You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        '''
        ...

    @builtins.property
    @jsii.member(jsii_name="webserverAccessMode")
    @abc.abstractmethod
    def webserver_access_mode(self) -> typing.Optional["WebserverAccessMode"]:
        '''The Apache Airflow Web server access mode.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="webserverUrl")
    @abc.abstractmethod
    def webserver_url(self) -> typing.Optional[builtins.str]:
        '''The URL of your Apache Airflow UI.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="webserverVpcEndpointService")
    @abc.abstractmethod
    def webserver_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's web server.'''
        ...

    @builtins.property
    @jsii.member(jsii_name="weeklyMaintenanceWindowStart")
    @abc.abstractmethod
    def weekly_maintenance_window_start(self) -> typing.Optional[builtins.str]:
        '''The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM.

        For example: TUE:03:30. You can specify a start time in 30 minute increments only.

        Supported input includes the following:
        MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        ...


class _EnvironmentBaseProxy(
    EnvironmentBase,
    jsii.proxy_for(_aws_cdk_ceddda9d.Resource), # type: ignore[misc]
):
    @builtins.property
    @jsii.member(jsii_name="airflowConfigurationOptions")
    def airflow_configuration_options(
        self,
    ) -> typing.Mapping[builtins.str, builtins.str]:
        '''A list of key-value pairs containing the Airflow configuration options for your environment.

        For example, core.default_timezone: utc.
        '''
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "airflowConfigurationOptions"))

    @builtins.property
    @jsii.member(jsii_name="environmentArn")
    def environment_arn(self) -> builtins.str:
        '''The ARN for the Amazon MWAA environment.'''
        return typing.cast(builtins.str, jsii.get(self, "environmentArn"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''The name of your Amazon MWAA environment.'''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="airflowVersion")
    def airflow_version(self) -> typing.Optional["AirflowVersion"]:
        '''The version of Apache Airflow to use for the environment.

        If no value is specified, defaults to the latest version.

        If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        '''
        return typing.cast(typing.Optional["AirflowVersion"], jsii.get(self, "airflowVersion"))

    @builtins.property
    @jsii.member(jsii_name="celeryExecutorQueue")
    def celery_executor_queue(self) -> typing.Optional[builtins.str]:
        '''The queue ARN for the environment's Celery Executor.

        Amazon MWAA uses a Celery Executor to distribute tasks across multiple workers.
        When you create an environment in a shared VPC, you must provide access to the Celery Executor queue from your VPC.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "celeryExecutorQueue"))

    @builtins.property
    @jsii.member(jsii_name="dagS3Path")
    def dag_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the DAGs folder on your Amazon S3 bucket.

        For example, dags.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "dagS3Path"))

    @builtins.property
    @jsii.member(jsii_name="databaseVpcEndpointService")
    def database_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's Amazon RDS database.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "databaseVpcEndpointService"))

    @builtins.property
    @jsii.member(jsii_name="endpointManagement")
    def endpoint_management(self) -> typing.Optional["EndpointManagement"]:
        '''Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA.

        If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC.
        If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        '''
        return typing.cast(typing.Optional["EndpointManagement"], jsii.get(self, "endpointManagement"))

    @builtins.property
    @jsii.member(jsii_name="environmentClass")
    def environment_class(self) -> typing.Optional["EnvironmentClass"]:
        '''The environment class type.'''
        return typing.cast(typing.Optional["EnvironmentClass"], jsii.get(self, "environmentClass"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"]:
        '''The execution role in IAM that allows MWAA to access AWS resources in your environment.'''
        return typing.cast(typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"], jsii.get(self, "executionRole"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment.

        You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        '''
        return typing.cast(typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"], jsii.get(self, "kmsKey"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfiguration")
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''The Apache Airflow logs being sent to CloudWatch Logs.'''
        return typing.cast(typing.Optional["LoggingConfiguration"], jsii.get(self, "loggingConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationDagProcessingLogsCloudWatchLogGroupArn")
    def logging_configuration_dag_processing_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow DAG processing logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationDagProcessingLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationSchedulerLogsCloudWatchLogGroupArn")
    def logging_configuration_scheduler_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Scheduler logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationSchedulerLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationTaskLogsCloudWatchLogGroupArn")
    def logging_configuration_task_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow task logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationTaskLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationWebserverLogsCloudWatchLogGroupArn")
    def logging_configuration_webserver_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Web server logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationWebserverLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationWorkerLogsCloudWatchLogGroupArn")
    def logging_configuration_worker_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Worker logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationWorkerLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="maxWebservers")
    def max_webservers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network
        calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to
        the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in
        MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxWebservers"))

    @builtins.property
    @jsii.member(jsii_name="maxWorkers")
    def max_workers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more
        tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or
        the number you specify in MinWorkers.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxWorkers"))

    @builtins.property
    @jsii.member(jsii_name="minWebservers")
    def min_webservers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load,
        decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "minWebservers"))

    @builtins.property
    @jsii.member(jsii_name="minWorkers")
    def min_workers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you
        specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving
        the worker count you specify in the MinWorkers field. For example, 2.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "minWorkers"))

    @builtins.property
    @jsii.member(jsii_name="networkConfiguration")
    def network_configuration(self) -> typing.Optional["NetworkConfiguration"]:
        '''The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.'''
        return typing.cast(typing.Optional["NetworkConfiguration"], jsii.get(self, "networkConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="pluginsS3ObjectVersion")
    def plugins_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the plugins.zip file on your Amazon S3 bucket.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "pluginsS3ObjectVersion"))

    @builtins.property
    @jsii.member(jsii_name="pluginsS3Path")
    def plugins_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "pluginsS3Path"))

    @builtins.property
    @jsii.member(jsii_name="requirementsS3ObjectVersion")
    def requirements_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the requirements.txt file on your Amazon S3 bucket.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "requirementsS3ObjectVersion"))

    @builtins.property
    @jsii.member(jsii_name="requirementsS3Path")
    def requirements_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "requirementsS3Path"))

    @builtins.property
    @jsii.member(jsii_name="schedulers")
    def schedulers(self) -> typing.Optional[jsii.Number]:
        '''The number of schedulers that you want to run in your environment.

        Valid values:
        v2 - For environments larger than mw1.micro, accepts values from 2 to 5.
        Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        v1 - Accepts 1.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "schedulers"))

    @builtins.property
    @jsii.member(jsii_name="sourceBucket")
    def source_bucket(self) -> typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"]:
        '''The Amazon S3 bucket where your DAG code and supporting files are stored.'''
        return typing.cast(typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"], jsii.get(self, "sourceBucket"))

    @builtins.property
    @jsii.member(jsii_name="startupScriptS3ObjectVersion")
    def startup_script_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the startup shell script in your Amazon S3 bucket.

        You must specify the version ID that Amazon S3 assigns to the file every time you update the script.
        Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long.

        The following is an example:
        3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "startupScriptS3ObjectVersion"))

    @builtins.property
    @jsii.member(jsii_name="startupScriptS3Path")
    def startup_script_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the startup shell script in your Amazon S3 bucket.

        For example, s3://mwaa-environment/startup.sh.
        Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process.
        You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "startupScriptS3Path"))

    @builtins.property
    @jsii.member(jsii_name="webserverAccessMode")
    def webserver_access_mode(self) -> typing.Optional["WebserverAccessMode"]:
        '''The Apache Airflow Web server access mode.'''
        return typing.cast(typing.Optional["WebserverAccessMode"], jsii.get(self, "webserverAccessMode"))

    @builtins.property
    @jsii.member(jsii_name="webserverUrl")
    def webserver_url(self) -> typing.Optional[builtins.str]:
        '''The URL of your Apache Airflow UI.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "webserverUrl"))

    @builtins.property
    @jsii.member(jsii_name="webserverVpcEndpointService")
    def webserver_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's web server.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "webserverVpcEndpointService"))

    @builtins.property
    @jsii.member(jsii_name="weeklyMaintenanceWindowStart")
    def weekly_maintenance_window_start(self) -> typing.Optional[builtins.str]:
        '''The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM.

        For example: TUE:03:30. You can specify a start time in 30 minute increments only.

        Supported input includes the following:
        MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "weeklyMaintenanceWindowStart"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, EnvironmentBase).__jsii_proxy_class__ = lambda : _EnvironmentBaseProxy


class Environment(
    EnvironmentBase,
    metaclass=jsii.JSIIMeta,
    jsii_type="@robhan-cdk-lib/aws_mwaa.Environment",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        airflow_configuration_options: typing.Mapping[builtins.str, builtins.str],
        name: builtins.str,
        airflow_version: typing.Optional["AirflowVersion"] = None,
        dag_s3_path: typing.Optional[builtins.str] = None,
        endpoint_management: typing.Optional["EndpointManagement"] = None,
        environment_class: typing.Optional["EnvironmentClass"] = None,
        execution_role: typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"] = None,
        kms_key: typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"] = None,
        logging_configuration: typing.Optional[typing.Union["LoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        max_webservers: typing.Optional[jsii.Number] = None,
        max_workers: typing.Optional[jsii.Number] = None,
        min_webservers: typing.Optional[jsii.Number] = None,
        min_workers: typing.Optional[jsii.Number] = None,
        network_configuration: typing.Optional[typing.Union["NetworkConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        plugins_s3_object_version: typing.Optional[builtins.str] = None,
        plugins_s3_path: typing.Optional[builtins.str] = None,
        requirements_s3_object_version: typing.Optional[builtins.str] = None,
        requirements_s3_path: typing.Optional[builtins.str] = None,
        schedulers: typing.Optional[jsii.Number] = None,
        source_bucket: typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"] = None,
        startup_script_s3_object_version: typing.Optional[builtins.str] = None,
        startup_script_s3_path: typing.Optional[builtins.str] = None,
        webserver_access_mode: typing.Optional["WebserverAccessMode"] = None,
        weekly_maintenance_window_start: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param airflow_configuration_options: A list of key-value pairs containing the Airflow configuration options for your environment. For example, core.default_timezone: utc.
        :param name: The name of your Amazon MWAA environment.
        :param airflow_version: The version of Apache Airflow to use for the environment. If no value is specified, defaults to the latest version. If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        :param dag_s3_path: The relative path to the DAGs folder on your Amazon S3 bucket. For example, dags.
        :param endpoint_management: Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA. If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC. If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        :param environment_class: The environment class type.
        :param execution_role: The execution role in IAM that allows MWAA to access AWS resources in your environment.
        :param kms_key: The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment. You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        :param logging_configuration: The Apache Airflow logs being sent to CloudWatch Logs.
        :param max_webservers: The maximum number of web servers that you want to run in your environment. Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers. Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        :param max_workers: The maximum number of workers that you want to run in your environment. MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or the number you specify in MinWorkers.
        :param min_webservers: The minimum number of web servers that you want to run in your environment. Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load, decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers. Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        :param min_workers: The minimum number of workers that you want to run in your environment. MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the worker count you specify in the MinWorkers field. For example, 2.
        :param network_configuration: The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.
        :param plugins_s3_object_version: The version of the plugins.zip file on your Amazon S3 bucket.
        :param plugins_s3_path: The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.
        :param requirements_s3_object_version: The version of the requirements.txt file on your Amazon S3 bucket.
        :param requirements_s3_path: The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.
        :param schedulers: The number of schedulers that you want to run in your environment. Valid values: v2 - For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1. v1 - Accepts 1.
        :param source_bucket: The Amazon S3 bucket where your DAG code and supporting files are stored.
        :param startup_script_s3_object_version: The version of the startup shell script in your Amazon S3 bucket. You must specify the version ID that Amazon S3 assigns to the file every time you update the script. Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long. The following is an example: 3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        :param startup_script_s3_path: The relative path to the startup shell script in your Amazon S3 bucket. For example, s3://mwaa-environment/startup.sh. Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process. You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        :param webserver_access_mode: The Apache Airflow Web server access mode.
        :param weekly_maintenance_window_start: The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM. For example: TUE:03:30. You can specify a start time in 30 minute increments only. Supported input includes the following: MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5caedcd0e4f79944eef6be911818e685afe29161ed637d59813b0c34497c9a53)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = EnvironmentProps(
            airflow_configuration_options=airflow_configuration_options,
            name=name,
            airflow_version=airflow_version,
            dag_s3_path=dag_s3_path,
            endpoint_management=endpoint_management,
            environment_class=environment_class,
            execution_role=execution_role,
            kms_key=kms_key,
            logging_configuration=logging_configuration,
            max_webservers=max_webservers,
            max_workers=max_workers,
            min_webservers=min_webservers,
            min_workers=min_workers,
            network_configuration=network_configuration,
            plugins_s3_object_version=plugins_s3_object_version,
            plugins_s3_path=plugins_s3_path,
            requirements_s3_object_version=requirements_s3_object_version,
            requirements_s3_path=requirements_s3_path,
            schedulers=schedulers,
            source_bucket=source_bucket,
            startup_script_s3_object_version=startup_script_s3_object_version,
            startup_script_s3_path=startup_script_s3_path,
            webserver_access_mode=webserver_access_mode,
            weekly_maintenance_window_start=weekly_maintenance_window_start,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromEnvironmentAttributes")
    @builtins.classmethod
    def from_environment_attributes(
        cls,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        airflow_configuration_options: typing.Mapping[builtins.str, builtins.str],
        environment_arn: builtins.str,
        name: builtins.str,
        airflow_version: typing.Optional["AirflowVersion"] = None,
        celery_executor_queue: typing.Optional[builtins.str] = None,
        dag_s3_path: typing.Optional[builtins.str] = None,
        database_vpc_endpoint_service: typing.Optional[builtins.str] = None,
        endpoint_management: typing.Optional["EndpointManagement"] = None,
        environment_class: typing.Optional["EnvironmentClass"] = None,
        execution_role: typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"] = None,
        kms_key: typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"] = None,
        logging_configuration: typing.Optional[typing.Union["LoggingConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        logging_configuration_dag_processing_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
        logging_configuration_scheduler_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
        logging_configuration_task_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
        logging_configuration_webserver_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
        logging_configuration_worker_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
        max_webservers: typing.Optional[jsii.Number] = None,
        max_workers: typing.Optional[jsii.Number] = None,
        min_webservers: typing.Optional[jsii.Number] = None,
        min_workers: typing.Optional[jsii.Number] = None,
        network_configuration: typing.Optional[typing.Union["NetworkConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        plugins_s3_object_version: typing.Optional[builtins.str] = None,
        plugins_s3_path: typing.Optional[builtins.str] = None,
        requirements_s3_object_version: typing.Optional[builtins.str] = None,
        requirements_s3_path: typing.Optional[builtins.str] = None,
        schedulers: typing.Optional[jsii.Number] = None,
        source_bucket: typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"] = None,
        startup_script_s3_object_version: typing.Optional[builtins.str] = None,
        startup_script_s3_path: typing.Optional[builtins.str] = None,
        webserver_access_mode: typing.Optional["WebserverAccessMode"] = None,
        webserver_url: typing.Optional[builtins.str] = None,
        webserver_vpc_endpoint_service: typing.Optional[builtins.str] = None,
        weekly_maintenance_window_start: typing.Optional[builtins.str] = None,
    ) -> "IEnvironment":
        '''
        :param scope: -
        :param id: -
        :param airflow_configuration_options: A list of key-value pairs containing the Airflow configuration options for your environment. For example, core.default_timezone: utc.
        :param environment_arn: The ARN for the Amazon MWAA environment.
        :param name: The name of your Amazon MWAA environment.
        :param airflow_version: The version of Apache Airflow to use for the environment. If no value is specified, defaults to the latest version. If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        :param celery_executor_queue: The queue ARN for the environment's Celery Executor. Amazon MWAA uses a Celery Executor to distribute tasks across multiple workers. When you create an environment in a shared VPC, you must provide access to the Celery Executor queue from your VPC.
        :param dag_s3_path: The relative path to the DAGs folder on your Amazon S3 bucket. For example, dags.
        :param database_vpc_endpoint_service: The VPC endpoint for the environment's Amazon RDS database.
        :param endpoint_management: Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA. If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC. If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        :param environment_class: The environment class type.
        :param execution_role: The execution role in IAM that allows MWAA to access AWS resources in your environment.
        :param kms_key: The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment. You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        :param logging_configuration: The Apache Airflow logs being sent to CloudWatch Logs.
        :param logging_configuration_dag_processing_logs_cloud_watch_log_group_arn: The ARN for the CloudWatch Logs group where the Apache Airflow DAG processing logs are published.
        :param logging_configuration_scheduler_logs_cloud_watch_log_group_arn: The ARN for the CloudWatch Logs group where the Apache Airflow Scheduler logs are published.
        :param logging_configuration_task_logs_cloud_watch_log_group_arn: The ARN for the CloudWatch Logs group where the Apache Airflow task logs are published.
        :param logging_configuration_webserver_logs_cloud_watch_log_group_arn: The ARN for the CloudWatch Logs group where the Apache Airflow Web server logs are published.
        :param logging_configuration_worker_logs_cloud_watch_log_group_arn: The ARN for the CloudWatch Logs group where the Apache Airflow Worker logs are published.
        :param max_webservers: The maximum number of web servers that you want to run in your environment. Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers. Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        :param max_workers: The maximum number of workers that you want to run in your environment. MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or the number you specify in MinWorkers.
        :param min_webservers: The minimum number of web servers that you want to run in your environment. Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load, decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers. Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        :param min_workers: The minimum number of workers that you want to run in your environment. MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the worker count you specify in the MinWorkers field. For example, 2.
        :param network_configuration: The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.
        :param plugins_s3_object_version: The version of the plugins.zip file on your Amazon S3 bucket.
        :param plugins_s3_path: The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.
        :param requirements_s3_object_version: The version of the requirements.txt file on your Amazon S3 bucket.
        :param requirements_s3_path: The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.
        :param schedulers: The number of schedulers that you want to run in your environment. Valid values: v2 - For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1. v1 - Accepts 1.
        :param source_bucket: The Amazon S3 bucket where your DAG code and supporting files are stored.
        :param startup_script_s3_object_version: The version of the startup shell script in your Amazon S3 bucket. You must specify the version ID that Amazon S3 assigns to the file every time you update the script. Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long. The following is an example: 3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        :param startup_script_s3_path: The relative path to the startup shell script in your Amazon S3 bucket. For example, s3://mwaa-environment/startup.sh. Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process. You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        :param webserver_access_mode: The Apache Airflow Web server access mode.
        :param webserver_url: The URL of your Apache Airflow UI.
        :param webserver_vpc_endpoint_service: The VPC endpoint for the environment's web server.
        :param weekly_maintenance_window_start: The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM. For example: TUE:03:30. You can specify a start time in 30 minute increments only. Supported input includes the following: MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__95cc4f4257f86486302fcb2e763d242a3040b6f4ce19c4cd9698055844e13d0c)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = EnvironmentAttributes(
            airflow_configuration_options=airflow_configuration_options,
            environment_arn=environment_arn,
            name=name,
            airflow_version=airflow_version,
            celery_executor_queue=celery_executor_queue,
            dag_s3_path=dag_s3_path,
            database_vpc_endpoint_service=database_vpc_endpoint_service,
            endpoint_management=endpoint_management,
            environment_class=environment_class,
            execution_role=execution_role,
            kms_key=kms_key,
            logging_configuration=logging_configuration,
            logging_configuration_dag_processing_logs_cloud_watch_log_group_arn=logging_configuration_dag_processing_logs_cloud_watch_log_group_arn,
            logging_configuration_scheduler_logs_cloud_watch_log_group_arn=logging_configuration_scheduler_logs_cloud_watch_log_group_arn,
            logging_configuration_task_logs_cloud_watch_log_group_arn=logging_configuration_task_logs_cloud_watch_log_group_arn,
            logging_configuration_webserver_logs_cloud_watch_log_group_arn=logging_configuration_webserver_logs_cloud_watch_log_group_arn,
            logging_configuration_worker_logs_cloud_watch_log_group_arn=logging_configuration_worker_logs_cloud_watch_log_group_arn,
            max_webservers=max_webservers,
            max_workers=max_workers,
            min_webservers=min_webservers,
            min_workers=min_workers,
            network_configuration=network_configuration,
            plugins_s3_object_version=plugins_s3_object_version,
            plugins_s3_path=plugins_s3_path,
            requirements_s3_object_version=requirements_s3_object_version,
            requirements_s3_path=requirements_s3_path,
            schedulers=schedulers,
            source_bucket=source_bucket,
            startup_script_s3_object_version=startup_script_s3_object_version,
            startup_script_s3_path=startup_script_s3_path,
            webserver_access_mode=webserver_access_mode,
            webserver_url=webserver_url,
            webserver_vpc_endpoint_service=webserver_vpc_endpoint_service,
            weekly_maintenance_window_start=weekly_maintenance_window_start,
        )

        return typing.cast("IEnvironment", jsii.sinvoke(cls, "fromEnvironmentAttributes", [scope, id, attrs]))

    @jsii.member(jsii_name="isEnvironment")
    @builtins.classmethod
    def is_environment(cls, x: typing.Any) -> builtins.bool:
        '''
        :param x: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7959ab616fb8602cff9e37f75ee4b0f7b75f4963daad74b8e571e648d8ece8a5)
            check_type(argname="argument x", value=x, expected_type=type_hints["x"])
        return typing.cast(builtins.bool, jsii.sinvoke(cls, "isEnvironment", [x]))

    @builtins.property
    @jsii.member(jsii_name="airflowConfigurationOptions")
    def airflow_configuration_options(
        self,
    ) -> typing.Mapping[builtins.str, builtins.str]:
        '''A list of key-value pairs containing the Airflow configuration options for your environment.

        For example, core.default_timezone: utc.
        '''
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "airflowConfigurationOptions"))

    @builtins.property
    @jsii.member(jsii_name="environmentArn")
    def environment_arn(self) -> builtins.str:
        '''The ARN for the Amazon MWAA environment.'''
        return typing.cast(builtins.str, jsii.get(self, "environmentArn"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''The name of your Amazon MWAA environment.'''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="airflowVersion")
    def airflow_version(self) -> typing.Optional["AirflowVersion"]:
        '''The version of Apache Airflow to use for the environment.

        If no value is specified, defaults to the latest version.

        If you specify a newer version number for an existing environment, the version update requires some service interruption before taking effect.
        '''
        return typing.cast(typing.Optional["AirflowVersion"], jsii.get(self, "airflowVersion"))

    @builtins.property
    @jsii.member(jsii_name="celeryExecutorQueue")
    def celery_executor_queue(self) -> typing.Optional[builtins.str]:
        '''The queue ARN for the environment's Celery Executor.

        Amazon MWAA uses a Celery Executor to distribute tasks across multiple workers.
        When you create an environment in a shared VPC, you must provide access to the Celery Executor queue from your VPC.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "celeryExecutorQueue"))

    @builtins.property
    @jsii.member(jsii_name="dagS3Path")
    def dag_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the DAGs folder on your Amazon S3 bucket.

        For example, dags.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "dagS3Path"))

    @builtins.property
    @jsii.member(jsii_name="databaseVpcEndpointService")
    def database_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's Amazon RDS database.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "databaseVpcEndpointService"))

    @builtins.property
    @jsii.member(jsii_name="endpointManagement")
    def endpoint_management(self) -> typing.Optional["EndpointManagement"]:
        '''Defines whether the VPC endpoints configured for the environment are created, and managed, by the customer or by Amazon MWAA.

        If set to SERVICE, Amazon MWAA will create and manage the required VPC endpoints in your VPC.
        If set to CUSTOMER, you must create, and manage, the VPC endpoints in your VPC.
        '''
        return typing.cast(typing.Optional["EndpointManagement"], jsii.get(self, "endpointManagement"))

    @builtins.property
    @jsii.member(jsii_name="environmentClass")
    def environment_class(self) -> typing.Optional["EnvironmentClass"]:
        '''The environment class type.'''
        return typing.cast(typing.Optional["EnvironmentClass"], jsii.get(self, "environmentClass"))

    @builtins.property
    @jsii.member(jsii_name="executionRole")
    def execution_role(self) -> typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"]:
        '''The execution role in IAM that allows MWAA to access AWS resources in your environment.'''
        return typing.cast(typing.Optional["_aws_cdk_aws_iam_ceddda9d.IRole"], jsii.get(self, "executionRole"))

    @builtins.property
    @jsii.member(jsii_name="kmsKey")
    def kms_key(self) -> typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"]:
        '''The AWS Key Management Service (KMS) key to encrypt and decrypt the data in your environment.

        You can use an AWS KMS key managed by MWAA, or a customer-managed KMS key (advanced).
        '''
        return typing.cast(typing.Optional["_aws_cdk_aws_kms_ceddda9d.IKey"], jsii.get(self, "kmsKey"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfiguration")
    def logging_configuration(self) -> typing.Optional["LoggingConfiguration"]:
        '''The Apache Airflow logs being sent to CloudWatch Logs.'''
        return typing.cast(typing.Optional["LoggingConfiguration"], jsii.get(self, "loggingConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationDagProcessingLogsCloudWatchLogGroupArn")
    def logging_configuration_dag_processing_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow DAG processing logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationDagProcessingLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationSchedulerLogsCloudWatchLogGroupArn")
    def logging_configuration_scheduler_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Scheduler logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationSchedulerLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationTaskLogsCloudWatchLogGroupArn")
    def logging_configuration_task_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow task logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationTaskLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationWebserverLogsCloudWatchLogGroupArn")
    def logging_configuration_webserver_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Web server logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationWebserverLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="loggingConfigurationWorkerLogsCloudWatchLogGroupArn")
    def logging_configuration_worker_logs_cloud_watch_log_group_arn(
        self,
    ) -> typing.Optional[builtins.str]:
        '''The ARN for the CloudWatch Logs group where the Apache Airflow Worker logs are published.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "loggingConfigurationWorkerLogsCloudWatchLogGroupArn"))

    @builtins.property
    @jsii.member(jsii_name="maxWebservers")
    def max_webservers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. For example, in scenarios where your workload requires network
        calls to the Apache Airflow REST API with a high transaction-per-second (TPS) rate, Amazon MWAA will increase the number of web servers up to
        the number set in MaxWebserers. As TPS rates decrease Amazon MWAA disposes of the additional web servers, and scales down to the number set in
        MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxWebservers"))

    @builtins.property
    @jsii.member(jsii_name="maxWorkers")
    def max_workers(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you specify in the MaxWorkers field. For example, 20. When there are no more
        tasks running, and no more in the queue, MWAA disposes of the extra workers leaving the one worker that is included with your environment, or
        the number you specify in MinWorkers.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxWorkers"))

    @builtins.property
    @jsii.member(jsii_name="minWebservers")
    def min_webservers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of web servers that you want to run in your environment.

        Amazon MWAA scales the number of Apache Airflow web servers up to the number you specify for MaxWebservers when you interact with your Apache
        Airflow environment using Apache Airflow REST API, or the Apache Airflow CLI. As the transaction-per-second rate, and the network load,
        decrease, Amazon MWAA disposes of the additional web servers, and scales down to the number set in MinxWebserers.

        Valid values: For environments larger than mw1.micro, accepts values from 2 to 5. Defaults to 2 for all environment sizes except mw1.micro,
        which defaults to 1.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "minWebservers"))

    @builtins.property
    @jsii.member(jsii_name="minWorkers")
    def min_workers(self) -> typing.Optional[jsii.Number]:
        '''The minimum number of workers that you want to run in your environment.

        MWAA scales the number of Apache Airflow workers up to the number you
        specify in the MaxWorkers field. When there are no more tasks running, and no more in the queue, MWAA disposes of the extra workers leaving
        the worker count you specify in the MinWorkers field. For example, 2.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "minWorkers"))

    @builtins.property
    @jsii.member(jsii_name="networkConfiguration")
    def network_configuration(self) -> typing.Optional["NetworkConfiguration"]:
        '''The VPC networking components used to secure and enable network traffic between the AWS resources for your environment.'''
        return typing.cast(typing.Optional["NetworkConfiguration"], jsii.get(self, "networkConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="pluginsS3ObjectVersion")
    def plugins_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the plugins.zip file on your Amazon S3 bucket.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "pluginsS3ObjectVersion"))

    @builtins.property
    @jsii.member(jsii_name="pluginsS3Path")
    def plugins_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the plugins.zip file on your Amazon S3 bucket. For example, plugins.zip.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "pluginsS3Path"))

    @builtins.property
    @jsii.member(jsii_name="requirementsS3ObjectVersion")
    def requirements_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the requirements.txt file on your Amazon S3 bucket.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "requirementsS3ObjectVersion"))

    @builtins.property
    @jsii.member(jsii_name="requirementsS3Path")
    def requirements_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the requirements.txt file on your Amazon S3 bucket. For example, requirements.txt.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "requirementsS3Path"))

    @builtins.property
    @jsii.member(jsii_name="schedulers")
    def schedulers(self) -> typing.Optional[jsii.Number]:
        '''The number of schedulers that you want to run in your environment.

        Valid values:
        v2 - For environments larger than mw1.micro, accepts values from 2 to 5.
        Defaults to 2 for all environment sizes except mw1.micro, which defaults to 1.
        v1 - Accepts 1.
        '''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "schedulers"))

    @builtins.property
    @jsii.member(jsii_name="sourceBucket")
    def source_bucket(self) -> typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"]:
        '''The Amazon S3 bucket where your DAG code and supporting files are stored.'''
        return typing.cast(typing.Optional["_aws_cdk_aws_s3_ceddda9d.IBucket"], jsii.get(self, "sourceBucket"))

    @builtins.property
    @jsii.member(jsii_name="startupScriptS3ObjectVersion")
    def startup_script_s3_object_version(self) -> typing.Optional[builtins.str]:
        '''The version of the startup shell script in your Amazon S3 bucket.

        You must specify the version ID that Amazon S3 assigns to the file every time you update the script.
        Version IDs are Unicode, UTF-8 encoded, URL-ready, opaque strings that are no more than 1,024 bytes long.

        The following is an example:
        3sL4kqtJlcpXroDTDmJ+rmSpXd3dIbrHY+MTRCxf3vjVBH40Nr8X8gdRQBpUMLUo
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "startupScriptS3ObjectVersion"))

    @builtins.property
    @jsii.member(jsii_name="startupScriptS3Path")
    def startup_script_s3_path(self) -> typing.Optional[builtins.str]:
        '''The relative path to the startup shell script in your Amazon S3 bucket.

        For example, s3://mwaa-environment/startup.sh.
        Amazon MWAA runs the script as your environment starts, and before running the Apache Airflow process.
        You can use this script to install dependencies, modify Apache Airflow configuration options, and set environment variables.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "startupScriptS3Path"))

    @builtins.property
    @jsii.member(jsii_name="webserverAccessMode")
    def webserver_access_mode(self) -> typing.Optional["WebserverAccessMode"]:
        '''The Apache Airflow Web server access mode.'''
        return typing.cast(typing.Optional["WebserverAccessMode"], jsii.get(self, "webserverAccessMode"))

    @builtins.property
    @jsii.member(jsii_name="webserverUrl")
    def webserver_url(self) -> typing.Optional[builtins.str]:
        '''The URL of your Apache Airflow UI.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "webserverUrl"))

    @builtins.property
    @jsii.member(jsii_name="webserverVpcEndpointService")
    def webserver_vpc_endpoint_service(self) -> typing.Optional[builtins.str]:
        '''The VPC endpoint for the environment's web server.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "webserverVpcEndpointService"))

    @builtins.property
    @jsii.member(jsii_name="weeklyMaintenanceWindowStart")
    def weekly_maintenance_window_start(self) -> typing.Optional[builtins.str]:
        '''The day and time of the week to start weekly maintenance updates of your environment in the following format: DAY:HH:MM.

        For example: TUE:03:30. You can specify a start time in 30 minute increments only.

        Supported input includes the following:
        MON|TUE|WED|THU|FRI|SAT|SUN:([01]\\d|2[0-3]):(00|30)
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "weeklyMaintenanceWindowStart"))


__all__ = [
    "AirflowVersion",
    "EndpointManagement",
    "Environment",
    "EnvironmentAttributes",
    "EnvironmentBase",
    "EnvironmentClass",
    "EnvironmentProps",
    "IEnvironment",
    "LogLevel",
    "LoggingConfiguration",
    "ModuleLoggingConfiguration",
    "NetworkConfiguration",
    "WebserverAccessMode",
    "WorkerReplacementStrategy",
]

publication.publish()

def _typecheckingstub__d75f091b184b8fb2d88550b01b5b1291a3af0d350440b3c1dadc6631ec062c57(
    *,
    airflow_configuration_options: typing.Mapping[builtins.str, builtins.str],
    environment_arn: builtins.str,
    name: builtins.str,
    airflow_version: typing.Optional[AirflowVersion] = None,
    celery_executor_queue: typing.Optional[builtins.str] = None,
    dag_s3_path: typing.Optional[builtins.str] = None,
    database_vpc_endpoint_service: typing.Optional[builtins.str] = None,
    endpoint_management: typing.Optional[EndpointManagement] = None,
    environment_class: typing.Optional[EnvironmentClass] = None,
    execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    logging_configuration: typing.Optional[typing.Union[LoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    logging_configuration_dag_processing_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
    logging_configuration_scheduler_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
    logging_configuration_task_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
    logging_configuration_webserver_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
    logging_configuration_worker_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
    max_webservers: typing.Optional[jsii.Number] = None,
    max_workers: typing.Optional[jsii.Number] = None,
    min_webservers: typing.Optional[jsii.Number] = None,
    min_workers: typing.Optional[jsii.Number] = None,
    network_configuration: typing.Optional[typing.Union[NetworkConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    plugins_s3_object_version: typing.Optional[builtins.str] = None,
    plugins_s3_path: typing.Optional[builtins.str] = None,
    requirements_s3_object_version: typing.Optional[builtins.str] = None,
    requirements_s3_path: typing.Optional[builtins.str] = None,
    schedulers: typing.Optional[jsii.Number] = None,
    source_bucket: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    startup_script_s3_object_version: typing.Optional[builtins.str] = None,
    startup_script_s3_path: typing.Optional[builtins.str] = None,
    webserver_access_mode: typing.Optional[WebserverAccessMode] = None,
    webserver_url: typing.Optional[builtins.str] = None,
    webserver_vpc_endpoint_service: typing.Optional[builtins.str] = None,
    weekly_maintenance_window_start: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__adae2e01428b106a0a65893828e0f65d1e96376eb6556581f26b272553f74e81(
    *,
    airflow_configuration_options: typing.Mapping[builtins.str, builtins.str],
    name: builtins.str,
    airflow_version: typing.Optional[AirflowVersion] = None,
    dag_s3_path: typing.Optional[builtins.str] = None,
    endpoint_management: typing.Optional[EndpointManagement] = None,
    environment_class: typing.Optional[EnvironmentClass] = None,
    execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    logging_configuration: typing.Optional[typing.Union[LoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    max_webservers: typing.Optional[jsii.Number] = None,
    max_workers: typing.Optional[jsii.Number] = None,
    min_webservers: typing.Optional[jsii.Number] = None,
    min_workers: typing.Optional[jsii.Number] = None,
    network_configuration: typing.Optional[typing.Union[NetworkConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    plugins_s3_object_version: typing.Optional[builtins.str] = None,
    plugins_s3_path: typing.Optional[builtins.str] = None,
    requirements_s3_object_version: typing.Optional[builtins.str] = None,
    requirements_s3_path: typing.Optional[builtins.str] = None,
    schedulers: typing.Optional[jsii.Number] = None,
    source_bucket: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    startup_script_s3_object_version: typing.Optional[builtins.str] = None,
    startup_script_s3_path: typing.Optional[builtins.str] = None,
    webserver_access_mode: typing.Optional[WebserverAccessMode] = None,
    weekly_maintenance_window_start: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__587e90c0429a944bc98095249fe5cd300a90dcf33089932ed503e117deb58614(
    *,
    dag_processing_logs: typing.Optional[typing.Union[ModuleLoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    scheduler_logs: typing.Optional[typing.Union[ModuleLoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    task_logs: typing.Optional[typing.Union[ModuleLoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    web_server_logs: typing.Optional[typing.Union[ModuleLoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    worker_logs: typing.Optional[typing.Union[ModuleLoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7b6b5c584242899ae7800864118420958302bf2568da5e2d6f5a683e345399aa(
    *,
    cloud_watch_log_group: typing.Optional[_aws_cdk_aws_logs_ceddda9d.ILogGroup] = None,
    enabled: typing.Optional[builtins.bool] = None,
    log_level: typing.Optional[LogLevel] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__66a8db1008fda8f8cf9a9e9d41de07bde3dc8b894d4a91cd243e4e3057ff04ae(
    *,
    security_groups: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISecurityGroup]] = None,
    subnets: typing.Optional[typing.Sequence[_aws_cdk_aws_ec2_ceddda9d.ISubnet]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad5873da45b6688f4c218055f06ff0d6a531da884f4fbcf05c463ed354d7521f(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    account: typing.Optional[builtins.str] = None,
    environment_from_arn: typing.Optional[builtins.str] = None,
    physical_name: typing.Optional[builtins.str] = None,
    region: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5caedcd0e4f79944eef6be911818e685afe29161ed637d59813b0c34497c9a53(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    airflow_configuration_options: typing.Mapping[builtins.str, builtins.str],
    name: builtins.str,
    airflow_version: typing.Optional[AirflowVersion] = None,
    dag_s3_path: typing.Optional[builtins.str] = None,
    endpoint_management: typing.Optional[EndpointManagement] = None,
    environment_class: typing.Optional[EnvironmentClass] = None,
    execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    logging_configuration: typing.Optional[typing.Union[LoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    max_webservers: typing.Optional[jsii.Number] = None,
    max_workers: typing.Optional[jsii.Number] = None,
    min_webservers: typing.Optional[jsii.Number] = None,
    min_workers: typing.Optional[jsii.Number] = None,
    network_configuration: typing.Optional[typing.Union[NetworkConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    plugins_s3_object_version: typing.Optional[builtins.str] = None,
    plugins_s3_path: typing.Optional[builtins.str] = None,
    requirements_s3_object_version: typing.Optional[builtins.str] = None,
    requirements_s3_path: typing.Optional[builtins.str] = None,
    schedulers: typing.Optional[jsii.Number] = None,
    source_bucket: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    startup_script_s3_object_version: typing.Optional[builtins.str] = None,
    startup_script_s3_path: typing.Optional[builtins.str] = None,
    webserver_access_mode: typing.Optional[WebserverAccessMode] = None,
    weekly_maintenance_window_start: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__95cc4f4257f86486302fcb2e763d242a3040b6f4ce19c4cd9698055844e13d0c(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    airflow_configuration_options: typing.Mapping[builtins.str, builtins.str],
    environment_arn: builtins.str,
    name: builtins.str,
    airflow_version: typing.Optional[AirflowVersion] = None,
    celery_executor_queue: typing.Optional[builtins.str] = None,
    dag_s3_path: typing.Optional[builtins.str] = None,
    database_vpc_endpoint_service: typing.Optional[builtins.str] = None,
    endpoint_management: typing.Optional[EndpointManagement] = None,
    environment_class: typing.Optional[EnvironmentClass] = None,
    execution_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.IRole] = None,
    kms_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.IKey] = None,
    logging_configuration: typing.Optional[typing.Union[LoggingConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    logging_configuration_dag_processing_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
    logging_configuration_scheduler_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
    logging_configuration_task_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
    logging_configuration_webserver_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
    logging_configuration_worker_logs_cloud_watch_log_group_arn: typing.Optional[builtins.str] = None,
    max_webservers: typing.Optional[jsii.Number] = None,
    max_workers: typing.Optional[jsii.Number] = None,
    min_webservers: typing.Optional[jsii.Number] = None,
    min_workers: typing.Optional[jsii.Number] = None,
    network_configuration: typing.Optional[typing.Union[NetworkConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    plugins_s3_object_version: typing.Optional[builtins.str] = None,
    plugins_s3_path: typing.Optional[builtins.str] = None,
    requirements_s3_object_version: typing.Optional[builtins.str] = None,
    requirements_s3_path: typing.Optional[builtins.str] = None,
    schedulers: typing.Optional[jsii.Number] = None,
    source_bucket: typing.Optional[_aws_cdk_aws_s3_ceddda9d.IBucket] = None,
    startup_script_s3_object_version: typing.Optional[builtins.str] = None,
    startup_script_s3_path: typing.Optional[builtins.str] = None,
    webserver_access_mode: typing.Optional[WebserverAccessMode] = None,
    webserver_url: typing.Optional[builtins.str] = None,
    webserver_vpc_endpoint_service: typing.Optional[builtins.str] = None,
    weekly_maintenance_window_start: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7959ab616fb8602cff9e37f75ee4b0f7b75f4963daad74b8e571e648d8ece8a5(
    x: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

for cls in [IEnvironment]:
    typing.cast(typing.Any, cls).__protocol_attrs__ = typing.cast(typing.Any, cls).__protocol_attrs__ - set(['__jsii_proxy_class__', '__jsii_type__'])
