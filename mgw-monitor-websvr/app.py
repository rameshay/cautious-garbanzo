import os
import ssl
from flask import Flask, render_template
from redis import Redis
import logging
from logging.handlers import RotatingFileHandler

from functools import wraps
from flask import request, Response


app = Flask(__name__)
redis_status = Redis(host=os.environ['DB_PORT_6379_TCP_ADDR'], port=os.environ['DB_PORT_6379_TCP_PORT'], db=1)


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    app.logger.info('Username = %s, password = %s', username, password)
    user = os.environ['AUTH_USER']
    secret = os.environ['AUTH_SECRET']
    return str(username) == user and str(password) == secret

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@requires_auth
def hello():
    code_dict = {}
    strings_dict = {}
    allkeys = redis_status.keys('web_status:eoe*')
    app.logger.info('allkeys = %s' % allkeys)
    for key in allkeys:
        status_code = redis_status.hget(key, 'status_code')
        status_string = redis_status.hget(key, 'status_string')
        app.logger.info("code = %s" % status_code )
        app.logger.info("string = %s" % status_string )
        (dummy,gw) = key.split(':')
        code_dict[gw] = str(status_code)
        strings_dict[gw] = str(status_string)
    return render_template('index.html', codes = code_dict, error_strings = strings_dict, title = 'EoE Gateway Status Page')

if __name__ == "__main__":
    handler = RotatingFileHandler('/var/log/app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('/etc/ssl/private/el-vpn-server-Key.pem',
               '/etc/ssl/certs/el-vpn-server-Cert.pem')
    app.logger.addHandler(handler)
    app.run(host="0.0.0.0", port=443, debug=True, ssl_context=context, threaded=True)
