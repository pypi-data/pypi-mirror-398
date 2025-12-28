[![Test python](https://github.com/yu-iskw/bq-validator/actions/workflows/test.yml/badge.svg)](https://github.com/yu-iskw/bq-validator/actions/workflows/test.yml)
<a href="https://pypi.org/project/bq-validator" target="_blank">
<img src="https://img.shields.io/pypi/v/bq-validator?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://pypi.org/project/bq-validator" target="_blank">
<img src="https://img.shields.io/pypi/pyversions/bq-validator.svg?color=%2334D058" alt="Supported Python versions">
</a>

# bq-validator

This is a yet another python-based BigQuery query validator.

The `bq query --dry_run` command enables us to validate queries.
However, the `bq` command doesn't support service account impersonation, even though it supports workload identity federation credentials at Google Cloud SDK 390.0.0.
The `bq-validator` command would be useful, when we take advantage of service account impersonation to validate BigQuery queries.

## Install

The package is available on [pypi](https://pypi.org/project/bq-validator/)

```bash
pip install -U bq-validator
```

## How to use

```bash
$ bq-validator --help
Usage: bq-validator [OPTIONS] PATH

  Validate BigQuery queries

  PATH is either of a SQL file path or a directory. When it is a directory,
  the command recursively validates all SQL files in the directory.

Options:
  --quota_project TEXT            BigQuery client project ID
  --client_project TEXT           BigQuery client project ID
  --client_location TEXT          BigQuery client location
  --impersonate_service_account TEXT
                                  Impersonate service account email
  --num_parallels INTEGER         Number of parallel query validations
  --verbose                       Enable verbose output
  --version                       Show the version and exit.
  --help                          Show this message and exit.
```
