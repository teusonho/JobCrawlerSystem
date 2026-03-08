# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from scrapy.exceptions import DropItem
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from .items import JobItem
from .models import Base, JobInfo

class JobcrawlerprojectPipeline:
    def __init__(self, db_uri: str):
        self.db_uri = db_uri
        self.engine = None
        self.Session = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_uri=crawler.settings.get('MYSQL_DATABASE_URI', 'sqlite:///jobs.db')
        )

    def open_spider(self, spider):
        """爬虫启动时初始化数据库连接"""
        try:
            # 创建同步引擎
            self.engine = create_engine(
                self.db_uri,
                echo=False,
                pool_pre_ping=True,  # 自动回收失效连接
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600   # 每小时回收连接（防 MySQL gone away）
            )
            # 创建表（如果不存在）
            Base.metadata.create_all(self.engine)

            # 创建会话工厂
            self.Session = sessionmaker(bind=self.engine)
            spider.logger.info("[JobInfoDbPipeline]数据库连接已建立")
        except Exception as e:
            spider.logger.error(f"[JobInfoDbPipeline]数据库初始化失败:\n{e}")
            raise

    def process_item(self, item, spider):
        """同步保存 item 到数据库"""
        if not isinstance(item, JobItem):
            return item

        session = self.Session()
        try:
            # 转换为模型实例
            job = JobInfo(**dict(item))
            session.add(job)
            session.commit()
            spider.logger.debug(f"[JobInfoDbPipeline]已保存职位: {item.get('name')}")
        except SQLAlchemyError as e:
            session.rollback()
            spider.logger.error(f"[JobInfoDbPipeline]Rollback due to DB error: {e}")
            raise DropItem(f"Database error: {e}")
        except Exception as e:
            session.rollback()
            spider.logger.error(f"[JobInfoDbPipeline]Unexpected error saving item: {e}")
            raise DropItem(f"Unexpected error: {e}")
        finally:
            session.close()

        return item

    def close_spider(self, spider):
        """爬虫结束时关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            spider.logger.info("[JobInfoDbPipeline]数据库连接已关闭")