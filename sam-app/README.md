# bunq2ynab for AWS Lambda. 

Forked from [wesselt/bunq2ynab](https://github.com/wesselt/bunq2ynab). 

```bash
├── README.md                  <- this file
├── bunq2ynab         
│   ├── app.py                 <- __main__ called from AWS Lambda
│   ├── applocal.py            <- __main__ use this when running locally
│   ├── bunq.py                <- Implements bunq API
│   ├── bunq2ynab.py           <- Implements sync between bunq and ynab
│   ├── common.py              <- Implements common logging function
│   ├── config.json            <- Example config file, populate yourself
│   ├── config.py              <- Implements reading and writing config
│   ├── errors.py              <- Implements Error classes
│   ├── logger.py              <- Implements logging
│   ├── parameter_store.py     <- Implements SSM for storing/reading config
│   ├── requirements.txt       <- Used by build process to install dependencies
│   └── ynab.py                <- Implements YNAB
├── event.json
└── template.yaml              <- SAM template, only used to build.
```

