#!/usr/bin/env python
import json
import os
from redis import Redis

def export_to_redis(json_in):
    role = json_in["common"]["assigned"]
    print ("Role is " +str(role))
    redis_host = os.environ['DB_PORT_6379_TCP_ADDR']
    redis_port =os.environ['DB_PORT_6379_TCP_PORT']
    #redis_host = json_in[role]["redis_host"]
    #redis_port = json_in[role]["redis_port"]
    try:
        r_status = Redis(host=redis_host, port=redis_port,db=json_in[role]["redis_status_db_index"])
    except Exception as ex:
        print("Redis Connect to Status DB failed Excepton = " + str(ex))
    try:
        r_cfg = Redis(host=redis_host, port=redis_port,db=json_in[role]["redis_cfg_db_index"])
    except Exception as ex:
        print("Redis Connect to Cfg Db failed Excepton = " + str(ex))

    monitorDict = json_in["eoe"]["mgw_to_monitor"]
    for gw in monitorDict.keys():
        print("Key = " + str(gw) + " Value = " + str(monitorDict.get(gw)))
        try:
            r_cfg.set(gw, monitorDict.get(gw))
            value = r_cfg.get(gw)
            print("gateway to monitor = " + str(value))
        except Exception as ex:
            print("Setting Redis failed :" + str(json_in["mgw_to_monitor"]) + " Excepton = " + str(ex))

        status = r_status.get(gw)
        if (status):
            print("Skipping over instance " + str(gw) + " Status is " + str(status))
        else:
            r_status.set(gw, '200 : Status OK')

    monitorDict = json_in["eoe"]["monitor_vars"]
    for var in monitorDict.keys():
        print(" Key = " + str (var) + " value = " + str(monitorDict.get(var)))
        try:
            r_cfg.set(var, monitorDict.get(var))
        except Exception as ex:
            print("Could not set var =" + str(var) + " to " + str(monitorDict.get(var)) + str(ex))



if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", default="gw_monitor.json",
                      help=" json formatted configuration file")
    (options, args) = parser.parse_args()

    try:
        with open(options.file) as json_data:
            cfg_data = json.load(json_data)
            json_data.close()
            export_to_redis(cfg_data)
    except Exception as ex:
        print("Bad Json File" + str(ex))
