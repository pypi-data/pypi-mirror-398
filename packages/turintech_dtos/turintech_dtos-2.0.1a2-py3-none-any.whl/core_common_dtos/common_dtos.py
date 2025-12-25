# pylint: disable=no-self-argument
# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from datetime import datetime
from typing import Generic, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from pydantic.generics import GenericModel

# Core Source imports
from core_common_data_types.type_definitions import DataModelT, GenericT
from core_utils_file.data_utils import get_current_datetime
from core_utils_file.validators import validate_is_uuid

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["UpdatedAt", "CreatedAt", "DateTimeInfo", "StatusInfo", "ModelId"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                      DTO Models                                                      #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class UpdatedAt(BaseModel):
    """
    Fields to store the update time.
    """

    updated_at: datetime = Field(
        default_factory=get_current_datetime, description="Date and time of information update"
    )


class CreatedAt(BaseModel):
    """
    Fields to store the creation time.
    """

    created_at: datetime = Field(
        default_factory=get_current_datetime, description="Date and time of information creation"
    )


class DateTimeInfo(CreatedAt):
    """
    Fields to store the creation and update time of a DTO.
    """

    updated_at: Optional[datetime] = Field(default=None, description="Date and time of information update")


# -------------------------------------------- Status -------------------------------------------- #


class StatusInfo(UpdatedAt, GenericModel, Generic[GenericT]):
    """
    Base class for all status information DTOs.
    """

    status: GenericT = Field(..., description="Status value")
    status_details: Optional[str] = Field(default=None, description="Status details")


class ModelId(GenericModel, Generic[DataModelT]):
    """
    Data that identifies a data model.
    """

    # type: ignore[return-value]

    uuid: UUID = Field(..., description="Unique ID")

    # Validators
    _validate_uuid = field_validator("uuid")(validate_is_uuid)

    @property
    def id(self) -> str:  # pylint: disable=C0103
        return str(self.uuid)

    @property
    def data_id(self) -> DataModelT:
        return self._generic_type()(**self.dict())  # type: ignore

    @classmethod
    def _generic_type(cls) -> type:
        return cls.__mro__[1]
