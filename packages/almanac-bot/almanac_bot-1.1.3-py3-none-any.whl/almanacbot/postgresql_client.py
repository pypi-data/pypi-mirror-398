import datetime
from typing import List

import sqlalchemy
from sqlalchemy import (
    Select,
    and_,
    create_engine,
    extract,
    func,
    insert,
    null,
    or_,
    select,
)
from sqlalchemy.orm import Session

from almanacbot.ephemeris import Ephemeris


class PostgreSQLClient:
    """Class serving as PostgreSQL client"""

    def __init__(
        self,
        user: str,
        password: str,
        hostname: str,
        database: str,
        ephemeris_table: str,
        logging_echo: bool,
    ):
        self.engine = create_engine(
            f"postgresql+psycopg://{user}:{password}@{hostname}/{database}",
            echo=logging_echo,
        )
        self.ephemeris_table: str = ephemeris_table

    def get_today_ephemeris(self) -> List[Ephemeris]:
        """Get all ephemeris entries for today using month+day matching."""
        now = sqlalchemy.func.now()
        query: Select = select(Ephemeris).filter(
            and_(
                extract("MONTH", Ephemeris.date) == extract("MONTH", now),
                extract("DAY", Ephemeris.date) == extract("DAY", now),
            )
        )
        with Session(self.engine) as session:
            ephs: List[Ephemeris] = session.scalars(query).all()
            return ephs

    def get_untweeted_today_ephemeris(self) -> List[Ephemeris]:
        """
        Get ephemeris entries for today that haven't been tweeted yet today.

        Uses month+day matching (handles leap years correctly) and checks
        that last_tweeted_at is either NULL or before today (idempotency).
        """
        now = func.now()
        today_start = func.date_trunc("day", now)

        query: Select = select(Ephemeris).filter(
            and_(
                extract("MONTH", Ephemeris.date) == extract("MONTH", now),
                extract("DAY", Ephemeris.date) == extract("DAY", now),
                or_(
                    Ephemeris.last_tweeted_at.is_(None),
                    Ephemeris.last_tweeted_at < today_start,
                ),
            )
        )
        with Session(self.engine) as session:
            ephs: List[Ephemeris] = session.scalars(query).all()
            return ephs

    def mark_as_tweeted(self, ephemeris_id: int) -> None:
        """Mark an ephemeris entry as tweeted with current UTC timestamp."""
        with Session(self.engine) as session:
            eph = session.get(Ephemeris, ephemeris_id)
            if eph:
                eph.last_tweeted_at = datetime.datetime.now(datetime.timezone.utc)
                session.commit()

    def count_ephemeris(self) -> int:
        with Session(self.engine) as session:
            stmnt = func.count(Ephemeris.id)
            return session.execute(stmnt).scalar()

    def insert_ephemeris(self, eph: Ephemeris):
        with Session(self.engine) as session:
            stmnt = insert(Ephemeris).values(
                date=eph.date,
                text=eph.text,
                location=(
                    sqlalchemy.func.point(eph.location.latitude, eph.location.longitude)
                    if eph.location is not None
                    else null()
                ),
            )
            session.execute(stmnt)
            session.commit()
