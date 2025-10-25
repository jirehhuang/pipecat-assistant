---
name: Convert template
about: Convert template
title: Convert template
labels: []
assignees: []
---

# Checklist

- [ ] Add `main` ruleset
- [ ] Update `FUNCTION_NAME` in [ci-cd.yml](.github/workflows/ci-cd.yml)
- [ ] Create Lambda execution role
- [ ] Modify the docstring in [`__init__.py`](lambda_function/__init__.py)
- [ ] Tailor the [README](README.md)
- [ ] Delete the issue template
- [ ] Add API Gateway trigger
- [ ] Create Alexa skill

# Instructions

## Add `main` ruleset

Create and activate a branch ruleset named `main ruleset` that applies to the default branch (`main`).
Ensure the following are selected:

- Restrict deletions
- Require a pull request before merging
    - Require conversation resolution before merging
    - Automatically request Copilot code review
    - Allowed merge methods: Merge, Squash
- Block force pushes

## Create Lambda execution role

[Create Lambda execution role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html#permissions-executionrole-console) named "`FUNCTION_NAME`-role" with policy `AWSLambdaBasicExecutionRole`.
Attach any additional policies that the function will require, such as `AmazonDynamoDBFullAccess`.
If named correctly, this role will automatically be attached to the Lambda when it is created by the workflow.

## Add API Gateway trigger

1. Navigate to AWS Console > API Gateway and create a new REST API with name "`FUNCTION_NAME`-staging" (Regional, IPv4)
1. Create a method with type ANY and integration with Lambda function "{`FUNCTION_NAME` ARN}:staging", where the appended ":staging" points to the staging alias
1. Edit the method request settings to require API key
1. Deploy the API to a new stage named "staging" and copy the invoke URL to `.env` as `STAGING_API_URL`
1. Create a usage plan named "`FUNCTION_NAME`-plan-staging" and add the associated REST API and stage
1. Add a new API key named "`FUNCTION_NAME`-api-key-staging" and add it to `.env` and [GitHub actions secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets) as `STAGING_API_KEY`

After merging the pull request into `main`, repeat these steps for "prod" in place of "staging" and re-run the workflow.
You can also repeat with "latest" in place of "staging" to test the latest deployment locally.

## Create Alexa skill

If the Lambda will be the backend for an Alexa skill, [create a custom Alexa skill](https://developer.amazon.com/en-US/docs/alexa/custom-skills/steps-to-build-a-custom-skill.html) by creating it in the developer console and choosing to provision your own backend.
Alternatively, you can create it with a hosted backend and update the endpoint.

Then, navigate to the build endpoint and add the Lambda ARN for all applicable regions.
Copy the Alexa Skill ID and add it as an Alexa trigger in the Lambda function configuration.
If desired, the integration can be established for a specific alias, such as by appending ":staging" to the Lambda ARN and then adding the Skill ID as a trigger in the staging alias configuration.
