# Robot Framework MongoDBLibrary

MongoDBLibrary is a test library for [Robot Framework](https://robotframework.org/) that provides keywords for interacting with MongoDB databases.

## Features
- Connect to MongoDB instances
- Perform CRUD operations
- Support for authentication and connection pooling
- Designed for use in Robot Framework test suites

## Installation

```bash
pip install robotframework-mongodb
```

Or with Poetry:

```bash
poetry add robotframework-mongodb
```

## Usage Example

```robotframework
*** Settings ***
Library    MongoDBLibrary

*** Test Cases ***
Connect To MongoDB
    Connect To Database    mongodb://localhost:27017    mydb
    # ... your test steps ...
```

## License
MIT

## Author
MobyNl <markmoberts@gmail.com>
