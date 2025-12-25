#
# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2024-01-30 15:04:55 alex>
#
# pylint: disable=E501

"""
SOLIDserver DNS record management

"""

import logging
import time
import ipaddress
# import pprint

from SOLIDserverRest.Exception import (SDSInitError,
                                       SDSError,
                                       SDSDNSError,
                                       SDSEmptyError,
                                       SDSIpAddressError)

from .class_params import ClassParams
from .dns_zone import DNS_zone
from .dns_view import DNS_view
from .sds import SDS
from .dns import DNS
from .validators import (INTValidator,
                         STRValidator)
from typing import Union
from collections import OrderedDict


class DNS_record(ClassParams):  # pylint: disable=C0103
    """ class to manipulate a DNS record object, from a zone """
    # -------------------------------------

    def __init__(self, sds=None, name=None, rr_type=None,
                 class_params=None):
        """init the record object"""

        if sds and not isinstance(sds, SDS):
            raise SDSInitError(message="sds param is not of type SDS")

        super().__init__(sds, name)

        self.zone = None
        self.dns_server = None
        self.dns_view = None
        self.ttl = 3600
        self.values = {}
        self.rr_type = None

        if rr_type:
            self.rr_type = str(rr_type)

        if class_params is not None:
            self.set_class_params(class_params)

    # -------------------------------------
    def set_zone(self, zone):
        """ link the record to a zone on the dns server """
        if not isinstance(zone, DNS_zone):
            raise SDSDNSError(message="record needs to be attached to a zone")

        self.zone = zone
        self.dns_server = zone.dns_server

    # -------------------------------------
    def set_view(self, dns_view):
        """ link the record to a view on the dns server """
        if not isinstance(dns_view, DNS_view):
            raise SDSDNSError(
                message="linking record to a view requires valid view")

        self.dns_view = dns_view

        if not self.dns_server:
            self.dns_server = dns_view.dns_server

    # -------------------------------------
    def set_dns(self, dns):
        """ link the zone to a dns server object """
        if not isinstance(dns, DNS):
            raise SDSDNSError(message="zone for linking is not a zone object")

        self.dns_server = dns

    # -------------------------------------
    def set_type(self, rr_type, **kvargs):
        """ set the type for the record
            args depending on record type:
             * A/AAAA: ip
             * MX: priority, target
             * TXT: txt
             * NS: target
             * CNAME, DNAME: target
             * SRV: priority, weight, port, target
        """

        self.rr_type = str(rr_type)

        if len(kvargs) == 0:
            return

        if self.rr_type == 'A':
            if len(kvargs) < 1 or 'ip' not in kvargs:
                raise SDSDNSError(message="A require ip")
            self.set_values([kvargs['ip']])

        elif self.rr_type == 'AAAA':
            if len(kvargs) < 1 or 'ip' not in kvargs:
                raise SDSDNSError(message="AAAA require ip")
            self.set_values([kvargs['ip']])

        elif self.rr_type == 'MX':
            if (len(kvargs) < 2
                or 'priority' not in kvargs
                    or 'target' not in kvargs):
                raise SDSDNSError(message="MX require prority and target")
            self.set_values([kvargs['priority'],
                             kvargs['target']])

        elif self.rr_type == 'SRV':
            if (len(kvargs) < 4
                or 'priority' not in kvargs
                or 'weight' not in kvargs
                or 'port' not in kvargs
                    or 'target' not in kvargs):
                raise SDSDNSError(message="SRV require ip")

            # the target should not have a leading .
            _target = kvargs['target']
            if _target.endswith('.'):
                _target = _target[:-1]

            self.set_values([kvargs['priority'],
                             kvargs['weight'],
                             kvargs['port'],
                             _target])

        elif self.rr_type == 'TXT':
            if len(kvargs) < 1 or 'txt' not in kvargs:
                raise SDSDNSError(message="TXT requires txt")
            self.set_values([kvargs['txt']])

        elif self.rr_type == 'NS':
            if len(kvargs) < 1 or 'target' not in kvargs:
                raise SDSDNSError(message="NS requires target")
            self.set_values([kvargs['target']])

        elif self.rr_type in ['CNAME', 'DNAME']:
            if len(kvargs) < 1 or 'target' not in kvargs:
                raise SDSDNSError(message=f"{self.rr_type} requires target")
            self.set_values([kvargs['target']])

    # -------------------------------------

    def set_values(self, avalues):
        """ set the values depending on the record type """
        if not self.rr_type:
            raise SDSDNSError(message='need to set type of'
                              ' record before values')

        if self.rr_type == 'A':
            # check v1 is an ip address
            try:
                ipaddress.IPv4Address(avalues[0])
            except ipaddress.AddressValueError as err:
                raise SDSDNSError(message="record A requires"
                                  " an IPv4 address") from err

            self.values = {
                '1': avalues[0]
            }

        elif self.rr_type == 'AAAA':
            # check v1 is an ip address
            try:
                ipaddress.IPv6Address(avalues[0])
            except ipaddress.AddressValueError as err:
                raise SDSDNSError(message="record AAAA "
                                  "requires an IPv6 address") from err

            self.values = {
                '1': avalues[0]
            }

        elif self.rr_type in 'TXT':
            self.values = {
                '1': str(avalues[0])
            }

        elif self.rr_type == 'NS':
            self.values = {
                '1': str(avalues[0])
            }

        elif self.rr_type in ['CNAME', 'DNAME']:
            self.values = {
                '1': str(avalues[0])
            }

        elif self.rr_type == 'MX':
            self.values = {
                '1': int(avalues[0]),
                '2': str(avalues[1])
            }

        elif self.rr_type == 'SRV':
            # the target should not have a leading .
            _target = str(avalues[3])
            if _target.endswith('.'):
                _target = _target[:-1]

            self.values = {
                '1': int(avalues[0]),
                '2': int(avalues[1]),
                '3': int(avalues[2]),
                '4': _target,
            }

        else:
            raise SDSDNSError(message="unknown type"
                              f" of record {self.rr_type}")

    # -------------------------------------
    def set_ttl(self, ttl):
        """ set the ttl for this record """

        self.ttl = max(int(ttl), 5)

    # -------------------------------------
    def create(self, sync=True):
        """creates the DNS record in the zone"""
        if self.sds is None:
            raise SDSInitError(message="not connected")

        if not self.rr_type:
            raise SDSDNSError(message="record type not set")

        if '1' not in self.values:
            raise SDSDNSError(
                message=f"no values set for record {self.rr_type}")

        if not self.dns_server:
            raise SDSDNSError(
                message=f"RR creation requires a DNS server")

        params = {
            'rr_name': self.name,
            'rr_type': self.rr_type,
            'dns_id': self.dns_server.myid,
            'rr_ttl': str(self.ttl),
            'value1': self.values['1'],
            **self.additional_params
        }

        if self.zone:
            params['dnszone_id'] = self.zone.myid

        if self.dns_view:
            params['dnsview_id'] = self.dns_view.myid

        for _v in ['2', '3', '4', '5', '6', '7']:
            if _v in self.values:
                params[f'value{_v}'] = self.values[_v]

        self.prepare_class_params('rr', params)

        try:
            rjson = self.sds.query("dns_rr_create",
                                   params=params)
        except SDSError as err:   # pragma: no cover
            raise SDSDNSError(message="create DNS record") from err

        if 'errno' in rjson and int(rjson['errno']) > 0:
            raise SDSDNSError(message="record:"
                              f" {rjson['errmsg']}")

        rjson = rjson[0]
        if 'ret_oid' in rjson:
            self.myid = int(rjson['ret_oid'])

        if sync:
            self.refresh()

    # -------------------------------------
    def _wait_for_synch(self, delete=False):
        """wait for the DNS record to be in sync"""
        if self.myid is None or self.myid == -1:
            raise SDSDNSError(message="missing DNS record id")

        _wait_delay = 0.01

        for _ in range(10):
            try:
                rjson = self.sds.query("dns_rr_info",
                                       params={
                                           "rr_id": self.myid,
                                       })
            except SDSEmptyError:
                if delete:
                    return None

                time.sleep(_wait_delay)
                continue
            except SDSError:
                return None

            if not rjson:   # pragma: no cover
                raise SDSDNSError(message="DNS record sync error")

            if not delete:
                # we wait for the zone to be pushed to the server
                if rjson[0]['delayed_create_time'] == '0':
                    return rjson
            else:
                # we wait for the zone to be deleted from the server
                if rjson[0]['delayed_delete_time'] == '0':
                    return None

            # logging.info('not yet in synch %s %f', self.name, _wait_delay)
            _wait_delay *= 2
            time.sleep(_wait_delay)

        raise SDSDNSError(message="DNS record"
                          " sync takes too long")

    # -------------------------------------
    def refresh(self):
        """refresh content of the DNS record from the SDS"""
        if self.sds is None:
            raise SDSDNSError(message="not connected")

        if self.myid is None or self.myid == -1:
            self.set_additional_where_params(rr_type=self.rr_type)
            self.set_additional_where_params(dns_id=self.dns_server.myid)
            if self.zone:
                self.set_additional_where_params(dnszone_name=self.zone.name)
            if self.dns_view:
                self.set_additional_where_params(dnsview_id=self.dns_view.myid)

            # values:
            # only when you use these to search the good record
            # eg. A or AAAA which can be multiple, not CNAME which is unique
            #     by FQDN
            if len(self.values) > 0:
                if self.rr_type in ['A', 'AAAA', 'TXT', 'NS']:
                    self.set_additional_where_params(value1=self.values['1'])
                elif self.rr_type in ['MX']:
                    self.set_additional_where_params(
                        value1=str(self.values['1']),
                        value2=str(self.values['2']))
                elif self.rr_type in ['SRV']:
                    self.set_additional_where_params(
                        value3=str(self.values['3']),
                        value4=str(self.values['4'])
                    )

            rr_id = self._get_id_by_name('dns_rr_list',
                                         'rr_full',
                                         self.name,
                                         key_id='rr')

            self.clean_additional_where_params()
        else:
            rr_id = self.myid

        if rr_id is None:
            raise SDSDNSError(message="non existant DNS record to refresh")

        self.myid = rr_id
        rjson = self._wait_for_synch()

        if not rjson:   # pragma: no cover
            raise SDSDNSError(message="DNS record refresh error, len of array")

        rjson = rjson[0]

        for label in [
                'dns_class_name',
                'dns_cloud',
                'dns_comment',
                'dns_type',
                'dns_version',
                'rr_class_name',
                'rr_full_name_utf',
                'rr_glue',
                'ttl',
                'value1',
                'value2',
                'value3',
                'value4',
                'value5',
                'value6',
                'value7'
        ]:
            if label not in rjson:   # pragma: no cover
                raise SDSDNSError("parameter"
                                  f" {label}"
                                  " not found in DNS zone")
            self.params[label] = rjson[label]

        if 'rr_class_parameters' in rjson:
            self.update_class_params(rjson['rr_class_parameters'])

        # get the name
        self.name = rjson['rr_full_name_utf']

        # get the TTL
        self.ttl = int(rjson['ttl'])

        # get the record type
        self.rr_type = rjson['rr_type']

        self.set_values([rjson['value1'],
                         rjson['value2'],
                         rjson['value3'],
                         rjson['value4'],
                         rjson['value5'],
                         rjson['value6'],
                         rjson['value7']])

        # update zone if the zone was not provided, get it from
        # the id
        if not self.zone:
            self.zone = DNS_zone(sds=self.sds,
                                 name=rjson['dnszone_name'])
            self.zone.set_dns(self.dns_server)
            self.zone.refresh()

        # if the zone is in a view
        if 'dnsview_id' in rjson and not self.dns_view:
            _dns_view = DNS_view(sds=self.sds, dns_server=self.dns_server)
            _dns_view.myid = int(rjson['dnsview_id'])
            if _dns_view.myid > 0:
                _dns_view.refresh()
                self.dns_view = _dns_view

    # -------------------------------------

    def delete(self, sync=True):
        """deletes the DNS record from the zone"""
        if self.sds is None:
            raise SDSDNSError(message="not connected")

        if self.myid is None or self.myid == -1:
            raise SDSDNSError(message="missing DNS RR id")

        try:
            rjson = self.sds.query("dns_rr_delete",
                                   params={
                                       'rr_id': self.myid,
                                       **self.additional_params
                                   })
            if 'errmsg' in rjson:  # pragma: no cover
                raise SDSDNSError(message=f"DNS record delete,"
                                  f" {rjson['errmsg']}")
        except SDSError as err:
            raise SDSDNSError(message="DNS record delete error") from err

        if sync:
            time.sleep(0.1)
            self._wait_for_synch(delete=True)

        self.myid = -1

    # -------------------------------------
    def update(self):
        """ update the record in SDS """

        if self.sds is None:
            return

        if self.zone is None:
            return

        if not self.rr_type:
            return

        if '1' not in self.values:
            return

        params = {
            'rr_id': self.myid,
            'rr_ttl': str(self.ttl),
            'value1': self.values['1'],
            **self.additional_params
        }

        for _v in ['2', '3', '4', '5', '6', '7']:
            if _v in self.values:
                params[f'value{_v}'] = self.values[_v]

        self.prepare_class_params('rr', params)

        # logging.info(params)

        rjson = self.sds.query("dns_rr_update",
                               params=params)

        if 'errmsg' in rjson:  # pragma: no cover
            raise SDSIpAddressError(message="rr update error, "
                                    f"{rjson['errmsg']}")

        self.refresh()

    # -------------------------------------
    def __str__(self):
        """return the string notation of the DNS record object"""
        return_val = f"*RR* name={self.name}"

        if self.myid and self.myid != -1:
            return_val += f" [#{self.myid}]"

        if self.zone:
            return_val += f" server={self.dns_server.name}"
            if self.zone:
                return_val += f" zone={self.zone.name}"

        if self.rr_type:
            return_val += f" {self.rr_type}"
            if self.rr_type in ['A', 'AAAA', 'CNAME', 'DNAME']:
                if '1' in self.values:
                    return_val += f"={self.values['1']}"
            elif self.rr_type == 'TXT':
                if '1' in self.values:
                    return_val += f"='{self.values['1']}'"
            elif self.rr_type == 'MX':
                if '1' in self.values and '2' in self.values:
                    return_val += f"='{self.values['2']} [{self.values['1']}]'"
            elif self.rr_type == 'SRV':
                if (
                    '1' in self.values and
                    '2' in self.values and
                    '3' in self.values and
                    '4' in self.values
                ):
                    return_val += f"='p={self.values['1']}"
                    return_val += f", w={self.values['2']}"
                    return_val += f", {self.values['4']}:{self.values['3']}"

            return_val += f" ttl={self.ttl}"

            if 'rr_glue' in self.params:
                return_val += f" glue={self.params['rr_glue']}"

        return_val += str(super().__str__())

        return return_val


