import json
import requests
import uuid

from common import log_request, log_reply
from config import configuration
from decimal import Decimal
from logger import configure_logger

LOGGER = configure_logger(__name__)

class ynabapi:
    def __init__(self, configlocation):
        self.config = configuration(configlocation)
        self.url    = 'https://api.youneedabudget.com/'

    def call(self, action, method, data_obj=None):
        data = json.dumps(data_obj) if data_obj else ''
        headers = {
            'Authorization': 'Bearer ' + self.config.value['ynab']['accesstoken'],
            'Content-type': 'application/json'
        }
        log_request(action, method, headers, data_obj)
        if action == 'GET':
            reply = requests.get(self.url + method, headers=headers)
        elif action == 'POST':
            reply = requests.post(self.url + method, headers=headers, data=data)
        log_reply(reply)
        result = reply.json()
        if "error" in result:
            raise Exception("{0} (details: {1})".format(
                result["error"]["name"], result["error"]["detail"]))
        return result["data"]

    def is_uuid(self, id):
        try:
            uuid.UUID("{" + id + "}")
            return True
        except ValueError as e:
            return False

    def get_budget_id(self, budget_name):
        if self.is_uuid(budget_name):
            return budget_name

        reply = self.get('v1/budgets')
        for b in reply["budgets"]:
            if b["name"].casefold() == budget_name.casefold():
                return b["id"]
        raise Exception("YNAB budget '{0}' not found".format(budget_name))

    def get_account_id(self, budget_id, account_name):
        if self.is_uuid(account_name):
            return account_name

        reply = self.get('v1/budgets/' + budget_id + "/accounts")
        for a in reply["accounts"]:
            if a["name"].casefold() == account_name.casefold():
                return a["id"]
        raise Exception("YNAB account '{0}' not found".format(account_name))

    def upload_transactions(self, budget_id, account_id, transactions):
        ynab_transactions = []
        for t in transactions:
            milliunits = str((1000 * Decimal(t["amount"])).quantize(1))
            # Calculate import_id for YNAB duplicate detection
            occurrence = 1 + len([y for y in ynab_transactions
                        if y["amount"] == milliunits and y["date"] == t["date"]])
            ynab_transactions.append({
                "account_id": account_id,
                "date": t["date"],
                "amount": milliunits,
                "payee_name": t["payee"][:50],  # YNAB payee is max 50 chars
                "memo": t["description"][:100],  # YNAB memo is max 100 chars
                "cleared": "cleared",
                "import_id": "YNAB:{}:{}:{}".format(
                    milliunits, t["date"], occurrence)
            })

        method = "v1/budgets/" + budget_id + "/transactions/bulk"
        result = self.post(method, {"transactions": ynab_transactions})
        return result["bulk"]

    def get(self, method):
        return self.call('GET', method)

    def post(self, method, data):
        return self.call('POST', method, data)

    def print_accounts(self, budget_id):
        result = self.get("v1/budgets/" + budget_id + "/accounts")
        for a in result["accounts"]:
            balance = Decimal(a["balance"])/Decimal(1000)
            LOGGER.info("  {0:10,}  {1:<25} ({2})".format(
                balance, a["name"], a["type"]))
    
    def list_budget(self):
        result = self.get("v1/budgets")
        for b in result["budgets"]:
            LOGGER.info('Accounts for budget "{0}":'.format(b["name"]))
            self.print_accounts(b["id"])