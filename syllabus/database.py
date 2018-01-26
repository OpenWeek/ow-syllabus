import os

import binascii
from sqlalchemy import create_engine
from sqlalchemy.engine import ResultProxy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from syllabus import get_root_path

database_path = os.path.join(get_root_path(), 'database.sqlite')
engine = create_engine('sqlite:///%s' % database_path, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

current_version = 1


def create_db():
    from syllabus.models.user import User
    change_pwd_bytes = os.urandom(20)
    change_pwd_hex = binascii.hexlify(change_pwd_bytes).decode()
    u = User('admin', 'admin@localhost', hash_password=None, change_password_url=change_pwd_hex)
    db_session.add(u)
    db_session.commit()
    connection = engine.connect()
    connection.execute("PRAGMA main.user_version=%d;" % current_version)


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import syllabus.models.user

    Base.metadata.create_all(bind=engine)
    from syllabus.models.user import User
    users = User.query.all()
    if len(users) == 0:
        create_db()


def update_database():
    connection = engine.connect()
    version = connection.execute("PRAGMA main.user_version;").first()[0]
    if version < current_version:
        print("database version (%d) is outdated, updating database to version %d", current_version)
    if version < 1:
        print("updating to version 1")
        connection.execute("ALTER TABLE users ADD COLUMN right STRING(30);")
    connection.execute("PRAGMA main.user_version=%d;" % current_version)