class ExtendedDNSRecord(DNS_record):
    """Class to enable extending DNSRecord class without impacting it.
       Overrides update and set_values methods from DNS_record,
       provides _update_values method. Record type specific attributes
       get set directly on the class, eg a TXTRecord would have a text
       attribute. Supports duplicate detection when fetching records
       and can perform validation

    """
    # -------------------------------------

    def __init__(self, sds: SDS, server: Union[str, DNS],
                 zone: Union[str, DNS_zone], name: str,
                 mapping_dict: dict, rr_type: str,
                 myid: int = None, ttl: int = 3600,
                 fetch_existing: bool = False,
                 class_params: dict = None,
                 **kwargs):
        """Extended DNSRecord class"""

        if isinstance(server, str):
            _server = DNS(sds=sds, name=server)
            _server.refresh()
        elif isinstance(server, DNS):
            _server = server
        else:
            raise SDSError("Must provide a server")
        self.server = _server

        if isinstance(zone, str):
            _zone = DNS_zone(sds=sds, name=zone)
            _zone.set_dns(self.server)
            _zone.refresh()

        elif isinstance(zone, DNS_zone):
            _zone = zone
        else:
            raise SDSError("Must provide a zone")

        if name is not None:
            if _zone.name not in name:
                if name == "":
                    name = _zone.name
                else:
                    name = f"{name}.{_zone.name}"

        super().__init__(sds, name)
        self.set_zone(_zone)
        self.mapping_dict = mapping_dict
        self.rr_type = rr_type
        self.myid = myid

        if fetch_existing:
            if len([_ for _ in [name, myid] if _ is not None]) == 0:
                raise SDSError("Must provide name or myid to fetch existing")
            if not myid:
                # If not providing an ID check for duplicates
                params = {
                    "WHERE": f"rr_full_name='{self.name}'"
                }
                params["WHERE"] += f" and rr_type='{self.rr_type}'"
                params["WHERE"] += f" and dns_id={self.zone.dns_server.myid}"
                params["WHERE"] += f" and dnszone_name='{self.zone.name}'"
                provided_kwargs = [k for k in self.mapping_dict.keys()
                                   if kwargs.get(k) is not None]
                with_params_statement = ""
                if len(provided_kwargs) > 0:  # disable=E501
                    with_params_statement = "with params: "
                    for key in provided_kwargs:
                        add_param = {"value{}".format(
                            self.mapping_dict[key]["value"]): str(
                                kwargs[key]
                        )}
                        _map_val = self.mapping_dict[key]["value"]
                        params["WHERE"] += f' and value{_map_val}='
                        params["WHERE"] += f"'{str(kwargs[key])}'"

                        with_params_statement += (
                            "value"
                            f"{self.mapping_dict[key]['value']}")
                        f"={str(kwargs[key])}, "

                        self.set_additional_where_params(**add_param)
                    with_params_statement = with_params_statement[:-2] + " "

                try:
                    duplicate_check = self.sds.query("dns_rr_list",
                                                     params=params)
                except SDSEmptyError:
                    raise SDSError(f"{name} {self.rr_type} record"
                                   f" {with_params_statement} does not"
                                   f" exist in zone {self.zone.name}"
                                   f" on server {self.server.name}"
                                   )

                num_results = len(duplicate_check)
                if num_results > 1:
                    found_ids = [_["rr_id"] for _ in duplicate_check]
                    if num_results < 5:
                        msg = f"Found {num_results} records with"
                        f" name {self.name} {with_params_statement}"
                        msg += f"({', '.join(found_ids)}), provide"
                        " additional filter criteria or use myid"
                    else:
                        msg = f"Found {num_results} records"
                        f" with name {self.name}"
                        f" {with_params_statement}, "
                        msg += "provide additional filter criteria or use myid"

                    raise SDSError(msg)

            try:
                self.refresh()
            except SDSDNSError:
                raise
            except SDSError:
                raise SDSError(f"{name} {self.rr_type}"
                               f" record {with_params_statement}"
                               " does not exist in"
                               f" zone {self.zone.name}"
                               f" on server {self.server.name}"
                               )
        else:
            if myid is not None:
                raise SDSError("Can not provide an ID if not"
                               " fetching an existing record")
            if not isinstance(name, str):
                raise SDSError("Must provide a name")

            missing = [_ for _ in self.mapping_dict.keys()
                       if _ not in kwargs.keys()
                       ] + [_ for _ in self.mapping_dict.keys()
                            if kwargs.get(_) is None]
            if len(missing) > 0:
                raise SDSError(
                    f"If initializing a new {self.rr_type} record non Null"
                    " values must be provided"
                    "for {}".format(", ".join(missing))
                )

            self.set_values([kwargs.get(key) for key
                             in self.mapping_dict.keys()])

            self.set_ttl(ttl)

        if class_params is not None:
            self.set_class_params(class_params)

    def set_values(self, avalues: list = []):
        """Updates values in the values dict and directly in the class dict,
           validating if a validator was provided

        """
        for real_name, value_dict in self.mapping_dict.items():
            try:
                for validator in value_dict.get("validators", []):
                    validator.validate(avalues[value_dict["index"]], real_name)
                _avalindex = value_dict["type"](avalues[value_dict["index"]])
                self.values[value_dict["value"]] = _avalindex
                self.__dict__[real_name] = _avalindex
            except TypeError:
                raise SDSError(f"{real_name} must be"
                               f" of type {value_dict['type']}")
            except ipaddress.AddressValueError as err:
                raise SDSError(message="record requires"
                               " an IP address") from err

    def _update_values(self):
        """Sets values in the values attribute from the attributes found
           directly on the class after validating them

        """
        for real_name, v_dict in self.mapping_dict.items():
            _selfrealname = self.__dict__[real_name]
            for validator in v_dict.get("validators", []):
                validator.validate(_selfrealname, real_name)
            self.values[v_dict["value"]] = v_dict["type"](_selfrealname)

    def update(self):
        """update the record in SDS, applies any local changes based on direct
           attributes

        """
        self._update_values()

        if self.sds is None:
            return

        if self.zone is None:
            return

        if not self.rr_type:
            return

        if '1' not in self.values:
            return

        params = {
            'rr_id': self.myid,
            'rr_ttl': str(self.ttl),
            'value1': self.values['1'],
            **self.additional_params
        }

        for _v in ['2', '3', '4', '5', '6', '7']:
            if _v in self.values:
                params[f'value{_v}'] = self.values[_v]

        self.prepare_class_params('rr', params)

        rjson = self.sds.query("dns_rr_update",
                               params=params)

        if 'errmsg' in rjson:  # pragma: no cover
            raise SDSIpAddressError(message="rr update error, "
                                    f"{rjson['errmsg']}")

        self.refresh()


