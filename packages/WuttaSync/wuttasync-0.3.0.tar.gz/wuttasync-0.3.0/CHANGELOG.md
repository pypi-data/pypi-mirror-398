
# Changelog
All notable changes to WuttaSync will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## v0.3.0 (2025-12-20)

### Feat

- add `warnings` mode for import/export handlers, commands
- add the `import-versions` command, handler logic

### Fix

- run all models when none specified, for import/export commands
- allow passing just `key` to ImportCommandHandler
- add `--comment` param for `import-versions` command
- add basic data type coercion for CSV -> SQLAlchemy import
- refactor some more for tests + pylint
- refactor per pylint; add to tox
- format all code with black
- tweak logging when deleting object
- add logging when deleting target object

## v0.2.1 (2025-06-29)

### Fix

- avoid empty keys for importer
- do not assign simple/supported fields in Importer constructor
- make `--input-path` optional for import/export commands

## v0.2.0 (2024-12-07)

### Feat

- add `wutta import-csv` command

### Fix

- expose `ToWuttaHandler`, `ToWutta` in `wuttasync.importing` namespace
- implement deletion logic; add cli params for max changes
- add `--key` (or `--keys`) param for import/export commands
- add `--list-models` option for import/export commands
- require latest wuttjamaican
- add `--fields` and `--exclude` params for import/export cli

## v0.1.0 (2024-12-05)

### Feat

- initial release
