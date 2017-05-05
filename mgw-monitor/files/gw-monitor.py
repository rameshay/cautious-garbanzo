#!/bin/env python
import os
import sys
import subprocess
import time
import traceback
import logging
from redis import Redis
import pycurl

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


class monitorDb:
    def __init__(self, instance=None):
        self._instance = instance
        try:
            self._rh_cfg = Redis(host=os.environ['DB_PORT_6379_TCP_ADDR'], port=os.environ[
                                 'DB_PORT_6379_TCP_PORT'], db=0)
        except Exception as ex:
            print("Redis Connect to Status DB failed Excepton = " + str(ex))
        try:
            self._rh_status = Redis(host=os.environ['DB_PORT_6379_TCP_ADDR'], port=os.environ[
                                    'DB_PORT_6379_TCP_PORT'], db=1)
        except Exception as ex:
            print("Redis Connect to Cfg Db failed Excepton = " + str(ex))
        try:
            self._rh_keepalives = Redis(host=os.environ['DB_PORT_6379_TCP_ADDR'], port=os.environ[
                                        'DB_PORT_6379_TCP_PORT'], db=2)
        except Exception as ex:
            print("Redis Connect to KeepAlives Db failed Excepton = " + str(ex))

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
                        'named': 'MobileGateway Named Service Down', 'elastica': 'MobileGateway Elastica Service Down'}
        ts = time.gmtime()
        if (self._rh_status):
            key = 'consec_errors:' + str(self._instance)
            consecErrorDict = self._rh_status.hget(key)
            consecErrorDict['index'] = (
                consecErrorDict['index'] + 1) % consec_error_threshold
            consecErrorDict['flags'][(consecErrorDict['index'])] = state
            consecErrorDict['ts'][(consecErrorDict['index'])] = ts
            flag = reduce(lambda x, y: x | y, consecErrorDict['flags'])
            self._rh_status.hmset(key, consecErrorDict)
            key = 'status:' + str(self._instance)
            if (flag is False):
                self._rh_status.hset(key, 'code', 200)
                self._rh_status.hset(key, 'string', 'Success')
            else:
                self._rh_status.hset(key, 'code', 500)
                self._rh_status.hset(key, 'string', errorStrings['module'])

    def set_gw_errors(self, module, *args):
        ts = time.gmtime()
        if (self.rh_status):
            key = 'errors:' + str(self._instance)
            self._rh_status.hincrby(key, module, 1)
            self._rh_status.hset(key, module + str('_ts'), ts)
        if (args):
            self._rh_status.hset(key, module + str('_url'), str(args))

    def set_gw_monitor_start(self):
        if (self._rh_keepalives):
            self._rh_keepalives.pexpire(self._instance, 30 * 1000)


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
        logger.info("%s to mgw: %s", str(oper), vpn_command)

        connect_flag = False
        while [connect_flag is False]:
            try:
                subprocess.check_output(
                    vpn_command, shell=True, stderr=subprocess.STDOUT)
                connect_flag = True
                self._db_handle.set_gw_status(
                    'charon', connect_flag, self._consec_threshold)
            except Exception as ex:
                self._db_handle.set_gw_status(
                    'charon', connect_flag, self._consec_threshold)
                logger.critical("Exception occured when " +
                                str(oper) + "ting, " + str(ex))
                logger.critical(traceback.format_exc())
                time.sleep(5)

    def check_named(self):
        dig_cmd = "/usr/bin/dig @172.20.254.254 www.box.com +short"
        dig_success = False
        while [dig_success is False]:
            try:
                dig_out = subprocess.check_output(
                    dig_cmd, shell=True, stderr=subprocess.STDOUT)
                if (dig_out.find("172.20.*")):
                    logger.info("dig successful: " + str(dig_out))
                    dig_success = True
                    self._db_handle.set_gw_status(
                        'named', dig_success, self._consec_threshold)
            except Exception as exc:
                self._db_handle.set_gw_status(
                    'named', dig_success, self._consec_threshold)
                logger.error("Exception taken for unable to verify synthetic ip for box.com, out = " +
                             str('dig_out') + " : Exception" + str(exc))
                time.sleep(5)

    def check_gw(self, url):
        _rcode = 0
        c = pycurl.Curl()
        c.setopt(c.PROXY, self._db_handle.db.get_gw_monitor_var('proxy'))
        c.setopt(c.SSL_VERIFYPEER, 1)
        c.setopt(c.SSL_VERIFYHOST, 2)
        c.setopt(pycurl.CONNECT_TIMEOUT,
                 self._db_handle.get_gw_monitor_var('connect_timeout'))
        c.setopt(pycurl.CURL_MAX_TIME,
                 self._db_handle.get_gw_monitor_var('curl_max_time'))
        try:
            c.perform()
            _rcode = c.getinfo(pycurl.RESPONSE_CODE)
            c.close()
        except Exception as exc:
            logger.error('Curl Exception for url = ' +
                         str(url) + ":Exception = " + str(exc))
            self._db_handle.set_gw_status(
                'curl', False, self._consec_threshold)
        if (_rcode is not 200):
            self._db_handle.set_gw_status(
                'curl', False, self._consec_threshold)
        else:
            self._db_handle.set_gw_status(
                'curl', True, self._consec_threshold)


def perform_health_check(params):

    db = monitorDb(instance=os.environ['MGW_INSTANCE_NAME'])
    _proxy = db.get_gw_monitor_var('proxy')
    _curl_connect_timeout = db.get_gw_monitor_var('curl_connect_timeout')
    _curl_max_time = db.get_gw_monitor_var('curl_max_time')
    _consec_failure_total_cnt = db.get_gw_monitor_var('consec_fail_threshold')
    _url_whitelist = db.get_gw_monitor_var('url_white_list')
    _duty_cycle_time = db.get_gw_monitor_var('duty_cycle_in_minutes')

    logger.info("Final configs: CURL_CONNECT_TIMEOUT: %s, "
                "CURL_MAX_TIME: %s, PROXY: %s, "
                "CONSEC_FAILURE_TOTAL_CNT: %s"
                "URL_WHITE_LIST: %s, DUTY_CYCLE_TIME: %d",
                _curl_connect_timeout, _curl_max_time,
                _proxy, _consec_failure_total_cnt, _url_whitelist, _duty_cycle_time)

    gwOps = gwOperations(db, _consec_failure_total_cnt)

    while True:
        start = time.time()
        gwOps.check_charon('connect')
        logger.info("Gateway Connection = " +
                    str((1000 * (time.time() - start))) + " Milliseconds")
        gwOps.check_named()
        logger.info("Named Connection + Gateway Connection = " +
                    str((1000 * (time.time() - start))) + " Milliseconds")
        for url in _url_whitelist:
            gwOps.check_gw(url)
            time.sleep(1)
            time_left = (60 * _duty_cycle_time) - (time.time() - start)
            if (time_left < 0):
                gwOperations.check_charon('disconnect')
                time.sleep(5)
                time_left = (60 * _duty_cycle_time)
                break


if __name__ == "__main__":
    if [os.environ['MGW_INSTANCE_NAME'] is None]:
        sys.exit(-1)

    logger = logging.getLogger('check_mgw_health')
    logger.setLevel(logging.INFO)

#    fh = logging.FileHandler(
#        '/var/log/elastica/check_mgw_health' + '.log')
    fh = logging.SysLogHandler(address=('syslog', 514))
    formatter = ('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    perform_health_check()
