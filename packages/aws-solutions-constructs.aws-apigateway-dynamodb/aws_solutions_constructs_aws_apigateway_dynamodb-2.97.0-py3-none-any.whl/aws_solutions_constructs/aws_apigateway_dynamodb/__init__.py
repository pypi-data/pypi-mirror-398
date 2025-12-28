r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-apigateway-dynamodb/README.adoc)
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

import aws_cdk.aws_apigateway as _aws_cdk_aws_apigateway_ceddda9d
import aws_cdk.aws_dynamodb as _aws_cdk_aws_dynamodb_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import constructs as _constructs_77d1e7e8


class ApiGatewayToDynamoDB(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-apigateway-dynamodb.ApiGatewayToDynamoDB",
):
    '''
    :summary: The ApiGatewayToDynamoDB class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        additional_create_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_delete_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_read_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_update_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        allow_create_operation: typing.Optional[builtins.bool] = None,
        allow_delete_operation: typing.Optional[builtins.bool] = None,
        allow_read_operation: typing.Optional[builtins.bool] = None,
        allow_update_operation: typing.Optional[builtins.bool] = None,
        api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
        create_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        create_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        create_request_template: typing.Optional[builtins.str] = None,
        create_usage_plan: typing.Optional[builtins.bool] = None,
        delete_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        delete_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        delete_request_template: typing.Optional[builtins.str] = None,
        dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_table_obj: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        read_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        read_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        read_request_template: typing.Optional[builtins.str] = None,
        resource_name: typing.Optional[builtins.str] = None,
        update_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        update_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        update_request_template: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param additional_create_request_templates: Optional Create Request Templates for content-types other than ``application/json``. Use the ``createRequestTemplate`` property to set the request template for the ``application/json`` content-type. This property can only be specified if the ``allowCreateOperation`` property is set to true. Default: - None
        :param additional_delete_request_templates: Optional Delete request templates for content-types other than ``application/json``. Use the ``deleteRequestTemplate`` property to set the request template for the ``application/json`` content-type. This property can only be specified if the ``allowDeleteOperation`` property is set to true. Default: - None
        :param additional_read_request_templates: Optional Read Request Templates for content-types other than ``application/json``. Use the ``readRequestTemplate`` property to set the request template for the ``application/json`` content-type. Default: - None
        :param additional_update_request_templates: Optional Update Request Templates for content-types other than ``application/json``. Use the ``updateRequestTemplate`` property to set the request template for the ``application/json`` content-type. This property can only be specified if the ``allowUpdateOperation`` property is set to true. Default: - None
        :param allow_create_operation: Whether to deploy an API Gateway Method for POST HTTP operations on the DynamoDB table (i.e. dynamodb:PutItem). Default: - false
        :param allow_delete_operation: Whether to deploy API Gateway Method for DELETE HTTP operations on DynamoDB table (i.e. dynamodb:DeleteItem). Default: - false
        :param allow_read_operation: Whether to deploy an API Gateway Method for GET HTTP operations on DynamoDB table (i.e. dynamodb:Query). Default: - true
        :param allow_update_operation: Whether to deploy API Gateway Method for PUT HTTP operations on DynamoDB table (i.e. dynamodb:UpdateItem). Default: - false
        :param api_gateway_props: Optional - user provided props to override the default props for the API Gateway. Default: - Default properties are used.
        :param create_integration_responses: Optional, custom API Gateway Integration Response for the create method. This property can only be specified if the ``allowCreateOperation`` property is set to true. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param create_method_responses: Optional, custom API Gateway Method Responses for the create action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param create_request_template: API Gateway Request Template for the create method for the default ``application/json`` content-type. This property is required if the ``allowCreateOperation`` property is set to true. Default: - None
        :param create_usage_plan: Whether to create a Usage Plan attached to the API. Must be true if apiGatewayProps.defaultMethodOptions.apiKeyRequired is true Default: - true (to match legacy behavior)
        :param delete_integration_responses: Optional, custom API Gateway Integration Response for the delete method. This property can only be specified if the ``allowDeleteOperation`` property is set to true. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param delete_method_responses: Optional, custom API Gateway Method Responses for the delete action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param delete_request_template: API Gateway Request Template for the delete method for the default ``application/json`` content-type. This property can only be specified if the ``allowDeleteOperation`` property is set to true. Default: - ``{ \\ "TableName": "DYNAMODB_TABLE_NAME", \\ "Key": { \\ "${partitionKeyName}": { \\ "S": "$input.params('PARTITION_KEY_NAME')" \\ } \\ }, \\ "ReturnValues": "ALL_OLD" \\ }``
        :param dynamo_table_props: Optional user provided props to override the default props for the DynamoDB Table. Providing both this and ``existingTableInterface`` is an error. Default: - Partition key ID: string
        :param existing_table_obj: Existing instance of DynamoDB table object, providing both this and ``dynamoTableProps`` will cause an error. Default: - None
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param read_integration_responses: Optional, custom API Gateway Integration Response for the read method. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param read_method_responses: Optional, custom API Gateway Method Responses for the read action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param read_request_template: API Gateway Request Template for the read method for the default ``application/json`` content-type. The default template only supports a partition key and not partition + sort keys. Default: - ``{ \\ "TableName": "DYNAMODB_TABLE_NAME", \\ "KeyConditionExpression": "PARTITION_KEY_NAME = :v1", \\ "ExpressionAttributeValues": { \\ ":v1": { \\ "S": "$input.params('PARTITION_KEY_NAME')" \\ } \\ } \\ }``
        :param resource_name: Optional resource name on the API This property is useful if your integration does not directly use the partition key name. Default: - partition key name, retrieved from the DynamoDB table object
        :param update_integration_responses: Optional, custom API Gateway Integration Response for the update method. This property can only be specified if the ``allowUpdateOperation`` property is set to true. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param update_method_responses: Optional, custom API Gateway Method Responses for the update action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param update_request_template: API Gateway Request Template for the update method. This property is required if the ``allowUpdateOperation`` property is set to true. Default: - None

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the ApiGatewayToDynamoDB class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2d19ee8ef37452b3cc026fd476b098d59eff0a90d0cbae8d3a736dc5fc92c0d0)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ApiGatewayToDynamoDBProps(
            additional_create_request_templates=additional_create_request_templates,
            additional_delete_request_templates=additional_delete_request_templates,
            additional_read_request_templates=additional_read_request_templates,
            additional_update_request_templates=additional_update_request_templates,
            allow_create_operation=allow_create_operation,
            allow_delete_operation=allow_delete_operation,
            allow_read_operation=allow_read_operation,
            allow_update_operation=allow_update_operation,
            api_gateway_props=api_gateway_props,
            create_integration_responses=create_integration_responses,
            create_method_responses=create_method_responses,
            create_request_template=create_request_template,
            create_usage_plan=create_usage_plan,
            delete_integration_responses=delete_integration_responses,
            delete_method_responses=delete_method_responses,
            delete_request_template=delete_request_template,
            dynamo_table_props=dynamo_table_props,
            existing_table_obj=existing_table_obj,
            log_group_props=log_group_props,
            read_integration_responses=read_integration_responses,
            read_method_responses=read_method_responses,
            read_request_template=read_request_template,
            resource_name=resource_name,
            update_integration_responses=update_integration_responses,
            update_method_responses=update_method_responses,
            update_request_template=update_request_template,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="apiGateway")
    def api_gateway(self) -> _aws_cdk_aws_apigateway_ceddda9d.RestApi:
        return typing.cast(_aws_cdk_aws_apigateway_ceddda9d.RestApi, jsii.get(self, "apiGateway"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayLogGroup")
    def api_gateway_log_group(self) -> _aws_cdk_aws_logs_ceddda9d.LogGroup:
        return typing.cast(_aws_cdk_aws_logs_ceddda9d.LogGroup, jsii.get(self, "apiGatewayLogGroup"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayRole")
    def api_gateway_role(self) -> _aws_cdk_aws_iam_ceddda9d.Role:
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Role, jsii.get(self, "apiGatewayRole"))

    @builtins.property
    @jsii.member(jsii_name="dynamoTable")
    def dynamo_table(self) -> _aws_cdk_aws_dynamodb_ceddda9d.Table:
        return typing.cast(_aws_cdk_aws_dynamodb_ceddda9d.Table, jsii.get(self, "dynamoTable"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayCloudWatchRole")
    def api_gateway_cloud_watch_role(
        self,
    ) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role]:
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role], jsii.get(self, "apiGatewayCloudWatchRole"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-apigateway-dynamodb.ApiGatewayToDynamoDBProps",
    jsii_struct_bases=[],
    name_mapping={
        "additional_create_request_templates": "additionalCreateRequestTemplates",
        "additional_delete_request_templates": "additionalDeleteRequestTemplates",
        "additional_read_request_templates": "additionalReadRequestTemplates",
        "additional_update_request_templates": "additionalUpdateRequestTemplates",
        "allow_create_operation": "allowCreateOperation",
        "allow_delete_operation": "allowDeleteOperation",
        "allow_read_operation": "allowReadOperation",
        "allow_update_operation": "allowUpdateOperation",
        "api_gateway_props": "apiGatewayProps",
        "create_integration_responses": "createIntegrationResponses",
        "create_method_responses": "createMethodResponses",
        "create_request_template": "createRequestTemplate",
        "create_usage_plan": "createUsagePlan",
        "delete_integration_responses": "deleteIntegrationResponses",
        "delete_method_responses": "deleteMethodResponses",
        "delete_request_template": "deleteRequestTemplate",
        "dynamo_table_props": "dynamoTableProps",
        "existing_table_obj": "existingTableObj",
        "log_group_props": "logGroupProps",
        "read_integration_responses": "readIntegrationResponses",
        "read_method_responses": "readMethodResponses",
        "read_request_template": "readRequestTemplate",
        "resource_name": "resourceName",
        "update_integration_responses": "updateIntegrationResponses",
        "update_method_responses": "updateMethodResponses",
        "update_request_template": "updateRequestTemplate",
    },
)
class ApiGatewayToDynamoDBProps:
    def __init__(
        self,
        *,
        additional_create_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_delete_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_read_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_update_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        allow_create_operation: typing.Optional[builtins.bool] = None,
        allow_delete_operation: typing.Optional[builtins.bool] = None,
        allow_read_operation: typing.Optional[builtins.bool] = None,
        allow_update_operation: typing.Optional[builtins.bool] = None,
        api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
        create_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        create_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        create_request_template: typing.Optional[builtins.str] = None,
        create_usage_plan: typing.Optional[builtins.bool] = None,
        delete_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        delete_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        delete_request_template: typing.Optional[builtins.str] = None,
        dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_table_obj: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        read_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        read_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        read_request_template: typing.Optional[builtins.str] = None,
        resource_name: typing.Optional[builtins.str] = None,
        update_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        update_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        update_request_template: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param additional_create_request_templates: Optional Create Request Templates for content-types other than ``application/json``. Use the ``createRequestTemplate`` property to set the request template for the ``application/json`` content-type. This property can only be specified if the ``allowCreateOperation`` property is set to true. Default: - None
        :param additional_delete_request_templates: Optional Delete request templates for content-types other than ``application/json``. Use the ``deleteRequestTemplate`` property to set the request template for the ``application/json`` content-type. This property can only be specified if the ``allowDeleteOperation`` property is set to true. Default: - None
        :param additional_read_request_templates: Optional Read Request Templates for content-types other than ``application/json``. Use the ``readRequestTemplate`` property to set the request template for the ``application/json`` content-type. Default: - None
        :param additional_update_request_templates: Optional Update Request Templates for content-types other than ``application/json``. Use the ``updateRequestTemplate`` property to set the request template for the ``application/json`` content-type. This property can only be specified if the ``allowUpdateOperation`` property is set to true. Default: - None
        :param allow_create_operation: Whether to deploy an API Gateway Method for POST HTTP operations on the DynamoDB table (i.e. dynamodb:PutItem). Default: - false
        :param allow_delete_operation: Whether to deploy API Gateway Method for DELETE HTTP operations on DynamoDB table (i.e. dynamodb:DeleteItem). Default: - false
        :param allow_read_operation: Whether to deploy an API Gateway Method for GET HTTP operations on DynamoDB table (i.e. dynamodb:Query). Default: - true
        :param allow_update_operation: Whether to deploy API Gateway Method for PUT HTTP operations on DynamoDB table (i.e. dynamodb:UpdateItem). Default: - false
        :param api_gateway_props: Optional - user provided props to override the default props for the API Gateway. Default: - Default properties are used.
        :param create_integration_responses: Optional, custom API Gateway Integration Response for the create method. This property can only be specified if the ``allowCreateOperation`` property is set to true. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param create_method_responses: Optional, custom API Gateway Method Responses for the create action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param create_request_template: API Gateway Request Template for the create method for the default ``application/json`` content-type. This property is required if the ``allowCreateOperation`` property is set to true. Default: - None
        :param create_usage_plan: Whether to create a Usage Plan attached to the API. Must be true if apiGatewayProps.defaultMethodOptions.apiKeyRequired is true Default: - true (to match legacy behavior)
        :param delete_integration_responses: Optional, custom API Gateway Integration Response for the delete method. This property can only be specified if the ``allowDeleteOperation`` property is set to true. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param delete_method_responses: Optional, custom API Gateway Method Responses for the delete action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param delete_request_template: API Gateway Request Template for the delete method for the default ``application/json`` content-type. This property can only be specified if the ``allowDeleteOperation`` property is set to true. Default: - ``{ \\ "TableName": "DYNAMODB_TABLE_NAME", \\ "Key": { \\ "${partitionKeyName}": { \\ "S": "$input.params('PARTITION_KEY_NAME')" \\ } \\ }, \\ "ReturnValues": "ALL_OLD" \\ }``
        :param dynamo_table_props: Optional user provided props to override the default props for the DynamoDB Table. Providing both this and ``existingTableInterface`` is an error. Default: - Partition key ID: string
        :param existing_table_obj: Existing instance of DynamoDB table object, providing both this and ``dynamoTableProps`` will cause an error. Default: - None
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param read_integration_responses: Optional, custom API Gateway Integration Response for the read method. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param read_method_responses: Optional, custom API Gateway Method Responses for the read action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param read_request_template: API Gateway Request Template for the read method for the default ``application/json`` content-type. The default template only supports a partition key and not partition + sort keys. Default: - ``{ \\ "TableName": "DYNAMODB_TABLE_NAME", \\ "KeyConditionExpression": "PARTITION_KEY_NAME = :v1", \\ "ExpressionAttributeValues": { \\ ":v1": { \\ "S": "$input.params('PARTITION_KEY_NAME')" \\ } \\ } \\ }``
        :param resource_name: Optional resource name on the API This property is useful if your integration does not directly use the partition key name. Default: - partition key name, retrieved from the DynamoDB table object
        :param update_integration_responses: Optional, custom API Gateway Integration Response for the update method. This property can only be specified if the ``allowUpdateOperation`` property is set to true. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param update_method_responses: Optional, custom API Gateway Method Responses for the update action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param update_request_template: API Gateway Request Template for the update method. This property is required if the ``allowUpdateOperation`` property is set to true. Default: - None

        :summary: The properties for the ApiGatewayToDynamoDB class.
        '''
        if isinstance(api_gateway_props, dict):
            api_gateway_props = _aws_cdk_aws_apigateway_ceddda9d.RestApiProps(**api_gateway_props)
        if isinstance(dynamo_table_props, dict):
            dynamo_table_props = _aws_cdk_aws_dynamodb_ceddda9d.TableProps(**dynamo_table_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__58088b1487acfcd4ecedaab51f9d82c918ccc6b7505df05d95bb32d30d839ee5)
            check_type(argname="argument additional_create_request_templates", value=additional_create_request_templates, expected_type=type_hints["additional_create_request_templates"])
            check_type(argname="argument additional_delete_request_templates", value=additional_delete_request_templates, expected_type=type_hints["additional_delete_request_templates"])
            check_type(argname="argument additional_read_request_templates", value=additional_read_request_templates, expected_type=type_hints["additional_read_request_templates"])
            check_type(argname="argument additional_update_request_templates", value=additional_update_request_templates, expected_type=type_hints["additional_update_request_templates"])
            check_type(argname="argument allow_create_operation", value=allow_create_operation, expected_type=type_hints["allow_create_operation"])
            check_type(argname="argument allow_delete_operation", value=allow_delete_operation, expected_type=type_hints["allow_delete_operation"])
            check_type(argname="argument allow_read_operation", value=allow_read_operation, expected_type=type_hints["allow_read_operation"])
            check_type(argname="argument allow_update_operation", value=allow_update_operation, expected_type=type_hints["allow_update_operation"])
            check_type(argname="argument api_gateway_props", value=api_gateway_props, expected_type=type_hints["api_gateway_props"])
            check_type(argname="argument create_integration_responses", value=create_integration_responses, expected_type=type_hints["create_integration_responses"])
            check_type(argname="argument create_method_responses", value=create_method_responses, expected_type=type_hints["create_method_responses"])
            check_type(argname="argument create_request_template", value=create_request_template, expected_type=type_hints["create_request_template"])
            check_type(argname="argument create_usage_plan", value=create_usage_plan, expected_type=type_hints["create_usage_plan"])
            check_type(argname="argument delete_integration_responses", value=delete_integration_responses, expected_type=type_hints["delete_integration_responses"])
            check_type(argname="argument delete_method_responses", value=delete_method_responses, expected_type=type_hints["delete_method_responses"])
            check_type(argname="argument delete_request_template", value=delete_request_template, expected_type=type_hints["delete_request_template"])
            check_type(argname="argument dynamo_table_props", value=dynamo_table_props, expected_type=type_hints["dynamo_table_props"])
            check_type(argname="argument existing_table_obj", value=existing_table_obj, expected_type=type_hints["existing_table_obj"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
            check_type(argname="argument read_integration_responses", value=read_integration_responses, expected_type=type_hints["read_integration_responses"])
            check_type(argname="argument read_method_responses", value=read_method_responses, expected_type=type_hints["read_method_responses"])
            check_type(argname="argument read_request_template", value=read_request_template, expected_type=type_hints["read_request_template"])
            check_type(argname="argument resource_name", value=resource_name, expected_type=type_hints["resource_name"])
            check_type(argname="argument update_integration_responses", value=update_integration_responses, expected_type=type_hints["update_integration_responses"])
            check_type(argname="argument update_method_responses", value=update_method_responses, expected_type=type_hints["update_method_responses"])
            check_type(argname="argument update_request_template", value=update_request_template, expected_type=type_hints["update_request_template"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if additional_create_request_templates is not None:
            self._values["additional_create_request_templates"] = additional_create_request_templates
        if additional_delete_request_templates is not None:
            self._values["additional_delete_request_templates"] = additional_delete_request_templates
        if additional_read_request_templates is not None:
            self._values["additional_read_request_templates"] = additional_read_request_templates
        if additional_update_request_templates is not None:
            self._values["additional_update_request_templates"] = additional_update_request_templates
        if allow_create_operation is not None:
            self._values["allow_create_operation"] = allow_create_operation
        if allow_delete_operation is not None:
            self._values["allow_delete_operation"] = allow_delete_operation
        if allow_read_operation is not None:
            self._values["allow_read_operation"] = allow_read_operation
        if allow_update_operation is not None:
            self._values["allow_update_operation"] = allow_update_operation
        if api_gateway_props is not None:
            self._values["api_gateway_props"] = api_gateway_props
        if create_integration_responses is not None:
            self._values["create_integration_responses"] = create_integration_responses
        if create_method_responses is not None:
            self._values["create_method_responses"] = create_method_responses
        if create_request_template is not None:
            self._values["create_request_template"] = create_request_template
        if create_usage_plan is not None:
            self._values["create_usage_plan"] = create_usage_plan
        if delete_integration_responses is not None:
            self._values["delete_integration_responses"] = delete_integration_responses
        if delete_method_responses is not None:
            self._values["delete_method_responses"] = delete_method_responses
        if delete_request_template is not None:
            self._values["delete_request_template"] = delete_request_template
        if dynamo_table_props is not None:
            self._values["dynamo_table_props"] = dynamo_table_props
        if existing_table_obj is not None:
            self._values["existing_table_obj"] = existing_table_obj
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props
        if read_integration_responses is not None:
            self._values["read_integration_responses"] = read_integration_responses
        if read_method_responses is not None:
            self._values["read_method_responses"] = read_method_responses
        if read_request_template is not None:
            self._values["read_request_template"] = read_request_template
        if resource_name is not None:
            self._values["resource_name"] = resource_name
        if update_integration_responses is not None:
            self._values["update_integration_responses"] = update_integration_responses
        if update_method_responses is not None:
            self._values["update_method_responses"] = update_method_responses
        if update_request_template is not None:
            self._values["update_request_template"] = update_request_template

    @builtins.property
    def additional_create_request_templates(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Optional Create Request Templates for content-types other than ``application/json``.

        Use the ``createRequestTemplate`` property to set the request template for the ``application/json`` content-type.
        This property can only be specified if the ``allowCreateOperation`` property is set to true.

        :default: - None
        '''
        result = self._values.get("additional_create_request_templates")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def additional_delete_request_templates(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Optional Delete request templates for content-types other than ``application/json``.

        Use the ``deleteRequestTemplate`` property to set the request template for the ``application/json`` content-type.
        This property can only be specified if the ``allowDeleteOperation`` property is set to true.

        :default: - None
        '''
        result = self._values.get("additional_delete_request_templates")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def additional_read_request_templates(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Optional Read Request Templates for content-types other than ``application/json``.

        Use the ``readRequestTemplate`` property to set the request template for the ``application/json`` content-type.

        :default: - None
        '''
        result = self._values.get("additional_read_request_templates")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def additional_update_request_templates(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Optional Update Request Templates for content-types other than ``application/json``.

        Use the ``updateRequestTemplate`` property to set the request template for the ``application/json`` content-type.
        This property can only be specified if the ``allowUpdateOperation`` property is set to true.

        :default: - None
        '''
        result = self._values.get("additional_update_request_templates")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def allow_create_operation(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy an API Gateway Method for POST HTTP operations on the DynamoDB table (i.e. dynamodb:PutItem).

        :default: - false
        '''
        result = self._values.get("allow_create_operation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def allow_delete_operation(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy API Gateway Method for DELETE HTTP operations on DynamoDB table (i.e. dynamodb:DeleteItem).

        :default: - false
        '''
        result = self._values.get("allow_delete_operation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def allow_read_operation(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy an API Gateway Method for GET HTTP operations on DynamoDB table (i.e. dynamodb:Query).

        :default: - true
        '''
        result = self._values.get("allow_read_operation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def allow_update_operation(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy API Gateway Method for PUT HTTP operations on DynamoDB table (i.e. dynamodb:UpdateItem).

        :default: - false
        '''
        result = self._values.get("allow_update_operation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def api_gateway_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps]:
        '''Optional - user provided props to override the default props for the API Gateway.

        :default: - Default properties are used.
        '''
        result = self._values.get("api_gateway_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps], result)

    @builtins.property
    def create_integration_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]]:
        '''Optional, custom API Gateway Integration Response for the create method.

        This property can only be specified if the ``allowCreateOperation`` property is set to true.

        :default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        '''
        result = self._values.get("create_integration_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]], result)

    @builtins.property
    def create_method_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]]:
        '''Optional, custom API Gateway Method Responses for the create action.

        :default:

        - [
        {
        statusCode: "200",
        responseParameters: {
        "method.response.header.Content-Type": true
        }
        },
        {
        statusCode: "500",
        responseParameters: {
        "method.response.header.Content-Type": true
        },
        }
        ]
        '''
        result = self._values.get("create_method_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]], result)

    @builtins.property
    def create_request_template(self) -> typing.Optional[builtins.str]:
        '''API Gateway Request Template for the create method for the default ``application/json`` content-type.

        This property is required if the ``allowCreateOperation`` property is set to true.

        :default: - None
        '''
        result = self._values.get("create_request_template")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def create_usage_plan(self) -> typing.Optional[builtins.bool]:
        '''Whether to create a Usage Plan attached to the API.

        Must be true if
        apiGatewayProps.defaultMethodOptions.apiKeyRequired is true

        :default: - true (to match legacy behavior)
        '''
        result = self._values.get("create_usage_plan")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def delete_integration_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]]:
        '''Optional, custom API Gateway Integration Response for the delete method.

        This property can only be specified if the ``allowDeleteOperation`` property is set to true.

        :default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        '''
        result = self._values.get("delete_integration_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]], result)

    @builtins.property
    def delete_method_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]]:
        '''Optional, custom API Gateway Method Responses for the delete action.

        :default:

        - [
        {
        statusCode: "200",
        responseParameters: {
        "method.response.header.Content-Type": true
        }
        },
        {
        statusCode: "500",
        responseParameters: {
        "method.response.header.Content-Type": true
        },
        }
        ]
        '''
        result = self._values.get("delete_method_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]], result)

    @builtins.property
    def delete_request_template(self) -> typing.Optional[builtins.str]:
        '''API Gateway Request Template for the delete method for the default ``application/json`` content-type.

        This property can only be specified if the ``allowDeleteOperation`` property is set to true.

        :default: - ``{ \\ "TableName": "DYNAMODB_TABLE_NAME", \\ "Key": { \\ "${partitionKeyName}": { \\ "S": "$input.params('PARTITION_KEY_NAME')" \\ } \\ }, \\ "ReturnValues": "ALL_OLD" \\ }``
        '''
        result = self._values.get("delete_request_template")
        return typing.cast(typing.Optional[builtins.str], result)

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
    def existing_table_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table]:
        '''Existing instance of DynamoDB table object, providing both this and ``dynamoTableProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_table_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table], result)

    @builtins.property
    def log_group_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps]:
        '''User provided props to override the default props for the CloudWatchLogs LogGroup.

        :default: - Default props are used
        '''
        result = self._values.get("log_group_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps], result)

    @builtins.property
    def read_integration_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]]:
        '''Optional, custom API Gateway Integration Response for the read method.

        :default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        '''
        result = self._values.get("read_integration_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]], result)

    @builtins.property
    def read_method_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]]:
        '''Optional, custom API Gateway Method Responses for the read action.

        :default:

        - [
        {
        statusCode: "200",
        responseParameters: {
        "method.response.header.Content-Type": true
        }
        },
        {
        statusCode: "500",
        responseParameters: {
        "method.response.header.Content-Type": true
        },
        }
        ]
        '''
        result = self._values.get("read_method_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]], result)

    @builtins.property
    def read_request_template(self) -> typing.Optional[builtins.str]:
        '''API Gateway Request Template for the read method for the default ``application/json`` content-type.

        The default template only supports a partition key and not partition + sort keys.

        :default: - ``{ \\ "TableName": "DYNAMODB_TABLE_NAME", \\ "KeyConditionExpression": "PARTITION_KEY_NAME = :v1", \\ "ExpressionAttributeValues": { \\ ":v1": { \\ "S": "$input.params('PARTITION_KEY_NAME')" \\ } \\ } \\ }``
        '''
        result = self._values.get("read_request_template")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def resource_name(self) -> typing.Optional[builtins.str]:
        '''Optional resource name on the API This property is useful if your integration does not directly use the partition key name.

        :default: - partition key name, retrieved from the DynamoDB table object
        '''
        result = self._values.get("resource_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def update_integration_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]]:
        '''Optional, custom API Gateway Integration Response for the update method.

        This property can only be specified if the ``allowUpdateOperation`` property is set to true.

        :default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        '''
        result = self._values.get("update_integration_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]], result)

    @builtins.property
    def update_method_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]]:
        '''Optional, custom API Gateway Method Responses for the update action.

        :default:

        - [
        {
        statusCode: "200",
        responseParameters: {
        "method.response.header.Content-Type": true
        }
        },
        {
        statusCode: "500",
        responseParameters: {
        "method.response.header.Content-Type": true
        },
        }
        ]
        '''
        result = self._values.get("update_method_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]], result)

    @builtins.property
    def update_request_template(self) -> typing.Optional[builtins.str]:
        '''API Gateway Request Template for the update method.

        This property is required if the ``allowUpdateOperation`` property is set to true.

        :default: - None
        '''
        result = self._values.get("update_request_template")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApiGatewayToDynamoDBProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "ApiGatewayToDynamoDB",
    "ApiGatewayToDynamoDBProps",
]

publication.publish()

def _typecheckingstub__2d19ee8ef37452b3cc026fd476b098d59eff0a90d0cbae8d3a736dc5fc92c0d0(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    additional_create_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_delete_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_read_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_update_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    allow_create_operation: typing.Optional[builtins.bool] = None,
    allow_delete_operation: typing.Optional[builtins.bool] = None,
    allow_read_operation: typing.Optional[builtins.bool] = None,
    allow_update_operation: typing.Optional[builtins.bool] = None,
    api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
    create_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    create_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    create_request_template: typing.Optional[builtins.str] = None,
    create_usage_plan: typing.Optional[builtins.bool] = None,
    delete_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    delete_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    delete_request_template: typing.Optional[builtins.str] = None,
    dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_table_obj: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    read_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    read_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    read_request_template: typing.Optional[builtins.str] = None,
    resource_name: typing.Optional[builtins.str] = None,
    update_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    update_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    update_request_template: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__58088b1487acfcd4ecedaab51f9d82c918ccc6b7505df05d95bb32d30d839ee5(
    *,
    additional_create_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_delete_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_read_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_update_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    allow_create_operation: typing.Optional[builtins.bool] = None,
    allow_delete_operation: typing.Optional[builtins.bool] = None,
    allow_read_operation: typing.Optional[builtins.bool] = None,
    allow_update_operation: typing.Optional[builtins.bool] = None,
    api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
    create_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    create_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    create_request_template: typing.Optional[builtins.str] = None,
    create_usage_plan: typing.Optional[builtins.bool] = None,
    delete_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    delete_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    delete_request_template: typing.Optional[builtins.str] = None,
    dynamo_table_props: typing.Optional[typing.Union[_aws_cdk_aws_dynamodb_ceddda9d.TableProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_table_obj: typing.Optional[_aws_cdk_aws_dynamodb_ceddda9d.Table] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    read_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    read_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    read_request_template: typing.Optional[builtins.str] = None,
    resource_name: typing.Optional[builtins.str] = None,
    update_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    update_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    update_request_template: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
