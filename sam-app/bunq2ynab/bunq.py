import base64
import json
import requests
import socket

from common import log_request, log_reply
from config import configuration
from decimal import Decimal
from logger import configure_logger
from OpenSSL import crypto

LOGGER = configure_logger(__name__)

url = "https://api.bunq.com/"

account_path = {
    'MonetaryAccountJoint': 'monetary-account-joint',
    'MonetaryAccountBank': 'monetary-account-bank',
    'MonetaryAccountSavings': 'monetary-account-savings',
}

class bunqapi:
    def __init__(self, configlocation):
        self.config = configuration(configlocation)

    def get_private_key(self):
        pem_str = self.config.value['bunq']['priv_key']
        if pem_str:
            return crypto.load_privatekey(crypto.FILETYPE_PEM, pem_str)
        else: 
            LOGGER.info("Generating new private key...")
            key = crypto.PKey()
            key.generate_key(crypto.TYPE_RSA, 2048)
            pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
            self.config.value['bunq']['priv_key'] = pem.decode("utf-8")
            self.config.save(self.config.value)
            return key

    def get_public_key(self):
        private_key = self.get_private_key()
        pem = crypto.dump_publickey(crypto.FILETYPE_PEM, private_key)
        return crypto.load_publickey(crypto.FILETYPE_PEM, pem)

    def get_installation_token(self):
        token = self.config.value['bunq']['install_token']
        if token:
            return token.rstrip("\r\n")
        LOGGER.info("Requesting installation token...")
        public_key = self.get_public_key()
        pem = crypto.dump_publickey(crypto.FILETYPE_PEM, public_key)
        method = "v1/installation"
        data = {
            "client_public_key": pem.decode("utf-8")
        }
        reply = self.post(method, data)
        installation_token = server_public = None
        for row in reply:
            if "Token" in row:
                installation_token = row["Token"]["token"]
            elif "ServerPublicKey" in row:
                server_public = row["ServerPublicKey"]["server_public_key"]
        if not installation_token:
            raise Exception("No token returned by installation")
        if not server_public:
            raise Exception("No server public key returned by installation")
        self.config.value['bunq']['install_token'] = installation_token
        self.config.value['bunq']['server_pub_key'] = server_public
        self.config.save(self.config.value)
        self.register_device()
        return installation_token

    def get_server_public(self):
        pem_str = self.config.value['bunq']['server_pub_key']
        if pem_str:
            return crypto.load_publickey(crypto.FILETYPE_PEM, pem_str)
        raise Exception(
            "Server public key not found.")

    def register_device(self):
        ip = requests.get('https://ipv4.icanhazip.com').text.rstrip()
        LOGGER.info("Registering IP " + ip)
        method = "v1/device-server"
        data = {
            "description": "bunq2ynab on " + socket.getfqdn(),
            "secret": self.config.value['bunq']['api_token'],
            "permitted_ips": [ip]
        }
        self.post(method, data)

    def get_session_token(self):
        token = self.config.value['bunq']['session_token']
        if token:
            return token.rstrip("\r\n")
        LOGGER.info("Requesting session token...")
        method = "v1/session-server"
        data = {
            "secret": self.config.value['bunq']['api_token']
        }
        reply = self.post(method, data)
        session_token = None
        for row in reply:
            if "Token" in row:
                session_token = row["Token"]["token"]
        if not session_token:
            raise Exception("No token returned by session-server")
        self.config.value['bunq']['session_token'] = session_token
        self.config.save(self.config.value)
        return session_token

    def sign(self, action, method, headers, data):
        # Installation requests are not signed
        if method.startswith("v1/installation"):
            return
        # device-server and session-server use the installation token
        # Other endpoints use a session token
        if (method.startswith("v1/device-server") or
                method.startswith("v1/session-server")):
            headers['X-Bunq-Client-Authentication'] = self.get_installation_token()
        else:
            headers['X-Bunq-Client-Authentication'] = self.get_session_token()
        ciphertext = action + " /" + method + "\n"
        for name in sorted(headers.keys()):
            ciphertext += name + ": " + headers[name] + "\n"
        ciphertext += "\n" + data
        private_key = self.get_private_key()
        sig = crypto.sign(private_key, ciphertext, 'sha256')
        sig_str = base64.b64encode(sig).decode("utf-8")
        headers['X-Bunq-Client-Signature'] = sig_str

    def verify(self, method, code, headers, data):
        # Installation responses are not signed
        if method.startswith("v1/installation"):
            return
        # Insufficient authentication errors are not signed
        if headers["Content-Type"] == "application/json":
            result = json.loads(data)
            if ("Error" in result and result["Error"][0]["error_description"]
                    == "Insufficient authentication."):
                return
        ciphertext = str(code) + "\n"
        for name in sorted(headers.keys()):
            name = "-".join(map(str.capitalize, name.lower().split("-")))
            if name.startswith("X-Bunq-") and name != "X-Bunq-Server-Signature":
                ciphertext += name + ": " + headers[name] + "\n"
        ciphertext += "\n" + data
        server_public = self.get_server_public()
        x509 = crypto.X509()
        x509.set_pubkey(server_public)
        sig_str = headers["X-Bunq-Server-Signature"]
        sig = base64.b64decode(sig_str)
        # Raises an exception when verification fails
        crypto.verify(x509, sig, ciphertext, 'sha256')

    def call_requests(self, action, method, data_obj):
        data = json.dumps(data_obj) if data_obj else ''
        headers = {
            'Cache-Control': 'no-cache',
            'User-Agent': 'bunq2ynab',
            'X-Bunq-Client-Request-Id': '0',
            'X-Bunq-Geolocation': '0 0 0 0 NL',
            'X-Bunq-Language': 'en_US',
            'X-Bunq-Region': 'nl_NL'
        }
        self.sign(action, method, headers, data)
        log_request(action, method, headers, data_obj)
        if action == "GET":
            reply = requests.get(url + method, headers=headers)
        elif action == "POST":
            reply = requests.post(url + method, headers=headers, data=data)
        elif action == "PUT":
            reply = requests.put(url + method, headers=headers, data=data)
        elif action == "DELETE":
            reply = requests.delete(url + method, headers=headers)
        log_reply(reply)
        self.verify(method, reply.status_code, reply.headers, reply.text)
        if reply.headers["Content-Type"] == "application/json":
            return reply.json()
        return reply.text

    def call(self, action, method, data=None):
        result = self.call_requests(action, method, data)
        if isinstance(result, str):
            return result
        if ("Error" in result and
                result["Error"][0]["error_description"]
                == "Insufficient authorisation."):
            #delete_file(session_token_file)
            result = self.call_requests(action, method, data)
            if isinstance(result, str):
                return result
        if "Error" in result:
            raise Exception(result["Error"][0]["error_description"])
        return result["Response"]

    def print_accounts(self, userid):
        method = 'v1/user/{0}/monetary-account'.format(userid)
        for a in self.get(method):
            for k, v in a.items():
                LOGGER.info("  {0:28}  {1:10,} {2:3}  ({3})".format(
                    v["description"],
                    Decimal(v["balance"]["value"]),
                    v["balance"]["currency"],
                    v["id"]))
    
    def list_users(self):
        users = self.get('v1/user')
        for u in users:
            for k, v in u.items():
                LOGGER.info('{0} "{1}" ({2})'.format(k, v["display_name"], v["id"]))
                self.print_accounts(v["id"])

    def get_path(self, account_type):
        return account_path[account_type]

    def get(self, method):
        return self.call('GET', method)

    def post(self, method, data):
        return self.call('POST', method, data)

    def put(self, method, data):
        return self.call('PUT', method, data)

    def delete(self, method):
        return self.call('DELETE', method)

    def get_user_id(self, user_name):
        for u in self.get('v1/user'):
            for k, v in u.items():
                if (v["display_name"].casefold() == user_name.casefold() or
                        str(v["id"]) == user_name):
                    return str(v["id"])
        raise Exception("BUNQ user '{0}' not found".format(user_name))
    
    
    def get_account_type(self, user_id, account_id):
        reply = self.get('v1/user/{0}/monetary-account/{1}'.format(
                    user_id, account_id))
        return next(iter(reply[0]))
    
    
    def get_account_id(self, user_id, account_name):
        reply = self.get('v1/user/{0}/monetary-account'.format(user_id))
        for entry in reply:
            account_type = next(iter(entry))
            account = entry[account_type]
            if (account["description"].casefold() == account_name.casefold() or
                    str(account["id"]) == account_name):
                return str(account["id"])
        raise Exception("BUNQ account '{0}' not found".format(account_name))
    
    
    def get_callbacks(self, user_id, account_id):
        method = 'v1/user/{0}/monetary-account/{1}'.format(user_id, account_id)
        result = self.get(method)[0]
        account_type = next(iter(result))
        return result[account_type]["notification_filters"]
    
    
    def put_callbacks(self, user_id, account_id, new_notifications):
        data = {
             "notification_filters": new_notifications
        }
        account_type = self.get_account_type(user_id, account_id)
        method = 'v1/user/{}/{}/{}'.format(
                 user_id, self.get_path(account_type), account_id)
        self.put(method, data)
    
    
    def get_transactions(self, user_id, account_id):
        method = ("v1/user/{0}/monetary-account/{1}/payment?count=100"
                  .format(user_id, account_id))
        payments = self.get(method)
    
        print("Translating payments...")
        transactions = []
        first_day = None
        last_day = None
        unsorted_payments = [p["Payment"] for p in payments]
        payments = sorted(unsorted_payments, key=lambda p: p["created"])
        for p in payments:
            if p["amount"]["currency"] != "EUR":
                raise Exception("Non-euro payment: " + p["amount"]["currency"])
            date = p["created"][:10]
            if not first_day or date < first_day:
                first_day = date
            if not last_day or last_day < date:
                last_day = date
    
            transactions.append({
                "amount": p["amount"]["value"],
                "date": date,
                "payee": p["counterparty_alias"]["display_name"],
                "description": p["description"]
            })
    
        # For correct duplicate calculation, return only complete days
        return [t for t in transactions 
                if first_day < t["date"] or t["date"] == last_day]