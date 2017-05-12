#!/usr/bin/env python
import json
import os
from redis import Redis

def export_to_redis(json_in, redis_h_p):
    if (redis_h_p is None):
        redis_host = os.environ['DB_PORT_6379_TCP_ADDR']
        redis_port =os.environ['DB_PORT_6379_TCP_PORT']
    else:
        (redis_host, redis_port) = redis_h_p.split(':')

    print("Redis host %s port %s", redis_host, redis_port)
    role = json_in["common"]["assigned"]
    print ("Role is " +str(role))
    try:
        r_cfg = Redis(host=redis_host, port=redis_port,db=json_in[role]["redis_cfg_db_index"])
    except Exception as ex:
        print("Redis Connect to Cfg Db failed Excepton = " + str(ex))

    monitorDict = json_in["common"]["monitor_vars"]
    for var in monitorDict.keys():
        print(" Key = " + str (var) + " value = " + str(monitorDict.get(var)))
        try:
            r_cfg.set(var, monitorDict.get(var))
        except Exception as ex:
            print("Could not set var =" + str(var) + " to " + str(monitorDict.get(var)) + str(ex))

    monitorDict = json_in[role]["mgw_to_monitor"]
    for gw in monitorDict.keys():
        print("Key = " + str(gw) + " Value = " + str(monitorDict.get(gw)))
        try:
            r_cfg.set(gw, monitorDict.get(gw))
            value = r_cfg.get(gw)
            print("gateway to monitor = " + str(value))
        except Exception as ex:
            print("Setting Redis failed :" + str(json_in["mgw_to_monitor"]) + " Excepton = " + str(ex))


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", default="gw_monitor.json",
                      help=" json formatted configuration file")
    parser.add_option("-c", "--connect", default="127.0.0.1:6379",
                      help="redis_host:redis_port")
    (options, args) = parser.parse_args()
    redis_host_port=options.connect

    try:
        with open(options.file) as json_data:
            cfg_data = json.load(json_data)
            json_data.close()
            export_to_redis(cfg_data, redis_host_port)
    except Exception as ex:
        print("Bad Json File" + str(ex))
