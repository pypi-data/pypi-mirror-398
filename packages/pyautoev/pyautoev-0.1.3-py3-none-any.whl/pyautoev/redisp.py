# -*- coding: utf-8 -*-

import redis


def redis_conn(host='localhost', port=6379, db=0):
    pool = redis.ConnectionPool(host=host, port=port, db=db, decode_responses=True)
    rd = redis.Redis(connection_pool=pool)
    return rd


def set_value(host='localhost', db=0, port=6379, key=None, value=None):
    rd = redis_conn(host=host, port=port, db=db)
    rd.set(key, value)
    rd.close()


def get_value(host='localhost', db=0, port=6379, key=None):
    rd = redis_conn(host=host, port=port, db=db)
    result = rd.get(key)
    rd.close()
    return result


def delete_value(host='localhost', db=0, port=6379, key=None):
    rd = redis_conn(host=host, port=port, db=db)
    rd.delete(key)
    rd.close()
