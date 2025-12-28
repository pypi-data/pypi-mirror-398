# -*- coding: utf-8 -*-

__doc__ = """
Feature Redis存储配置
"""


class RedisStoreConfig:
    def __init__(self, host='localhost', port=6379, db=0, password=None, instance_id=None):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._instance_id = instance_id

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def db(self):
        return self._db

    @property
    def password(self):
        return self._password

    @property
    def instance_id(self):
        return self._instance_id

    @property
    def connection_string(self):
        if self.password:
            connection_string = f"{self.host}:{self.port},db={self.db},password={self._password}"
        else:
            connection_string = f"{self.host}:{self.port},db={self.db}"
        return connection_string

    def __repr__(self):
        return f"RedisStoreConfig(host={self.host}, port={self.port}, db={self.db}, instance_id={self.instance_id})"

    def __str__(self):
        return self.__repr__()