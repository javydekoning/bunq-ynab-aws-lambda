#!/usr/bin/env python3

from aws_cdk import (
    aws_events as events,
    aws_lambda as lambda_,
    aws_events_targets as targets,
    aws_ssm as ssm,
    aws_iam as iam,
    core,
)

class bunq2ynab(core.Stack):
    def __init__(self, app: core.App, id: str) -> None:
        super().__init__(app, id)

        with open("ssm.json", encoding="utf8") as ssmjson:
            ssmvalue = ssmjson.read()

        param = ssm.StringParameter(
            self, "bunq2ynabParam", 
            parameter_name='/lambda/bunq2ynab',
            string_value=ssmvalue
        )

        lambdaFn = lambda_.Function(
            self, "MyCDKapp",
            code=lambda_.Code.asset('./sam-app/.aws-sam/build/bunq2ynab'),
            handler="app.lambda_handler",
            timeout=core.Duration.seconds(300),
            runtime=lambda_.Runtime.PYTHON_3_7,
            environment= {
                "LIST_MODE": "0",
                "LOG_LEVEL": "INFO",
                "SSM_PARAM": param.parameter_name
            }
        )

        #Add ssm permissions to the Lambda Role.
        polst = iam.PolicyStatement(
            actions=['ssm:GetParameter','ssm:PutParameter'],
            resources=[param.parameter_arn]
        )
       
        lambdaFn.add_to_role_policy(polst)

        #Run every 15 minutes.
        rule = events.Rule(
            self, "Rule",
            schedule=events.Schedule.expression('rate(15 minutes)')
        )
        rule.add_target(targets.LambdaFunction(lambdaFn))

app = core.App()
bunq2ynab(app, "bunq2ynab")
app.synth()
