from typing import List

import sqlalchemy
from sqlalchemy import Select, create_engine, extract, func, insert, null, select
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
        query: Select = select(Ephemeris).filter(
            extract("DOY", Ephemeris.date) == extract("DOY", sqlalchemy.func.now())
        )
        with Session(self.engine) as session:
            ephs: List[Ephemeris] = session.scalars(query).all()
            return ephs

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