class NAPTRRecord(ExtendedDNSRecord):
    """NAPTR record """
    # -------------------------------------
    mapping_dict = OrderedDict({
        "order": {
            "value": "1",
            "type": int,
            "index": 0,
            "validators": [INTValidator(min_val=0, max_val=65535)]
        },
        "preference": {
            "value": "2",
            "type": int,
            "index": 1,
            "validators": [INTValidator(min_val=0, max_val=65535)]
        },
        "flags": {
            "value": "3",
            "type": str,
            "index": 2,
            "validators": []
        },
        "services": {
            "value": "4",
            "type": str,
            "index": 3,
            "validators": []
        },
        "regex": {
            "value": "5",
            "type": str,
            "index": 4,
            "validators": []
        },
        "replace": {
            "value": "6",
            "type": str,
            "index": 5,
            "validators": []
        }
    })
    rr_type = "NAPTR"

    def __init__(self, sds: SDS, server: Union[str, DNS],
                 zone: Union[str, DNS_zone], name: str = None,
                 myid: int = None, ttl: int = 3600,
                 fetch_existing: bool = False,
                 class_params: dict = None, order: int = None,
                 preference: int = None,
                 flags: str = None, services: str = None, regex: str = None,
                 replace: str = None):
        """A DNS NAPTR Resource Record. If not fetching an existing record,
           all NAPTR record specific arguments must be provided. For
           more details on NAPTR records refer to RFC 3403 available
           on IETF website at http://tools.ietf.org/html/rfc3403.

        Args:
            sds (SOLIDserverRest.adv.sds.SDS): A connected SDS server
            instance

            server (str|SOLIDserverRest.adv.dns.DNS): A SOLIDserver
            DNS object or the name of a DNS server configured on the
            provided sds

            zone (str|SOLIDserverRest.adv.dns_zone.DNS_zone): A DNS
            zone object or the name of a DNS zone configured on the
            provided sds and server

            name (str, optional): The name of the DNS Resource
            record. If the name does not end in the zone name the zone
            name will be appended

            myid (int, optional): The id of the DNS Resource Record

            ttl (int, default 3600): How long the DNS settings are
            cached for before they are refreshed

            fetch_existing (bool, default False): Whether or not to
            fetch an existing record. If true, must provide either
            name or myid. If providing myid, everything but myid is
            ignored

            class_params (dict, optional): The DNS Resource Records
            class parameters order (int, optional): A number between 0
            and 65535 defining which RR has priority if there are
            several NAPTR RRs in the zone. The lowest value has the
            priority over the other record(s) preference (int,
            optional): A number between 0 and 65535 defining which RR
            has priority if there are several NAPTR RRs that have the
            same order in the zone. The lowest value has priority over
            the other record(s).

            flags (str, optional): The string that corresponds to the
            action you want your client application to perform. The
            flag specified impacts the data expected in the field
            Services, Regex and/or Replace.

            services (str, optional): The services parameters to which
            applies the action specified in the field Flags.You must
            respect your client application syntax

            regex (str, optional): The string that contains a
            substitution expression matching the format <delimit ereg
            delimit substitution delimit flag> to which applies the
            action specified the field Flags.

            replace (str, optional): An FQDN domain name to which
            applies the action specified in the field Flags.You can
            specify no domain name if you type in . (dot) in the
            field.

        """

        super().__init__(
            sds=sds,
            server=server,
            zone=zone,
            name=name,
            mapping_dict=self.mapping_dict,
            rr_type=self.rr_type,
            myid=myid,
            ttl=ttl,
            fetch_existing=fetch_existing,
            class_params=class_params,
            order=order,
            preference=preference,
            flags=flags,
            services=services,
            regex=regex,
            replace=replace
        )


