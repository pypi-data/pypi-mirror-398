import time
from ast import Dict
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.types import JSON
from sqlmodel import Field, Session, SQLModel, delete, func, select, update

from logis.data_type import DEFAULT_PYDANTIC_MODEL_CONFIG

DATA_DIR = Path(__file__).parent.parent / "data"
assert DATA_DIR.exists()


class Event(SQLModel, table=True):
    __tablename__ = "event"
    id: Optional[int] = Field(
        default=None, primary_key=True, sa_column_kwargs={"autoincrement": True}
    )
    time: float
    type: str
    data: str

    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG

from uuid import uuid4

db_file = f"sqlite:///{DATA_DIR}/test.db"
engine = create_engine(db_file, echo=True)
SQLModel.metadata.create_all(engine)


def test_insert():

    s = Session(bind=engine)

    events = []
    size = 1000000
    for i in range(size):
        event = Event(time=i, type="test", data="test")
        events.append(event)

    start = time.time()
    s.bulk_save_objects(events)
    s.commit()
    end = time.time()
    print(f"insert {size} events cost {end-start} seconds")

    s.close()


def test_select():
    s = Session(bind=engine, close_resets_only=True)
    start = time.time()
    size = s.exec(select(func.count()).where(Event.id < 100000)).first()
    dt1 = time.time() - start
    # close_resets_only=True意味着close未必立即关闭还是有被复用的可能
    s.close()
    print(f"select {size} events cost {dt1} seconds")

    start = time.time()
    tmps = s.query(Event).filter(Event.id < 100000).all()
    dt2 = time.time() - start
    print(f"query {len(tmps)} events cost {dt2} seconds")

    assert dt1 <= dt2
