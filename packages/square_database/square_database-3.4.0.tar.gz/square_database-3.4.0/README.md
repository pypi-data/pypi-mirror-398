# square_database

> 📌 versioning: see [CHANGELOG.md](./CHANGELOG.md).

## about

a database layer for my personal server. this service exposes database operations as a fastapi application, powered by
pluggable orm models (by default from square_database_structure, but you can swap in your own).

## goals

- centralized database api
- pluggable orm models
- simple crud operations
- stored procedure support
- realtime via websockets

## installation

```shell
pip install square_database[all]
```

## usage

### configuration

update the settings in `config.ini` and `config.testing.ini` to match your environment (database url, logging, etc).

### models

this service requires orm models from a pluggable module. the default is [
`square_database_structure`](https://github.com/thepmsquare/square_database_structure), but you can provide your own
module if needed.

### running the service

```shell
python square_database/main.py
```

## env

- python>=3.12.0

> feedback is appreciated. thank you!
