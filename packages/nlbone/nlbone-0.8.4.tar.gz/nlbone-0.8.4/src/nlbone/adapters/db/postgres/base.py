from sqlalchemy.orm import declarative_base, registry

Base = declarative_base()
mapper_registry = registry(metadata=Base.metadata)
