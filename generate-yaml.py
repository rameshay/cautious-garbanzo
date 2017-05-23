#!/usr/local/bin/python

def generate_yaml(dict):
    hdr='''\
version: "3"
services:
    '''
#    print 'version: '+'"'+'3'+'"'
#    print "services:"
    print str(hdr)
    ii = 1
    for key in dict.keys():
        print "    mgw-monitor-"+str(ii)+':'
        print "        image: mgw-monitor:latest"
        print "        command: bash ./files/docker-entry-point.sh"
        print "        privileged: true"
        print "        links: "
        print "            - mgw-monitor-syslog"
        print "            - mgw-monitor-redis"
        print "        volumes: "
        print "            - /var/log/elastica/"+key+":/var"
        print "        environment: "
        print "            - MGW_INSTANCE_NAME="+key
        print "            - DB_PORT_6379_TCP_ADDR=mgw-monitor-redis"
        print "            - DB_PORT_6379_TCP_PORT=6379"
        ii += 1

def generate_json(dict):
    header = '''\
{
    "common": {
        "assigned" : "eoe",
        "monitor_vars" : {
           "curl_connect_timeout" : 10,
           "curl_max_time" : 5,
           "consec_fail_threshold" : 3,
           "proxy" : "172.20.254.254:3128",
           "duty_cycle_in_minutes" : 30,
           "url_white_list" : 
            [
               "https://github.com",
               "https://apps.groupdocs.com",
               "https://exportwriter.zoho.com",
               "https://en.4sync.com",
               "https://www.surveymonkey.com",
               "https://slack.com",
               "https://mail.aol.com",
               "https://mail.yahoo.com",
               "https://portal.azure.com",
               "https://docs.google.com",
               "https://mail.live.com"
           ]
        }
    },
   "eoe": {
         "redis_host" : "local-redis",
         "redis_port" : 6917,
         "redis_cfg_db_index" : 0,
         "redis_status_db_index" : 1,
         "mgw_to_monitor" : {
'''
    footer='''\
         }
    },
    "dummy" : "end_of_file"
}
 '''
    print header
    for key in dict.keys():
        print "            "+'"'+str(key)+'" : "'+str(dict[key])+'",'
    print footer

def getEoeList():
    my_dict = \
    {
     'eoe-pdx-mobile-gateway-05da89105f4fdcf46':'10.0.55.146',
     'eoe-pdx-mobile-gateway-034d61437ed2a4899':'10.0.52.124',
     'eoe-pdx-mobile-gateway-0e7e761fef3b815ac':'10.0.48.20',
     'eoe-pdx-mobile-gateway-0fceaa9c17213e29e':'10.0.55.109',
     'eoe-pdx-mobile-gateway-06303d0889b8b8326':'10.0.51.159',
     'eoe-pdx-mobile-gateway-0475e93504bbd561d':'10.0.52.145',
     'eoe-pdx-mobile-gateway-0690f08a69b32b3a0':'10.0.49.200',
     'eoe-pdx-mobile-gateway-0ab03cf50d432f18a':'10.0.55.203',
     'eoe-pdx-mobile-gateway-02f650a5ca233a8b4':'10.0.48.165',
     'eoe-pdx-mobile-gateway-0e77bebb18cc2af08':'10.0.48.78',
     'eoe-pdx-mobile-gateway-0f7f086f87916ed23':'10.0.52.186',
     'eoe-pdx-mobile-gateway-0f2a4874845a6f952':'10.0.54.110',
    }
    return(my_dict)

def getPrdList():
    my_dict  = \
    {
        'prd-sig-mobile-gateway-0f50139b3846199d7':'54.169.128.115',
        'prd-sig-mobile-gateway-08d73d5370e4fda45':'54.169.130.27',
        'prd-sig-mobile-gateway-0bb04348405f34fa3':'54.169.103.213',
        'prd-sjc-mobile-gateway-01c583e62216805b9':'54.193.92.244',
        'prd-sjc-mobile-gateway-021e06d975e07d054':'54.183.110.219',
        'prd-sjc-mobile-gateway-0b2bec56cd0b9d7a9':'54.183.128.144',
        'prd-sjc-mobile-gateway-061e8d404156df3bf':'54.193.95.82',
        'prd-sjc-mobile-gateway-0e1038aec9fd3bd0d':'54.241.190.152',
        'prd-sjc-mobile-gateway-0293b75e5c2bd04de':'54.241.190.155',
        'prd-sjc-mobile-gateway-0c06141e77d43a6a7':'54.241.190.149',
        'prd-sjc-mobile-gateway-02037b0ca54daea0f':'54.183.225.7',
        'prd-sjc-mobile-gateway-0f298281cb8443a68':'54.241.190.150',
        'prd-sjc-mobile-gateway-0b153c20458431409':'54.241.190.151'
    }
    return(my_dict)


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-e", "--eoe", action="store_true",
                      help=" generate the yaml file to append to docker-compose")
    parser.add_option("-p", "--prd", action="store_true",
                      help=" generate the yaml file to append to docker-compose")
    parser.add_option("-c", "--cfg", action="store_true",
                      help=" generate the cfg.json file to populate redis db")
    (options, args) = parser.parse_args()

    if (options.eoe is True):
        generate_yaml(getEoeList())
    elif(options.prd is True):
        generate_yaml(getPrdList())
    elif(options.cfg is True):
        generate_json(eoeGwDict)
    else:
        print "Horrible not to pass a variable"
        print "yaml = " + str(options.yaml) + " cfg = " + str(options.cfg)

