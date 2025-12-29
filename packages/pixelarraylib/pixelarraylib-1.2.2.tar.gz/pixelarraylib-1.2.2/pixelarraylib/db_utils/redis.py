import traceback
from typing import List
import redis
import redis.asyncio as aioredis
from pixelarraylib.monitor.feishu import Feishu

feishu_alert = Feishu("devtoolkit服务报警")


class RedisUtils:
    def __init__(self, host, port, password, db):
        """
        description:
            初始化Redis工具类
        parameters:
            host(str): Redis主机地址
            port(int): Redis端口
            password(str): Redis密码
            db(int): Redis数据库编号
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
        )

    def get_redis_client(self):
        """
        description:
            获取Redis客户端对象
        return:
            redis_client(redis.Redis): Redis客户端对象
        """
        return self.redis_client

    def set(self, key, value, expire_seconds=None):
        """
        description:
            设置缓存
        parameters:
            key(str): 缓存键
            value(str): 缓存值
            expire_seconds(int): 缓存过期时间
        return:
            flag(bool): 是否设置成功
        """
        try:
            self.redis_client.set(key, value, ex=expire_seconds)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    def get(self, key, default_value=""):
        """
        description:
            获取缓存
        parameters:
            key(str): 缓存键
            default_value(str): 默认值
        return:
            value(str): 缓存值
        """
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default_value
            return value.decode()
        except Exception as e:
            print(traceback.format_exc())
            return default_value

    def delete(self, key):
        """
        description:
            删除缓存
        parameters:
            key(str): 缓存键
        return:
            flag(bool): 是否删除成功
        """
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    def delete_many(self, keys: List[str]) -> bool:
        """
        description:
            删除多个缓存
        parameters:
            keys(list): 缓存键列表
        return:
            flag(bool): 是否删除成功
        """
        try:
            self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    def set_hash(self, key, field, value, expire_seconds=None):
        """
        description:
            设置哈希表
        parameters:
            key(str): 哈希表键
            field(str): 哈希表字段
            value(str): 哈希表值
            expire_seconds(int, optional): 哈希表过期时间（秒），默认为None表示不过期
        return:
            flag(bool): 是否设置成功
        """
        try:
            self.redis_client.hset(key, field, value)
            if expire_seconds is not None:
                self.redis_client.expire(key, expire_seconds)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    def get_hash(self, key, field):
        """
        description:
            获取哈希表的值
        parameters:
            key(str): 哈希表键
            field(str): 哈希表字段
        return:
            value(str): 哈希表值
        """
        try:
            value = self.redis_client.hget(key, field)
            if value is None:
                return ""
            return value.decode()
        except Exception as e:
            print(traceback.format_exc())
            return ""

    def delete_hash(self, key, field):
        """
        description:
            删除哈希表的值
        parameters:
            key(str): 哈希表键
            field(str): 哈希表字段
        return:
            flag(bool): 是否删除成功
        """
        try:
            self.redis_client.hdel(key, field)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    def list_hash_keys(self, key):
        """
        description:
            获取哈希表的所有键
        parameters:
            key(str): 哈希表键
        return:
            keys(list): 哈希表的键
        """
        try:
            return [key.decode() for key in self.redis_client.hkeys(key)]
        except Exception as e:
            print(traceback.format_exc())
            return []

    def list_keys(self, prefix=""):
        """
        description:
            获取所有以指定前缀开头的键
        parameters:
            prefix(str): 键前缀，默认为空字符串，表示获取所有键
        return:
            keys(list): 键列表
        """
        try:
            # 使用 Redis 的 scan 方法替代 keys，避免大数据量时阻塞
            cursor = 0
            keys = []
            pattern = f"{prefix}*" if prefix else "*"
            while True:
                cursor, batch = self.redis_client.scan(
                    cursor=cursor, match=pattern, count=1000
                )
                keys.extend(batch)
                if cursor == 0:
                    break
            return [key.decode() for key in keys]
        except Exception as e:
            print(traceback.format_exc())
            return []

    def __del__(self):
        """
        description:
            析构函数，关闭Redis连接
        """
        self.redis_client.close()


class RedisUtilsAsync:
    def __init__(self, host, port, password, db):
        self.async_redis_client = aioredis.from_url(
            f"redis://:{password}@{host}:{port}/{db}"
        )

    async def get_async_redis_client(self):
        """
        description:
            获取异步Redis客户端对象
        return:
            async_redis_client(aioredis.Redis): 异步Redis客户端对象
        """
        return self.async_redis_client

    async def set(self, key, value, expire_seconds=None):
        """
        description:
            异步设置缓存
        parameters:
            key(str): 缓存键
            value(str): 缓存值
            expire_seconds(int): 缓存过期时间
        return:
            flag(bool): 是否设置成功
        """
        try:
            await self.async_redis_client.set(key, value, ex=expire_seconds)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    async def get(self, key, default_value=""):
        """
        description:
            异步获取缓存
        parameters:
            key(str): 缓存键
            default_value(str): 默认值
        return:
            value(str): 缓存值
        """
        try:
            value = await self.async_redis_client.get(key)
            if value is None:
                return default_value
            return value.decode()
        except Exception as e:
            print(traceback.format_exc())
            return default_value

    async def delete(self, key):
        """
        description:
            异步删除缓存
        parameters:
            key(str): 缓存键
        return:
            flag(bool): 是否删除成功
        """
        try:
            await self.async_redis_client.delete(key)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    async def delete_many(self, keys: List[str]) -> bool:
        """
        description:
            异步删除多个缓存
        parameters:
            keys(list): 缓存键列表
        return:
            flag(bool): 是否删除成功
        """
        try:
            await self.async_redis_client.delete(*keys)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    async def set_hash(self, key, field, value, expire_seconds=None):
        """
        description:
            异步设置哈希表
        parameters:
            key(str): 哈希表键
            field(str): 哈希表字段
            value(str): 哈希表值
            expire_seconds(int, optional): 哈希表过期时间（秒），默认为None表示不过期
        return:
            flag(bool): 是否设置成功
        """
        try:
            await self.async_redis_client.hset(key, field, value)
            if expire_seconds is not None:
                await self.async_redis_client.expire(key, expire_seconds)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    async def get_hash(self, key, field):
        """
        description:
            异步获取哈希表的值
        parameters:
            key(str): 哈希表键
            field(str): 哈希表字段
        return:
            value(str): 哈希表值
        """
        try:
            value = await self.async_redis_client.hget(key, field)
            if value is None:
                return ""
            return value.decode()
        except Exception as e:
            print(traceback.format_exc())
            return ""

    async def delete_hash(self, key, field):
        """
        description:
            异步删除哈希表的值
        parameters:
            key(str): 哈希表键
            field(str): 哈希表字段
        return:
            flag(bool): 是否删除成功
        """
        try:
            await self.async_redis_client.hdel(key, field)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    async def list_hash_keys(self, key):
        """
        description:
            异步获取哈希表的所有键
        parameters:
            key(str): 哈希表键
        return:
            keys(list): 哈希表的键
        """
        try:
            keys = await self.async_redis_client.hkeys(key)
            return [key.decode() for key in keys]
        except Exception as e:
            print(traceback.format_exc())
            return []

    async def list_keys(self, prefix=""):
        """
        description:
            异步获取所有以指定前缀开头的键
        parameters:
            prefix(str): 键前缀，默认为空字符串，表示获取所有键
        return:
            keys(list): 键列表
        """
        try:
            # 使用 Redis 的 scan 方法替代 keys，避免大数据量时阻塞
            cursor = 0
            keys = []
            pattern = f"{prefix}*" if prefix else "*"
            while True:
                cursor, batch = await self.async_redis_client.scan(
                    cursor=cursor, match=pattern, count=1000
                )
                keys.extend(batch)
                if cursor == 0:
                    break
            return [key.decode() for key in keys]
        except Exception as e:
            print(traceback.format_exc())
            return []

    async def close(self):
        """
        description:
            关闭异步Redis连接
        """
        if self.async_redis_client:
            await self.async_redis_client.close()
