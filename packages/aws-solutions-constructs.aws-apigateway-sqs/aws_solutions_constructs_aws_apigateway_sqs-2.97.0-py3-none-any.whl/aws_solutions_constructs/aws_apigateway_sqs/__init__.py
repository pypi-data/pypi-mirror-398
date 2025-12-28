r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-apigateway-sqs/README.adoc)
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
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import aws_cdk.aws_sqs as _aws_cdk_aws_sqs_ceddda9d
import constructs as _constructs_77d1e7e8


class ApiGatewayToSqs(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-apigateway-sqs.ApiGatewayToSqs",
):
    '''
    :summary: The ApiGatewayToSqs class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        additional_create_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_delete_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_read_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        allow_create_operation: typing.Optional[builtins.bool] = None,
        allow_delete_operation: typing.Optional[builtins.bool] = None,
        allow_read_operation: typing.Optional[builtins.bool] = None,
        api_gateway_props: typing.Any = None,
        create_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        create_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        create_request_template: typing.Optional[builtins.str] = None,
        create_usage_plan: typing.Optional[builtins.bool] = None,
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        delete_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        delete_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        delete_request_template: typing.Optional[builtins.str] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        message_schema: typing.Optional[typing.Mapping[builtins.str, typing.Union[_aws_cdk_aws_apigateway_ceddda9d.JsonSchema, typing.Dict[builtins.str, typing.Any]]]] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        read_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        read_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        read_request_template: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param additional_create_request_templates: Optional Create Request Templates for content-types other than ``application/json``. Use the ``createRequestTemplate`` property to set the request template for the ``application/json`` content-type. Default: - None
        :param additional_delete_request_templates: Optional Delete request templates for content-types other than ``application/json``. Use the ``deleteRequestTemplate`` property to set the request template for the ``application/json`` content-type. Default: - None
        :param additional_read_request_templates: Optional Read Request Templates for content-types other than ``application/json``. Use the ``readRequestTemplate`` property to set the request template for the ``application/json`` content-type. This property can only be specified if the ``allowReadOperation`` property is not set to false. Default: - None
        :param allow_create_operation: Whether to deploy an API Gateway Method for POST HTTP operations on the queue (i.e. sqs:SendMessage). Default: - false
        :param allow_delete_operation: Whether to deploy an API Gateway Method for HTTP DELETE operations on the queue (i.e. sqs:DeleteMessage). Default: - false
        :param allow_read_operation: Whether to deploy an API Gateway Method for GET HTTP operations on the queue (i.e. sqs:ReceiveMessage). Default: - true
        :param api_gateway_props: Optional - user provided props to override the default props for the API Gateway. Default: - Default properties are used.
        :param create_integration_responses: Optional, custom API Gateway Integration Response for the create method. This property can only be specified if the ``allowCreateOperation`` property is set to true. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param create_method_responses: Optional, custom API Gateway Method Responses for the create action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param create_request_template: API Gateway Request Template for the create method for the default ``application/json`` content-type. This property can only be specified if the ``allowCreateOperation`` property is set to true. Default: - 'Action=SendMessage&MessageBody=$util.urlEncode("$input.body")'
        :param create_usage_plan: Whether to create a Usage Plan attached to the API. Must be true if apiGatewayProps.defaultMethodOptions.apiKeyRequired is true Default: - true (to match legacy behavior)
        :param dead_letter_queue_props: Optional user provided properties for the dead letter queue. Default: - Default props are used
        :param delete_integration_responses: Optional, custom API Gateway Integration Response for the delete method. This property can only be specified if the ``allowDeleteOperation`` property is set to true. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param delete_method_responses: Optional, custom API Gateway Method Responses for the create action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param delete_request_template: API Gateway Request Template for THE delete method for the default ``application/json`` content-type. This property can only be specified if the ``allowDeleteOperation`` property is set to true. Default: - "Action=DeleteMessage&ReceiptHandle=$util.urlEncode($input.params('receiptHandle'))"
        :param deploy_dead_letter_queue: Whether to deploy a secondary queue to be used as a dead letter queue. Default: - required field.
        :param enable_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps. Default: - False if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
        :param encryption_key: An optional, imported encryption key to encrypt the SQS Queue with. Default: - None
        :param encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SQS queue with. Default: - None
        :param existing_queue_obj: Existing instance of SQS queue object, providing both this and queueProps will cause an error. Default: - None
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue. Default: - required only if deployDeadLetterQueue = true.
        :param message_schema: Optional schema to define format of incoming message in API request body. Example: { "application/json": { schema: api.JsonSchemaVersion.DRAFT4, title: 'pollResponse', type: api.JsonSchemaType.OBJECT, required: ['firstProperty', 'antotherProperty'], additionalProperties: false, properties: { firstProperty: { type: api.JsonSchemaType.STRING }, antotherProperty: { type: api.JsonSchemaType.STRING } } } Only relevant for create operation, if allowCreateOperation is not true, then supplying this is an error. Sending this value causes this construct to turn on validation for the request body. Default: - None
        :param queue_props: Optional - user provided properties to override the default properties for the SQS queue. Providing both this and ``existingQueueObj`` will cause an error. Default: - Default props are used
        :param read_integration_responses: Optional, custom API Gateway Integration Response for the read method. This property can only be specified if the ``allowReadOperation`` property is not set to false. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param read_method_responses: Optional, custom API Gateway Method Responses for the create action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param read_request_template: API Gateway Request Template for the read method for the default ``application/json`` content-type. This property can only be specified if the ``allowReadOperation`` property is not set to false. Default: - "Action=ReceiveMessage"

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the ApiGatewayToSqs class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__09ecc354d79c3e48682fe4f327af488b07fbaae3ff1c1533d46af5a4fb29bc03)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ApiGatewayToSqsProps(
            additional_create_request_templates=additional_create_request_templates,
            additional_delete_request_templates=additional_delete_request_templates,
            additional_read_request_templates=additional_read_request_templates,
            allow_create_operation=allow_create_operation,
            allow_delete_operation=allow_delete_operation,
            allow_read_operation=allow_read_operation,
            api_gateway_props=api_gateway_props,
            create_integration_responses=create_integration_responses,
            create_method_responses=create_method_responses,
            create_request_template=create_request_template,
            create_usage_plan=create_usage_plan,
            dead_letter_queue_props=dead_letter_queue_props,
            delete_integration_responses=delete_integration_responses,
            delete_method_responses=delete_method_responses,
            delete_request_template=delete_request_template,
            deploy_dead_letter_queue=deploy_dead_letter_queue,
            enable_encryption_with_customer_managed_key=enable_encryption_with_customer_managed_key,
            encryption_key=encryption_key,
            encryption_key_props=encryption_key_props,
            existing_queue_obj=existing_queue_obj,
            log_group_props=log_group_props,
            max_receive_count=max_receive_count,
            message_schema=message_schema,
            queue_props=queue_props,
            read_integration_responses=read_integration_responses,
            read_method_responses=read_method_responses,
            read_request_template=read_request_template,
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
    @jsii.member(jsii_name="sqsQueue")
    def sqs_queue(self) -> _aws_cdk_aws_sqs_ceddda9d.Queue:
        return typing.cast(_aws_cdk_aws_sqs_ceddda9d.Queue, jsii.get(self, "sqsQueue"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayCloudWatchRole")
    def api_gateway_cloud_watch_role(
        self,
    ) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role]:
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role], jsii.get(self, "apiGatewayCloudWatchRole"))

    @builtins.property
    @jsii.member(jsii_name="deadLetterQueue")
    def dead_letter_queue(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.DeadLetterQueue]:
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.DeadLetterQueue], jsii.get(self, "deadLetterQueue"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-apigateway-sqs.ApiGatewayToSqsProps",
    jsii_struct_bases=[],
    name_mapping={
        "additional_create_request_templates": "additionalCreateRequestTemplates",
        "additional_delete_request_templates": "additionalDeleteRequestTemplates",
        "additional_read_request_templates": "additionalReadRequestTemplates",
        "allow_create_operation": "allowCreateOperation",
        "allow_delete_operation": "allowDeleteOperation",
        "allow_read_operation": "allowReadOperation",
        "api_gateway_props": "apiGatewayProps",
        "create_integration_responses": "createIntegrationResponses",
        "create_method_responses": "createMethodResponses",
        "create_request_template": "createRequestTemplate",
        "create_usage_plan": "createUsagePlan",
        "dead_letter_queue_props": "deadLetterQueueProps",
        "delete_integration_responses": "deleteIntegrationResponses",
        "delete_method_responses": "deleteMethodResponses",
        "delete_request_template": "deleteRequestTemplate",
        "deploy_dead_letter_queue": "deployDeadLetterQueue",
        "enable_encryption_with_customer_managed_key": "enableEncryptionWithCustomerManagedKey",
        "encryption_key": "encryptionKey",
        "encryption_key_props": "encryptionKeyProps",
        "existing_queue_obj": "existingQueueObj",
        "log_group_props": "logGroupProps",
        "max_receive_count": "maxReceiveCount",
        "message_schema": "messageSchema",
        "queue_props": "queueProps",
        "read_integration_responses": "readIntegrationResponses",
        "read_method_responses": "readMethodResponses",
        "read_request_template": "readRequestTemplate",
    },
)
class ApiGatewayToSqsProps:
    def __init__(
        self,
        *,
        additional_create_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_delete_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_read_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        allow_create_operation: typing.Optional[builtins.bool] = None,
        allow_delete_operation: typing.Optional[builtins.bool] = None,
        allow_read_operation: typing.Optional[builtins.bool] = None,
        api_gateway_props: typing.Any = None,
        create_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        create_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        create_request_template: typing.Optional[builtins.str] = None,
        create_usage_plan: typing.Optional[builtins.bool] = None,
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        delete_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        delete_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        delete_request_template: typing.Optional[builtins.str] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        message_schema: typing.Optional[typing.Mapping[builtins.str, typing.Union[_aws_cdk_aws_apigateway_ceddda9d.JsonSchema, typing.Dict[builtins.str, typing.Any]]]] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        read_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        read_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        read_request_template: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param additional_create_request_templates: Optional Create Request Templates for content-types other than ``application/json``. Use the ``createRequestTemplate`` property to set the request template for the ``application/json`` content-type. Default: - None
        :param additional_delete_request_templates: Optional Delete request templates for content-types other than ``application/json``. Use the ``deleteRequestTemplate`` property to set the request template for the ``application/json`` content-type. Default: - None
        :param additional_read_request_templates: Optional Read Request Templates for content-types other than ``application/json``. Use the ``readRequestTemplate`` property to set the request template for the ``application/json`` content-type. This property can only be specified if the ``allowReadOperation`` property is not set to false. Default: - None
        :param allow_create_operation: Whether to deploy an API Gateway Method for POST HTTP operations on the queue (i.e. sqs:SendMessage). Default: - false
        :param allow_delete_operation: Whether to deploy an API Gateway Method for HTTP DELETE operations on the queue (i.e. sqs:DeleteMessage). Default: - false
        :param allow_read_operation: Whether to deploy an API Gateway Method for GET HTTP operations on the queue (i.e. sqs:ReceiveMessage). Default: - true
        :param api_gateway_props: Optional - user provided props to override the default props for the API Gateway. Default: - Default properties are used.
        :param create_integration_responses: Optional, custom API Gateway Integration Response for the create method. This property can only be specified if the ``allowCreateOperation`` property is set to true. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param create_method_responses: Optional, custom API Gateway Method Responses for the create action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param create_request_template: API Gateway Request Template for the create method for the default ``application/json`` content-type. This property can only be specified if the ``allowCreateOperation`` property is set to true. Default: - 'Action=SendMessage&MessageBody=$util.urlEncode("$input.body")'
        :param create_usage_plan: Whether to create a Usage Plan attached to the API. Must be true if apiGatewayProps.defaultMethodOptions.apiKeyRequired is true Default: - true (to match legacy behavior)
        :param dead_letter_queue_props: Optional user provided properties for the dead letter queue. Default: - Default props are used
        :param delete_integration_responses: Optional, custom API Gateway Integration Response for the delete method. This property can only be specified if the ``allowDeleteOperation`` property is set to true. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param delete_method_responses: Optional, custom API Gateway Method Responses for the create action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param delete_request_template: API Gateway Request Template for THE delete method for the default ``application/json`` content-type. This property can only be specified if the ``allowDeleteOperation`` property is set to true. Default: - "Action=DeleteMessage&ReceiptHandle=$util.urlEncode($input.params('receiptHandle'))"
        :param deploy_dead_letter_queue: Whether to deploy a secondary queue to be used as a dead letter queue. Default: - required field.
        :param enable_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps. Default: - False if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
        :param encryption_key: An optional, imported encryption key to encrypt the SQS Queue with. Default: - None
        :param encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SQS queue with. Default: - None
        :param existing_queue_obj: Existing instance of SQS queue object, providing both this and queueProps will cause an error. Default: - None
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue. Default: - required only if deployDeadLetterQueue = true.
        :param message_schema: Optional schema to define format of incoming message in API request body. Example: { "application/json": { schema: api.JsonSchemaVersion.DRAFT4, title: 'pollResponse', type: api.JsonSchemaType.OBJECT, required: ['firstProperty', 'antotherProperty'], additionalProperties: false, properties: { firstProperty: { type: api.JsonSchemaType.STRING }, antotherProperty: { type: api.JsonSchemaType.STRING } } } Only relevant for create operation, if allowCreateOperation is not true, then supplying this is an error. Sending this value causes this construct to turn on validation for the request body. Default: - None
        :param queue_props: Optional - user provided properties to override the default properties for the SQS queue. Providing both this and ``existingQueueObj`` will cause an error. Default: - Default props are used
        :param read_integration_responses: Optional, custom API Gateway Integration Response for the read method. This property can only be specified if the ``allowReadOperation`` property is not set to false. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param read_method_responses: Optional, custom API Gateway Method Responses for the create action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param read_request_template: API Gateway Request Template for the read method for the default ``application/json`` content-type. This property can only be specified if the ``allowReadOperation`` property is not set to false. Default: - "Action=ReceiveMessage"

        :summary: The properties for the ApiGatewayToSqs class.
        '''
        if isinstance(dead_letter_queue_props, dict):
            dead_letter_queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**dead_letter_queue_props)
        if isinstance(encryption_key_props, dict):
            encryption_key_props = _aws_cdk_aws_kms_ceddda9d.KeyProps(**encryption_key_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if isinstance(queue_props, dict):
            queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**queue_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0b4d5e44aa1091822c16f5f2ee960065e35aa980d66f3bc2142bc7d44ed15fde)
            check_type(argname="argument additional_create_request_templates", value=additional_create_request_templates, expected_type=type_hints["additional_create_request_templates"])
            check_type(argname="argument additional_delete_request_templates", value=additional_delete_request_templates, expected_type=type_hints["additional_delete_request_templates"])
            check_type(argname="argument additional_read_request_templates", value=additional_read_request_templates, expected_type=type_hints["additional_read_request_templates"])
            check_type(argname="argument allow_create_operation", value=allow_create_operation, expected_type=type_hints["allow_create_operation"])
            check_type(argname="argument allow_delete_operation", value=allow_delete_operation, expected_type=type_hints["allow_delete_operation"])
            check_type(argname="argument allow_read_operation", value=allow_read_operation, expected_type=type_hints["allow_read_operation"])
            check_type(argname="argument api_gateway_props", value=api_gateway_props, expected_type=type_hints["api_gateway_props"])
            check_type(argname="argument create_integration_responses", value=create_integration_responses, expected_type=type_hints["create_integration_responses"])
            check_type(argname="argument create_method_responses", value=create_method_responses, expected_type=type_hints["create_method_responses"])
            check_type(argname="argument create_request_template", value=create_request_template, expected_type=type_hints["create_request_template"])
            check_type(argname="argument create_usage_plan", value=create_usage_plan, expected_type=type_hints["create_usage_plan"])
            check_type(argname="argument dead_letter_queue_props", value=dead_letter_queue_props, expected_type=type_hints["dead_letter_queue_props"])
            check_type(argname="argument delete_integration_responses", value=delete_integration_responses, expected_type=type_hints["delete_integration_responses"])
            check_type(argname="argument delete_method_responses", value=delete_method_responses, expected_type=type_hints["delete_method_responses"])
            check_type(argname="argument delete_request_template", value=delete_request_template, expected_type=type_hints["delete_request_template"])
            check_type(argname="argument deploy_dead_letter_queue", value=deploy_dead_letter_queue, expected_type=type_hints["deploy_dead_letter_queue"])
            check_type(argname="argument enable_encryption_with_customer_managed_key", value=enable_encryption_with_customer_managed_key, expected_type=type_hints["enable_encryption_with_customer_managed_key"])
            check_type(argname="argument encryption_key", value=encryption_key, expected_type=type_hints["encryption_key"])
            check_type(argname="argument encryption_key_props", value=encryption_key_props, expected_type=type_hints["encryption_key_props"])
            check_type(argname="argument existing_queue_obj", value=existing_queue_obj, expected_type=type_hints["existing_queue_obj"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
            check_type(argname="argument max_receive_count", value=max_receive_count, expected_type=type_hints["max_receive_count"])
            check_type(argname="argument message_schema", value=message_schema, expected_type=type_hints["message_schema"])
            check_type(argname="argument queue_props", value=queue_props, expected_type=type_hints["queue_props"])
            check_type(argname="argument read_integration_responses", value=read_integration_responses, expected_type=type_hints["read_integration_responses"])
            check_type(argname="argument read_method_responses", value=read_method_responses, expected_type=type_hints["read_method_responses"])
            check_type(argname="argument read_request_template", value=read_request_template, expected_type=type_hints["read_request_template"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if additional_create_request_templates is not None:
            self._values["additional_create_request_templates"] = additional_create_request_templates
        if additional_delete_request_templates is not None:
            self._values["additional_delete_request_templates"] = additional_delete_request_templates
        if additional_read_request_templates is not None:
            self._values["additional_read_request_templates"] = additional_read_request_templates
        if allow_create_operation is not None:
            self._values["allow_create_operation"] = allow_create_operation
        if allow_delete_operation is not None:
            self._values["allow_delete_operation"] = allow_delete_operation
        if allow_read_operation is not None:
            self._values["allow_read_operation"] = allow_read_operation
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
        if dead_letter_queue_props is not None:
            self._values["dead_letter_queue_props"] = dead_letter_queue_props
        if delete_integration_responses is not None:
            self._values["delete_integration_responses"] = delete_integration_responses
        if delete_method_responses is not None:
            self._values["delete_method_responses"] = delete_method_responses
        if delete_request_template is not None:
            self._values["delete_request_template"] = delete_request_template
        if deploy_dead_letter_queue is not None:
            self._values["deploy_dead_letter_queue"] = deploy_dead_letter_queue
        if enable_encryption_with_customer_managed_key is not None:
            self._values["enable_encryption_with_customer_managed_key"] = enable_encryption_with_customer_managed_key
        if encryption_key is not None:
            self._values["encryption_key"] = encryption_key
        if encryption_key_props is not None:
            self._values["encryption_key_props"] = encryption_key_props
        if existing_queue_obj is not None:
            self._values["existing_queue_obj"] = existing_queue_obj
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props
        if max_receive_count is not None:
            self._values["max_receive_count"] = max_receive_count
        if message_schema is not None:
            self._values["message_schema"] = message_schema
        if queue_props is not None:
            self._values["queue_props"] = queue_props
        if read_integration_responses is not None:
            self._values["read_integration_responses"] = read_integration_responses
        if read_method_responses is not None:
            self._values["read_method_responses"] = read_method_responses
        if read_request_template is not None:
            self._values["read_request_template"] = read_request_template

    @builtins.property
    def additional_create_request_templates(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Optional Create Request Templates for content-types other than ``application/json``.

        Use the ``createRequestTemplate`` property to set the request template for the ``application/json`` content-type.

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
        This property can only be specified if the ``allowReadOperation`` property is not set to false.

        :default: - None
        '''
        result = self._values.get("additional_read_request_templates")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def allow_create_operation(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy an API Gateway Method for POST HTTP operations on the queue (i.e. sqs:SendMessage).

        :default: - false
        '''
        result = self._values.get("allow_create_operation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def allow_delete_operation(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy an API Gateway Method for HTTP DELETE operations on the queue (i.e. sqs:DeleteMessage).

        :default: - false
        '''
        result = self._values.get("allow_delete_operation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def allow_read_operation(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy an API Gateway Method for GET HTTP operations on the queue (i.e. sqs:ReceiveMessage).

        :default: - true
        '''
        result = self._values.get("allow_read_operation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def api_gateway_props(self) -> typing.Any:
        '''Optional - user provided props to override the default props for the API Gateway.

        :default: - Default properties are used.
        '''
        result = self._values.get("api_gateway_props")
        return typing.cast(typing.Any, result)

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

        This property can only be specified if the ``allowCreateOperation`` property is set to true.

        :default: - 'Action=SendMessage&MessageBody=$util.urlEncode("$input.body")'
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
    def dead_letter_queue_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''Optional user provided properties for the dead letter queue.

        :default: - Default props are used
        '''
        result = self._values.get("dead_letter_queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

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
        result = self._values.get("delete_method_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]], result)

    @builtins.property
    def delete_request_template(self) -> typing.Optional[builtins.str]:
        '''API Gateway Request Template for THE delete method for the default ``application/json`` content-type.

        This property can only be specified if the ``allowDeleteOperation`` property is set to true.

        :default: - "Action=DeleteMessage&ReceiptHandle=$util.urlEncode($input.params('receiptHandle'))"
        '''
        result = self._values.get("delete_request_template")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def deploy_dead_letter_queue(self) -> typing.Optional[builtins.bool]:
        '''Whether to deploy a secondary queue to be used as a dead letter queue.

        :default: - required field.
        '''
        result = self._values.get("deploy_dead_letter_queue")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_encryption_with_customer_managed_key(
        self,
    ) -> typing.Optional[builtins.bool]:
        '''If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key.

        This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps.

        :default: - False if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
        '''
        result = self._values.get("enable_encryption_with_customer_managed_key")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def encryption_key(self) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key]:
        '''An optional, imported encryption key to encrypt the SQS Queue with.

        :default: - None
        '''
        result = self._values.get("encryption_key")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key], result)

    @builtins.property
    def encryption_key_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps]:
        '''Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SQS queue with.

        :default: - None
        '''
        result = self._values.get("encryption_key_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_kms_ceddda9d.KeyProps], result)

    @builtins.property
    def existing_queue_obj(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue]:
        '''Existing instance of SQS queue object, providing both this  and queueProps will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_queue_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue], result)

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
    def max_receive_count(self) -> typing.Optional[jsii.Number]:
        '''The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue.

        :default: - required only if deployDeadLetterQueue = true.
        '''
        result = self._values.get("max_receive_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def message_schema(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, _aws_cdk_aws_apigateway_ceddda9d.JsonSchema]]:
        '''Optional schema to define format of incoming message in API request body.

        Example:
        {
        "application/json": {
        schema: api.JsonSchemaVersion.DRAFT4,
        title: 'pollResponse',
        type: api.JsonSchemaType.OBJECT,
        required: ['firstProperty', 'antotherProperty'],
        additionalProperties: false,
        properties: {
        firstProperty: { type: api.JsonSchemaType.STRING },
        antotherProperty: { type: api.JsonSchemaType.STRING }
        }
        }

        Only relevant for create operation, if allowCreateOperation is not true, then supplying this
        is an error.

        Sending this value causes this construct to turn on validation for the request body.

        :default: - None
        '''
        result = self._values.get("message_schema")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, _aws_cdk_aws_apigateway_ceddda9d.JsonSchema]], result)

    @builtins.property
    def queue_props(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''Optional - user provided properties to override the default properties for the SQS queue.

        Providing both this and ``existingQueueObj`` will cause an error.

        :default: - Default props are used
        '''
        result = self._values.get("queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

    @builtins.property
    def read_integration_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]]:
        '''Optional, custom API Gateway Integration Response for the read method.

        This property can only be specified if the ``allowReadOperation`` property is not set to false.

        :default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        '''
        result = self._values.get("read_integration_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]], result)

    @builtins.property
    def read_method_responses(
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
        result = self._values.get("read_method_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]], result)

    @builtins.property
    def read_request_template(self) -> typing.Optional[builtins.str]:
        '''API Gateway Request Template for the read method for the default ``application/json`` content-type.

        This property can only be specified if the ``allowReadOperation`` property is not set to false.

        :default: - "Action=ReceiveMessage"
        '''
        result = self._values.get("read_request_template")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApiGatewayToSqsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "ApiGatewayToSqs",
    "ApiGatewayToSqsProps",
]

publication.publish()

def _typecheckingstub__09ecc354d79c3e48682fe4f327af488b07fbaae3ff1c1533d46af5a4fb29bc03(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    additional_create_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_delete_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_read_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    allow_create_operation: typing.Optional[builtins.bool] = None,
    allow_delete_operation: typing.Optional[builtins.bool] = None,
    allow_read_operation: typing.Optional[builtins.bool] = None,
    api_gateway_props: typing.Any = None,
    create_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    create_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    create_request_template: typing.Optional[builtins.str] = None,
    create_usage_plan: typing.Optional[builtins.bool] = None,
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    delete_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    delete_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    delete_request_template: typing.Optional[builtins.str] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    message_schema: typing.Optional[typing.Mapping[builtins.str, typing.Union[_aws_cdk_aws_apigateway_ceddda9d.JsonSchema, typing.Dict[builtins.str, typing.Any]]]] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    read_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    read_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    read_request_template: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0b4d5e44aa1091822c16f5f2ee960065e35aa980d66f3bc2142bc7d44ed15fde(
    *,
    additional_create_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_delete_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_read_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    allow_create_operation: typing.Optional[builtins.bool] = None,
    allow_delete_operation: typing.Optional[builtins.bool] = None,
    allow_read_operation: typing.Optional[builtins.bool] = None,
    api_gateway_props: typing.Any = None,
    create_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    create_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    create_request_template: typing.Optional[builtins.str] = None,
    create_usage_plan: typing.Optional[builtins.bool] = None,
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    delete_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    delete_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    delete_request_template: typing.Optional[builtins.str] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    message_schema: typing.Optional[typing.Mapping[builtins.str, typing.Union[_aws_cdk_aws_apigateway_ceddda9d.JsonSchema, typing.Dict[builtins.str, typing.Any]]]] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    read_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    read_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    read_request_template: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
