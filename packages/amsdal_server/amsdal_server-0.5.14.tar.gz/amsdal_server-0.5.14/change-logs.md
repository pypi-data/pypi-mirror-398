## [v0.5.14](https://pypi.org/project/amsdal_server/0.5.14/) - 2025-12-22

### Changed

- Update pydantic to 2.12

## [v0.5.13](https://pypi.org/project/amsdal_server/0.5.13/) - 2025-12-11

### Changed

- Unquote filter values

## [v0.5.12](https://pypi.org/project/amsdal_server/0.5.12/) - 2025-12-07

### Added

- Support for contrib transactions

## [v0.5.11](https://pypi.org/project/amsdal_server/0.5.11/) - 2025-12-02

### Added

- Support for MFA

## [v0.5.10](https://pypi.org/project/amsdal_server/0.5.10/) - 2025-11-14

### Added

- Support for nested filters

## [v0.5.9](https://pypi.org/project/amsdal_server/0.5.9/) - 2025-09-04

### Added

- Support for file storages

## [v0.5.8](https://pypi.org/project/amsdal_server/0.5.8/) - 2025-08-12

### Added

- Disposition type for file downloads.

## [v0.5.7](https://pypi.org/project/amsdal_server/0.5.7/) - 2025-08-06

### Changes

- Improvements for slack notifications middleware

## [v0.5.6](https://pypi.org/project/amsdal_server/0.5.6/) - 2025-08-05

### Changes

- Improvements for slack notifications middleware

## [v0.5.5](https://pypi.org/project/amsdal_server/0.5.5/) - 2025-07-31

### Changes

- Switched to uv package manager

## [v0.5.4](https://pypi.org/project/amsdal_server/0.5.4/) - 2025-07-28

### Changes

- Adjustments to slack notifications

## [v0.5.3](https://pypi.org/project/amsdal_server/0.5.3/) - 2025-07-15

### Added

- Slack notification middleware added to handle exceptions and send alerts to a Slack channel.

## [v0.5.2](https://pypi.org/project/amsdal_server/0.5.2/) - 2025-07-04

### Changed

- Optimizations for files

## [v0.5.1](https://pypi.org/project/amsdal_server/0.5.1/) - 2025-06-23

### Fixed

- Fix handling of mimetypes for files

## [v0.5.0](https://pypi.org/project/amsdal_server/0.5.0/) - 2025-05-22

### Changed

- Adjustments for the migrations improvements

## [v0.4.2](https://pypi.org/project/amsdal_server/0.4.2/) - 2025-04-26

### Fixed

- Fix for partial models

## [v0.4.1](https://pypi.org/project/amsdal_server/0.4.1/) - 2025-03-11

### Fixed

- Normalize lakehouse address
- Force insert for create APIs

## [v0.4.0](https://pypi.org/project/amsdal_server/0.4.0/) - 2025-02-25

### Changed

- Update `amsdal` version

## [v0.3.6](https://pypi.org/project/amsdal_server/0.3.6/) - 2024-02-18


### Fixed

- Return valid metadata on `all_versions=true` (metadata-all-versions)


## [v0.3.5](https://pypi.org/project/amsdal_server/0.3.5/) - 2024-01-10


### Added

- Async delete (async-delete)


## [v0.3.4](https://pypi.org/project/amsdal_server/0.3.4/) - 2024-12-14


### Added

- Support async properties (async-properties)

## [v0.3.3](https://pypi.org/project/amsdal_server/0.3.3/) - 2024-12-09


### Added

- async_build_missing_models function (async-build-missing-models)


## [v0.3.2](https://pypi.org/project/amsdal_server/0.3.2/) - 2024-12-07


### Added

- Async support (async-support)
## [v0.3.1](https://pypi.org/project/amsdal_server/0.3.1/) - 2024-12-02


### Added

- Added support for Inf values (inf-values)
## [v0.3.0](https://pypi.org/project/amsdal_server/0.3.0/) - 2024-11-28


### Changed

- Metadata redesign: moving metadata into historical connection (metadata-redesign)
## [v0.2.5](https://pypi.org/project/amsdal_server/0.2.5/) - 2024-11-11


### Added

- Cache options (cache-options)
## [v0.2.4](https://pypi.org/project/amsdal_server/0.2.4/) - 2024-11-06


### Added

- Select related for object requests (select-related)
## [v0.2.3](https://pypi.org/project/amsdal_server/0.2.3/) - 2024-10-28


### Fixed

- Fixed list objects with file optimized flag (fil-optimized)
## [v0.2.2](https://pypi.org/project/amsdal_server/0.2.2/) - 2024-10-25


### Changed

- Change file download to async to not use threads (async-file-download)
## [v0.2.1](https://pypi.org/project/amsdal_server/0.2.1/) - 2024-10-23


### Added

- Psycopg OTEL package (psycopg-otel)
## [v0.2.0](https://pypi.org/project/amsdal_server/0.2.0/) - 2024-10-16


### Added

- AMSDAL Glue integration (amsdal-glue)
## [v0.1.25](https://pypi.org/project/amsdal_server/0.1.25/) - 2024-10-04


