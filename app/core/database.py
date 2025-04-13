from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings


engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)