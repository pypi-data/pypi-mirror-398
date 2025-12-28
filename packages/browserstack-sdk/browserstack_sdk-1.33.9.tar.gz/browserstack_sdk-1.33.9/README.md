# browserstack-sdk
Python SDK for browserstack selenium-webdriver tests. Easily run your tests across multiple platforms and manage test context.

* Install the package using:
`pip install browserstack-sdk`

* Verify your install with:
`browserstack-sdk --version`

## Config
* Specify the config in a `browserstack.yml` file at root of your project.

## Running python, robot and pabot tests across multiple platforms using SDK

### Robot & Pabot
1. To run your Robot test on browserstack, use `browserstack-sdk robot <test-file>.robot`.
2. To run multiple tests in parallel on browserstack, use `browserstack-sdk pabot <test-files>*.robot`.

### Python:
1. If you have test script written in vanilla python, you can easily run that test across platforms on browserstack.
2. Use `browserstack-sdk <test-file>.py`.
