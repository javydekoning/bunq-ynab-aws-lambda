# bunq2ynab (AWS Lambda)

A tool to sync one or more [bunq](https://www.bunq.com/) accounts to [YNAB](https://www.youneedabudget.com/). It's build to run in AWS Lambda at near zero costs.

This project is a fork from [wesselt/bunq2ynab](https://github.com/wesselt/bunq2ynab).

## Changes in this fork:
  * Improved logging.
  * Single config location.
    * Config can be stored in an AWS SSM Parameter (for use by AWS Lambda)
    * Or a single `.json` file.
  * AWS Lambda compatible
  * AWS CDK (Python to deploy the app)
  * Consolidated to a single main `.py` file to be executed by AWS Lambda. Added an environment variable for listing bunq and YNAB budgets.
  * Added a commandline switch (`-l`) for listing bunq and YNAB budgets.

The `__main__` file for Lambda is `app.py`, I also included an `applocal.py` to run on your local machine. 

## Building and deploying: 

To build and deploy this project yourself, you will need: 

* [Serverless Application Model (SAM)](https://github.com/awslabs/serverless-application-model), you can find install instructions [here](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) 
* [AWS-CDK](https://github.com/aws/aws-cdk). You can install from NPM like this:
  * `npm i -g aws-cdk`

## Building the app: 

Go into the project folder and run `sam build`. This will install the Python modules such as `requests`. I recommend using the `--use-container` command-line switch. This will require that you have Docker installed and running.

```
cd projectfolder/sam-app
sam build --use-container
```

## Deploying the app: 

```
cdk bootstrap
cdk deploy
```

This will create a `AWSLambdaBasicExecutionRole`, the Lambda itself, SSM Parameter (to store config) and a CloudWatch Events rule that runs the Lambda on a 15 min interval to sync from Bunq to Ynab. The `AWSLambdaBasicExecutionRole` will be granted `ssm:GetParameter` and `ssm:PutParameter` permissions to the created SSM Parameter to store and fetch the configuration. 


## Getting started

To get started you need a config with atleast the bunq `api_token` and the YNAB `accesstoken` populated. The other bunq and YNAB parameters will get populated on first run.

* You can get the BUNQ in the BUNQ mobile app. Click your picture, then Security, API keys, then add a key using the plus on the top right. Choose to "Reveal" the API key and share it. **Don't share this API key with anyone!**
* You can get the YNAB access token [here](https://app.youneedabudget.com/settings/developer).  

The bunq2ynab section will hold the sync pairs. e.g. which bunq account to which YNAB account. If you don't know what they are you can run the Lambda in `LIST_MODE` by setting the environment variable to `1` **OR** run `applocal.py` with the `-l` commandline switch.

Here is an example config file: 

```
{
	"bunq": {
		"api_token": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
		"priv_key": "",
		"install_token": "",
		"server_pub_key": "",
		"session_token": ""
	},
	"bunq2ynab": [{
			"bunq_user": "",
			"bunq_acc": "",
			"ynab_budget": "",
			"ynab_acc": ""
		},
		{
			"bunq_user": "",
			"bunq_acc": "",
			"ynab_budget": "",
			"ynab_acc": ""
		}
	],
	"ynab": {
		"accesstoken": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
		"clientid": "",
		"clientsecret": ""
	}
}
```
