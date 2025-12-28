r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-fargate-dynamodb/README.adoc)
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

import aws_cdk.aws_dynamodb as _aws_cdk_aws_dynamodb_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_ecs as _aws_cdk_aws_ecs_ceddda9d
import constructs as _constructs_77d1e7e8


class FargateToDynamoDB(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-fargate-dynamodb.FargateToDynamoDB",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        public_api: builtins.bool,
        cluster_props: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ClusterProps, typing.Dict[builtins.str, typing.Any]]] = None,
        container_definition_props: typing.Any = None,
        dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
        ecr_image_version: typing.Optional[builtins.str] = None,
        ecr_repository_arn: typing.Optional[builtins.str] = None,
        existing_container_definition_object: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition] = None,
        existing_fargate_service_object: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.FargateService] = None,
        existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        fargate_service_props: typing.Any = None,
        fargate_task_definition_props: typing.Any = None,
        table_arn_environment_variable_name: typing.Optional[builtins.str] = None,
        table_environment_variable_name: typing.Optional[builtins.str] = None,
        table_permissions: typing.Optional[builtins.str] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param public_api: Whether the construct is deploying a private or public API. This has implications for the VPC deployed by this construct.
        :param cluster_props: Optional properties to create a new ECS cluster.
        :param container_definition_props: -
        :param dynamo_table_props: Optional user provided props to override the default props for the DynamoDB Table. Providing both this and ``existingTableInterface`` is an error. Default: - Partition key ID: string
        :param ecr_image_version: The version of the image to use from the repository. Default: - 'latest'
        :param ecr_repository_arn: The arn of an ECR Repository containing the image to use to generate the containers. format: arn:aws:ecr:[region]:[account number]:repository/[Repository Name]
        :param existing_container_definition_object: -
        :param existing_fargate_service_object: A Fargate Service already instantiated (probably by another Solutions Construct). If this is specified, then no props defining a new service can be provided, including: existingImageObject, ecrImageVersion, containerDefinitionProps, fargateTaskDefinitionProps, ecrRepositoryArn, fargateServiceProps, clusterProps, existingClusterInterface. If this value is provided, then existingContainerDefinitionObject must be provided as well. Default: - none
        :param existing_table_interface: Optional - existing DynamoDB table, providing both this and ``dynamoTableProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC in which to deploy the construct. Providing both this and vpcProps is an error. If the client provides an existing Fargate service, this value must be the VPC where the service is running. An DynamoDB Interface endpoint will be added to this VPC. Default: - none
        :param fargate_service_props: Optional values to override default Fargate Task definition properties (fargate-defaults.ts). The construct will default to launching the service is the most isolated subnets available (precedence: Isolated, Private and Public). Override those and other defaults here. defaults - fargate-defaults.ts
        :param fargate_task_definition_props: -
        :param table_arn_environment_variable_name: Optional Name for the container environment variable set to the ARN for the DynamoDB table. Default: - DYNAMODB_TABLE_ARN
        :param table_environment_variable_name: Optional Name for the container environment variable set to the name of the DynamoDB table. Default: - DYNAMODB_TABLE_NAME
        :param table_permissions: Optional table permissions to grant to the Fargate service. One of the following may be specified: ``All``, ``Read``, ``ReadWrite``, ``Write``. Default: - 'ReadWrite'
        :param vpc_props: Optional custom properties for a VPC the construct will create. This VPC will be used by the new Fargate service the construct creates (that's why targetGroupProps can't include a VPC). Providing both this and existingVpc is an error. An DynamoDB Interface endpoint will be included in this VPC. Default: - none
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8f669099000f03dcd7c38dccb42889260b2917b06111e3f3b2967e177e876c38)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = FargateToDynamoDBProps(
            public_api=public_api,
            cluster_props=cluster_props,
            container_definition_props=container_definition_props,
            dynamo_table_props=dynamo_table_props,
            ecr_image_version=ecr_image_version,
            ecr_repository_arn=ecr_repository_arn,
            existing_container_definition_object=existing_container_definition_object,
            existing_fargate_service_object=existing_fargate_service_object,
            existing_table_interface=existing_table_interface,
            existing_vpc=existing_vpc,
            fargate_service_props=fargate_service_props,
            fargate_task_definition_props=fargate_task_definition_props,
            table_arn_environment_variable_name=table_arn_environment_variable_name,
            table_environment_variable_name=table_environment_variable_name,
            table_permissions=table_permissions,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="container")
    def container(self) -> _aws_cdk_aws_ecs_ceddda9d.ContainerDefinition:
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition, jsii.get(self, "container"))

    @builtins.property
    @jsii.member(jsii_name="dynamoTableInterface")
    def dynamo_table_interface(self) -> _aws_cdk_aws_dynamodb_ceddda9d.ITable:
        return typing.cast(_aws_cdk_aws_dynamodb_ceddda9d.ITable, jsii.get(self, "dynamoTableInterface"))

    @builtins.property
    @jsii.member(jsii_name="service")
    def service(self) -> _aws_cdk_aws_ecs_ceddda9d.FargateService:
        return typing.cast(_aws_cdk_aws_ecs_ceddda9d.FargateService, jsii.get(self, "service"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, jsii.get(self, "vpc"))

    @builtins.property
    @jsii.member(jsii_name="dynamoTable")
    def dynamo_table(self) -> typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table]:
        return typing.cast(typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table], jsii.get(self, "dynamoTable"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-fargate-dynamodb.FargateToDynamoDBProps",
    jsii_struct_bases=[],
    name_mapping={
        "public_api": "publicApi",
        "cluster_props": "clusterProps",
        "container_definition_props": "containerDefinitionProps",
        "dynamo_table_props": "dynamoTableProps",
        "ecr_image_version": "ecrImageVersion",
        "ecr_repository_arn": "ecrRepositoryArn",
        "existing_container_definition_object": "existingContainerDefinitionObject",
        "existing_fargate_service_object": "existingFargateServiceObject",
        "existing_table_interface": "existingTableInterface",
        "existing_vpc": "existingVpc",
        "fargate_service_props": "fargateServiceProps",
        "fargate_task_definition_props": "fargateTaskDefinitionProps",
        "table_arn_environment_variable_name": "tableArnEnvironmentVariableName",
        "table_environment_variable_name": "tableEnvironmentVariableName",
        "table_permissions": "tablePermissions",
        "vpc_props": "vpcProps",
    },
)
class FargateToDynamoDBProps:
    def __init__(
        self,
        *,
        public_api: builtins.bool,
        cluster_props: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ClusterProps, typing.Dict[builtins.str, typing.Any]]] = None,
        container_definition_props: typing.Any = None,
        dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
        ecr_image_version: typing.Optional[builtins.str] = None,
        ecr_repository_arn: typing.Optional[builtins.str] = None,
        existing_container_definition_object: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition] = None,
        existing_fargate_service_object: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.FargateService] = None,
        existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        fargate_service_props: typing.Any = None,
        fargate_task_definition_props: typing.Any = None,
        table_arn_environment_variable_name: typing.Optional[builtins.str] = None,
        table_environment_variable_name: typing.Optional[builtins.str] = None,
        table_permissions: typing.Optional[builtins.str] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param public_api: Whether the construct is deploying a private or public API. This has implications for the VPC deployed by this construct.
        :param cluster_props: Optional properties to create a new ECS cluster.
        :param container_definition_props: -
        :param dynamo_table_props: Optional user provided props to override the default props for the DynamoDB Table. Providing both this and ``existingTableInterface`` is an error. Default: - Partition key ID: string
        :param ecr_image_version: The version of the image to use from the repository. Default: - 'latest'
        :param ecr_repository_arn: The arn of an ECR Repository containing the image to use to generate the containers. format: arn:aws:ecr:[region]:[account number]:repository/[Repository Name]
        :param existing_container_definition_object: -
        :param existing_fargate_service_object: A Fargate Service already instantiated (probably by another Solutions Construct). If this is specified, then no props defining a new service can be provided, including: existingImageObject, ecrImageVersion, containerDefinitionProps, fargateTaskDefinitionProps, ecrRepositoryArn, fargateServiceProps, clusterProps, existingClusterInterface. If this value is provided, then existingContainerDefinitionObject must be provided as well. Default: - none
        :param existing_table_interface: Optional - existing DynamoDB table, providing both this and ``dynamoTableProps`` will cause an error. Default: - None
        :param existing_vpc: An existing VPC in which to deploy the construct. Providing both this and vpcProps is an error. If the client provides an existing Fargate service, this value must be the VPC where the service is running. An DynamoDB Interface endpoint will be added to this VPC. Default: - none
        :param fargate_service_props: Optional values to override default Fargate Task definition properties (fargate-defaults.ts). The construct will default to launching the service is the most isolated subnets available (precedence: Isolated, Private and Public). Override those and other defaults here. defaults - fargate-defaults.ts
        :param fargate_task_definition_props: -
        :param table_arn_environment_variable_name: Optional Name for the container environment variable set to the ARN for the DynamoDB table. Default: - DYNAMODB_TABLE_ARN
        :param table_environment_variable_name: Optional Name for the container environment variable set to the name of the DynamoDB table. Default: - DYNAMODB_TABLE_NAME
        :param table_permissions: Optional table permissions to grant to the Fargate service. One of the following may be specified: ``All``, ``Read``, ``ReadWrite``, ``Write``. Default: - 'ReadWrite'
        :param vpc_props: Optional custom properties for a VPC the construct will create. This VPC will be used by the new Fargate service the construct creates (that's why targetGroupProps can't include a VPC). Providing both this and existingVpc is an error. An DynamoDB Interface endpoint will be included in this VPC. Default: - none
        '''
        if isinstance(cluster_props, dict):
            cluster_props = _aws_cdk_aws_ecs_ceddda9d.ClusterProps(**cluster_props)
        if isinstance(dynamo_table_props, dict):
            dynamo_table_props = _aws_cdk_aws_dynamodb_ceddda9d.TableProps(**dynamo_table_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f16d47b4e52c89df9c24841843144e557bb56ab11c40415ff1cc8d01e2a5b91f)
            check_type(argname="argument public_api", value=public_api, expected_type=type_hints["public_api"])
            check_type(argname="argument cluster_props", value=cluster_props, expected_type=type_hints["cluster_props"])
            check_type(argname="argument container_definition_props", value=container_definition_props, expected_type=type_hints["container_definition_props"])
            check_type(argname="argument dynamo_table_props", value=dynamo_table_props, expected_type=type_hints["dynamo_table_props"])
            check_type(argname="argument ecr_image_version", value=ecr_image_version, expected_type=type_hints["ecr_image_version"])
            check_type(argname="argument ecr_repository_arn", value=ecr_repository_arn, expected_type=type_hints["ecr_repository_arn"])
            check_type(argname="argument existing_container_definition_object", value=existing_container_definition_object, expected_type=type_hints["existing_container_definition_object"])
            check_type(argname="argument existing_fargate_service_object", value=existing_fargate_service_object, expected_type=type_hints["existing_fargate_service_object"])
            check_type(argname="argument existing_table_interface", value=existing_table_interface, expected_type=type_hints["existing_table_interface"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument fargate_service_props", value=fargate_service_props, expected_type=type_hints["fargate_service_props"])
            check_type(argname="argument fargate_task_definition_props", value=fargate_task_definition_props, expected_type=type_hints["fargate_task_definition_props"])
            check_type(argname="argument table_arn_environment_variable_name", value=table_arn_environment_variable_name, expected_type=type_hints["table_arn_environment_variable_name"])
            check_type(argname="argument table_environment_variable_name", value=table_environment_variable_name, expected_type=type_hints["table_environment_variable_name"])
            check_type(argname="argument table_permissions", value=table_permissions, expected_type=type_hints["table_permissions"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "public_api": public_api,
        }
        if cluster_props is not None:
            self._values["cluster_props"] = cluster_props
        if container_definition_props is not None:
            self._values["container_definition_props"] = container_definition_props
        if dynamo_table_props is not None:
            self._values["dynamo_table_props"] = dynamo_table_props
        if ecr_image_version is not None:
            self._values["ecr_image_version"] = ecr_image_version
        if ecr_repository_arn is not None:
            self._values["ecr_repository_arn"] = ecr_repository_arn
        if existing_container_definition_object is not None:
            self._values["existing_container_definition_object"] = existing_container_definition_object
        if existing_fargate_service_object is not None:
            self._values["existing_fargate_service_object"] = existing_fargate_service_object
        if existing_table_interface is not None:
            self._values["existing_table_interface"] = existing_table_interface
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if fargate_service_props is not None:
            self._values["fargate_service_props"] = fargate_service_props
        if fargate_task_definition_props is not None:
            self._values["fargate_task_definition_props"] = fargate_task_definition_props
        if table_arn_environment_variable_name is not None:
            self._values["table_arn_environment_variable_name"] = table_arn_environment_variable_name
        if table_environment_variable_name is not None:
            self._values["table_environment_variable_name"] = table_environment_variable_name
        if table_permissions is not None:
            self._values["table_permissions"] = table_permissions
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def public_api(self) -> builtins.bool:
        '''Whether the construct is deploying a private or public API.

        This has implications for the VPC deployed
        by this construct.
        '''
        result = self._values.get("public_api")
        assert result is not None, "Required property 'public_api' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def cluster_props(self) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ClusterProps]:
        '''Optional properties to create a new ECS cluster.'''
        result = self._values.get("cluster_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ClusterProps], result)

    @builtins.property
    def container_definition_props(self) -> typing.Any:
        result = self._values.get("container_definition_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def dynamo_table_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.TableProps]:
        '''Optional user provided props to override the default props for the DynamoDB Table.

        Providing both this and
        ``existingTableInterface`` is an error.

        :default: - Partition key ID: string
        '''
        result = self._values.get("dynamo_table_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.TableProps], result)

    @builtins.property
    def ecr_image_version(self) -> typing.Optional[builtins.str]:
        '''The version of the image to use from the repository.

        :default: - 'latest'
        '''
        result = self._values.get("ecr_image_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ecr_repository_arn(self) -> typing.Optional[builtins.str]:
        '''The arn of an ECR Repository containing the image to use to generate the containers.

        format:
        arn:aws:ecr:[region]:[account number]:repository/[Repository Name]
        '''
        result = self._values.get("ecr_repository_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def existing_container_definition_object(
        self,
    ) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition]:
        result = self._values.get("existing_container_definition_object")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition], result)

    @builtins.property
    def existing_fargate_service_object(
        self,
    ) -> typing.Optional[_aws_cdk_aws_ecs_ceddda9d.FargateService]:
        '''A Fargate Service already instantiated (probably by another Solutions Construct).

        If
        this is specified, then no props defining a new service can be provided, including:
        existingImageObject, ecrImageVersion, containerDefinitionProps, fargateTaskDefinitionProps,
        ecrRepositoryArn, fargateServiceProps, clusterProps, existingClusterInterface. If this value
        is provided, then existingContainerDefinitionObject must be provided as well.

        :default: - none
        '''
        result = self._values.get("existing_fargate_service_object")
        return typing.cast(typing.Optional[_aws_cdk_aws_ecs_ceddda9d.FargateService], result)

    @builtins.property
    def existing_table_interface(
        self,
    ) -> typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable]:
        '''Optional - existing DynamoDB table, providing both this and ``dynamoTableProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_table_interface")
        return typing.cast(typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable], result)

    @builtins.property
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC in which to deploy the construct.

        Providing both this and
        vpcProps is an error. If the client provides an existing Fargate service,
        this value must be the VPC where the service is running. An DynamoDB Interface
        endpoint will be added to this VPC.

        :default: - none
        '''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def fargate_service_props(self) -> typing.Any:
        '''Optional values to override default Fargate Task definition properties (fargate-defaults.ts). The construct will default to launching the service is the most isolated subnets available (precedence: Isolated, Private and Public). Override those and other defaults here.

        defaults - fargate-defaults.ts
        '''
        result = self._values.get("fargate_service_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def fargate_task_definition_props(self) -> typing.Any:
        result = self._values.get("fargate_task_definition_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def table_arn_environment_variable_name(self) -> typing.Optional[builtins.str]:
        '''Optional Name for the container environment variable set to the ARN for the DynamoDB table.

        :default: - DYNAMODB_TABLE_ARN
        '''
        result = self._values.get("table_arn_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def table_environment_variable_name(self) -> typing.Optional[builtins.str]:
        '''Optional Name for the container environment variable set to the name of the DynamoDB table.

        :default: - DYNAMODB_TABLE_NAME
        '''
        result = self._values.get("table_environment_variable_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def table_permissions(self) -> typing.Optional[builtins.str]:
        '''Optional table permissions to grant to the Fargate service.

        One of the following may be specified: ``All``, ``Read``, ``ReadWrite``, ``Write``.

        :default: - 'ReadWrite'
        '''
        result = self._values.get("table_permissions")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vpc_props(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps]:
        '''Optional custom properties for a VPC the construct will create.

        This VPC will
        be used by the new Fargate service the construct creates (that's
        why targetGroupProps can't include a VPC). Providing
        both this and existingVpc is an error. An DynamoDB Interface
        endpoint will be included in this VPC.

        :default: - none
        '''
        result = self._values.get("vpc_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "FargateToDynamoDBProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "FargateToDynamoDB",
    "FargateToDynamoDBProps",
]

publication.publish()

def _typecheckingstub__8f669099000f03dcd7c38dccb42889260b2917b06111e3f3b2967e177e876c38(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    public_api: builtins.bool,
    cluster_props: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ClusterProps, typing.Dict[builtins.str, typing.Any]]] = None,
    container_definition_props: typing.Any = None,
    dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ecr_image_version: typing.Optional[builtins.str] = None,
    ecr_repository_arn: typing.Optional[builtins.str] = None,
    existing_container_definition_object: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition] = None,
    existing_fargate_service_object: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.FargateService] = None,
    existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    fargate_service_props: typing.Any = None,
    fargate_task_definition_props: typing.Any = None,
    table_arn_environment_variable_name: typing.Optional[builtins.str] = None,
    table_environment_variable_name: typing.Optional[builtins.str] = None,
    table_permissions: typing.Optional[builtins.str] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f16d47b4e52c89df9c24841843144e557bb56ab11c40415ff1cc8d01e2a5b91f(
    *,
    public_api: builtins.bool,
    cluster_props: typing.Optional[typing.Union[_aws_cdk_aws_ecs_ceddda9d.ClusterProps, typing.Dict[builtins.str, typing.Any]]] = None,
    container_definition_props: typing.Any = None,
    dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ecr_image_version: typing.Optional[builtins.str] = None,
    ecr_repository_arn: typing.Optional[builtins.str] = None,
    existing_container_definition_object: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.ContainerDefinition] = None,
    existing_fargate_service_object: typing.Optional[_aws_cdk_aws_ecs_ceddda9d.FargateService] = None,
    existing_table_interface: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.ITable] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    fargate_service_props: typing.Any = None,
    fargate_task_definition_props: typing.Any = None,
    table_arn_environment_variable_name: typing.Optional[builtins.str] = None,
    table_environment_variable_name: typing.Optional[builtins.str] = None,
    table_permissions: typing.Optional[builtins.str] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