class TXTRecord(ExtendedDNSRecord):
    """TXT record """
    # -------------------------------------
    mapping_dict = OrderedDict({
        "text": {
            "value": "1",
            "type": str,
            "index": 0,
            "validators": [STRValidator(max_len=255)]
        },
    })
    rr_type = "TXT"

    def __init__(self, sds: SDS, server: Union[str, DNS],
                 zone: Union[str, DNS_zone], name: str = None,
                 myid: int = None, ttl: int = 3600,
                 fetch_existing: bool = False, class_params=None,
                 text: str = None):
        """A DNS TXT Resource Record. If not fetching an existing record, all
        TXT record specific arguments must be provided.

        Args:
            sds (SOLIDserverRest.adv.sds.SDS): A connected SDS server
            instance

            server (str|SOLIDserverRest.adv.dns.DNS): A SOLIDserver
            DNS object or the name of a DNS server configured on the
            provided sds

            zone (str|SOLIDserverRest.adv.dns_zone.DNS_zone): A DNS
            zone object or the name of a DNS zone configured on the
            provided sds and server

            name (str, optional): The name of the DNS Resource
            record. If the name does not end in the zone name the zone
            name will be appended

            myid (int, optional): The id of the DNS Resource Record

            ttl (int, default 3600): How long the DNS settings are
            cached for before they are refreshed

            fetch_existing (bool, default False): Whether or not to
            fetch an existing record. If true, must provide either
            name or myid. If providing myid, everything but myid is
            ignored

            class_params (dict, optional): The DNS Resource Records
            class parameters

            text (str, optional): The description of your choice
            (max. 255 characters including spaces)

        """
        super().__init__(
            sds=sds,
            server=server,
            zone=zone,
            name=name,
            mapping_dict=self.mapping_dict,
            rr_type=self.rr_type,
            myid=myid,
            ttl=ttl,
            fetch_existing=fetch_existing,
            class_params=class_params,
            text=text
        )


