from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column,String,create_engine,Text,Integer,ForeignKey,DateTime,desc,asc
from sqlalchemy.orm import sessionmaker,relationship,scoped_session
from sqlalchemy.ext.declarative import declarative_base
Base=declarative_base()
def get_engine_mysql(host='127.0.0.1',user='test123',pwd='123456',port=3306,database='test',max_overflow=0,pool_size=-1,encoding='utf-8')->sessionmaker:
    engine = create_engine(f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{database}",encoding=encoding, max_overflow=max_overflow, pool_size=pool_size)
    Base.metadata.create_all(engine)
    DBSession = sessionmaker(bind=engine)
    return scoped_session(DBSession)
def get_engine_sqlite(dbPath='test.db')->sessionmaker:
    engine = create_engine(f'sqlite:///{dbPath}', connect_args={'check_same_thread': False}, echo=False)
    Base.metadata.create_all(engine)
    DBSession = sessionmaker(bind=engine)
    return scoped_session(DBSession)
if __name__ == '__main__':
    session=get_engine_mysql()
    print(session)
    session.add()