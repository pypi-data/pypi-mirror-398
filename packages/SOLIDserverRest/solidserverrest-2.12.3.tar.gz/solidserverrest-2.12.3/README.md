[![License](https://img.shields.io/badge/License-BSD%202--Clause-blue.svg)](https://opensource.org/licenses/BSD-2-Clause)

[![pipeline status](https://gitlab.com/efficientip/solidserverrest/badges/master/pipeline.svg)](https://gitlab.com/efficientip/solidserverrest/commits/master)

# SOLIDserverRest

This 'SOLIDserverRest' allows to easily interact with [SOLIDserver](https://www.efficientip.com/products/solidserver/)'s REST API.
It allows managing all IPAM objects through CRUD operations.

* ***Free software***: BSD2 License

This 'SOLIDserverRest' is compatible with [SOLIDserver](https://www.efficientip.com/products/solidserver/) version 7 and ownward.

# Install
Install 'SOLIDserverRest' using pip in your virtualenv:

```
	pip install SOLIDserverRest
```

# Usage

## Using the SOLIDserverRest advanced object (recommended)

### With basic authentication

All commands and object manipulation are going through a SOLIDserver main object, handling the connection to the manager and pushing API calls. The creation of a SOLIDserver object is done like that:
```
from SOLIDserverRest import *
from SOLIDserverRest import adv as sdsadv

SDS_HOST = "192.168.254.254"
SDS_LOGIN = "foo"
SDS_PWD = "bar"

sds = sdsadv.SDS(ip_address=SDS_HOST,
                 user=SDS_LOGIN,
                 pwd=SDS_PWD)
try:
    sds.connect()
except SDSError as e:
    logging.error(e)
    exit(1)

print(sds)

```

## With token authentication (SDS release >= 8.4.0)

```
from SOLIDserverRest import *
from SOLIDserverRest import adv as sdsadv

SDS_HOST = "192.168.254.254"
SDS_TOKEN_ID = "8628f88cbd40df99903d6f385caa0462"
SDS_TOKEN_SEC = "ca8ec3c0f07b380c4723349230901d40a84ba4b4987c12863b66b0b5297ad922"

sds = sdsadv.SDS(ip_address=SDS_HOST)
sds.set_token_creds(keyid=SDS_TOKEN_ID,
                    keysecret=SDS_TOKEN_SEC)
try:
    sds.connect(method="token")
except SDSError as e:
    logging.error(e)
    exit(1)

print(sds)

```

More examples in the example directory.

## Using the SOLIDserverRest object (basic mapping)

The raw API is mapped using the SOLIDserverRest object which handle the connection, prepare the formating and handle some errors. It can be usefull twhen the advanced library is not yet implementing an object that you require in your code.

### 1. Declare endpoint API point
Set the API endpoint you want to talk with through API. Could use an IP address
(v4 or v6) or a host name
* host = IP address of the SOLIDserver server
```
con = SOLIDserverRest("fqdn_host.org")
```

### 2. Specify connection method
You can use native connection mode using SOLIDserver default method which provide
authentication through headers in the requests with information
encoded in base64

* user = user who want to use
* password = password of the user

```python
	con.use_native_sds(user="apiuser", password="apipwd")
```

You can also use the basic authentication method for connecting the SOLIDserver.

* user = user who want to use
* password = password of the user

```python
	con.use_basicauth_sds(user="apiuser", password="apipwd")
```

### 3. Set TLS security
SSL certificate chain is validated by default, to disable it, use the set_ssl_verify method

```python
        con.set_ssl_verify(False)  # True by default
	rest_answer = con.query("method", "parameters")
```

Otherwise, you have to provide the certificate file:
```python
    con = SOLIDserverRest(SERVER)
```
If the certificate file is not valide, an exception ```SDSInitError``` is raised.

### 4. Request to SOLIDserver API

You need parameters:
* method = choose your method in the list below
* parameters = Python dictionary with parameters you want to use

```python
	rest_answer = con.query("method", "parameters")
```

### 5. Analyze answer

* rest_answer => object name
* rest_answer.status_code => current http answer code set in the object
* rest_answer.content => Answer core from SOLIDserver API set in the object

Example:
```python
	print(rest_answer)
	print(rest_answer.status_code)
	print(rest_answer.content)
```

# Methods that could be used
Methods are organized to match the ontology used in SOLIDServer, you will find:
* Sites - address spaces
* Subnets (v4 and v6)
* Pools (v4 and v6)
* Addresses (v4 and v6)
* Aliases (v4 and v6)
* DNS servers, views, zones, RR, acl, key
* application manager
* DHCP server, scope, shared net, range, static, group, options
* device manager
* VLAN manager
* Network Object Manager

More information about supported methods in the [specific document](docs/METHODS.md)

# Tests

Last set of tests run on 29/Sep/2025 using:
 * SOLIDserver release 8.3.2
 * python libs:
   * requests           2.32.5
   * urllib3            2.5.0
   * idna               3.10
   * PySocks            1.7.1
   * chardet            5.2.0
   * pyOpenSSL          25.3.0
   * packaging          24.2
   * macaddress         2.0.2

## coverage results
```
---------- coverage: platform win32, python 3.11.3-final-0 -----------
Name                                        Stmts   Miss  Cover
---------------------------------------------------------------
SOLIDserverRest\Exception.py                   24      4    83%
SOLIDserverRest\SOLIDserverRest.py            168     20    88%
SOLIDserverRest\__init__.py                     4      0   100%
SOLIDserverRest\adv\__init__.py                16      0   100%
SOLIDserverRest\adv\base.py                   116     19    84%
SOLIDserverRest\adv\class_params.py            97      4    96%
SOLIDserverRest\adv\device.py                  86     72    16%
SOLIDserverRest\adv\device_tools.py           127    113    11%
SOLIDserverRest\adv\devif.py                  121     99    18%
SOLIDserverRest\adv\dns.py                    149     65    56%
SOLIDserverRest\adv\dns_record.py             403    117    71%
SOLIDserverRest\adv\dns_view.py               104     37    64%
SOLIDserverRest\adv\dns_zone.py               143     19    87%
SOLIDserverRest\adv\ipaddress.py              151      5    97%
SOLIDserverRest\adv\network.py                228      8    96%
SOLIDserverRest\adv\nom_folder.py             118      9    92%
SOLIDserverRest\adv\nom_interface.py          317     47    85%
SOLIDserverRest\adv\nom_network_object.py     126     27    79%
SOLIDserverRest\adv\sds.py                    149     10    93%
SOLIDserverRest\adv\space.py                  147     50    66%
SOLIDserverRest\adv\validators.py              28      6    79%
SOLIDserverRest\mapper.py                      24      0   100%
---------------------------------------------------------------
TOTAL                                        2846    731    74%
```