class ARecord(ExtendedDNSRecord):
    """A record """
    # -------------------------------------
    mapping_dict = OrderedDict({
        "ipv4_address": {
            "value": "1",
            "type": ipaddress.IPv4Address,
            "index": 0,
            "validators": []
        },
    })
    rr_type = "A"

    def __init__(self, sds: SDS, server: Union[str, DNS],
                 zone: Union[str, DNS_zone], name: str = None,
                 myid: int = None,
                 ttl: int = 3600,
                 fetch_existing: bool = False,
                 class_params=None,
                 ipv4_address: ipaddress.IPv4Address = None,):
        """A DNS A Resource Record. If not fetching an existing record, all A
        record specific arguments must be provided.

        Args:
            sds (SOLIDserverRest.adv.sds.SDS): A connected SDS server
            instance

            server (str|SOLIDserverRest.adv.dns.DNS): A SOLIDserver
            DNS object or the name of a DNS server configured on the
            provided sds

            zone (str|SOLIDserverRest.adv.dns_zone.DNS_zone): A DNS
            zone object or the name of a DNS zone configured on the
            provided sds and server

            name (str, optional): The name of the DNS Resource
            record. If the name does not end in the zone name the zone
            name will be appended

            myid (int, optional): The id of the DNS Resource Record

            ttl (int, default 3600): How long the DNS settings are
            cached for before they are refreshed

            fetch_existing (bool, default False): Whether or not to
            fetch an existing record. If true, must provide either
            name or myid. If providing myid, everything but myid is
            ignored

            class_params (dict, optional): The DNS Resource Records
            class parameters

            ipv4_address (ipaddress.IPv4Address, optional): The IPv4
            Address of the host

        """

        super().__init__(
            sds=sds,
            server=server,
            zone=zone,
            name=name,
            mapping_dict=self.mapping_dict,
            rr_type=self.rr_type,
            myid=myid,
            ttl=ttl,
            fetch_existing=fetch_existing,
            class_params=class_params,
            ipv4_address=ipv4_address
        )


