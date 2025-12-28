r'''
# AWS Resource Naming
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


@jsii.data_type(
    jsii_type="@gammarers/aws-resource-naming.ResourceAutoNaming",
    jsii_struct_bases=[],
    name_mapping={"type": "type"},
)
class ResourceAutoNaming:
    def __init__(self, *, type: "ResourceNamingType") -> None:
        '''
        :param type: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__28a02cc4583d76f3b0ceec83bb5e1ca2058c297411271cbd1600630d3d3d653c)
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "type": type,
        }

    @builtins.property
    def type(self) -> "ResourceNamingType":
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast("ResourceNamingType", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceAutoNaming(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@gammarers/aws-resource-naming.ResourceDefaultNaming",
    jsii_struct_bases=[],
    name_mapping={"type": "type"},
)
class ResourceDefaultNaming:
    def __init__(self, *, type: "ResourceNamingType") -> None:
        '''
        :param type: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__57fa6963424c8053c6ca770b74abe39433f08e92d66cd14d915200de0b3692a3)
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "type": type,
        }

    @builtins.property
    def type(self) -> "ResourceNamingType":
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast("ResourceNamingType", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceDefaultNaming(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(jsii_type="@gammarers/aws-resource-naming.ResourceNamingType")
class ResourceNamingType(enum.Enum):
    DEFAULT = "DEFAULT"
    AUTO = "AUTO"
    CUSTOM = "CUSTOM"


__all__ = [
    "ResourceAutoNaming",
    "ResourceDefaultNaming",
    "ResourceNamingType",
]

publication.publish()

def _typecheckingstub__28a02cc4583d76f3b0ceec83bb5e1ca2058c297411271cbd1600630d3d3d653c(
    *,
    type: ResourceNamingType,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__57fa6963424c8053c6ca770b74abe39433f08e92d66cd14d915200de0b3692a3(
    *,
    type: ResourceNamingType,
) -> None:
    """Type checking stubs"""
    pass
