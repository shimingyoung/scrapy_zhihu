# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from twisted.enterprise import adbapi
#import MySQLdb # pip install mysqlclient
import sqlite3

class ZhihuPipeline(object):
    def process_item(self, item, spider):
        return item

class MysqlTwistedPipeline(object):
    # 采用异步的机制写入mysql
    def __init__(self, dbpool):
        self.dbpool = dbpool
    @classmethod
    def from_settings(cls, settings):
        #dbparms = dict(
        #    host=settings["localhost"],
        #    db=settings["zhihu_db"],
        #    user=settings[""],
        #    passwd=settings[""],
        #    charset='utf8',
        #    cursorclass=MySQLdb.cursors.DictCursor,
        #    use_unicode=True,
        #dbparms = dict(
        filename = "C://TEMP//zhihu//sqlite_db//zhihu.db",
        #      
        #)
        dbpool = adbapi.ConnectionPool("sqlite3", filename, check_same_thread=False)
        return cls(dbpool)
    def process_item(self, item, spider):
        # use twisted mysql
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)  
    def handle_error(self, failure, item, spider):
        print(failure)
    def do_insert(self, cursor, item):
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)