r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-alb-lambda/README.adoc)
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
import aws_cdk.aws_elasticloadbalancingv2 as _aws_cdk_aws_elasticloadbalancingv2_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import constructs as _constructs_77d1e7e8


class AlbToLambda(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-alb-lambda.AlbToLambda",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        public_api: builtins.bool,
        alb_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_load_balancer_obj: typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        listener_props: typing.Any = None,
        load_balancer_props: typing.Any = None,
        log_alb_access_logs: typing.Optional[builtins.bool] = None,
        rule_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.AddRuleProps, typing.Dict[builtins.str, typing.Any]]] = None,
        target_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param public_api: Whether the construct is deploying a private or public API. This has implications for the VPC and ALB.
        :param alb_logging_bucket_props: Optional properties to customize the bucket used to store the ALB Access Logs. Supplying this and setting logAccessLogs to false is an error. Default: - none
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_load_balancer_obj: Existing Application Load Balancer to incorporate into the construct architecture. Providing both this and loadBalancerProps is an error. The VPC containing this loadBalancer must match the VPC provided in existingVpc. Default: - none
        :param existing_vpc: An existing VPC in which to deploy the construct. Providing both this and vpcProps is an error. If the client provides an existing load balancer and/or existing Private Hosted Zone, those constructs must exist in this VPC. Default: - none
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param listener_props: Props to define the listener. Must be provided when adding the listener to an ALB (eg - when creating the alb), may not be provided when adding a second target to an already established listener. When provided, must include either a certificate or protocol: HTTP Default: - none
        :param load_balancer_props: Optional custom properties for a new loadBalancer. Providing both this and existingLoadBalancer is an error. This cannot specify a VPC, it will use the VPC in existingVpc or the VPC created by the construct. Default: - none
        :param log_alb_access_logs: Whether to turn on Access Logs for the Application Load Balancer. Uses an S3 bucket with associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param rule_props: Rules for directing traffic to the target being created. May not be specified for the first listener added to an ALB, and must be specified for the second target added to a listener. Add a second target by instantiating this construct a second time and providing the existingAlb from the first instantiation. Default: - none
        :param target_props: Optional custom properties for a new target group. While this is a standard attribute of props for ALB constructs, there are few pertinent properties for a Lambda target. Default: - none
        :param vpc_props: Optional custom properties for a VPC the construct will create. This VPC will be used by the new ALB and any Private Hosted Zone the construct creates (that's why loadBalancerProps and privateHostedZoneProps can't include a VPC). Providing both this and existingVpc is an error. Default: - none
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__47c84aa1f4e57804c1df1fde7ad6e0004815a921333c77f39bdcc7d529fd6cf7)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = AlbToLambdaProps(
            public_api=public_api,
            alb_logging_bucket_props=alb_logging_bucket_props,
            existing_lambda_obj=existing_lambda_obj,
            existing_load_balancer_obj=existing_load_balancer_obj,
            existing_vpc=existing_vpc,
            lambda_function_props=lambda_function_props,
            listener_props=listener_props,
            load_balancer_props=load_balancer_props,
            log_alb_access_logs=log_alb_access_logs,
            rule_props=rule_props,
            target_props=target_props,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "lambdaFunction"))

    @builtins.property
    @jsii.member(jsii_name="listener")
    def listener(
        self,
    ) -> _aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationListener:
        return typing.cast(_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationListener, jsii.get(self, "listener"))

    @builtins.property
    @jsii.member(jsii_name="loadBalancer")
    def load_balancer(
        self,
    ) -> _aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer:
        return typing.cast(_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer, jsii.get(self, "loadBalancer"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> _aws_cdk_aws_ec2_ceddda9d.IVpc:
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IVpc, jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-alb-lambda.AlbToLambdaProps",
    jsii_struct_bases=[],
    name_mapping={
        "public_api": "publicApi",
        "alb_logging_bucket_props": "albLoggingBucketProps",
        "existing_lambda_obj": "existingLambdaObj",
        "existing_load_balancer_obj": "existingLoadBalancerObj",
        "existing_vpc": "existingVpc",
        "lambda_function_props": "lambdaFunctionProps",
        "listener_props": "listenerProps",
        "load_balancer_props": "loadBalancerProps",
        "log_alb_access_logs": "logAlbAccessLogs",
        "rule_props": "ruleProps",
        "target_props": "targetProps",
        "vpc_props": "vpcProps",
    },
)
class AlbToLambdaProps:
    def __init__(
        self,
        *,
        public_api: builtins.bool,
        alb_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
        existing_load_balancer_obj: typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
        listener_props: typing.Any = None,
        load_balancer_props: typing.Any = None,
        log_alb_access_logs: typing.Optional[builtins.bool] = None,
        rule_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.AddRuleProps, typing.Dict[builtins.str, typing.Any]]] = None,
        target_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param public_api: Whether the construct is deploying a private or public API. This has implications for the VPC and ALB.
        :param alb_logging_bucket_props: Optional properties to customize the bucket used to store the ALB Access Logs. Supplying this and setting logAccessLogs to false is an error. Default: - none
        :param existing_lambda_obj: Optional - instance of an existing Lambda Function object, providing both this and ``lambdaFunctionProps`` will cause an error. Default: - None
        :param existing_load_balancer_obj: Existing Application Load Balancer to incorporate into the construct architecture. Providing both this and loadBalancerProps is an error. The VPC containing this loadBalancer must match the VPC provided in existingVpc. Default: - none
        :param existing_vpc: An existing VPC in which to deploy the construct. Providing both this and vpcProps is an error. If the client provides an existing load balancer and/or existing Private Hosted Zone, those constructs must exist in this VPC. Default: - none
        :param lambda_function_props: Optional - user provided props to override the default props for the Lambda function. Providing both this and ``existingLambdaObj`` is an error. Default: - Default props are used
        :param listener_props: Props to define the listener. Must be provided when adding the listener to an ALB (eg - when creating the alb), may not be provided when adding a second target to an already established listener. When provided, must include either a certificate or protocol: HTTP Default: - none
        :param load_balancer_props: Optional custom properties for a new loadBalancer. Providing both this and existingLoadBalancer is an error. This cannot specify a VPC, it will use the VPC in existingVpc or the VPC created by the construct. Default: - none
        :param log_alb_access_logs: Whether to turn on Access Logs for the Application Load Balancer. Uses an S3 bucket with associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param rule_props: Rules for directing traffic to the target being created. May not be specified for the first listener added to an ALB, and must be specified for the second target added to a listener. Add a second target by instantiating this construct a second time and providing the existingAlb from the first instantiation. Default: - none
        :param target_props: Optional custom properties for a new target group. While this is a standard attribute of props for ALB constructs, there are few pertinent properties for a Lambda target. Default: - none
        :param vpc_props: Optional custom properties for a VPC the construct will create. This VPC will be used by the new ALB and any Private Hosted Zone the construct creates (that's why loadBalancerProps and privateHostedZoneProps can't include a VPC). Providing both this and existingVpc is an error. Default: - none
        '''
        if isinstance(alb_logging_bucket_props, dict):
            alb_logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**alb_logging_bucket_props)
        if isinstance(lambda_function_props, dict):
            lambda_function_props = _aws_cdk_aws_lambda_ceddda9d.FunctionProps(**lambda_function_props)
        if isinstance(rule_props, dict):
            rule_props = _aws_cdk_aws_elasticloadbalancingv2_ceddda9d.AddRuleProps(**rule_props)
        if isinstance(target_props, dict):
            target_props = _aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroupProps(**target_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2177c773c0a9d19ffa971091d405b8bfede89e769ab8b482aa58382b6fc4c3ed)
            check_type(argname="argument public_api", value=public_api, expected_type=type_hints["public_api"])
            check_type(argname="argument alb_logging_bucket_props", value=alb_logging_bucket_props, expected_type=type_hints["alb_logging_bucket_props"])
            check_type(argname="argument existing_lambda_obj", value=existing_lambda_obj, expected_type=type_hints["existing_lambda_obj"])
            check_type(argname="argument existing_load_balancer_obj", value=existing_load_balancer_obj, expected_type=type_hints["existing_load_balancer_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument lambda_function_props", value=lambda_function_props, expected_type=type_hints["lambda_function_props"])
            check_type(argname="argument listener_props", value=listener_props, expected_type=type_hints["listener_props"])
            check_type(argname="argument load_balancer_props", value=load_balancer_props, expected_type=type_hints["load_balancer_props"])
            check_type(argname="argument log_alb_access_logs", value=log_alb_access_logs, expected_type=type_hints["log_alb_access_logs"])
            check_type(argname="argument rule_props", value=rule_props, expected_type=type_hints["rule_props"])
            check_type(argname="argument target_props", value=target_props, expected_type=type_hints["target_props"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "public_api": public_api,
        }
        if alb_logging_bucket_props is not None:
            self._values["alb_logging_bucket_props"] = alb_logging_bucket_props
        if existing_lambda_obj is not None:
            self._values["existing_lambda_obj"] = existing_lambda_obj
        if existing_load_balancer_obj is not None:
            self._values["existing_load_balancer_obj"] = existing_load_balancer_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if lambda_function_props is not None:
            self._values["lambda_function_props"] = lambda_function_props
        if listener_props is not None:
            self._values["listener_props"] = listener_props
        if load_balancer_props is not None:
            self._values["load_balancer_props"] = load_balancer_props
        if log_alb_access_logs is not None:
            self._values["log_alb_access_logs"] = log_alb_access_logs
        if rule_props is not None:
            self._values["rule_props"] = rule_props
        if target_props is not None:
            self._values["target_props"] = target_props
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def public_api(self) -> builtins.bool:
        '''Whether the construct is deploying a private or public API.

        This has implications for the VPC and ALB.
        '''
        result = self._values.get("public_api")
        assert result is not None, "Required property 'public_api' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def alb_logging_bucket_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps]:
        '''Optional properties to customize the bucket used to store the ALB Access Logs.

        Supplying this and setting logAccessLogs to false is an error.

        :default: - none
        '''
        result = self._values.get("alb_logging_bucket_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_s3_ceddda9d.BucketProps], result)

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
    def existing_load_balancer_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer]:
        '''Existing Application Load Balancer to incorporate into the construct architecture.

        Providing both this and loadBalancerProps is an
        error. The VPC containing this loadBalancer must match the VPC provided in existingVpc.

        :default: - none
        '''
        result = self._values.get("existing_load_balancer_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer], result)

    @builtins.property
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC in which to deploy the construct.

        Providing both this and
        vpcProps is an error. If the client provides an existing load balancer and/or
        existing Private Hosted Zone, those constructs must exist in this VPC.

        :default: - none
        '''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def lambda_function_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps]:
        '''Optional - user provided props to override the default props for the Lambda function.

        Providing both this and ``existingLambdaObj`` is an error.

        :default: - Default props are used
        '''
        result = self._values.get("lambda_function_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_lambda_ceddda9d.FunctionProps], result)

    @builtins.property
    def listener_props(self) -> typing.Any:
        '''Props to define the listener.

        Must be provided when adding the listener
        to an ALB (eg - when creating the alb), may not be provided when adding
        a second target to an already established listener. When provided, must include
        either a certificate or protocol: HTTP

        :default: - none
        '''
        result = self._values.get("listener_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def load_balancer_props(self) -> typing.Any:
        '''Optional custom properties for a new loadBalancer.

        Providing both this and
        existingLoadBalancer is an error. This cannot specify a VPC, it will use the VPC
        in existingVpc or the VPC created by the construct.

        :default: - none
        '''
        result = self._values.get("load_balancer_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def log_alb_access_logs(self) -> typing.Optional[builtins.bool]:
        '''Whether to turn on Access Logs for the Application Load Balancer.

        Uses an S3 bucket
        with associated storage costs. Enabling Access Logging is a best practice.

        :default: - true
        '''
        result = self._values.get("log_alb_access_logs")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def rule_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.AddRuleProps]:
        '''Rules for directing traffic to the target being created.

        May not be specified
        for the first listener added to an ALB, and must be specified for the second
        target added to a listener. Add a second target by instantiating this construct a
        second time and providing the existingAlb from the first instantiation.

        :default: - none
        '''
        result = self._values.get("rule_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.AddRuleProps], result)

    @builtins.property
    def target_props(
        self,
    ) -> typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroupProps]:
        '''Optional custom properties for a new target group.

        While this is a standard
        attribute of props for ALB constructs, there are few pertinent properties for a Lambda target.

        :default: - none
        '''
        result = self._values.get("target_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroupProps], result)

    @builtins.property
    def vpc_props(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps]:
        '''Optional custom properties for a VPC the construct will create.

        This VPC will
        be used by the new ALB and any Private Hosted Zone the construct creates (that's
        why loadBalancerProps and privateHostedZoneProps can't include a VPC). Providing
        both this and existingVpc is an error.

        :default: - none
        '''
        result = self._values.get("vpc_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AlbToLambdaProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "AlbToLambda",
    "AlbToLambdaProps",
]

publication.publish()

def _typecheckingstub__47c84aa1f4e57804c1df1fde7ad6e0004815a921333c77f39bdcc7d529fd6cf7(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    public_api: builtins.bool,
    alb_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_load_balancer_obj: typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    listener_props: typing.Any = None,
    load_balancer_props: typing.Any = None,
    log_alb_access_logs: typing.Optional[builtins.bool] = None,
    rule_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.AddRuleProps, typing.Dict[builtins.str, typing.Any]]] = None,
    target_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2177c773c0a9d19ffa971091d405b8bfede89e769ab8b482aa58382b6fc4c3ed(
    *,
    public_api: builtins.bool,
    alb_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_lambda_obj: typing.Optional[_aws_cdk_aws_lambda_ceddda9d.Function] = None,
    existing_load_balancer_obj: typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    lambda_function_props: typing.Optional[typing.Union[_aws_cdk_aws_lambda_ceddda9d.FunctionProps, typing.Dict[builtins.str, typing.Any]]] = None,
    listener_props: typing.Any = None,
    load_balancer_props: typing.Any = None,
    log_alb_access_logs: typing.Optional[builtins.bool] = None,
    rule_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.AddRuleProps, typing.Dict[builtins.str, typing.Any]]] = None,
    target_props: typing.Optional[typing.Union[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationTargetGroupProps, typing.Dict[builtins.str, typing.Any]]] = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
