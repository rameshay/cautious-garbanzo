import os
import sys
import socket
import pyping
import subprocess
import time
from datetime import datetime
import traceback
import logging
from redis import Redis
import requests
from functools import reduce


'''
The configuration database are sets mostly indexed by instance name.
The status database are hsets hash indexed named variables.
For instance '
hgetall(errors::eoe-pdx-mobile-gateway-id) { charon:100, charon_ts:UTC-, named:20, named_ts:UTC-, curl:55, curl_ts:UTC, curl_url:'www.box.com', via_miss:50, via_miss_ts:UTC- , via_curl:'www.google.com'}
hgetall(consec_errors:eoe-pdx-mobile-gateway-id) { index:2, flags[False,False,True], ts[UTC-1, UTC-2, UTC-3] }
hgetall(status:eoe-pdx-mobile-gateway-id)  { code:500,string:'consecutive charon failures'}
hgetall(performance:eoe-pdx-mobile-gateway-id)  { min_curl:500,max_curl:30000,avg_curl:2000, min_connect:1, max_connect:20, avg_connect:7, min_lkup:10, max_lkup:20, avg_lkup:14}
get(keepalives)  {instance-ids} with a 30 second expiry
'''

def string_to_bool(inputString):
    out = [False]*len(inputString)
    ii = 0
    for val in inputString:
        if val == 'True':
            out[ii] = True
        ii += 1
    return out

class monitorDb:
    def __init__(self, instance=None):
        self._instance = instance
        self._status_flag_dict = {}
        self._time_stamps_dict = {}
        try:
            self._rh_cfg = Redis(host=os.environ['DB_PORT_6379_TCP_ADDR'], port=os.environ[
                                 'DB_PORT_6379_TCP_PORT'], db=0)
        except Exception as ex:
            logger.critical("Redis Connect to Status DB failed Excepton = " + str(ex))
        try:
            self._rh_status = Redis(host=os.environ['DB_PORT_6379_TCP_ADDR'], port=os.environ[
                                    'DB_PORT_6379_TCP_PORT'], db=1)
        except Exception as ex:
            logger.critical("Redis Connect to Cfg Db failed Excepton = " + str(ex))
        try:
            self._rh_keepalives = Redis(host=os.environ['DB_PORT_6379_TCP_ADDR'], port=os.environ[
                                        'DB_PORT_6379_TCP_PORT'], db=2)
        except Exception as ex:
            logger.critical("Redis Connect to KeepAlives Db failed Excepton = " + str(ex))

    def init_status_flags_ts(self,consec_fail_cnt):
        logger.info("Initializing DB consec_error = %d", int(consec_fail_cnt))
        ii = 0
        key = 'consec_errors:'+str(self._instance)
        while (ii < int(consec_fail_cnt)):
            self._status_flag_dict['flags_'+str(ii)] = False
            self._time_stamps_dict['ts_'+str(ii)] = str(datetime.utcnow())
            ii += 1

        if(len(self._rh_status.hmget(key, self._status_flag_dict.keys())) < consec_fail_cnt):
            logger.info("Initializing status_flag dict")
            self._rh_status.hmset('consec_errors:',self._status_flag_dict)
        if(len(self._rh_status.hmget(key, self._time_stamps_dict.keys())) < consec_fail_cnt):
            logger.info("Initializing timestamp dict")
            self._rh_status.hmset('consec_errors:',self._time_stamps_dict)

    def get_all_gw_instance(self):
        gw_instances = []
        if (self._rh_cfg):
            gw_instances = self._rh_cfg.get('eoe*')
        return gw_instances

    def get_monitor_var(self, key):
        val = None
        if (self._rh_cfg):
            val = self._rh_cfg.get(key)
        return val

    def get_gw_ip(self):
        gw_ip = None
        if (self._rh_cfg):
            gw_ip = self._rh_cfg.get(self._instance)
        return gw_ip

    def get_gw_status(self, val):
        gw_status = None
        if (self._rh_status):
            key = 'status:'+str(self._instance)
            gw_status = self._rh_status.hget(key, val)
        return gw_status


    def set_gw_web_status(self, module, flag):
        errorStrings = {'charon': 'MobileGateway VPN service down',
                        'named': 'MobileGateway Named Service Down',
                        'elastica': 'MobileGateway Elastica Service Down'}
        webstatus_key = 'web_status:' + str(self._instance)
        statusDict = self._rh_status.hgetall(webstatus_key)
        if (len(statusDict) == 0):
            self._rh_status.hset(webstatus_key, 'status_code', 500)
            self._rh_status.hset(webstatus_key, 'status_string', 'Initialization incomplete')
        if (flag is True):
            self._rh_status.hset(webstatus_key, 'status_code', 200)
            self._rh_status.hset(webstatus_key, 'status_string', 'Success')
        else:
            self._rh_status.hset(webstatus_key, 'status_code', 500)
            self._rh_status.hset(webstatus_key, 'status_string', errorStrings[str(module)])
        logger.info("Setting web_status module %s to %s",str(module), str(flag))

    def set_consec_error_status(self, module, state, consec_error_threshold):
        flags_array = [False]*int(consec_error_threshold)
        consec_key = 'consec_errors:'+str(self._instance)
        consec_index = int(self._rh_status.hget(consec_key,'index'))
        self._rh_status.hincrby(consec_key, 'index', 1)
        consec_index %= int(consec_error_threshold)
        flags_array = string_to_bool(self._rh_status.hmget(consec_key,self._status_flag_dict.keys()))
        flags_array[consec_index] = state
        flag = reduce(lambda x, y: x | y, flags_array)
        self.set_gw_web_status(module, flag)

        key = 'flags_'+str(consec_index)
        self._rh_status.hset(consec_key, key, state)
        ts_key = 'ts_' + str(consec_index)
        tStamp = datetime.utcnow()
        self._rh_status.hset(consec_key, ts_key, str(tStamp))
        logger.info("Setting consecErrorDict to %s " % self._rh_status.hgetall(consec_key).items())


    def set_gw_monitor_keepalive(self):
        if (self._rh_keepalives):
            self._rh_keepalives.pexpire(self._instance, 31 * 1000)


