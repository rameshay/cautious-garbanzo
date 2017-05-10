import os
import sys
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
    out = []
    string = inputString.replace(" ","")
    string = string.split(',')
    for val in string:
        if val == 'True':
            out.append(True)
        elif val == 'False':
            out.append(False)
    return out

class monitorDb:
    def __init__(self, instance=None):
        self._instance = instance
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

    def get_all_gw_instance(self):
        gw_instances = [None]
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

    def get_gw_status(self):
        gw_status = None
        if (self._rh_status):
            gw_status = self._rh_status.hget(self._instance)
        return gw_status

    def set_gw_status(self, module, state, consec_error_threshold):
        errorStrings = {'charon': 'MobileGateway VPN service down',
                        'named': 'MobileGateway Named Service Down',
                        'elastica': 'MobileGateway Elastica Service Down'}
        tStamp = datetime.utcnow()
        logger.info(" Time now is %s" % tStamp)
        if (self._rh_status):
            key = 'consec_errors:' + str(self._instance)
            if (len(self._rh_status.hgetall(key)) == 0):
                consecErrorDictDefault = {}
                consecErrorDictDefault['index'] = 0
                consecErrorDictDefault['flags'] = 'False, False, False'
                consecErrorDictDefault['ts_0'] = str(tStamp)
                consecErrorDictDefault['ts_1'] = str(tStamp)
                consecErrorDictDefault['ts_2'] = str(tStamp)
                logger.info("Creating defaultDict = %s" % consecErrorDictDefault.items())
                self._rh_status.hmset(key, consecErrorDictDefault)

            status_index = int(self._rh_status.hget(key,'index'))
            self._rh_status.hincrby(key, 'index', 1)
            status_index %= int(consec_error_threshold)
            flags = string_to_bool(self._rh_status.hget(key,'flags'))
            if (len(flags) > status_index):
                flags[status_index] = state
            flag = reduce(lambda x, y: x | y, flags)
            key = 'status:' + str(self._instance)
            statusDict = self._rh_status.hgetall(key)
            if (len(statusDict) == 0):
                self._rh_status.hset(key, 'status_code', 200)
                self._rh_status.hset(key, 'status_string', 'Success')
            logger.info("Status Dict = %s " % statusDict.items())
            if (flag is False):
                self._rh_status.hset(key, 'status_code', 200)
                self._rh_status.hset(key, 'status_string', 'Success')
            else:
                self._rh_status.hset(key, 'status_code', 500)
                self._rh_status.hset(key, 'status_string', errorStrings[str(module)])
            self._rh_status.hset(key, 'flags', str(flags))
            ts_key = 'ts_' + str(status_index)
            self._rh_status.hset(key, ts_key, str(tStamp))
            logger.info("Setting consecErrorDict to %s " % self._rh_status.hgetall(key).items())
        else:
            logger.critical("Redis DB handle for status missing")


    def set_gw_errors(self, module, *args):
        ts = time.gmtime()
        if (self.rh_status):
            key = 'errors:' + str(self._instance)
            self._rh_status.hincrby(key, module, 1)
            self._rh_status.hset(key, module + str('_ts'), ts)
        if (args):
            self._rh_status.hset(key, module + str('_url'), str(args))

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
                self._db_handle.set_gw_status(
                    'charon', True, self._consec_threshold)
                logger.info(" %s to mgw: %s", str(oper), vpn_command)
                break
            except Exception as ex:
                self._db_handle.set_gw_status(
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
                    self._db_handle.set_gw_status(
                        'named', True, self._consec_threshold)
                    break
            except Exception as exc:
                self._db_handle.set_gw_status(
                    'named', False, self._consec_threshold)
                logger.error("Exception taken for unable to verify synthetic ip for box.com, out = " +
                             str('dig_out') + " : Exception" + str(exc))
                time.sleep(5)

class curlOperations():
    def __init__(self, proxy, timeout, maxtime):
        self._proxy = proxy
        self._timeout = timeout
        self._maxtime = maxtime

    def check_gw(self, url):
        headers = {'user-agent': 'gw-monitor/0.0.1'}
        r = requests.head(str(url), proxies=str(self._proxy),headers=headers, verify=False, timeout=(self._timeout, self._maxtime))
        logger.info("Request for url %s returned code %d", str(url), r.status_code)
        if (r.status_code == requests.codes.ok):
            viaHeader = r.headers['Via']
            if (viaHeader.find('Elastica Gateway Service')):
                return (True)
            else:
                logger.critical("Request for url %s returned code %d, missing via header ", str(url), r.status_code)
                return (False)
        else:
            return (False)


def start_monitoring(gw_to_monitor):

    try:
        db = monitorDb(gw_to_monitor)
    except Exception as exc:
        logger.error('Unable to connect to Redis, exception = ' + str(exc))
        sys.exit(-1)
    _proxy = db.get_monitor_var('proxy')
    _curl_connect_timeout = db.get_monitor_var('curl_connect_timeout')
    _curl_max_time = db.get_monitor_var('curl_max_time')
    _consec_failure_total_cnt = db.get_monitor_var('consec_fail_threshold')
    _url_whitelist = db.get_monitor_var('url_white_list')
    _duty_cycle_time = db.get_monitor_var('duty_cycle_in_minutes')

    logger.info("Final configs: CURL_CONNECT_TIMEOUT: %s, "
                "CURL_MAX_TIME: %s, PROXY: %s, "
                "CONSEC_FAILURE_TOTAL_CNT: %s, "
                "URL_WHITE_LIST: %s, DUTY_CYCLE_TIME: %s",
                str(_curl_connect_timeout), str(_curl_max_time),
                str(_proxy), str(_consec_failure_total_cnt),
                str(_url_whitelist), str(_duty_cycle_time))

    gwOps = gwOperations(db, _consec_failure_total_cnt)
    curlOps = curlOperations(_proxy, _curl_connect_timeout, _curl_max_time)

    start = time.time()
    db.set_gw_monitor_keepalive()
    gwOps.check_charon('connect')
    logger.info("Gateway Connection = " +
                str((1000 * (time.time() - start))) + " Milliseconds")
    while True:
        gwOps.check_named()
        logger.info("Named Connection + Gateway Connection = " +
                    str((1000 * (time.time() - start))) + " Milliseconds")
        curl_start = time.time()
        for url in _url_whitelist:
            rcode = curlOps.check_gw(url)
            curl_end = time.time()
            logger.info("Curl Operation for url %s returned rcode %d",str(url), rcode)
            logger.info("It took " + str(1000 * (curl_end - curl_start)) + " Milliseconds" + " for url " + str(url) + " to complete")
            curl_start = curl_end

        if (rcode is not 200):
            db.set_gw_status('curl', False, _consec_failure_total_cnt)
        else:
            db.set_gw_status('curl', True, _consec_failure_total_cnt)

        time.sleep(10)
        time_left = (60 * _duty_cycle_time) - (time.time() - start)
        if (time_left < 0):
           gwOperations.check_charon('disconnect')
           time.sleep(5)
           time_left = (60 * _duty_cycle_time)
           db.set_gw_monitor_keepalive()
           start = time.time()
           gwOps.check_charon('connect')
           logger.info("Gateway Connection = " + str((1000 * (time.time() - start))) + " Milliseconds")


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
        logger.info('Proceeding with gateway instance = ' + str(gw_to_monitor))
    start_monitoring(gw_to_monitor)
