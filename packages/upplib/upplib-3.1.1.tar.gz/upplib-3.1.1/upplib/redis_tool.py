from upplib import *
import redis


def get_id(config_redis='redis', key_name='a_b_c', expire_days=5) -> int | None:
    """
        获得自增的 id
    """
    try:
        config_redis_data = get_config_data(config_redis)
        client = redis.StrictRedis(
            host=config_redis_data['host'],
            port=config_redis_data['port'],
            db=config_redis_data['db'],
            password=config_redis_data['password'],
            socket_connect_timeout=5,
            decode_responses=True
        )
        new_id = client.incr(key_name)
        if new_id == 1:
            client.expire(key_name, 86400 * expire_days)
        return to_int(new_id)
    except:
        return None