class gwOperations():
    def __init__(self, dbH, consecThreshold):
        self._db_handle = dbH
        self._consec_threshold = consecThreshold

    def check_charon(self, oper):
        _gw_to_monitor = self._db_handle.get_gw_ip()
        vpn_command = '/usr/sbin/racoonctl -s /tmp/racoon.sock'
        if(oper == 'connect'):
            vpn_command += ' vc ' + str(_gw_to_monitor)
        else:
            vpn_command += ' vd ' + str(_gw_to_monitor)

        while (True):
            try:
                subprocess.check_output(
                    vpn_command, shell=True, stderr=subprocess.STDOUT)
                self._db_handle.set_consec_error_status(
                    'charon', True, self._consec_threshold)
                logger.info(" %s to mgw: %s", str(oper), vpn_command)
                break
            except Exception as ex:
                if (oper != 'connect'):
                    return
                self._db_handle.set_consec_error_status(
                    'charon', False, self._consec_threshold)
                logger.critical("Exception occured when " +
                                str(oper) + "ting, " + str(ex))
                logger.critical(traceback.format_exc())
                time.sleep(5)

    def check_named(self):
        dig_cmd = "/usr/bin/dig @172.20.254.254 www.box.com +short"
        while (True):
            try:
                dig_out = subprocess.check_output(
                    dig_cmd, shell=True, stderr=subprocess.STDOUT)
                if (dig_out.find("172.20.*")):
                    logger.info(" dig successful: " + str(dig_out))
                    self._db_handle.set_consec_error_status(
                        'named', True, self._consec_threshold)
                    break
            except Exception as exc:
                self._db_handle.set_consec_error_status(
                    'named', False, self._consec_threshold)
                logger.error("Exception taken for unable to verify synthetic ip for box.com, out = " +
                             str('dig_out') + " : Exception" + str(exc))
                time.sleep(5)

    def check_named_socket(self):
        while (True):
            try:
                box_com = socket.gethostbyname('www.box.com')
                if(box_com.find("172.20.") < 0):
                    time.sleep(1)
                    continue
                else:
                    logger.info(" named successful: " + str(box_com))
                    self._db_handle.set_consec_error_status(
                        'named', True, self._consec_threshold)
                    break
            except Exception as exc:
                self._db_handle.set_consec_error_status(
                    'named', False, self._consec_threshold)
                logger.error("Exception taken for unable to verify synthetic ip for box.com, out = " +
                             str('box_com') + " : Exception" + str(exc))
                time.sleep(5)

class curlOperations():
    def __init__(self, proxy, timeout, maxtime):
        self._proxy = str(proxy)
        self._timeout = timeout
        self._maxtime = maxtime

    def check_gw(self, url):
        #logger.info(" Requesting url = %s", url)
        headers = {'user-agent': 'gw-monitor/0.0.1'}
        proxies = {'https': self._proxy}
        try:
            r = requests.head(str(url), proxies=proxies,headers=headers, verify=False, timeout=(self._timeout, self._maxtime))
            if ((r.status_code == requests.codes.ok) or
                (r.status_code == requests.codes.found)):
                if(r.headers['Via'].find('Elastica Gateway Service') < 0):
                    logger.critical("missing via header response = %s", r.headers)
                    return(False)
                else:
                    return(True)
            else:
                logger.error("Request for url %s returned code %d time taken %d seconds",
                             r.url, r.status_code , r.elapsed.total_seconds())
                return False
        except Exception as ex:
            logger.error("Request for url %s raised exception %s", r.url,str(ex))
            return False


