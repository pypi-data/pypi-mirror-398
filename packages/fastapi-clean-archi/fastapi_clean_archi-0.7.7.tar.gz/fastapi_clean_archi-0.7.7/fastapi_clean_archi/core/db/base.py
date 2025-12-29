import uuid

from sqlalchemy import Column, Integer, DateTime, func, String, event
from sqlalchemy.orm import as_declarative, declarative_base, declared_attr, Session

Base = declarative_base()


@as_declarative()
class BaseModel(Base):
    __abstract__ = True

    hash_id = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    @declared_attr
    def __tablename__(cls):
        meta = getattr(cls, "Meta", None)
        if meta and hasattr(meta, "db_table"):
            return meta.db_table
        return cls.__name__.lower()

    @declared_attr
    def pk(cls):
        for attr in cls.__dict__.values():
            if isinstance(attr, Column) and attr.primary_key:
                return Column("id", Integer, index=True, unique=True, autoincrement=True)
        return Column("id", Integer, primary_key=True, index=True, unique=True, autoincrement=True)


@event.listens_for(Session, "before_flush")
def generate_hash_id(session, flush_context, instances):
    for instance in session.new:
        if instance.hash_id is None:
            if hasattr(instance, "user_id") and hasattr(instance, "created_at") and instance.created_at is not None:
                hash_id = str(uuid.uuid3(uuid.NAMESPACE_OID, f"{instance.user_id}_{instance.created_at}"))
            else:
                hash_id = str(uuid.uuid4())
            instance.hash_id = hash_id
