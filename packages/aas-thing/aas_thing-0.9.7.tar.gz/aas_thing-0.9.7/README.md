# Asset Administration Shell (AAS) Thing Python SDK  

[![PyPI Release](https://img.shields.io/badge/pypi-v1.0.0_-orange)](https://pypi.org/project/fml40-reference-implementation/)  [![License: LGPL v3](https://img.shields.io/badge/License-LGPLv3%20-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0.html)

A Python toolkit for building **Industry 4.0**-compliant Things using Asset Administration Shell (AAS), with seamless integration into the Smart Systems Service Infrastructure (S³I). 
Please refer to the whitepaper for details:

> Hoppen M., Chen, J., Roßmann, J. (2025) Smart Systems Service Infrastructure (S3I) — Design and deployment of the Smart Systems Service Infrastructure (S3I) for decentralized networking in Forestry 4.0. KWH4.0 Position Paper. DOI: [10.18154/RWTH-2025-03168](https://doi.org/10.18154/RWTH-2025-03168) 

---

## Table of Contents

- [Overview](#overview)  
- [Features](#features)  
  - [Core Functionality](#core-functionality)  
  - [Roadmap](#roadmap) 
- [Technical Structure](#technical-structure)  
- [Installation](#installation)  
- [Documentation](#documentation)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Overview

The AAS Thing Python SDK helps you:

- Instantiate and manipulate AAS and submodels using the Eclipse [BaSyx Python SDK](https://github.com/eclipse-basyx/basyx-python-sdk)
- Exchange standardized I4.0 messages ([VDI 2193-1](https://www.vdi.de/fileadmin/pages/vdi_de/redakteure/richtlinien/inhaltsverzeichnisse/3134409.pdf)) over AMQP (store-and-forward) or (in future) HTTP  
- Authenticate, manage and discover services, exchange information via the S³I core (IdentityProvider, Directory, Repository, Broker)  

By following the AAS specification, your Things become members in Industry 4.0 ecosystems, interoperating securely and reliably.

---

## Features

### Core Functionality

- **AAS management**  
  Load and parse `.json`, `.xml`, or `.aasx` AAS on disk using [BaSyx Python SDK](https://github.com/eclipse-basyx/basyx-python-sdk).

- **Message-based communication**  
  Create, send and receive I4.0 messages (`I40Message`) combined with the AAS API specification defined in [Specification of the Asset Administration Shell Part 2](https://industrialdigitaltwin.org/en/content-hub/aasspecifications/specification-of-the-asset-administration-shell-part-2-application-programming-interfaces-idta-number-01002-3-0-4), over AMQP (store-and-forward) or (in future) HTTP.


- **S³I integration**  
  - **IdentityProvider**: OpenID Connect authentication via Keycloak  
  - **Broker**: AMQP 0.9 messaging with RabbitMQ  
  - **Directory & Repository**: Endpoint discovery and cloud storage  

### Global instance of S³I
  We provide a global instance of the S³I, which runs in a server located at [MMI](https://www.mmi.rwth-aachen.de/), RWTH Aachen University and can be used for testing. It includes:

| Name                        | Endpoint                                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------------------|
| `S³I IdentityProvider`      | https://idp.mmi-0.s3i.mmi-services.de/                                                                  |
| `S³I Broker`                | https://broker.mmi-0.s3i.mmi-services.de/                                                                |
| `S³I Directory`             | [https://dir.mmi-0.s3i.mmi-services.de/](https://dir.mmi-0.s3i.mmi-services.de/swagger-ui/index.html)   | 
| `S³I Repository`            | [https://repo.mmi-0.s3i.mmi-services.de/](https://repo.mmi-0.s3i.mmi-services.de/swagger-ui/index.html) |
| `S³I Config`                | [https://config.mmi-0.s3i.mmi-services.de/](https://config.mmi-0.s3i.mmi-services.de/apidoc)            |
| `S³I Postbox API`           | [https://postbox.mmi-0.s3i.mmi-services.de/](http://postbox.mmi-0.s3i.mmi-services.de/apidoc)           |	
| `S³I Manager (coming soon)` | http://manager.mmi-0.s3i.mmi-services.de/                                                               |	

### Roadmap of the SDK
In the near future, we will provide the supports to: 
- **Postbox API**: REST-based alternative to AMQP for sending and receiving I4.0 messages
- **Discovery Service**: Endpoint discovery using query parameters
- **Authorization**: XACML-based access control framework 
- **Events**: Support for AAS- and AMQP-based events
- **Server Infrastructure**: The open-source server infrastructure for the Smart Systems Service Infrastructure (S³I) and its configuration for docker and kubernetes

---

## Technical Structure

| Module                               | Purpose                                                                              |
|--------------------------------------|--------------------------------------------------------------------------------------|
| `aas_thing/core.py`                  | `BaseAASThing`: lifecycle, configuration, event loop                                 |
| `aas_thing/aas_connection.py`        | `AASConnector`: load/sync AAS & submodels                                            |
| `aas_thing/s3i_connection.py`        | `S3IConnector`: interface to S³I IdentityProvider, Broker                            | 
| `aas_thing/message_handler.py`       | `I40SemanticProtocolHandler`: handle_request, handle_reply of incoming I4.0 messages |
| `aas_thing/s3i.identity_provider.py` | `S3IIdentityProviderClient`: create connection to S³I IdP                            |
| `aas_thing/s3i.broker.py`            | `S3IBrokerAMQPClient`: create connection to S³I Broker                               |
| `aas_thing/s3i.directory.py`         | `S3IDirectoryClient`: create connection with S³I Directory                           |
| `aas_thing/s3i.repository.py`        | `S3IRepositoryClient`: create connection with S³I Repository                         |

---

## Installation

Install from PyPI:

```bash
$ python -m pip install aas-thing
```

Or build & install from source:

```bash
$ git clone git@git.rwth-aachen.de:co2for-it/s3i/aas-thing-python-sdk.git
$ cd aas-thing-python-sdk
$ python -m pip install .
```

## Documentation
Full API reference, tutorials, and demos are available in the [documentation](https://co2for-it.pages.rwth-aachen.de/s3i/aas-thing-python-sdk/).

## Contributing
Contributions, bug reports, and feature requests are welcome! 

Please:

- Fork the repository
- Create a feature branch (``git checkout -b feature/XYZ``)
- Commit your changes (``git commit -m "Add XYZ"``)
- Push to your fork (``git push origin feature/XYZ``)
- Open a Merge Request

See ``CONTRIBUTING.md`` for detailed guidelines.

## License
This project is licensed under the LGPL v3 License. See the ``LICENSE`` file for details.