### Fixed

- Fixed filed download for JSON files (json-download)
## [v0.1.24](https://pypi.org/project/amsdal_server/0.1.24/) - 2024-10-02


### Added

- OpenTelemetry optional dependencies (otel)
## [v0.1.23](https://pypi.org/project/amsdal_server/0.1.23/) - 2024-08-14


### Added

- Add connections liveness check to liveness probe (connection-is-alive)
## [v0.1.22](https://pypi.org/project/amsdal_server/0.1.22/) - 2024-08-08


### Fixed

- Fixed link in documentation (link-in-docs)
## [v0.1.21](https://pypi.org/project/amsdal_server/0.1.21/) - 2024-06-12

**Fixed**

- Fix include subclasses functionality (fix-include-subclasses-functionality)


## [v0.1.20](https://pypi.org/project/amsdal_server/0.1.20/) - 2024-06-12

**Added**

- Add case insensitive filters (add-case-insensitive-filters)


## [v0.1.19](https://pypi.org/project/amsdal_server/0.1.19/) - 2024-06-04

**Added**

- Filter controls generation (filter-controls-generation)


## [v0.1.18](https://pypi.org/project/amsdal_server/0.1.18/) - 2024-05-31

**Fixed**

- Build models from schemas in the DB if they do not exist in the file system (build-models-from-schemas-in-the-db-if-they-do-not-exist-in-the-file-system)


## [v0.1.17](https://pypi.org/project/amsdal_server/0.1.17/) - 2024-05-30

**Added**

- Bulk operations support (bulk-operations-support)


## [v0.1.16](https://pypi.org/project/amsdal_server/0.1.16/) - 2024-05-29

**Added**

- New endpoint for the file download that receives the object id as query parameter (new-endpoint-for-the-file-download-that-receives-the-object-id-as-query-parameter)


## [v0.1.15](https://pypi.org/project/amsdal_server/0.1.15/) - 2024-05-28

**Fixed**

- Fix for API Schema creation (fix-for-api-schema-creation)


## [v0.1.14](https://pypi.org/project/amsdal_server/0.1.14/) - 2024-05-09

**Changed**

- Improvement for the permissions (improvement-for-the-permissions)


## [v0.1.13](https://pypi.org/project/amsdal_server/0.1.13/) - 2024-04-25

**Changed**

- Improved logging for the server (improved-logging-for-the-server)


## [v0.1.12](https://pypi.org/project/amsdal_server/0.1.12/) - 2024-04-19

**Changed**

- Make file download endpoint sync (make-file-download-endpoint-sync)


## [v0.1.11](https://pypi.org/project/amsdal_server/0.1.11/) - 2024-04-19

**Fixed**

- Fixed image resize for PNG files (fixed-image-resize-for-png-files)



## [v0.1.10](https://pypi.org/project/amsdal_server/0.1.10/) - 2024-04-18

**Added**

- Image resize in file download (image-resize-in-file-download)


## [v0.1.9](https://pypi.org/project/amsdal_server/0.1.9/) - 2024-04-12

**Changed**

- Empty page size disables pagination (empty-page-size-disables-pagination)


## [v0.1.8](https://pypi.org/project/amsdal_server/0.1.8/) - 2024-04-11

**Added**

- Pagination and ordering added (pagination-and-ordering)


## [v0.1.7](https://pypi.org/project/amsdal_server/0.1.7/) - 2024-04-04

**Fixed**

- Handle corrupted files in file download (handle-corrupted-files-in-file-download)


## [v0.1.6](https://pypi.org/project/amsdal_server/0.1.6/) - 2024-04-04

**Added**

- Endpoint to download the file content (endpoint-to-download-the-file-content)



## [v0.1.5](https://pypi.org/project/amsdal_server/0.1.5/) - 2024-03-28

**Changed**

- Decode bytes in the transaction data (decode-bytes-in-the-transaction-data)



## [v0.1.4](https://pypi.org/project/amsdal_server/0.1.4/) - 2024-03-27

**Changed**

- Use actual `.count()` method to get the number of objects in the queryset (use-actual-count-method-to-get-the-number-of-objects-in-the-queryset)


## [v0.1.3](https://pypi.org/project/amsdal_server/0.1.3/) - 2024-03-22

**Fixed**

- Fix for filter by the latest version (fix-for-filter-by-the-latest-version)


## [v0.1.2](https://pypi.org/project/amsdal_server/0.1.2/) - 2024-03-21

**Changed** 

- Downgrade minimum version of Pydantic to 2.3


## [v0.1.1](https://pypi.org/project/amsdal_server/0.1.1/) - 2024-03-21

**Changed** 

- Change version pins to `compatible releases` (change-version-pins-to-compatible-releases)


## [v0.1.0](https://pypi.org/project/amsdal_server/0.1.0/) - 2024-03-21

**Changed** 

- Upgraded `amsdal_utils`, `amsdal_data`, `amsdal_model` and `amsdal` dependencies to `0.1.*` (upgraded-amsdal-utils-amsdal-data-amsdal-model-and-amsdal-dependencies)
