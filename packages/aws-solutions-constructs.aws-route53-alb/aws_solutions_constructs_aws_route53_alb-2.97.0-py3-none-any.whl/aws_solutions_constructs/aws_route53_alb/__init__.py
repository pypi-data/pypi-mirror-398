r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-route53-alb/README.adoc)
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
import aws_cdk.aws_route53 as _aws_cdk_aws_route53_ceddda9d
import aws_cdk.aws_s3 as _aws_cdk_aws_s3_ceddda9d
import constructs as _constructs_77d1e7e8


class Route53ToAlb(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-route53-alb.Route53ToAlb",
):
    '''
    :summary: Configures a Route53 Hosted Zone to route to an Application Load Balancer
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        public_api: builtins.bool,
        alb_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_hosted_zone_interface: typing.Optional[_aws_cdk_aws_route53_ceddda9d.IHostedZone] = None,
        existing_load_balancer_obj: typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        load_balancer_props: typing.Any = None,
        log_alb_access_logs: typing.Optional[builtins.bool] = None,
        private_hosted_zone_props: typing.Any = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param public_api: Whether to create a public or private API. This value has implications for the VPC, the type of Hosted Zone and the Application Load Balancer
        :param alb_logging_bucket_props: Optional properties to customize the bucket used to store the ALB Access Logs. Supplying this and setting logAccessLogs to false is an error. Default: - none
        :param existing_hosted_zone_interface: Existing Public or Private Hosted Zone. If a Private Hosted Zone, must exist in the same VPC specified in existingVpc Default: - None
        :param existing_load_balancer_obj: An existing Application Load Balancer. Providing both this and loadBalancerProps is an error. This ALB must exist in the same VPC specified in existingVPC Default: - None
        :param existing_vpc: An existing VPC. Providing both this and vpcProps is an error. If an existingAlb or existing Private Hosted Zone is provided, this value must be the VPC associated with those resources. Default: - None
        :param load_balancer_props: Custom properties for a new ALB. Providing both this and existingLoadBalancerObj is an error. These properties cannot include a VPC. Default: - None
        :param log_alb_access_logs: Whether to turn on Access Logs for the Application Load Balancer. Uses an S3 bucket with associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param private_hosted_zone_props: Custom properties for a new Private Hosted Zone. Cannot be specified for a public API. Cannot specify a VPC Default: - None
        :param vpc_props: Custom properties for a new VPC. Providing both this and existingVpc is an error. If an existingAlb or existing Private Hosted Zone is provided, those already exist in a VPC so this value cannot be provided. Default: - None

        :access: public
        :summary: Constructs a new instance of the Route53ToAlb class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c74334ab8edf2c3f82e7e52dfbde8d9327f0f5a5b10fbdc9522b565f09184b0b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = Route53ToAlbProps(
            public_api=public_api,
            alb_logging_bucket_props=alb_logging_bucket_props,
            existing_hosted_zone_interface=existing_hosted_zone_interface,
            existing_load_balancer_obj=existing_load_balancer_obj,
            existing_vpc=existing_vpc,
            load_balancer_props=load_balancer_props,
            log_alb_access_logs=log_alb_access_logs,
            private_hosted_zone_props=private_hosted_zone_props,
            vpc_props=vpc_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="hostedZone")
    def hosted_zone(self) -> _aws_cdk_aws_route53_ceddda9d.IHostedZone:
        return typing.cast(_aws_cdk_aws_route53_ceddda9d.IHostedZone, jsii.get(self, "hostedZone"))

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
    jsii_type="@aws-solutions-constructs/aws-route53-alb.Route53ToAlbProps",
    jsii_struct_bases=[],
    name_mapping={
        "public_api": "publicApi",
        "alb_logging_bucket_props": "albLoggingBucketProps",
        "existing_hosted_zone_interface": "existingHostedZoneInterface",
        "existing_load_balancer_obj": "existingLoadBalancerObj",
        "existing_vpc": "existingVpc",
        "load_balancer_props": "loadBalancerProps",
        "log_alb_access_logs": "logAlbAccessLogs",
        "private_hosted_zone_props": "privateHostedZoneProps",
        "vpc_props": "vpcProps",
    },
)
class Route53ToAlbProps:
    def __init__(
        self,
        *,
        public_api: builtins.bool,
        alb_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
        existing_hosted_zone_interface: typing.Optional[_aws_cdk_aws_route53_ceddda9d.IHostedZone] = None,
        existing_load_balancer_obj: typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        load_balancer_props: typing.Any = None,
        log_alb_access_logs: typing.Optional[builtins.bool] = None,
        private_hosted_zone_props: typing.Any = None,
        vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param public_api: Whether to create a public or private API. This value has implications for the VPC, the type of Hosted Zone and the Application Load Balancer
        :param alb_logging_bucket_props: Optional properties to customize the bucket used to store the ALB Access Logs. Supplying this and setting logAccessLogs to false is an error. Default: - none
        :param existing_hosted_zone_interface: Existing Public or Private Hosted Zone. If a Private Hosted Zone, must exist in the same VPC specified in existingVpc Default: - None
        :param existing_load_balancer_obj: An existing Application Load Balancer. Providing both this and loadBalancerProps is an error. This ALB must exist in the same VPC specified in existingVPC Default: - None
        :param existing_vpc: An existing VPC. Providing both this and vpcProps is an error. If an existingAlb or existing Private Hosted Zone is provided, this value must be the VPC associated with those resources. Default: - None
        :param load_balancer_props: Custom properties for a new ALB. Providing both this and existingLoadBalancerObj is an error. These properties cannot include a VPC. Default: - None
        :param log_alb_access_logs: Whether to turn on Access Logs for the Application Load Balancer. Uses an S3 bucket with associated storage costs. Enabling Access Logging is a best practice. Default: - true
        :param private_hosted_zone_props: Custom properties for a new Private Hosted Zone. Cannot be specified for a public API. Cannot specify a VPC Default: - None
        :param vpc_props: Custom properties for a new VPC. Providing both this and existingVpc is an error. If an existingAlb or existing Private Hosted Zone is provided, those already exist in a VPC so this value cannot be provided. Default: - None
        '''
        if isinstance(alb_logging_bucket_props, dict):
            alb_logging_bucket_props = _aws_cdk_aws_s3_ceddda9d.BucketProps(**alb_logging_bucket_props)
        if isinstance(vpc_props, dict):
            vpc_props = _aws_cdk_aws_ec2_ceddda9d.VpcProps(**vpc_props)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__99406f9599a239b14998eeeabcaea056cdaa34629036e63c2c5f956421fc9217)
            check_type(argname="argument public_api", value=public_api, expected_type=type_hints["public_api"])
            check_type(argname="argument alb_logging_bucket_props", value=alb_logging_bucket_props, expected_type=type_hints["alb_logging_bucket_props"])
            check_type(argname="argument existing_hosted_zone_interface", value=existing_hosted_zone_interface, expected_type=type_hints["existing_hosted_zone_interface"])
            check_type(argname="argument existing_load_balancer_obj", value=existing_load_balancer_obj, expected_type=type_hints["existing_load_balancer_obj"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument load_balancer_props", value=load_balancer_props, expected_type=type_hints["load_balancer_props"])
            check_type(argname="argument log_alb_access_logs", value=log_alb_access_logs, expected_type=type_hints["log_alb_access_logs"])
            check_type(argname="argument private_hosted_zone_props", value=private_hosted_zone_props, expected_type=type_hints["private_hosted_zone_props"])
            check_type(argname="argument vpc_props", value=vpc_props, expected_type=type_hints["vpc_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "public_api": public_api,
        }
        if alb_logging_bucket_props is not None:
            self._values["alb_logging_bucket_props"] = alb_logging_bucket_props
        if existing_hosted_zone_interface is not None:
            self._values["existing_hosted_zone_interface"] = existing_hosted_zone_interface
        if existing_load_balancer_obj is not None:
            self._values["existing_load_balancer_obj"] = existing_load_balancer_obj
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if load_balancer_props is not None:
            self._values["load_balancer_props"] = load_balancer_props
        if log_alb_access_logs is not None:
            self._values["log_alb_access_logs"] = log_alb_access_logs
        if private_hosted_zone_props is not None:
            self._values["private_hosted_zone_props"] = private_hosted_zone_props
        if vpc_props is not None:
            self._values["vpc_props"] = vpc_props

    @builtins.property
    def public_api(self) -> builtins.bool:
        '''Whether to create a public or private API.

        This value has implications
        for the VPC, the type of Hosted Zone and the Application Load Balancer
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
    def existing_hosted_zone_interface(
        self,
    ) -> typing.Optional[_aws_cdk_aws_route53_ceddda9d.IHostedZone]:
        '''Existing Public or Private Hosted Zone.

        If a Private Hosted Zone, must
        exist in the same VPC specified in existingVpc

        :default: - None
        '''
        result = self._values.get("existing_hosted_zone_interface")
        return typing.cast(typing.Optional[_aws_cdk_aws_route53_ceddda9d.IHostedZone], result)

    @builtins.property
    def existing_load_balancer_obj(
        self,
    ) -> typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer]:
        '''An existing Application Load Balancer.

        Providing both this and loadBalancerProps
        is an error. This ALB must exist in the same VPC specified in existingVPC

        :default: - None
        '''
        result = self._values.get("existing_load_balancer_obj")
        return typing.cast(typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer], result)

    @builtins.property
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC.

        Providing both this and vpcProps is an error. If an existingAlb or existing
        Private Hosted Zone is provided, this value must be the VPC associated with those resources.

        :default: - None
        '''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def load_balancer_props(self) -> typing.Any:
        '''Custom properties for a new ALB.

        Providing both this and existingLoadBalancerObj
        is an error. These properties cannot include a VPC.

        :default: - None
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
    def private_hosted_zone_props(self) -> typing.Any:
        '''Custom properties for a new Private Hosted Zone.

        Cannot be specified for a
        public API. Cannot specify a VPC

        :default: - None
        '''
        result = self._values.get("private_hosted_zone_props")
        return typing.cast(typing.Any, result)

    @builtins.property
    def vpc_props(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps]:
        '''Custom properties for a new VPC.

        Providing both this and existingVpc is
        an error. If an existingAlb or existing Private Hosted Zone is provided, those
        already exist in a VPC so this value cannot be provided.

        :default: - None
        '''
        result = self._values.get("vpc_props")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.VpcProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Route53ToAlbProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "Route53ToAlb",
    "Route53ToAlbProps",
]

publication.publish()

def _typecheckingstub__c74334ab8edf2c3f82e7e52dfbde8d9327f0f5a5b10fbdc9522b565f09184b0b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    public_api: builtins.bool,
    alb_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_hosted_zone_interface: typing.Optional[_aws_cdk_aws_route53_ceddda9d.IHostedZone] = None,
    existing_load_balancer_obj: typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    load_balancer_props: typing.Any = None,
    log_alb_access_logs: typing.Optional[builtins.bool] = None,
    private_hosted_zone_props: typing.Any = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__99406f9599a239b14998eeeabcaea056cdaa34629036e63c2c5f956421fc9217(
    *,
    public_api: builtins.bool,
    alb_logging_bucket_props: typing.Optional[typing.Union[_aws_cdk_aws_s3_ceddda9d.BucketProps, typing.Dict[builtins.str, typing.Any]]] = None,
    existing_hosted_zone_interface: typing.Optional[_aws_cdk_aws_route53_ceddda9d.IHostedZone] = None,
    existing_load_balancer_obj: typing.Optional[_aws_cdk_aws_elasticloadbalancingv2_ceddda9d.ApplicationLoadBalancer] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    load_balancer_props: typing.Any = None,
    log_alb_access_logs: typing.Optional[builtins.bool] = None,
    private_hosted_zone_props: typing.Any = None,
    vpc_props: typing.Optional[typing.Union[_aws_cdk_aws_ec2_ceddda9d.VpcProps, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
