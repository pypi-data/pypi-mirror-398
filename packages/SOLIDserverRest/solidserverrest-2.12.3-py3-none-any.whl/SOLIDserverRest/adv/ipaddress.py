# -*- Mode: Python; python-indent-offset: 4 -*-
#
# pylint: disable=R0801


"""
SOLIDserver ip address manager

"""

import binascii
import ipaddress
# import logging
# import pprint
import re
import socket

# import traceback

from packaging.version import Version, parse
from SOLIDserverRest.Exception import (SDSError, SDSIpAddressError,
                                       SDSIpAddressNotFoundError)

from .class_params import ClassParams
from .space import Space


class IpAddress(ClassParams):
    """ class to manipulate the SOLIDserver ip address """

    # -------------------------------------
    def __init__(self, sds=None,  # pylint: disable=too-many-arguments
                 space=None,
                 ipv4=None,
                 name=None,
                 class_params=None):
        """init an address object:
        - sds: object SOLIDserver, could be set afterwards
        - space: space object for this network
        """

        self.fqdn = None
        self.name = None

        super().__init__(sds, name)

        if space and not isinstance(space, Space):
            raise SDSIpAddressError("no valid space provided")

        self.space = space
        self.mac = None
        self.ipv4 = None
        self.fqdn = None

        if ipv4 is not None:
            self.ipv4 = self.check_ipv4_format(ipv4)
            if self.ipv4 is None:
                raise SDSIpAddressError("bad ipv4 format")

        if class_params is not None:
            self.set_class_params(class_params)

    # -------------------------------------
    @classmethod
    def check_ipv4_format(cls, addr):
        """ check the ip v4 format """
        ipv4 = None
        try:
            ipv4 = str(ipaddress.IPv4Address(addr))
        except ValueError:
            ipv4 = None

        return ipv4

    # -------------------------------------
    def clean_params(self):
        """ clean the object params """
        super().clean_params()

        self.ipv4 = None
        self.space = None
        self.mac = None
        self.fqdn = None

    # -------------------------------------
    def create(self):
        """ create the ip address in SDS """

        if self.sds is None:
            raise SDSIpAddressError(message="not connected")

        if self.space is None:
            raise SDSIpAddressError("no space attached to address for create")

        if self.ipv4 is None:
            raise SDSIpAddressError("no address for create")

        # if object already created
        if self.myid > 0:
            return

        params = {
            'hostaddr': self.ipv4,
            'site_id': self.space.params['site_id'],
            **self.additional_params
        }

        if self.name is not None:
            params['name'] = self.name

        if self.mac is not None:
            params['mac_addr'] = self.mac

        self.prepare_class_params('ip', params)

        # logging.info(params)

        rjson = self.sds.query("ip_address_create",
                               params=params)

        if 'errmsg' in rjson:
            raise SDSIpAddressError(message="creation, "
                                    + rjson['errmsg'])

        self.params['ip_id'] = int(rjson[0]['ret_oid'])
        self.myid = int(self.params['ip_id'])

        self.refresh()

    # -------------------------------------
    def get_id_by_ipaddr(self, ipaddr):
        """get the ID from its ip addr, return None if non existant"""

        params = {
            "limit": 1,
            **self.additional_params
        }

        _where_clause = ""

        if parse(self.sds.get_version()) >= Version("7.0.0"):
            _where_clause = f"hostaddr='{ipaddr}'"
        else:  # pragma: no cover
            _ipstr = binascii.hexlify(socket.inet_aton(ipaddr)).decode('ascii')
            _where_clause = f"ip_addr='{_ipstr}'"

        _where_clause += f" and site_id={self.space.myid}"
        params.update({"WHERE": _where_clause})

        try:
            rjson = self.sds.query('ip_address_list',
                                   params=params)
        except SDSError as err_descr:
            msg = f"cannot found object by ip addr {ipaddr}"
            msg += " / " + str(err_descr)
            raise SDSIpAddressNotFoundError(msg) from err_descr

        if rjson[0]['errno'] != '0':  # pragma: no cover
            raise SDSError("errno raised on get id by addr")

        return rjson[0]['ip_id']

    # -------------------------------------
    def refresh(self):
        """refresh content of the ip address from the SDS"""

        if self.sds is None:
            raise SDSIpAddressError(message="not connected")

        if self.myid <= 0:
            try:
                ip_id = self.get_id_by_ipaddr(ipaddr=self.ipv4)
            except SDSError as err_descr:
                msg = "cannot get ip addr id"
                msg += " / " + str(err_descr)
                raise SDSIpAddressNotFoundError(msg) from err_descr
        else:
            ip_id = self.myid

        params = {
            "ip_id": ip_id,
            **self.additional_params
        }

        rjson = self.sds.query("ip_address_info",
                               params=params)

        rjson = rjson[0]

        labels = ['ip_id',
                  #   'name',
                  #   'mac_addr',
                  'subnet_id',
                  'subnet_size',
                  'subnet_is_terminal',
                  ]
        if parse(self.sds.get_version()) >= Version("7.0.0"):
            labels.extend(['parent_subnet_start_hostaddr',
                           'parent_subnet_end_hostaddr',
                           'subnet_start_hostaddr',
                           'subnet_end_hostaddr'])

        for label in labels:
            if label not in rjson:  # pragma: no cover
                msg = f"parameter {label} not found in ip address"
                raise SDSIpAddressError(msg)
            self.params[label] = rjson[label]

        # logging.warning('update subnet ip in main')
        if 'mac_addr' in rjson:
            if not rjson['mac_addr'].startswith('EIP:'):
                self.set_mac(rjson['mac_addr'])

        if 'ip_class_name' in rjson and rjson['ip_class_name']:
            self.set_class_name(rjson['ip_class_name'])

        if 'name' in rjson and rjson['name'] != "":
            # do we have DNS sync
            _hostname = self.get_class_params('hostname')
            if _hostname and _hostname != rjson['name']:
                self.set_name(_hostname, rjson['name'])
            else:
                self.set_name(rjson['name'])

        self.myid = int(rjson['ip_id'])

        if 'ip_class_parameters' in rjson:   # pragma: no cover
            self.update_class_params(rjson['ip_class_parameters'])

        if not self.space:
            self.space = Space(sds=self.sds,
                               name=rjson['site_name'])
            self.space.refresh()

        self.ipv4 = rjson['hostaddr']

    # -------------------------------------
    def delete(self):
        """deletes the ip address in the SDS"""
        if self.sds is None:
            raise SDSIpAddressError(message="not connected")

        if self.myid == -1:
            raise SDSIpAddressNotFoundError("on delete")

        params = {
            'ip_id': self.myid,
            **self.additional_params
        }

        self.sds.query("ip_address_delete",
                       params=params)

        self.clean_params()

    # -------------------------------------
    def update(self):
        """ update the ip address in SDS """

        if self.sds is None:
            raise SDSIpAddressError(message="not connected")

        params = {
            'ip_id': self.myid,
            **self.additional_params
        }

        if self.mac is not None:
            params['mac_addr'] = self.mac

        self.prepare_class_params('ip', params)

        if self.fqdn:
            params['name'] = self.fqdn

        rjson = self.sds.query("ip_address_update",
                               params=params)

        if 'errmsg' in rjson:  # pragma: no cover
            raise SDSIpAddressError(message="ip addr update error, "
                                    + rjson['errmsg'])

        self.refresh()

    # -------------------------------------
    def set_param(self, param=None, value=None, exclude=None, name=None):
        """ set a specific param on the ip address object """
        super().set_param(param,
                          value,
                          exclude=['ip_id'],
                          name='name')

    # -------------------------------------
    def set_name(self, name=None, fqdn=None):
        """set the name of the ip address"""
        if fqdn:
            self.name = fqdn
            self.fqdn = fqdn
        else:
            if self.fqdn:
                if not self.fqdn.startswith(name):
                    raise SDSIpAddressError("set name requires fqdn")

            self.name = name

        self.set_class_params({'hostname': name})

    # -------------------------------------
    def set_ipv4(self, addr):
        """set the ip v4 address"""
        self.ipv4 = self.check_ipv4_format(addr)
        if self.ipv4 is None:
            raise SDSIpAddressError("bad ip v4 address format")

    # -------------------------------------
    def set_mac(self, mac):
        """set the mac address linked to this ip"""
        mac = mac.lower()
        if re.match("^[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$",
                    mac):
            mac = re.sub(r'-', ':', mac)
            mac = re.sub(r':', '', mac)
            mac = re.sub(r'(..)(..)(..)(..)(..)(..)',
                         '\\1:\\2:\\3:\\4:\\5:\\6',
                         mac)
            self.mac = mac
            # logging.info(self.mac)
        else:
            self.mac = None
            raise SDSIpAddressError("bad mac format")

    # -------------------------------------
    def __str__(self):  # pragma: no cover
        """return the string notation of the ip address object"""

        return_val = "*ip address*"

        if self.ipv4 is not None:
            return_val += f" {self.ipv4}"

        if self.name is not None:
            return_val += f" {self.name}"

        if self.mac is not None:
            return_val += f" {self.mac}"

        return_val += self.str_params(exclude=['ip_id',
                                               'name'])

        return_val += str(super().__str__())

        return return_val
