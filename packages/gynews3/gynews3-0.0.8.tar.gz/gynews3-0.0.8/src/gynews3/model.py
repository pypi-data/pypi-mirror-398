import os
from datetime import datetime, timedelta
from enum import StrEnum
from sqlmodel import (
    Field,
    SQLModel,
    Session,
    select,
    create_engine as sqlmodel_create_engine,
)
from sqlalchemy.exc import IntegrityError


class LinkType(StrEnum):
    NEWS = "NEWS"
    LOCAL_NEWS = "LOCAL_NEWS"
    BLOG = "BLOG"
    QA = "QA"
    BOARD = "BOARD"
    IT = "IT"
    ELECTRONICS = "ELECTRONICS"


class LinkStatus(StrEnum):
    NO_SUMMARY = "NO_SUMMARY"
    DONE = "DONE"
    FAILED_SUMMARIZATION = "FAILED_SUMMARIZATION"


class Link(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    type: LinkType
    status: LinkStatus = Field(default=LinkStatus.NO_SUMMARY)
    url: str = Field(unique=True)
    title: str | None = None
    content: str | None = None
    summary: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


def create_engine(db_url: str | None = None, create_tables: bool = False):
    from dotenv import load_dotenv

    load_dotenv()

    if db_url is None:
        db_url = os.getenv("GYNEWS3_CONN_URL", "sqlite:///gynews3.db")

    engine = sqlmodel_create_engine(db_url)

    if create_tables:
        SQLModel.metadata.create_all(engine)

    return engine


def create_session(engine):
    return Session(engine)


def save_links(
    session: Session, links: list[Link], ignore_integrity_error: bool = True
):
    try:
        for link in links:
            session.add(link)
        session.commit()
        return
    except IntegrityError as e:
        session.rollback()
        if not ignore_integrity_error:
            raise e

    for link in links:
        try:
            session.add(link)
            session.commit()
        except IntegrityError:
            session.rollback()
            continue


def get_all_links(session: Session):
    statement = select(Link)
    resp = session.exec(statement)
    links = resp.all()

    return links


def get_recent_links(session: Session, offset=0, limit=20, days: int = 7):
    cutoff_date = datetime.now() - timedelta(days=days)
    statement = (
        select(Link)
        .where(Link.created_at >= cutoff_date)
        .where(Link.status == LinkStatus.DONE)
        .offset(offset)
        .limit(limit)
    )
    resp = session.exec(statement)
    links = resp.all()

    return links


def get_unsummarized_links(session: Session):
    statement = select(Link).where(Link.status == LinkStatus.NO_SUMMARY)
    resp = session.exec(statement)
    links = resp.all()

    return links


def save_summarized_link(session: Session, link: Link):
    if link.summary is None or link.summary.strip() == "":
        raise ValueError(
            "Link summary cannot be None or empty when saving summarized link."
        )
    link.status = LinkStatus.DONE
    session.add(link)
    session.commit()
