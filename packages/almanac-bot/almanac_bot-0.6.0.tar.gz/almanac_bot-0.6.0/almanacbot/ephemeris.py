import datetime
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import TIMESTAMP, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import UserDefinedType
import sqlalchemy


class Base(DeclarativeBase):
    pass


@dataclass
class Location:
    latitude: float
    longitude: float


class LatLngType(UserDefinedType):
    """
    Custom SQLAlchemy type to handle POINT columns.

    References:

    - https://gist.github.com/kwatch/02b1a5a8899b67df2623
    - https://docs.sqlalchemy.org/en/14/core/custom_types.html#sqlalchemy.types.UserDefinedType  # noqa
    """

    # Can do because we made the Location dataclass hashable
    cache_ok = True

    def get_col_spec(self):
        return "POINT"

    def bind_expression(self, bindvalue):
        return sqlalchemy.func.POINT(bindvalue, type_=self)

    def bind_processor(self, dialect):
        """
        Return function to serialize a Location into a database string literal.
        """

        def process(value: Location | tuple[float, float] | None) -> str | None:
            if value is None:
                return None

            if isinstance(value, tuple):
                value = Location(*value)

            return f"({value.latitude},{value.longitude})"

        return process

    def result_processor(self, dialect, coltype):
        """
        Return function to parse a database string result into Python data type.
        """

        def process(value: str) -> Location | None:
            if value is None:
                return None

            latitude, longitude = value.strip("()").split(",")

            return Location(float(latitude), float(longitude))

        return process


@dataclass
class Ephemeris(Base):
    __tablename__ = "ephemeris"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True))
    text: Mapped[str] = mapped_column(Text)
    location: Mapped[Optional[Location]] = mapped_column(LatLngType, default=None)
