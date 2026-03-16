# sqlalchemy lets us interact with Postgres DB using python code instead of just raw SQL everyhwehre


from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
import os

# read .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# create the actual connection to Postgres using DB URL
engine = create_engine(DATABASE_URL)

# session is just talking to your DB: open session, do stuff, then close session
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

# base class that all DB models will inherit from
Base = declarative_base()


# function to open DB session, hand it to whoever needs it, and then close it when they are done
def get_db():
    db = SessionLocal()
    try:
        # yield creates geenerator functions (AKA produce sequence of values one at a time) 
        # (so yield pauses function exectuion and saves its state to be resumed from where it left off whenever the next time a value is requested)
        yield db
    finally:
        db.close()