class AAAARecord(ExtendedDNSRecord):
    """AAAA record """
    # -------------------------------------
    mapping_dict = OrderedDict({
        "ipv6_address": {
            "value": "1",
            "type": ipaddress.IPv6Address,
            "index": 0,
            "validators": []
        },
    })
    rr_type = "AAAA"

    def __init__(self, sds: SDS, server: Union[str, DNS],
                 zone: Union[str, DNS_zone], name: str = None,
                 myid: int = None, ttl: int = 3600,
                 fetch_existing: bool = False, class_params=None,
                 ipv6_address: ipaddress.IPv6Address = None,):
        """A DNS AAAA Resource Record. If not fetching an existing record, all
        AAAA record specific arguments must be provided.

        Args:
            sds (SOLIDserverRest.adv.sds.SDS): A connected SDS server instance

            server (str|SOLIDserverRest.adv.dns.DNS): A SOLIDserver
            DNS object or the name of a DNS server configured on the
            provided sds

            zone (str|SOLIDserverRest.adv.dns_zone.DNS_zone): A DNS
            zone object or the name of a DNS zone configured on the
            provided sds and server

            name (str, optional): The name of the DNS Resource
            record. If the name does not end in the zone name the zone
            name will be appended

            myid (int, optional): The id of the DNS Resource Record

            ttl (int, default 3600): How long the DNS settings are
            cached for before they are refreshed

            fetch_existing (bool, default False): Whether or not to
            fetch an existing record. If true, must provide either
            name or myid. If providing myid, everything but myid is
            ignored

            class_params (dict, optional): The DNS Resource Records
            class parameters

            ipv6_address (ipaddress.IPv6Address, optional): The IPv6
            Address of the host

        """

        super().__init__(
            sds=sds,
            server=server,
            zone=zone,
            name=name,
            mapping_dict=self.mapping_dict,
            rr_type=self.rr_type,
            myid=myid,
            ttl=ttl,
            fetch_existing=fetch_existing,
            class_params=class_params,
            ipv6_address=ipv6_address
        )


