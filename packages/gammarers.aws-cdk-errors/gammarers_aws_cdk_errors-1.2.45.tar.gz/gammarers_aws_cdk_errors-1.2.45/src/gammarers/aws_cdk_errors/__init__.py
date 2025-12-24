r'''
# AWS CDK Errors
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


class DeprecatedParameterUsageError(
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-cdk-errors.DeprecatedParameterUsageError",
):
    def __init__(
        self,
        parameter_name: builtins.str,
        message: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param parameter_name: -
        :param message: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ba5cdc23ea904c835138a694794585f306c3d952baa21ac5e16b0442f1fa7b2c)
            check_type(argname="argument parameter_name", value=parameter_name, expected_type=type_hints["parameter_name"])
            check_type(argname="argument message", value=message, expected_type=type_hints["message"])
        jsii.create(self.__class__, self, [parameter_name, message])

    @builtins.property
    @jsii.member(jsii_name="message")
    def message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "message"))

    @message.setter
    def message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__07653c8255f086f7aed5c0fb543cd58f30b7bf3af7777d1b2ff89eab043faaf5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "message", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9120114b9bbda4d5675230be5acf0f1b95e226a70a5da867fc0dbed1dffe500a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]


class InvalidHostingBucketDomainFormatError(
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-cdk-errors.InvalidHostingBucketDomainFormatError",
):
    def __init__(
        self,
        buket_name: builtins.str,
        message: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param buket_name: -
        :param message: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1890486e5c202b2bf94160306fd028a55885ac6c6dcbce3ca951c4a77cbf6d23)
            check_type(argname="argument buket_name", value=buket_name, expected_type=type_hints["buket_name"])
            check_type(argname="argument message", value=message, expected_type=type_hints["message"])
        jsii.create(self.__class__, self, [buket_name, message])

    @builtins.property
    @jsii.member(jsii_name="message")
    def message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "message"))

    @message.setter
    def message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a953e1228728eb1c24b1e9f28c892d5632fc4e73236e757b79516beaf86a57e4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "message", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c20f318d55439e664368cc4795fb7a2a837e1457ef4aeaed3cdc0120e705e499)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]


class InvalidHostingBucketDomainLabeFormatError(
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-cdk-errors.InvalidHostingBucketDomainLabeFormatError",
):
    def __init__(
        self,
        buket_name: builtins.str,
        message: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param buket_name: -
        :param message: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ae0c73edda8d0f1ddf76c9ebbf119f53f972cccf9ac3b4ec4a293f6606b4b8b4)
            check_type(argname="argument buket_name", value=buket_name, expected_type=type_hints["buket_name"])
            check_type(argname="argument message", value=message, expected_type=type_hints["message"])
        jsii.create(self.__class__, self, [buket_name, message])

    @builtins.property
    @jsii.member(jsii_name="message")
    def message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "message"))

    @message.setter
    def message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a7fc2d920e4a954e98e0760d15347c7db704d94c4331f6680cfb2ca41c4b9d44)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "message", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c731b9b00f9de14fc884e4962df8128c22f98daab7cbfb548bfb45b8fc5b9a82)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]


class InvalidInternalDefinitionParameterError(
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-cdk-errors.InvalidInternalDefinitionParameterError",
):
    def __init__(
        self,
        parameter_name: builtins.str,
        message: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param parameter_name: -
        :param message: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6d0ddf75dc7f98949d02fb0a98cdf16e296f25e273f36fe24c83b4864e85399b)
            check_type(argname="argument parameter_name", value=parameter_name, expected_type=type_hints["parameter_name"])
            check_type(argname="argument message", value=message, expected_type=type_hints["message"])
        jsii.create(self.__class__, self, [parameter_name, message])

    @builtins.property
    @jsii.member(jsii_name="message")
    def message(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "message"))

    @message.setter
    def message(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a03cbfd4503b92f8c124dcc073ac18ed32fa62efce9954780d4f484e0ebf7b6a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "message", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f4db2dd7384a1c93b54c61f2dc6574fbced6c8ac07b4df021879fb254b0b30a9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "DeprecatedParameterUsageError",
    "InvalidHostingBucketDomainFormatError",
    "InvalidHostingBucketDomainLabeFormatError",
    "InvalidInternalDefinitionParameterError",
]

publication.publish()

def _typecheckingstub__ba5cdc23ea904c835138a694794585f306c3d952baa21ac5e16b0442f1fa7b2c(
    parameter_name: builtins.str,
    message: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__07653c8255f086f7aed5c0fb543cd58f30b7bf3af7777d1b2ff89eab043faaf5(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9120114b9bbda4d5675230be5acf0f1b95e226a70a5da867fc0dbed1dffe500a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1890486e5c202b2bf94160306fd028a55885ac6c6dcbce3ca951c4a77cbf6d23(
    buket_name: builtins.str,
    message: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a953e1228728eb1c24b1e9f28c892d5632fc4e73236e757b79516beaf86a57e4(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c20f318d55439e664368cc4795fb7a2a837e1457ef4aeaed3cdc0120e705e499(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ae0c73edda8d0f1ddf76c9ebbf119f53f972cccf9ac3b4ec4a293f6606b4b8b4(
    buket_name: builtins.str,
    message: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a7fc2d920e4a954e98e0760d15347c7db704d94c4331f6680cfb2ca41c4b9d44(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c731b9b00f9de14fc884e4962df8128c22f98daab7cbfb548bfb45b8fc5b9a82(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6d0ddf75dc7f98949d02fb0a98cdf16e296f25e273f36fe24c83b4864e85399b(
    parameter_name: builtins.str,
    message: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a03cbfd4503b92f8c124dcc073ac18ed32fa62efce9954780d4f484e0ebf7b6a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f4db2dd7384a1c93b54c61f2dc6574fbced6c8ac07b4df021879fb254b0b30a9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass
