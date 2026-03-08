from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class JobInfo(Base):
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = Column(String(255), nullable=False, comment='职位名称')
    link = Column(String(500), index=True, comment='岗位详情页URL')
    boss_name = Column(String(100), comment='招聘者姓名')
    boss_title = Column(String(100), comment='招聘者职位')
    salary = Column(String(100), comment='薪资范围')
    skills = Column(Text, comment='技能标签')
    experience = Column(String(100), comment='工作经验')
    degree = Column(String(50), comment='学历要求')
    city = Column(String(50), comment='城市')
    area = Column(String(50), comment='区域')
    address = Column(String(50), comment='详细地址')
    company = Column(String(255), comment='公司名称')
    scale = Column(String(100), comment='公司规模')
    welfare = Column(Text, comment='公司福利')

    description = Column(Text, comment='职位描述')
    address_detail = Column(String(255), comment='详细地址')

    created_at = Column(
        DateTime,
        server_default=func.now(),
        comment='创建时间'
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment='最后更新时间'
    )

    LIST_FIELDS = ['skills', 'welfare']  # 定义list字段

    def __init__(self, **kwargs):
        # 预处理 list 字段
        for field in self.LIST_FIELDS:
            if field in kwargs:
                value = kwargs[field]
                if isinstance(value, list):
                    kwargs[field] = ','.join(str(v) for v in value)
                elif not isinstance(value, str):
                    kwargs[field] = ''
        super().__init__(**kwargs)

    __tablename__ = 'job_info'