class MXRecord(ExtendedDNSRecord):
    """MX record """
    # -------------------------------------
    mapping_dict = OrderedDict({
        "preference": {
            "value": "1",
            "type": int,
            "index": 0,
            "validators": [INTValidator(min_val=0, max_val=65535)]
        },
        "mail_server": {
            "value": "2",
            "type": str,
            "index": 1,
            "validators": []
        },
    })
    rr_type = "MX"

    def __init__(self, sds: SDS, server: Union[str, DNS],
                 zone: Union[str, DNS_zone], name: str = None,
                 myid: int = None, ttl: int = 3600,
                 fetch_existing: bool = False, class_params=None,
                 preference: int = None, mail_server: str = None):
        """A DNS MX Resource Record. If not fetching an existing record, all
        MX record specific arguments must be provided.

        Args:

            sds (SOLIDserverRest.adv.sds.SDS): A connected SDS server
            instance

            server (str|SOLIDserverRest.adv.dns.DNS): A SOLIDserver
            DNS object or the name of a DNS server configured on the
            provided sds

            zone (str|SOLIDserverRest.adv.dns_zone.DNS_zone): A DNS
            zone object or the name of a DNS zone configured on the
            provided sds and server

            name (str, optional): The name of the DNS Resource
            record. If the name does not end in the zone name the zone
            name will be appended

            myid (int, optional): The id of the DNS Resource Record

            ttl (int, default 3600): How long the DNS settings are
            cached for before they are refreshed

            fetch_existing (bool, default False): Whether or not to
            fetch an existing record. If true, must provide either
            name or myid. If providing myid, everything but myid is
            ignored

            class_params (dict, optional): The DNS Resource Records
            class parameters

            preference (int, optional): A number between 0 and 65535
            defining which server has priority if there are several
            RRs in the zone. The lowest value has priority over the
            other server(s)

            mail_server (str, optional): The SMTP (mail) server hostname

        """

        super().__init__(
            sds=sds,
            server=server,
            zone=zone,
            name=name,
            mapping_dict=self.mapping_dict,
            rr_type=self.rr_type,
            myid=myid,
            ttl=ttl,
            fetch_existing=fetch_existing,
            class_params=class_params,
            preference=preference,
            mail_server=mail_server
        )


