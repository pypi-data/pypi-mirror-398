from sqlalchemy import Column,String,create_engine,Text,Integer,ForeignKey,DateTime,Numeric
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import desc,asc,and_,or_,func
import datetime
Base=declarative_base()
#创建数据库表
class Customer(Base):
    __tablename__='customer'
    CUS_ID=Column(Integer,primary_key=True)                             #主键 用户ID
    CUS_PW=Column(String(50))                                           #用户密码
    CUS_NAME=Column(String(50))                                         #用户名
    def __str__(self):
        return 'customer对象 CUS_ID=%d'%self.CUS_ID
class Activity(Base):
    __tablename__ = 'activity'
    ACT_ID=Column(Integer,autoincrement=True,primary_key=True)          #主键活动ID 自增
    ACT_NAME=Column(String(50))                                         #活动名称
    ACT_STIME=Column(DateTime)                                          #开始时间
    ACT_ETIME=Column(DateTime)                                          #结束时间
    ACT_PLACE=Column(String(255))                                       #活动地点
    ACT_CON=Column(String(50))                                          #活动状态  是否能参与
    ACT_PAR=Column(Integer)                                             #活动目前参与人数
    ACT_CAP=Column(Integer)                                             #活动容量 人数上限
    ACT_INFO=Column(Text())                                             #活动信息
    CUS_ID=Column(Integer,ForeignKey(Customer.CUS_ID))                  #外键，活动创建者
    customer=relationship('Customer',backref='activity_customer')       #关联查询
    def __str__(self):
        return 'activity对象 ACT_ID=%d'%self.ACT_ID
    def get_date(self):
        return self.ACT_STIME.date().strftime('%Y{}%m{}%d{}').format('年','月','日')
class P_activity(Base):
    __tablename__ = 'p_activity'
    PAR_ID=Column(Integer,autoincrement=True,primary_key=True)          #主键 报名操作的ID 自增
    ACT_ID=Column(Integer,ForeignKey(Activity.ACT_ID))                  #外键 参与活动的ID
    CUS_ID=Column(Integer,ForeignKey(Customer.CUS_ID))                  #外键 报名的用户ID
    customer = relationship('Customer', backref='p_activity_customer')  #关联查询
    activity=relationship('Activity', backref='p_activity_activity')    #关联查询
    def __str__(self):
        return 'p_activity对象 PAR_ID=%d'%self.PAR_ID
class Comment(Base):
    __tablename__ = 'comment'
    COM_ID=Column(Integer,autoincrement=True,primary_key=True)      #主键 评论ID 自增
    CUS_ID=Column(Integer,ForeignKey(Customer.CUS_ID))              #外键 评论者ID
    customer = relationship('Customer', backref='comment_customer') #关联查询
    ACT_ID=Column(Integer,ForeignKey(Activity.ACT_ID))              #外键 活动ID
    activity = relationship('Activity', backref='comment_activity') #关联查询
    COM_TIME=Column(DateTime)#评论时间
    COM_INFO=Column(Text())#评论内容
#engine = create_engine('mysql+pymysql://alex:123456@192.168.181.128:3306/db_again3',encoding='utf-8')
engine = create_engine('sqlite:///shalong.db', connect_args={'check_same_thread': False},echo=False)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
#更新
a=session.query(Activity).get(Activity.ACT_ID==1)
a.ACT_PAR += 1
session.commit()
#新增
a=Customer(CUS_ID=1234,CUS_NAME='xxx',CUS_PW='122')
session.add(a)
session.commit()
#批量新增
lst=[Customer(CUS_ID=1234,CUS_NAME='xxx1',CUS_PW='122'),
     Customer(CUS_ID=1233,CUS_NAME='xxx2',CUS_PW='122'),
     Customer(CUS_ID=1232,CUS_NAME='xxx3',CUS_PW='122')]
session.add_all(lst)
session.commit()
#批量更新
session.query(Customer).filter(Customer.CUS_NAME=="xxx1").update({'CUS_PW':'111'})
session.commit()
#查询
session.query(Activity).filter(Activity.ACT_ID==1,Activity.ACT_NAME=='xx').order_by(asc(Activity.ACT_ID)).all()
#删除
session.query(Activity).delete(Activity.ACT_ID==1)

'''


func.count()
func.sum()
func.lower()
func.max()
func.extract()
func.abs()
func.row_number()
func.some_function()
func.rank()
func.to_tsvector()
func.random()
func.len()
func.min()
func.percentile_cont()
func.bernoulli()
func.coalesce()
func.bernoulli()
func.avg()
func.current_timestamp()
func.date()


#执行sql
session.execute('select * from table')
session.commit()
session.rollback()

#Top(2)  limit offset
session.query(profile.name).filter(...).first()
session.query(profile.name).filter(...).all()
session.query(profile.name).filter(...).limit(3).offset(2)  
session.query(profile.name).filter(...).all()[2:5]

运算符
== != < > >= <= 
模糊查询 like
session.query(Account).filter(Account.user_name.like('%name%'))
session.query(Account).filter(Account.user_name.like('name%'))
session.query(Account).filter(Account.user_name.like('%name'))

#in_   ~取反
session.query(Account).filter(~Account.title.in_(['Accountant','Engineer'])) 取反
session.query(Account).filter(~Account.id.in_([2000,3000,4000]))

#None is_ isnot
session.query(Account).filter(Account.salary!=None)
session.query(Account).filter(Account.salary.isnot(None))
session.query(Account).filter(Account,salary.is_(None))

逻辑and
session.query(Account).filter(Account.title=='Engineer',Account.salary=3000)
session.query(Account).filter(and_(Account.title=='Engineer',Account.salary=3000))
逻辑or
session.query(Account).filter(or_(Account.title=='Engineer',Account.salary=3000))

分组 group_by order_by
result = session.query(User.gender,func.count(User.id)).group_by(User.gender).all()
for i in result:
    print(i)

having where一样
result = session.query(User.age,func.count(User.id)).group_by(User.age).having(User.age>30).all()
for i in result:
    print(i)

提供子查询 subquery
sub = session.query(User.gender.label('gender'),User.age.label('age')).filter(User.username == 'name7').subquery()
result = session.query(User).filter(User.gender==sub.c.gender ,User.age == sub.c.age)
for i in result:
    print(i.username)

'''

