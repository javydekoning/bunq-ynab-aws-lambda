# bunq2ynab for AWS Lambda

Forked from [wesselt/bunq2ynab](https://github.com/wesselt/bunq2ynab). Modified to run on AWS Lambda.

## Deploying

- Deploy the application from the [Serverless Application Repository]([https://console.aws.amazon.com/serverlessrepo/)
- Enter your 'BunqApiToken' and 'YnabAccessToken'. Click Deploy and wait for the deployment to finish.
- Go to the [AWS Lambda console](https://console.aws.amazon.com/lambda/), and open the function.
- Click *"Select a test event"* , and configure a test event. You can use the standard `Hello World` example. Give it a name and click *"Create"*.
- Run the Lambda by clicking *"test"*.
- Scroll down in your *"log output"*, until you see your accounts and budgets in the log like this:

```
2020-05-04 14:29:21,448 | INFO | bunq | UserPerson "Your Name" (123456) | (bunq.py:166)
2020-05-04 14:29:21,834 | INFO | bunq |   Betaalrekening                  1,234.56 EUR  (78901234) | (bunq.py:156)
<redacted>
2020-05-04 14:29:22,353 | INFO | ynab | Accounts for budget "ThisIsYourBudgetName": | (ynab.py:100)
2020-05-04 14:29:22,824 | INFO | ynab |     1,234.56  BetaalBunq               (checking) | (ynab.py:94)
2020-05-04 14:29:22,833 | INFO | ynab |            0  SavingsBunq               (savings) | (ynab.py:94)
```

The configuration for this tool is stored in SSM Parameter Store. You will need to extract the following items from the output above for all accounts you would like to Sync!

- `bunq_user`: The number (123456) in the example above is your 'bunq_user' ID. Make a note of this.
- `bunq_acc`: Also make note of the accounts you'd like to sync (78901234) in the example above.
- `ynab_budget`: Make a note of your budget (ThisIsYourBudgetName) in the example above.
- `ynab_acc`: Finally find the account 'ynab_acc' (BetaalBunq) from the example above.

## Storing the configuration

You now have all the information you need to complete the configuration file.

- Go to the [AWS Systems Manager Parameter Store Console](https://console.aws.amazon.com/systems-manager/parameters)
- Open the **'bunq2ynab' parameter** and click **edit**
- Now add an entry for every account you'd like to sync (use the values you gathered above), like so:

```js
    {
      "bunq_acc": "78901234",
      "bunq_user": "123456",
      "ynab_acc": "BetaalBunq,
      "ynab_budget": "ThisIsYourBudgetName"
    },
    {
      "bunq_acc": "Example",
      "bunq_user": "Example",
      "ynab_acc": "Example,
      "ynab_budget": "Example"
    }
```
## Final test

- Go to the [AWS Lambda console](https://console.aws.amazon.com/lambda/), and open the function.
- Go to *"Environment variables"* and click edit.
- Disable *'LIST_MODE'* by setting the value to `0`.
- Save, and test your Lambda.
- Done! The Lambda will automatically sync every 5 minutes.

## Projected cost

All of the above should fall into the free-tier usage.
