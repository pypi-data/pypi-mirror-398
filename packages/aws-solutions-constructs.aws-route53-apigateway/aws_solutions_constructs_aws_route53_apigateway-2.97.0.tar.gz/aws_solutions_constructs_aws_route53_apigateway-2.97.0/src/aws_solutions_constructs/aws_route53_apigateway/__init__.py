r'''
Documentation for this pattern can be found [here](https://github.com/awslabs/aws-solutions-constructs/blob/main/source/patterns/%40aws-solutions-constructs/aws-route53-apigateway/README.adoc)
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
import aws_cdk.aws_certificatemanager as _aws_cdk_aws_certificatemanager_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_route53 as _aws_cdk_aws_route53_ceddda9d
import constructs as _constructs_77d1e7e8


class Route53ToApiGateway(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@aws-solutions-constructs/aws-route53-apigateway.Route53ToApiGateway",
):
    '''
    :summary: The Route53ToApiGateway class.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        existing_api_gateway_interface: _aws_cdk_aws_apigateway_ceddda9d.IRestApi,
        existing_certificate_interface: _aws_cdk_aws_certificatemanager_ceddda9d.ICertificate,
        public_api: builtins.bool,
        existing_hosted_zone_interface: typing.Optional[_aws_cdk_aws_route53_ceddda9d.IHostedZone] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        private_hosted_zone_props: typing.Any = None,
    ) -> None:
        '''
        :param scope: - represents the scope for all the resources.
        :param id: - this is a a scope-unique id.
        :param existing_api_gateway_interface: The existing API Gateway instance that will be protected with the Route 53 hosted zone. Default: - None
        :param existing_certificate_interface: An existing AWS Certificate Manager certificate for your custom domain name. Default: - None
        :param public_api: Whether to create a public or private API. This value has implications for the VPC, the type of Hosted Zone and the Application Load Balancer
        :param existing_hosted_zone_interface: Existing Public or Private Hosted Zone. If a Private Hosted Zone, must exist in the same VPC specified in existingVpc Default: - None
        :param existing_vpc: An existing VPC. If an existing Private Hosted Zone is provided, this value must be the VPC associated with those resources. Default: - None
        :param private_hosted_zone_props: Optional custom properties for a new Private Hosted Zone. Cannot be specified for a public API. Cannot specify a VPC, it will use the VPC in existingVpc or the VPC created by the construct. Providing both this and existingHostedZoneInterface is an error. Default: - None

        :access: public
        :since: 0.8.0
        :summary: Constructs a new instance of the Route53ToApiGateway class.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__271d9cfc9de165c5b68e8e993a6f6d5836736061fed1ce2b5a8b506cbddc8a36)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = Route53ToApiGatewayProps(
            existing_api_gateway_interface=existing_api_gateway_interface,
            existing_certificate_interface=existing_certificate_interface,
            public_api=public_api,
            existing_hosted_zone_interface=existing_hosted_zone_interface,
            existing_vpc=existing_vpc,
            private_hosted_zone_props=private_hosted_zone_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="apiGateway")
    def api_gateway(self) -> _aws_cdk_aws_apigateway_ceddda9d.RestApi:
        return typing.cast(_aws_cdk_aws_apigateway_ceddda9d.RestApi, jsii.get(self, "apiGateway"))

    @builtins.property
    @jsii.member(jsii_name="certificate")
    def certificate(self) -> _aws_cdk_aws_certificatemanager_ceddda9d.ICertificate:
        return typing.cast(_aws_cdk_aws_certificatemanager_ceddda9d.ICertificate, jsii.get(self, "certificate"))

    @builtins.property
    @jsii.member(jsii_name="hostedZone")
    def hosted_zone(self) -> _aws_cdk_aws_route53_ceddda9d.IHostedZone:
        return typing.cast(_aws_cdk_aws_route53_ceddda9d.IHostedZone, jsii.get(self, "hostedZone"))

    @builtins.property
    @jsii.member(jsii_name="vpc")
    def vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], jsii.get(self, "vpc"))


@jsii.data_type(
    jsii_type="@aws-solutions-constructs/aws-route53-apigateway.Route53ToApiGatewayProps",
    jsii_struct_bases=[],
    name_mapping={
        "existing_api_gateway_interface": "existingApiGatewayInterface",
        "existing_certificate_interface": "existingCertificateInterface",
        "public_api": "publicApi",
        "existing_hosted_zone_interface": "existingHostedZoneInterface",
        "existing_vpc": "existingVpc",
        "private_hosted_zone_props": "privateHostedZoneProps",
    },
)
class Route53ToApiGatewayProps:
    def __init__(
        self,
        *,
        existing_api_gateway_interface: _aws_cdk_aws_apigateway_ceddda9d.IRestApi,
        existing_certificate_interface: _aws_cdk_aws_certificatemanager_ceddda9d.ICertificate,
        public_api: builtins.bool,
        existing_hosted_zone_interface: typing.Optional[_aws_cdk_aws_route53_ceddda9d.IHostedZone] = None,
        existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
        private_hosted_zone_props: typing.Any = None,
    ) -> None:
        '''The properties for the Route53ToApiGateway class.

        :param existing_api_gateway_interface: The existing API Gateway instance that will be protected with the Route 53 hosted zone. Default: - None
        :param existing_certificate_interface: An existing AWS Certificate Manager certificate for your custom domain name. Default: - None
        :param public_api: Whether to create a public or private API. This value has implications for the VPC, the type of Hosted Zone and the Application Load Balancer
        :param existing_hosted_zone_interface: Existing Public or Private Hosted Zone. If a Private Hosted Zone, must exist in the same VPC specified in existingVpc Default: - None
        :param existing_vpc: An existing VPC. If an existing Private Hosted Zone is provided, this value must be the VPC associated with those resources. Default: - None
        :param private_hosted_zone_props: Optional custom properties for a new Private Hosted Zone. Cannot be specified for a public API. Cannot specify a VPC, it will use the VPC in existingVpc or the VPC created by the construct. Providing both this and existingHostedZoneInterface is an error. Default: - None
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ec5598551728f414e7a92cd2186b8e66e67a4774facc241466eb967775aedb36)
            check_type(argname="argument existing_api_gateway_interface", value=existing_api_gateway_interface, expected_type=type_hints["existing_api_gateway_interface"])
            check_type(argname="argument existing_certificate_interface", value=existing_certificate_interface, expected_type=type_hints["existing_certificate_interface"])
            check_type(argname="argument public_api", value=public_api, expected_type=type_hints["public_api"])
            check_type(argname="argument existing_hosted_zone_interface", value=existing_hosted_zone_interface, expected_type=type_hints["existing_hosted_zone_interface"])
            check_type(argname="argument existing_vpc", value=existing_vpc, expected_type=type_hints["existing_vpc"])
            check_type(argname="argument private_hosted_zone_props", value=private_hosted_zone_props, expected_type=type_hints["private_hosted_zone_props"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "existing_api_gateway_interface": existing_api_gateway_interface,
            "existing_certificate_interface": existing_certificate_interface,
            "public_api": public_api,
        }
        if existing_hosted_zone_interface is not None:
            self._values["existing_hosted_zone_interface"] = existing_hosted_zone_interface
        if existing_vpc is not None:
            self._values["existing_vpc"] = existing_vpc
        if private_hosted_zone_props is not None:
            self._values["private_hosted_zone_props"] = private_hosted_zone_props

    @builtins.property
    def existing_api_gateway_interface(
        self,
    ) -> _aws_cdk_aws_apigateway_ceddda9d.IRestApi:
        '''The existing API Gateway instance that will be protected with the Route 53 hosted zone.

        :default: - None
        '''
        result = self._values.get("existing_api_gateway_interface")
        assert result is not None, "Required property 'existing_api_gateway_interface' is missing"
        return typing.cast(_aws_cdk_aws_apigateway_ceddda9d.IRestApi, result)

    @builtins.property
    def existing_certificate_interface(
        self,
    ) -> _aws_cdk_aws_certificatemanager_ceddda9d.ICertificate:
        '''An existing AWS Certificate Manager certificate for your custom domain name.

        :default: - None
        '''
        result = self._values.get("existing_certificate_interface")
        assert result is not None, "Required property 'existing_certificate_interface' is missing"
        return typing.cast(_aws_cdk_aws_certificatemanager_ceddda9d.ICertificate, result)

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
    def existing_vpc(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc]:
        '''An existing VPC.

        If an existing Private Hosted Zone is provided,
        this value must be the VPC associated with those resources.

        :default: - None
        '''
        result = self._values.get("existing_vpc")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc], result)

    @builtins.property
    def private_hosted_zone_props(self) -> typing.Any:
        '''Optional custom properties for a new Private Hosted Zone.

        Cannot be specified for a
        public API. Cannot specify a VPC, it will use the VPC in existingVpc or the VPC created by the construct.
        Providing both this and existingHostedZoneInterface is an error.

        :default: - None
        '''
        result = self._values.get("private_hosted_zone_props")
        return typing.cast(typing.Any, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Route53ToApiGatewayProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "Route53ToApiGateway",
    "Route53ToApiGatewayProps",
]

publication.publish()

def _typecheckingstub__271d9cfc9de165c5b68e8e993a6f6d5836736061fed1ce2b5a8b506cbddc8a36(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    existing_api_gateway_interface: _aws_cdk_aws_apigateway_ceddda9d.IRestApi,
    existing_certificate_interface: _aws_cdk_aws_certificatemanager_ceddda9d.ICertificate,
    public_api: builtins.bool,
    existing_hosted_zone_interface: typing.Optional[_aws_cdk_aws_route53_ceddda9d.IHostedZone] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    private_hosted_zone_props: typing.Any = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ec5598551728f414e7a92cd2186b8e66e67a4774facc241466eb967775aedb36(
    *,
    existing_api_gateway_interface: _aws_cdk_aws_apigateway_ceddda9d.IRestApi,
    existing_certificate_interface: _aws_cdk_aws_certificatemanager_ceddda9d.ICertificate,
    public_api: builtins.bool,
    existing_hosted_zone_interface: typing.Optional[_aws_cdk_aws_route53_ceddda9d.IHostedZone] = None,
    existing_vpc: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.IVpc] = None,
    private_hosted_zone_props: typing.Any = None,
) -> None:
    """Type checking stubs"""
    pass
