r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-apigatewayv2websocket-sqs/README.adoc)
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

import aws_cdk.aws_apigatewayv2 as _aws_cdk_aws_apigatewayv2_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_kms as _aws_cdk_aws_kms_ceddda9d
import aws_cdk.aws_logs as _aws_cdk_aws_logs_ceddda9d
import aws_cdk.aws_sqs as _aws_cdk_aws_sqs_ceddda9d
import constructs as _constructs_77d1e7e8


class ApiGatewayV2WebSocketToSqs(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-apigatewayv2websocket-sqs.ApiGatewayV2WebSocketToSqs",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        create_default_route: typing.Optional[builtins.bool] = None,
        custom_route_name: typing.Optional[builtins.str] = None,
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        default_iam_authorization: typing.Optional[builtins.bool] = None,
        default_route_request_template: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        existing_web_socket_api: typing.Optional[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApi] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        web_socket_api_props: typing.Optional[typing.Union[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param create_default_route: Whether to create a $default route. If set to true, then it will use the value supplied with ``defaultRouteRequestTemplate``. At least one of createDefaultRoute or customRouteName must be provided. Default: - false.
        :param custom_route_name: The name of the route that will be sent through WebSocketApiProps.routeSelectionExpression when invoking the WebSocket endpoint. At least one of createDefaultRoute or customRouteName must be provided. Default: - None
        :param dead_letter_queue_props: Optional user provided properties for the dead letter queue. Default: - Default props are used
        :param default_iam_authorization: Add IAM authorization to the $connect path by default. Only set this to false if: 1) If plan to provide an authorizer with the ``$connect`` route; or 2) The API should be open (no authorization) (AWS recommends against deploying unprotected APIs). If an authorizer is specified in connectRouteOptions, this parameter is ignored and no default IAM authorizer will be created Default: - true
        :param default_route_request_template: Optional user provided API Gateway Request Template for the $default route or customRoute (if customRouteName is provided). Default: - construct will create and assign a template with default settings to send messages to Queue.
        :param deploy_dead_letter_queue: Whether to deploy a secondary queue to be used as a dead letter queue. Default: - required field.
        :param enable_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps. Default: - False if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
        :param encryption_key: An optional, imported encryption key to encrypt the SQS Queue with. Default: - None
        :param encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SQS queue with. Default: - None
        :param existing_queue_obj: Existing instance of SQS queue object, providing both this and queueProps will cause an error.
        :param existing_web_socket_api: Existing instance of WebSocket API object, providing both this and webSocketApiProps will cause an error. Default: - None
        :param log_group_props: Optional user-provided props to override the default props for the log group. Default: - Default props are used
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue. Default: - required only if deployDeadLetterQueue = true.
        :param queue_props: Optional - user provided properties to override the default properties for the SQS queue. Providing both this and ``existingQueueObj`` will cause an error. Default: - Default props are used
        :param web_socket_api_props: Optional user-provided props to override the default props for the API Gateway. Default: - Default properties are used.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f37fa6f73e46f6d9868a3a3fba942695c1871f3e14ca3f0c156d343212d4393e)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ApiGatewayV2WebSocketToSqsProps(
            create_default_route=create_default_route,
            custom_route_name=custom_route_name,
            dead_letter_queue_props=dead_letter_queue_props,
            default_iam_authorization=default_iam_authorization,
            default_route_request_template=default_route_request_template,
            deploy_dead_letter_queue=deploy_dead_letter_queue,
            enable_encryption_with_customer_managed_key=enable_encryption_with_customer_managed_key,
            encryption_key=encryption_key,
            encryption_key_props=encryption_key_props,
            existing_queue_obj=existing_queue_obj,
            existing_web_socket_api=existing_web_socket_api,
            log_group_props=log_group_props,
            max_receive_count=max_receive_count,
            queue_props=queue_props,
            web_socket_api_props=web_socket_api_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

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
    @jsii.member(jsii_name="webSocketApi")
    def web_socket_api(self) -> _aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApi:
        return typing.cast(_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApi, jsii.get(self, "webSocketApi"))

    @builtins.property
    @jsii.member(jsii_name="webSocketStage")
    def web_socket_stage(self) -> _aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketStage:
        return typing.cast(_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketStage, jsii.get(self, "webSocketStage"))

    @builtins.property
    @jsii.member(jsii_name="deadLetterQueue")
    def dead_letter_queue(
        self,
    ) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.DeadLetterQueue]:
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.DeadLetterQueue], jsii.get(self, "deadLetterQueue"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-apigatewayv2websocket-sqs.ApiGatewayV2WebSocketToSqsProps",
    jsii_struct_bases=[],
    name_mapping={
        "create_default_route": "createDefaultRoute",
        "custom_route_name": "customRouteName",
        "dead_letter_queue_props": "deadLetterQueueProps",
        "default_iam_authorization": "defaultIamAuthorization",
        "default_route_request_template": "defaultRouteRequestTemplate",
        "deploy_dead_letter_queue": "deployDeadLetterQueue",
        "enable_encryption_with_customer_managed_key": "enableEncryptionWithCustomerManagedKey",
        "encryption_key": "encryptionKey",
        "encryption_key_props": "encryptionKeyProps",
        "existing_queue_obj": "existingQueueObj",
        "existing_web_socket_api": "existingWebSocketApi",
        "log_group_props": "logGroupProps",
        "max_receive_count": "maxReceiveCount",
        "queue_props": "queueProps",
        "web_socket_api_props": "webSocketApiProps",
    },
)
class ApiGatewayV2WebSocketToSqsProps:
    def __init__(
        self,
        *,
        create_default_route: typing.Optional[builtins.bool] = None,
        custom_route_name: typing.Optional[builtins.str] = None,
        dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        default_iam_authorization: typing.Optional[builtins.bool] = None,
        default_route_request_template: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
        enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
        encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
        encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
        existing_web_socket_api: typing.Optional[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApi] = None,
        log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        max_receive_count: typing.Optional[jsii.Number] = None,
        queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
        web_socket_api_props: typing.Optional[typing.Union[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param create_default_route: Whether to create a $default route. If set to true, then it will use the value supplied with ``defaultRouteRequestTemplate``. At least one of createDefaultRoute or customRouteName must be provided. Default: - false.
        :param custom_route_name: The name of the route that will be sent through WebSocketApiProps.routeSelectionExpression when invoking the WebSocket endpoint. At least one of createDefaultRoute or customRouteName must be provided. Default: - None
        :param dead_letter_queue_props: Optional user provided properties for the dead letter queue. Default: - Default props are used
        :param default_iam_authorization: Add IAM authorization to the $connect path by default. Only set this to false if: 1) If plan to provide an authorizer with the ``$connect`` route; or 2) The API should be open (no authorization) (AWS recommends against deploying unprotected APIs). If an authorizer is specified in connectRouteOptions, this parameter is ignored and no default IAM authorizer will be created Default: - true
        :param default_route_request_template: Optional user provided API Gateway Request Template for the $default route or customRoute (if customRouteName is provided). Default: - construct will create and assign a template with default settings to send messages to Queue.
        :param deploy_dead_letter_queue: Whether to deploy a secondary queue to be used as a dead letter queue. Default: - required field.
        :param enable_encryption_with_customer_managed_key: If no key is provided, this flag determines whether the queue is encrypted with a new CMK or an AWS managed key. This flag is ignored if any of the following are defined: queueProps.encryptionMasterKey, encryptionKey or encryptionKeyProps. Default: - False if queueProps.encryptionMasterKey, encryptionKey, and encryptionKeyProps are all undefined.
        :param encryption_key: An optional, imported encryption key to encrypt the SQS Queue with. Default: - None
        :param encryption_key_props: Optional user provided properties to override the default properties for the KMS encryption key used to encrypt the SQS queue with. Default: - None
        :param existing_queue_obj: Existing instance of SQS queue object, providing both this and queueProps will cause an error.
        :param existing_web_socket_api: Existing instance of WebSocket API object, providing both this and webSocketApiProps will cause an error. Default: - None
        :param log_group_props: Optional user-provided props to override the default props for the log group. Default: - Default props are used
        :param max_receive_count: The number of times a message can be unsuccessfully dequeued before being moved to the dead-letter queue. Default: - required only if deployDeadLetterQueue = true.
        :param queue_props: Optional - user provided properties to override the default properties for the SQS queue. Providing both this and ``existingQueueObj`` will cause an error. Default: - Default props are used
        :param web_socket_api_props: Optional user-provided props to override the default props for the API Gateway. Default: - Default properties are used.

        :summary: The properties for the ApiGatewayV2WebSocketToSqs class.
        '''
        if isinstance(dead_letter_queue_props, dict):
            dead_letter_queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**dead_letter_queue_props)
        if isinstance(encryption_key_props, dict):
            encryption_key_props = _aws_cdk_aws_kms_ceddda9d.KeyProps(**encryption_key_props)
        if isinstance(log_group_props, dict):
            log_group_props = _aws_cdk_aws_logs_ceddda9d.LogGroupProps(**log_group_props)
        if isinstance(queue_props, dict):
            queue_props = _aws_cdk_aws_sqs_ceddda9d.QueueProps(**queue_props)
        if isinstance(web_socket_api_props, dict):
            web_socket_api_props = _aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApiProps(**web_socket_api_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b07a17aaa5507b1179984f079be450d3b362ed1531e33a497ba2c57b2236c6f7)
            check_type(argname="argument create_default_route", value=create_default_route, expected_type=type_hints["create_default_route"])
            check_type(argname="argument custom_route_name", value=custom_route_name, expected_type=type_hints["custom_route_name"])
            check_type(argname="argument dead_letter_queue_props", value=dead_letter_queue_props, expected_type=type_hints["dead_letter_queue_props"])
            check_type(argname="argument default_iam_authorization", value=default_iam_authorization, expected_type=type_hints["default_iam_authorization"])
            check_type(argname="argument default_route_request_template", value=default_route_request_template, expected_type=type_hints["default_route_request_template"])
            check_type(argname="argument deploy_dead_letter_queue", value=deploy_dead_letter_queue, expected_type=type_hints["deploy_dead_letter_queue"])
            check_type(argname="argument enable_encryption_with_customer_managed_key", value=enable_encryption_with_customer_managed_key, expected_type=type_hints["enable_encryption_with_customer_managed_key"])
            check_type(argname="argument encryption_key", value=encryption_key, expected_type=type_hints["encryption_key"])
            check_type(argname="argument encryption_key_props", value=encryption_key_props, expected_type=type_hints["encryption_key_props"])
            check_type(argname="argument existing_queue_obj", value=existing_queue_obj, expected_type=type_hints["existing_queue_obj"])
            check_type(argname="argument existing_web_socket_api", value=existing_web_socket_api, expected_type=type_hints["existing_web_socket_api"])
            check_type(argname="argument log_group_props", value=log_group_props, expected_type=type_hints["log_group_props"])
            check_type(argname="argument max_receive_count", value=max_receive_count, expected_type=type_hints["max_receive_count"])
            check_type(argname="argument queue_props", value=queue_props, expected_type=type_hints["queue_props"])
            check_type(argname="argument web_socket_api_props", value=web_socket_api_props, expected_type=type_hints["web_socket_api_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create_default_route is not None:
            self._values["create_default_route"] = create_default_route
        if custom_route_name is not None:
            self._values["custom_route_name"] = custom_route_name
        if dead_letter_queue_props is not None:
            self._values["dead_letter_queue_props"] = dead_letter_queue_props
        if default_iam_authorization is not None:
            self._values["default_iam_authorization"] = default_iam_authorization
        if default_route_request_template is not None:
            self._values["default_route_request_template"] = default_route_request_template
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
        if existing_web_socket_api is not None:
            self._values["existing_web_socket_api"] = existing_web_socket_api
        if log_group_props is not None:
            self._values["log_group_props"] = log_group_props
        if max_receive_count is not None:
            self._values["max_receive_count"] = max_receive_count
        if queue_props is not None:
            self._values["queue_props"] = queue_props
        if web_socket_api_props is not None:
            self._values["web_socket_api_props"] = web_socket_api_props

    @builtins.property
    def create_default_route(self) -> typing.Optional[builtins.bool]:
        '''Whether to create a $default route.

        If set to true, then it will use the value supplied with ``defaultRouteRequestTemplate``.
        At least one of createDefaultRoute or customRouteName must be provided.

        :default: - false.
        '''
        result = self._values.get("create_default_route")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def custom_route_name(self) -> typing.Optional[builtins.str]:
        '''The name of the route that will be sent through WebSocketApiProps.routeSelectionExpression when invoking the WebSocket endpoint. At least one of createDefaultRoute or customRouteName must be provided.

        :default: - None
        '''
        result = self._values.get("custom_route_name")
        return typing.cast(typing.Optional[builtins.str], result)

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
    def default_iam_authorization(self) -> typing.Optional[builtins.bool]:
        '''Add IAM authorization to the $connect path by default.

        Only set this to false if: 1) If plan to provide an authorizer with
        the ``$connect`` route; or 2) The API should be open (no authorization) (AWS recommends against deploying unprotected APIs).

        If an authorizer is specified in connectRouteOptions, this parameter is ignored and no default IAM authorizer will be created

        :default: - true
        '''
        result = self._values.get("default_iam_authorization")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def default_route_request_template(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Optional user provided API Gateway Request Template for the $default route or customRoute (if customRouteName is provided).

        :default: - construct will create and assign a template with default settings to send messages to Queue.
        '''
        result = self._values.get("default_route_request_template")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

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
        '''Existing instance of SQS queue object, providing both this  and queueProps will cause an error.'''
        result = self._values.get("existing_queue_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue], result)

    @builtins.property
    def existing_web_socket_api(
        self,
    ) -> typing.Optional[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApi]:
        '''Existing instance of WebSocket API object, providing both this and webSocketApiProps will cause an error.

        :default: - None
        '''
        result = self._values.get("existing_web_socket_api")
        return typing.cast(typing.Optional[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApi], result)

    @builtins.property
    def log_group_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_logs_ceddda9d.LogGroupProps]:
        '''Optional user-provided props to override the default props for the log group.

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
    def queue_props(self) -> typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps]:
        '''Optional - user provided properties to override the default properties for the SQS queue.

        Providing both this and ``existingQueueObj`` will cause an error.

        :default: - Default props are used
        '''
        result = self._values.get("queue_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_sqs_ceddda9d.QueueProps], result)

    @builtins.property
    def web_socket_api_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApiProps]:
        '''Optional user-provided props to override the default props for the API Gateway.

        :default: - Default properties are used.
        '''
        result = self._values.get("web_socket_api_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApiProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApiGatewayV2WebSocketToSqsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "ApiGatewayV2WebSocketToSqs",
    "ApiGatewayV2WebSocketToSqsProps",
]

publication.publish()

def _typecheckingstub__f37fa6f73e46f6d9868a3a3fba942695c1871f3e14ca3f0c156d343212d4393e(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    create_default_route: typing.Optional[builtins.bool] = None,
    custom_route_name: typing.Optional[builtins.str] = None,
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    default_iam_authorization: typing.Optional[builtins.bool] = None,
    default_route_request_template: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    existing_web_socket_api: typing.Optional[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApi] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    web_socket_api_props: typing.Optional[typing.Union[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b07a17aaa5507b1179984f079be450d3b362ed1531e33a497ba2c57b2236c6f7(
    *,
    create_default_route: typing.Optional[builtins.bool] = None,
    custom_route_name: typing.Optional[builtins.str] = None,
    dead_letter_queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    default_iam_authorization: typing.Optional[builtins.bool] = None,
    default_route_request_template: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    deploy_dead_letter_queue: typing.Optional[builtins.bool] = None,
    enable_encryption_with_customer_managed_key: typing.Optional[builtins.bool] = None,
    encryption_key: typing.Optional[_aws_cdk_aws_kms_ceddda9d.Key] = None,
    encryption_key_props: typing.Optional[typing.Union[_aws_cdk_aws_kms_ceddda9d.KeyProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_queue_obj: typing.Optional[_aws_cdk_aws_sqs_ceddda9d.Queue] = None,
    existing_web_socket_api: typing.Optional[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApi] = None,
    log_group_props: typing.Optional[typing.Union[_aws_cdk_aws_logs_ceddda9d.LogGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    max_receive_count: typing.Optional[jsii.Number] = None,
    queue_props: typing.Optional[typing.Union[_aws_cdk_aws_sqs_ceddda9d.QueueProps, typing.Dict[builtins.str, typing.Any]]] = None,
    web_socket_api_props: typing.Optional[typing.Union[_aws_cdk_aws_apigatewayv2_ceddda9d.WebSocketApiProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
