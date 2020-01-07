from logger import configure_logger
LOGGER = configure_logger(__name__)

def sync(config, b, y):
    for mapping in config.value['bunq2ynab']:
        bunq_user_name = mapping['bunq_user']
        bunq_account_name = mapping['bunq_acc']
        ynab_budget_name = mapping['ynab_budget']
        ynab_account_name = mapping['ynab_acc']
        LOGGER.info('Trying to sync Bunq user: {0} account: {1} to Ynab budget: {2} and account {3}.'.format(
            bunq_user_name, bunq_account_name, ynab_budget_name, ynab_account_name
        ))

        LOGGER.info("Getting BUNQ identifiers...")
        bunq_user_id = b.get_user_id(bunq_user_name)
        bunq_account_id = b.get_account_id(bunq_user_id, bunq_account_name)

        LOGGER.info("Getting YNAB identifiers...")
        ynab_budget_id = y.get_budget_id(ynab_budget_name)
        ynab_account_id = y.get_account_id(ynab_budget_id, ynab_account_name)

        LOGGER.info("Reading list of payments...")
        transactions = b.get_transactions(bunq_user_id, bunq_account_id)

        LOGGER.info("Uploading transactions to YNAB...")
        stats = y.upload_transactions(ynab_budget_id, ynab_account_id, transactions)
        LOGGER.info("Uploaded {0} new and {1} duplicate transactions.".format(
            len(stats["transaction_ids"]), len(stats["duplicate_import_ids"])))