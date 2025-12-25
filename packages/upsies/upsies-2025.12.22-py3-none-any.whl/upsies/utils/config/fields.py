""":class:`typing.Annotated` types to use for :class:`~.SubsectionBase` fields"""

import typing

import pydantic

from .. import types


def string(*, default, description, secret=False):
    """:class:`str` or :class:`pydantic.SecretStr`"""
    return typing.Annotated[
        pydantic.SecretStr if secret else str,
        pydantic.Field(
            default=default,
            description=description,
        ),
    ]


def boolean(*, default, description):
    """:class:`~.types.Bool`"""
    return typing.Annotated[
        types.Bool,
        pydantic.BeforeValidator(types.Bool),
        pydantic.Field(
            default=default,
            description=description,
        ),
    ]


def integer(*, default, description, min=None, max=None):
    """:class:`~.types.Integer`"""
    Integer = types.Integer(min=min, max=max)
    return typing.Annotated[
        Integer,
        pydantic.BeforeValidator(Integer),
        pydantic.Field(
            default=default,
            description=description,
        ),
    ]


def choice(*, default, options, description, empty_ok=False, case_sensitive=True):
    """:class:`~.types.Choice`"""
    Choice = types.Choice(options=options, empty_ok=empty_ok, case_sensitive=case_sensitive)
    return typing.Annotated[
        Choice,
        pydantic.BeforeValidator(Choice),
        pydantic.Field(
            default=default,
            description=description,
        ),
    ]


def custom(*, cls, default, description):
    """Custom type"""
    return typing.Annotated[
        cls,
        pydantic.BeforeValidator(cls),
        pydantic.Field(
            default=default,
            description=description,
        ),
    ]
