# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2023-02-24 13:08:42 alex>
#
# only for python v3

"""
SOLIDserver management server access
"""

import logging
import ipaddress
import socket
import json

from json.decoder import JSONDecodeError

from SOLIDserverRest.Exception import SDSInitError, SDSAuthError
from SOLIDserverRest.Exception import SDSEmptyError
from SOLIDserverRest import SOLIDserverRest

from .class_params import ClassParams

__all__ = ["SDS"]


# more than 7 arguments to class
# pylint: disable=R0902
class SDS(ClassParams):
    """ class to get connected to a SDS server """

    # ---------------------------
    def __init__(self, ip_address=None, user=None, pwd=None):
        """init the SDS object:
        """
        super().__init__()

        self.sds_ip = None
        if ip_address is not None:
            # is the ip_address an IPv4 one?
            try:
                ipaddress.IPv4Address(ip_address)
                self.set_server_ip(ip_address)
            except ipaddress.AddressValueError:
                self.set_server_name(ip_address)

        self.user = None
        self.pwd = None
        if user is not None and pwd is not None:
            self.set_credentials(user, pwd)

        self.version = None

        self.auth_method = None
        self.check_certificate = False

        # token authentication
        self.cred_token_keyid = None
        self.cred_token_keysecret = None

        self.sds = None
        self.timeout = 1

        self.proxy_socks = None

    # ---------------------------
    def set_server_ip(self, ip_address):
        """set the SOLIDserver IP address for the connection"""
        try:
            ipaddress.IPv4Address(ip_address)
        except ipaddress.AddressValueError as error:
            raise SDSInitError(message=f"IPv4 address of"
                               f" server error: {error}") from error

        self.sds_ip = ip_address

    # ---------------------------
    def set_server_name(self, fqdn):
        """set the SOLIDserver FQDN for the connection"""
        # check that the IP exists
        try:
            _ = socket.gethostbyname(fqdn)
        except socket.gaierror as error:
            raise SDSInitError(message=f"FQDN of the SDS: {error}") from error

        self.sds_ip = fqdn

    # ---------------------------
    def set_proxy_socks(self, proxy=None):
        """set the SOLIDserver connection through a socks proxy"""
        if proxy:
            self.proxy_socks = proxy

    # ---------------------------
    def set_credentials(self, user=None, pwd=None):
        """add user and login to credentials of this session"""
        if user is None or pwd is None:
            msg = "missing user or password in credentials"
            raise SDSInitError(message=msg)
        self.user = user
        self.pwd = pwd

    def set_token_creds(self, keyid=None, keysecret=None):
        """add token credentials to this session"""
        if keyid is None or keysecret is None:
            msg = "missing token information in credentials"
            raise SDSInitError(message=msg)
        self.cred_token_keyid = keyid
        self.cred_token_keysecret = keysecret

    # ---------------------------
    def set_check_cert(self, check=True):
        """whether we have to check the certificate, even if not provided"""
        self.check_certificate = check

    # ---------------------------
    def connect(self, method="basicauth", cert_file_path=None, timeout=None):
        """connects to SOLIDserver and check everything is OK by
           querying the version of the admin node in the member list

           method -- basicauth (default) or native (header based) or token
           cert_file_path -- disable SSL check if None (default)
                             file with cert if check enabled
        """

        if self.sds_ip is None:
            raise SDSInitError(message="missing ip for server for connect")

        self.sds = SOLIDserverRest(self.sds_ip)

        if method == "basicauth":
            if self.user is None or self.pwd is None:
                msg = "missing user or password in credentials for connect"
                raise SDSInitError(message=msg)
            self.sds.use_basicauth_sds(self.user, self.pwd)
            self.auth_method = "basic auth"
        elif method == "native":
            if self.user is None or self.pwd is None:
                msg = "missing user or password in credentials for connect"
                raise SDSInitError(message=msg)
            self.sds.use_native_sds(self.user, self.pwd)
            self.auth_method = "native"
        elif method == "token":
            if (self.cred_token_keyid is None
                    or self.cred_token_keysecret is None):
                msg = "missing token in credentials for connect"
                raise SDSInitError(message=msg)

            self.sds.use_token_sds(keyid=self.cred_token_keyid,
                                   keysecret=self.cred_token_keysecret)
            self.auth_method = "token"

        # certificate & SSL check
        if cert_file_path is not None:
            self.sds.set_certificate_file(cert_file_path)
            # self.check_certificate = True

        self.sds.set_ssl_verify(self.check_certificate)

        if isinstance(timeout, int):
            self.timeout = timeout

        if self.proxy_socks:
            self.sds.set_proxy(self.proxy_socks)

        self.version = self.get_version()

        if self.version is None:   # pragma: no cover
            self.version = "ukn"
            # need to check if a simple call to a space api is working

    # ---------------------------
    def disconnect(self):
        """disconnects from the SOLIDserver"""
        self.sds = None
        self.version = None
        self.sds_ip = None
        self.user = None
        self.pwd = None
        self.auth_method = None
        self.check_certificate = False
        self.timeout = 1
        self.cred_token_keyid = None
        self.cred_token_keysecret = None

    # ---------------------------
    def set_timeout(self, timeout=None):
        if isinstance(timeout, int):
            self.timeout = timeout

    # ---------------------------
    def get_version(self):
        """get software version of the SDS based on the management platform
        returns version as a string
        """

        if self.sds is None:
            raise SDSEmptyError(message="not connected")

        if self.version is not None:
            return self.version

        j = self.query("member_list",
                       params={
                           'WHERE': 'member_is_me=1',
                       },
                       option=False,
                       timeout=10)

        if j is None:   # pragma: no cover
            logging.error("error in getting answer on version")
            return None

        if 'connected' in j and not j['connected']:
            logging.error("not yet connected")
            return None

        if 'member_is_me' not in j[0]:   # pragma: no cover
            logging.error("error in getting version")
            return None

        self.version = j[0]['member_version']
        return self.version

    # ---------------------------
    def get_load(self):
        """get cpu, mem, io"""
        if self.sds is None:
            raise SDSEmptyError(message="not connected")

        j = self.query("member_list",
                       params={
                           'WHERE': 'member_is_me=1',
                       },
                       option=False)

        if j is None:   # pragma: no cover
            logging.error("error in getting answer on version")
            return None

        _r = {
            'cpu': float(j[0]['member_snmp_cpuload_percent']),
            'mem': int(j[0]['member_snmp_memory']),
            'hdd': int(j[0]['member_snmp_hdd']),
            'ioload': -1
        }

        # ioload is not available any more
        if 'member_snmp_ioload' in j[0]:
            _r['ioload'] = int(j[0]['member_snmp_ioload'])

        return _r

    # ---------------------------
    def query(self, method, params='', option=False, timeout=None):
        """execute a query towards the SDS"""

        if self.sds is None:
            raise SDSEmptyError(message="not connected")

        _timeout = self.timeout

        if isinstance(timeout, int):
            _timeout = timeout

        try:
            answer_req = self.sds.query(method,
                                        params=params,
                                        option=option,
                                        timeout=_timeout)

            if answer_req.status_code == 401:   # pragma: no cover
                # logging.error(answer_req)
                # logging.error(answer_req.json())
                raise SDSAuthError(message="authentication error")

            if answer_req.status_code == 204:
                raise SDSEmptyError(message="204 returned")

            try:
                j = answer_req.json()
                return j
            except JSONDecodeError:   # pragma: no cover
                logging.warning(
                    "no json in return, trying array and returns first entry")

                try:
                    j = json.loads(f'[{answer_req.content.decode()}]')
                    if isinstance(j, list):
                        return j[0]
                except ValueError:
                    pass

                logging.error("no json in return")
                return None

        except SDSAuthError as error:   # pragma: no cover
            raise SDSAuthError(f"{error}") from error

    # ---------------------------
    def __str__(self):
        """return the string notation of the server object"""
        connected = "not connected"
        if self.version:
            connected = (f"connected version={self.version}"
                         + f" auth={self.auth_method}")
        proxy = ""
        if self.proxy_socks:
            proxy = f" socks5h://{self.proxy_socks}"

        _r = f"sds ip={self.sds_ip}{proxy}"
        _r += f" cred={self.user} {connected}"
        if self.sds:
            _r += f", calls={self.sds.calls_counter}"

        return _r