class CNAMERecord(ExtendedDNSRecord):
    """CNAME record """
    # -------------------------------------
    mapping_dict = OrderedDict({
        "hostname": {
            "value": "1",
            "type": str,
            "index": 0,
            "validators": []
        },
    })
    rr_type = "CNAME"

    def __init__(self, sds: SDS, server: Union[str, DNS],
                 zone: Union[str, DNS_zone], name: str = None,
                 myid: int = None, ttl: int = 3600,
                 fetch_existing: bool = False, class_params=None,
                 hostname: str = None):
        """A DNS CNAME Resource Record. If not fetching an existing record,
           all CNAME record specific arguments must be provided.

        Args:
            sds (SOLIDserverRest.adv.sds.SDS): A connected SDS server
            instance

            server (str|SOLIDserverRest.adv.dns.DNS): A SOLIDserver
            DNS object or the name of a DNS server configured on the
            provided sds

            zone (str|SOLIDserverRest.adv.dns_zone.DNS_zone): A DNS
            zone object or the name of a DNS zone configured on the
            provided sds and server

            name (str, optional): The name of the DNS Resource
            record. If the name does not end in the zone name the zone
            name will be appended.  If the name does not end in the
            zone the zone name will be appended

            myid (int, optional): The id of the DNS Resource Record

            ttl (int, default 3600): How long the DNS settings are
            cached for before they are refreshed

            fetch_existing (bool, default False): Whether or not to
            fetch an existing record. If true, must provide either

            name or myid. If providing myid, everything but myid is
            ignored

            class_params (dict, optional): The DNS Resource Records
            class parameters

            hostname (str, optional): The hostname

        """

        super().__init__(
            sds=sds,
            server=server,
            zone=zone,
            name=name,
            mapping_dict=self.mapping_dict,
            rr_type=self.rr_type,
            myid=myid,
            ttl=ttl,
            fetch_existing=fetch_existing,
            class_params=class_params,
            hostname=hostname,
        )


class NSRecord(ExtendedDNSRecord):
    """NS record """
    # -------------------------------------
    mapping_dict = OrderedDict({
        "target": {
            "value": "1",
            "type": str,
            "index": 0,
            "validators": []
        },
    })
    rr_type = "NS"

    def __init__(self, sds: SDS, server: Union[str, DNS],
                 zone: Union[str, DNS_zone],
                 name: str = None,
                 myid: int = None,
                 ttl: int = 3600,
                 fetch_existing: bool = False,
                 class_params=None,
                 target: str = None):
        """A DNS NS Resource Record. If not fetching an existing record, all
        NS record specific arguments must be provided.

        Args:
            sds (SOLIDserverRest.adv.sds.SDS): A connected SDS server instance
            server (str|SOLIDserverRest.adv.dns.DNS): A SOLIDserver DNS
                   object or the name of a DNS server configured on
                   the provided sds
            zone (str|SOLIDserverRest.adv.dns_zone.DNS_zone): A DNS zone
                   object or the name of a DNS zone configured on the
                   provided sds and server
            name (str): The name of the DNS Resource record.  If the
                 name does not end in the zone name the zone name will
                 be appended
            myid (int, optional): The id of the DNS Resource Record
            ttl (int, default 3600): How long the DNS settings are cached
                 for before they are refreshed
            fetch_existing (bool, default False): Whether or not to fetch
                 an existing record. If true, must provide
            either name or myid. If providing myid, everything but myid
                 is ignored
            class_params (dict, optional): The DNS Resource Records
                 class parameters
            target (str, optional): The DNS server hostname

        """

        super().__init__(
            sds=sds,
            server=server,
            zone=zone,
            name=name,
            mapping_dict=self.mapping_dict,
            rr_type=self.rr_type,
            myid=myid,
            ttl=ttl,
            fetch_existing=fetch_existing,
            class_params=class_params,
            target=target,
        )