def start_monitoring(gw_to_monitor):
    try:
        db = monitorDb(gw_to_monitor)
    except Exception as exc:
        logger.critical('Unable to connect to Redis, exception = ' + str(exc))
        sys.exit(-1)
    _proxy = db.get_monitor_var('proxy')
    _curl_connect_timeout = float(db.get_monitor_var('curl_connect_timeout'))
    _curl_max_time = float(db.get_monitor_var('curl_max_time'))
    _consec_fail_cnt = db.get_monitor_var('consec_fail_threshold')
    _url_whitelist = db.get_monitor_var('url_white_list')
    _url_whitelist = _url_whitelist.replace("[", "")
    _url_whitelist = _url_whitelist.replace("]", "")
    _url_whitelist = _url_whitelist.replace("u'", "")
    _url_whitelist = _url_whitelist.replace("'", "")
    _url_whitelist = _url_whitelist.split(',')
    _duty_cycle_time = db.get_monitor_var('duty_cycle_in_minutes')

    logger.info("Final configs: CURL_CONNECT_TIMEOUT: %s, "
                "CURL_MAX_TIME: %s, PROXY: %s, "
                "consec_fail_cnt: %s, "
                "URL_WHITE_LIST: %s, DUTY_CYCLE_TIME: %s",
                str(_curl_connect_timeout), str(_curl_max_time),
                str(_proxy), str(_consec_fail_cnt),
                str(_url_whitelist), str(_duty_cycle_time))

    db.init_status_flags_ts(_consec_fail_cnt)
    gwOps = gwOperations(db, _consec_fail_cnt)
    curlOps = curlOperations(_proxy, _curl_connect_timeout, _curl_max_time)

    start = time.time()
    db.set_gw_monitor_keepalive()
    r = pyping.ping('172.20.254.254')
    if r.ret_code == 0:
        logger.info('Already connected to mgw disconnecting first before connect')
        gwOps.check_charon('disconnect')
    gwOps.check_charon('connect')
    logger.info("Gateway Connection = " +
                str((1000 * (time.time() - start))) + " Milliseconds")
    while True:
        gwOps.check_named()
        logger.info("Named Connection + Gateway Connection = " +
                    str((1000 * (time.time() - start))) + " Milliseconds")
        curl_start = time.time()
        rcodes = [True]*len(_url_whitelist)
        ii = 0
        for url in _url_whitelist:
            rcodes[ii] = curlOps.check_gw(str(url))
            ii += 1
        curl_end = time.time()
        if rcodes.count(True) > rcodes.count(False):
            status = True
        else:
            status = False
        db.set_consec_error_status('elastica', status, _consec_fail_cnt)
        logger.info("Status = %s It took %s Milliseconds for curl to complete, curl-rcodes = %s" ,
                    str(status),  str(1000 * (curl_end - curl_start)), str(rcodes))
        time.sleep(10)
        time_left = (60 * float(_duty_cycle_time)) - (time.time() - start)
        if (time_left < 10):
            logger.info("Disconnecting from Gateway and Reconnecting")
            gwOps.check_charon('disconnect')
            time.sleep(5)
            time_left = (60 * _duty_cycle_time)
            db.set_gw_monitor_keepalive()
            start = time.time()
            gwOps.check_charon('connect')
            logger.info("Gateway Connection = " + str((1000 * (time.time() - start))) + " Milliseconds")
        else:
            logger.info("Back to Curl duty_cycle_time_left = %d seconds", time_left)


if __name__ == "__main__":

    logger = logging.getLogger('check_mgw_health')
    logger.setLevel(logging.INFO)
    #fh = logging.StreamHandler()
    #fh = logging.SysLogHandler(address=('mgw-monitor-syslog', 514))
    fh = logging.FileHandler(
        '/var/log/gw-monitor' + '.log')
    formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    gw_to_monitor = str(os.environ['MGW_INSTANCE_NAME'])
    if (gw_to_monitor is None):
        logger.critical('Exiting cannot proceed without instance name')
        sys.exit(-1)
    else:
        logger.info('STARTING with gateway instance = ' + str(gw_to_monitor))
    start_monitoring(gw_to_monitor)
