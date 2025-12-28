r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-apigateway-kinesisstreams/README.adoc)
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
import aws_cdk.aws_cloudwatch as _aws_cdk_aws_cloudwatch_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kinesis as _aws_cdk_aws_kinesis_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import constructs as _constructs_77d1e7e8


class ApiGatewayToKinesisStreams(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-apigateway-kinesisstreams.ApiGatewayToKinesisStreams",
):
    '''
    :summary: The ApiGatewayToKinesisStreams class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        additional_put_record_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_put_records_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        create_usage_plan: typing.Optional[builtins.bool] = None,
        existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
        kinesis_stream_props: typing.Optional[typing.Union[_aws_cdk_aws_kinesis_ceddda9d.StreamProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        put_record_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        put_record_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        put_record_request_model: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        put_record_request_template: typing.Optional[builtins.str] = None,
        put_records_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        put_records_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        put_records_request_model: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        put_records_request_template: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param additional_put_record_request_templates: Optional PutRecord Request Templates for content-types other than ``application/json``. Use the ``putRecordRequestTemplate`` property to set the request template for the ``application/json`` content-type. Default: - None
        :param additional_put_records_request_templates: Optional PutRecords Request Templates for content-types other than ``application/json``. Use the ``putRecordsRequestTemplate`` property to set the request template for the ``application/json`` content-type. Default: - None
        :param api_gateway_props: Optional - user provided props to override the default props for the API Gateway. Default: - Default properties are used.
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. Default: - Alarms are created
        :param create_usage_plan: Whether to create a Usage Plan attached to the API. Must be true if apiGatewayProps.defaultMethodOptions.apiKeyRequired is true Default: - true (to match legacy behavior)
        :param existing_stream_obj: Existing instance of Kinesis Stream, providing both this and ``kinesisStreamProps`` will cause an error. Default: - None
        :param kinesis_stream_props: Optional user-provided props to override the default props for the Kinesis Data Stream. Default: - Default properties are used.
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param put_record_integration_responses: Optional, custom API Gateway Integration Response for the PutRecord action. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param put_record_method_responses: Optional, custom API Gateway Method Responses for the PutRecord action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param put_record_request_model: API Gateway request model for the PutRecord action. If not provided, a default one will be created. Default: - {"$schema":"http://json-schema.org/draft-04/schema#","title":"PutRecord proxy single-record payload","type":"object", "required":["data","partitionKey"],"properties":{"data":{"type":"string"},"partitionKey":{"type":"string"}}}
        :param put_record_request_template: API Gateway request template for the PutRecord action. If not provided, a default one will be used. Default: - { "StreamName": "${this.kinesisStream.streamName}", "Data": "$util.base64Encode($input.json('$.data'))", "PartitionKey": "$input.path('$.partitionKey')" }
        :param put_records_integration_responses: Optional, custom API Gateway Integration Response for the PutRecords action. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param put_records_method_responses: Optional, custom API Gateway Method Responses for the PutRecord action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param put_records_request_model: API Gateway request model for the PutRecords action. If not provided, a default one will be created. Default: - {"$schema":"http://json-schema.org/draft-04/schema#","title":"PutRecords proxy payload data","type":"object","required":["records"], "properties":{"records":{"type":"array","items":{"type":"object", "required":["data","partitionKey"],"properties":{"data":{"type":"string"},"partitionKey":{"type":"string"}}}}}}
        :param put_records_request_template: API Gateway request template for the PutRecords action for the default ``application/json`` content-type. If not provided, a default one will be used. Default: - { "StreamName": "${this.kinesisStream.streamName}", "Records": [ #foreach($elem in $input.path('$.records')) { "Data": "$util.base64Encode($elem.data)", "PartitionKey": "$elem.partitionKey"}#if($foreach.hasNext),#end #end ] }

        :access: public
        :since: 1.62.0
        :summary: Constructs a new instance of the ApiGatewayToKinesisStreams class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dc5a8c71642dbf9699f3dea17c6f8251fe9f7558ad898761072bbf3b6ce1b1f3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ApiGatewayToKinesisStreamsProps(
            additional_put_record_request_templates=additional_put_record_request_templates,
            additional_put_records_request_templates=additional_put_records_request_templates,
            api_gateway_props=api_gateway_props,
            create_cloud_watch_alarms=create_cloud_watch_alarms,
            create_usage_plan=create_usage_plan,
            existing_stream_obj=existing_stream_obj,
            kinesis_stream_props=kinesis_stream_props,
            log_group_props=log_group_props,
            put_record_integration_responses=put_record_integration_responses,
            put_record_method_responses=put_record_method_responses,
            put_record_request_model=put_record_request_model,
            put_record_request_template=put_record_request_template,
            put_records_integration_responses=put_records_integration_responses,
            put_records_method_responses=put_records_method_responses,
            put_records_request_model=put_records_request_model,
            put_records_request_template=put_records_request_template,
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
    @jsii.member(jsii_name="kinesisStream")
    def kinesis_stream(self) -> _aws_cdk_aws_kinesis_ceddda9d.Stream:
        return typing.cast(_aws_cdk_aws_kinesis_ceddda9d.Stream, jsii.get(self, "kinesisStream"))

    @builtins.property
    @jsii.member(jsii_name="apiGatewayCloudWatchRole")
    def api_gateway_cloud_watch_role(
        self,
    ) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role]:
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role], jsii.get(self, "apiGatewayCloudWatchRole"))

    @builtins.property
    @jsii.member(jsii_name="cloudwatchAlarms")
    def cloudwatch_alarms(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_cloudwatch_ceddda9d.Alarm]]:
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_cloudwatch_ceddda9d.Alarm]], jsii.get(self, "cloudwatchAlarms"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-apigateway-kinesisstreams.ApiGatewayToKinesisStreamsProps",
    jsii_struct_bases=[],
    name_mapping={
        "additional_put_record_request_templates": "additionalPutRecordRequestTemplates",
        "additional_put_records_request_templates": "additionalPutRecordsRequestTemplates",
        "api_gateway_props": "apiGatewayProps",
        "create_cloud_watch_alarms": "createCloudWatchAlarms",
        "create_usage_plan": "createUsagePlan",
        "existing_stream_obj": "existingStreamObj",
        "kinesis_stream_props": "kinesisStreamProps",
        "log_group_props": "logGroupProps",
        "put_record_integration_responses": "putRecordIntegrationResponses",
        "put_record_method_responses": "putRecordMethodResponses",
        "put_record_request_model": "putRecordRequestModel",
        "put_record_request_template": "putRecordRequestTemplate",
        "put_records_integration_responses": "putRecordsIntegrationResponses",
        "put_records_method_responses": "putRecordsMethodResponses",
        "put_records_request_model": "putRecordsRequestModel",
        "put_records_request_template": "putRecordsRequestTemplate",
    },
)
class ApiGatewayToKinesisStreamsProps:
    def __init__(
        self,
        *,
        additional_put_record_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        additional_put_records_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
        create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
        create_usage_plan: typing.Optional[builtins.bool] = None,
        existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
        kinesis_stream_props: typing.Optional[typing.Union[_aws_cdk_aws_kinesis_ceddda9d.StreamProps, typing.Dict[builtins.str, typing.Any]]] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        put_record_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        put_record_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        put_record_request_model: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        put_record_request_template: typing.Optional[builtins.str] = None,
        put_records_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        put_records_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
        put_records_request_model: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        put_records_request_template: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param additional_put_record_request_templates: Optional PutRecord Request Templates for content-types other than ``application/json``. Use the ``putRecordRequestTemplate`` property to set the request template for the ``application/json`` content-type. Default: - None
        :param additional_put_records_request_templates: Optional PutRecords Request Templates for content-types other than ``application/json``. Use the ``putRecordsRequestTemplate`` property to set the request template for the ``application/json`` content-type. Default: - None
        :param api_gateway_props: Optional - user provided props to override the default props for the API Gateway. Default: - Default properties are used.
        :param create_cloud_watch_alarms: Whether to create recommended CloudWatch alarms. Default: - Alarms are created
        :param create_usage_plan: Whether to create a Usage Plan attached to the API. Must be true if apiGatewayProps.defaultMethodOptions.apiKeyRequired is true Default: - true (to match legacy behavior)
        :param existing_stream_obj: Existing instance of Kinesis Stream, providing both this and ``kinesisStreamProps`` will cause an error. Default: - None
        :param kinesis_stream_props: Optional user-provided props to override the default props for the Kinesis Data Stream. Default: - Default properties are used.
        :param log_group_props: User provided props to override the default props for the CloudWatchLogs LogGroup. Default: - Default props are used
        :param put_record_integration_responses: Optional, custom API Gateway Integration Response for the PutRecord action. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param put_record_method_responses: Optional, custom API Gateway Method Responses for the PutRecord action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param put_record_request_model: API Gateway request model for the PutRecord action. If not provided, a default one will be created. Default: - {"$schema":"http://json-schema.org/draft-04/schema#","title":"PutRecord proxy single-record payload","type":"object", "required":["data","partitionKey"],"properties":{"data":{"type":"string"},"partitionKey":{"type":"string"}}}
        :param put_record_request_template: API Gateway request template for the PutRecord action. If not provided, a default one will be used. Default: - { "StreamName": "${this.kinesisStream.streamName}", "Data": "$util.base64Encode($input.json('$.data'))", "PartitionKey": "$input.path('$.partitionKey')" }
        :param put_records_integration_responses: Optional, custom API Gateway Integration Response for the PutRecords action. Default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        :param put_records_method_responses: Optional, custom API Gateway Method Responses for the PutRecord action. Default: - [ { statusCode: "200", responseParameters: { "method.response.header.Content-Type": true } }, { statusCode: "500", responseParameters: { "method.response.header.Content-Type": true }, } ]
        :param put_records_request_model: API Gateway request model for the PutRecords action. If not provided, a default one will be created. Default: - {"$schema":"http://json-schema.org/draft-04/schema#","title":"PutRecords proxy payload data","type":"object","required":["records"], "properties":{"records":{"type":"array","items":{"type":"object", "required":["data","partitionKey"],"properties":{"data":{"type":"string"},"partitionKey":{"type":"string"}}}}}}
        :param put_records_request_template: API Gateway request template for the PutRecords action for the default ``application/json`` content-type. If not provided, a default one will be used. Default: - { "StreamName": "${this.kinesisStream.streamName}", "Records": [ #foreach($elem in $input.path('$.records')) { "Data": "$util.base64Encode($elem.data)", "PartitionKey": "$elem.partitionKey"}#if($foreach.hasNext),#end #end ] }

        :summary: The properties for the ApiGatewayToKinesisStreamsProps class.
        '''
        if isinstance(api_gateway_props, dict):
            api_gateway_props = _aws_cdk_aws_apigateway_ceddda9d.RestApiProps(**api_gateway_props)
        if isinstance(kinesis_stream_props, dict):
            kinesis_stream_props = _aws_cdk_aws_kinesis_ceddda9d.StreamProps(**kinesis_stream_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if isinstance(put_record_request_model, dict):
            put_record_request_model = _aws_cdk_aws_apigateway_ceddda9d.ModelOptions(**put_record_request_model)
        if isinstance(put_records_request_model, dict):
            put_records_request_model = _aws_cdk_aws_apigateway_ceddda9d.ModelOptions(**put_records_request_model)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c59160af5b6e23e4ab9d93c180702410ea05a860aa79fb331743fb9ea40688b5)
            check_type(argname="argument additional_put_record_request_templates", value=additional_put_record_request_templates, expected_type=type_hints["additional_put_record_request_templates"])
            check_type(argname="argument additional_put_records_request_templates", value=additional_put_records_request_templates, expected_type=type_hints["additional_put_records_request_templates"])
            check_type(argname="argument api_gateway_props", value=api_gateway_props, expected_type=type_hints["api_gateway_props"])
            check_type(argname="argument create_cloud_watch_alarms", value=create_cloud_watch_alarms, expected_type=type_hints["create_cloud_watch_alarms"])
            check_type(argname="argument create_usage_plan", value=create_usage_plan, expected_type=type_hints["create_usage_plan"])
            check_type(argname="argument existing_stream_obj", value=existing_stream_obj, expected_type=type_hints["existing_stream_obj"])
            check_type(argname="argument kinesis_stream_props", value=kinesis_stream_props, expected_type=type_hints["kinesis_stream_props"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
            check_type(argname="argument put_record_integration_responses", value=put_record_integration_responses, expected_type=type_hints["put_record_integration_responses"])
            check_type(argname="argument put_record_method_responses", value=put_record_method_responses, expected_type=type_hints["put_record_method_responses"])
            check_type(argname="argument put_record_request_model", value=put_record_request_model, expected_type=type_hints["put_record_request_model"])
            check_type(argname="argument put_record_request_template", value=put_record_request_template, expected_type=type_hints["put_record_request_template"])
            check_type(argname="argument put_records_integration_responses", value=put_records_integration_responses, expected_type=type_hints["put_records_integration_responses"])
            check_type(argname="argument put_records_method_responses", value=put_records_method_responses, expected_type=type_hints["put_records_method_responses"])
            check_type(argname="argument put_records_request_model", value=put_records_request_model, expected_type=type_hints["put_records_request_model"])
            check_type(argname="argument put_records_request_template", value=put_records_request_template, expected_type=type_hints["put_records_request_template"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if additional_put_record_request_templates is not None:
            self._values["additional_put_record_request_templates"] = additional_put_record_request_templates
        if additional_put_records_request_templates is not None:
            self._values["additional_put_records_request_templates"] = additional_put_records_request_templates
        if api_gateway_props is not None:
            self._values["api_gateway_props"] = api_gateway_props
        if create_cloud_watch_alarms is not None:
            self._values["create_cloud_watch_alarms"] = create_cloud_watch_alarms
        if create_usage_plan is not None:
            self._values["create_usage_plan"] = create_usage_plan
        if existing_stream_obj is not None:
            self._values["existing_stream_obj"] = existing_stream_obj
        if kinesis_stream_props is not None:
            self._values["kinesis_stream_props"] = kinesis_stream_props
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props
        if put_record_integration_responses is not None:
            self._values["put_record_integration_responses"] = put_record_integration_responses
        if put_record_method_responses is not None:
            self._values["put_record_method_responses"] = put_record_method_responses
        if put_record_request_model is not None:
            self._values["put_record_request_model"] = put_record_request_model
        if put_record_request_template is not None:
            self._values["put_record_request_template"] = put_record_request_template
        if put_records_integration_responses is not None:
            self._values["put_records_integration_responses"] = put_records_integration_responses
        if put_records_method_responses is not None:
            self._values["put_records_method_responses"] = put_records_method_responses
        if put_records_request_model is not None:
            self._values["put_records_request_model"] = put_records_request_model
        if put_records_request_template is not None:
            self._values["put_records_request_template"] = put_records_request_template

    @builtins.property
    def additional_put_record_request_templates(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Optional PutRecord Request Templates for content-types other than ``application/json``.

        Use the ``putRecordRequestTemplate`` property to set the request template for the ``application/json`` content-type.

        :default: - None
        '''
        result = self._values.get("additional_put_record_request_templates")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def additional_put_records_request_templates(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Optional PutRecords Request Templates for content-types other than ``application/json``.

        Use the ``putRecordsRequestTemplate`` property to set the request template for the ``application/json`` content-type.

        :default: - None
        '''
        result = self._values.get("additional_put_records_request_templates")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

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
    def create_cloud_watch_alarms(self) -> typing.Optional[builtins.bool]:
        '''Whether to create recommended CloudWatch alarms.

        :default: - Alarms are created
        '''
        result = self._values.get("create_cloud_watch_alarms")
        return typing.cast(typing.Optional[builtins.bool], result)

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
    def existing_stream_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream]:
        '''Existing instance of Kinesis Stream, providing both this and ``kinesisStreamProps`` will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_stream_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream], result)

    @builtins.property
    def kinesis_stream_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.StreamProps]:
        '''Optional user-provided props to override the default props for the Kinesis Data Stream.

        :default: - Default properties are used.
        '''
        result = self._values.get("kinesis_stream_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.StreamProps], result)

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
    def put_record_integration_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]]:
        '''Optional, custom API Gateway Integration Response for the PutRecord action.

        :default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        '''
        result = self._values.get("put_record_integration_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]], result)

    @builtins.property
    def put_record_method_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]]:
        '''Optional, custom API Gateway Method Responses for the PutRecord action.

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
        result = self._values.get("put_record_method_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]], result)

    @builtins.property
    def put_record_request_model(
        self,
    ) -> typing.Optional[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions]:
        '''API Gateway request model for the PutRecord action.

        If not provided, a default one will be created.

        :default:

        - {"$schema":"http://json-schema.org/draft-04/schema#","title":"PutRecord proxy single-record payload","type":"object",
        "required":["data","partitionKey"],"properties":{"data":{"type":"string"},"partitionKey":{"type":"string"}}}
        '''
        result = self._values.get("put_record_request_model")
        return typing.cast(typing.Optional[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions], result)

    @builtins.property
    def put_record_request_template(self) -> typing.Optional[builtins.str]:
        '''API Gateway request template for the PutRecord action.

        If not provided, a default one will be used.

        :default:

        - { "StreamName": "${this.kinesisStream.streamName}", "Data": "$util.base64Encode($input.json('$.data'))",
        "PartitionKey": "$input.path('$.partitionKey')" }
        '''
        result = self._values.get("put_record_request_template")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def put_records_integration_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]]:
        '''Optional, custom API Gateway Integration Response for the PutRecords action.

        :default: - [{statusCode:"200"},{statusCode:"500",responseTemplates:{"text/html":"Error"},selectionPattern:"500"}]
        '''
        result = self._values.get("put_records_integration_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse]], result)

    @builtins.property
    def put_records_method_responses(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]]:
        '''Optional, custom API Gateway Method Responses for the PutRecord action.

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
        result = self._values.get("put_records_method_responses")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse]], result)

    @builtins.property
    def put_records_request_model(
        self,
    ) -> typing.Optional[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions]:
        '''API Gateway request model for the PutRecords action.

        If not provided, a default one will be created.

        :default:

        - {"$schema":"http://json-schema.org/draft-04/schema#","title":"PutRecords proxy payload data","type":"object","required":["records"],
        "properties":{"records":{"type":"array","items":{"type":"object",
        "required":["data","partitionKey"],"properties":{"data":{"type":"string"},"partitionKey":{"type":"string"}}}}}}
        '''
        result = self._values.get("put_records_request_model")
        return typing.cast(typing.Optional[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions], result)

    @builtins.property
    def put_records_request_template(self) -> typing.Optional[builtins.str]:
        '''API Gateway request template for the PutRecords action for the default ``application/json`` content-type.

        If not provided, a default one will be used.

        :default:

        - { "StreamName": "${this.kinesisStream.streamName}", "Records": [ #foreach($elem in $input.path('$.records'))
        { "Data": "$util.base64Encode($elem.data)", "PartitionKey": "$elem.partitionKey"}#if($foreach.hasNext),#end #end ] }
        '''
        result = self._values.get("put_records_request_template")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApiGatewayToKinesisStreamsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "ApiGatewayToKinesisStreams",
    "ApiGatewayToKinesisStreamsProps",
]

publication.publish()

def _typecheckingstub__dc5a8c71642dbf9699f3dea17c6f8251fe9f7558ad898761072bbf3b6ce1b1f3(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    additional_put_record_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_put_records_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    create_usage_plan: typing.Optional[builtins.bool] = None,
    existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
    kinesis_stream_props: typing.Optional[typing.Union[_aws_cdk_aws_kinesis_ceddda9d.StreamProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    put_record_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    put_record_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    put_record_request_model: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    put_record_request_template: typing.Optional[builtins.str] = None,
    put_records_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    put_records_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    put_records_request_model: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    put_records_request_template: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c59160af5b6e23e4ab9d93c180702410ea05a860aa79fb331743fb9ea40688b5(
    *,
    additional_put_record_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    additional_put_records_request_templates: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    api_gateway_props: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.RestApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
    create_cloud_watch_alarms: typing.Optional[builtins.bool] = None,
    create_usage_plan: typing.Optional[builtins.bool] = None,
    existing_stream_obj: typing.Optional[_aws_cdk_aws_kinesis_ceddda9d.Stream] = None,
    kinesis_stream_props: typing.Optional[typing.Union[_aws_cdk_aws_kinesis_ceddda9d.StreamProps, typing.Dict[builtins.str, typing.Any]]] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    put_record_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    put_record_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    put_record_request_model: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    put_record_request_template: typing.Optional[builtins.str] = None,
    put_records_integration_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.IntegrationResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    put_records_method_responses: typing.Optional[typing.Sequence[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.MethodResponse, typing.Dict[builtins.str, typing.Any]]]] = None,
    put_records_request_model: typing.Optional[typing.Union[_aws_cdk_aws_apigateway_ceddda9d.ModelOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    put_records_request_template: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
