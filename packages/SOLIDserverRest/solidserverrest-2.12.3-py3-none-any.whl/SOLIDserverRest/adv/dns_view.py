#
# -*- Mode: Python; python-indent-offset: 4 -*-
#
#

"""
SOLIDserver DNS view management

"""

# import ipaddress
import logging
import time

from SOLIDserverRest.Exception import (SDSInitError,
                                       SDSError,
                                       SDSDNSError)

from .class_params import ClassParams
from .dns import DNS
from .sds import SDS


class DNS_view(ClassParams):  # pylint: disable=C0103
    """ class to manipulate a DNS view object """

    # -------------------------------------
    def __init__(self, sds=None,
                 name=None,
                 dns_server=None,
                 class_params=None):
        """init the DNS zone object:
        - sds: object SOLIDserver, could be set afterwards
        - name: dns view name
        """

        if sds and not isinstance(sds, SDS):
            raise SDSInitError(message="sds param is not of type SDS")

        super().__init__(sds, name)

        self.dns_server = None

        if dns_server:
            self.set_dns(dns_server)

        self.params = {
        }

        if class_params is not None:
            self.set_class_params(class_params)

    # -------------------------------------
    def set_dns(self, dns):
        """ link the view to a dns server object """
        if not isinstance(dns, DNS):
            raise SDSDNSError(message="not a DNS server object")

        self.dns_server = dns

    # -------------------------------------
    def _wait_for_synch(self, delete=False):
        """waith for the DNS view to be in sync"""
        if self.myid is None or self.myid == -1:
            raise SDSDNSError(message="missing DNS view id")

        _wait_delay = 1.0

        for _ in range(10):
            try:
                rjson = self.sds.query("dns_view_info",
                                       params={
                                           "dnsview_id": self.myid,
                                       })
            except SDSError:
                return None

            if not rjson:   # pragma: no cover
                raise SDSDNSError(message="DNS view sync error")

            if not delete:
                # we wait for the zone to be pushed to the server
                if rjson[0]['delayed_create_time'] == '0':
                    return rjson
            else:
                # we wait for the zone to be deleted from the server
                if rjson[0]['delayed_delete_time'] == '0':
                    return None

            logging.debug('not yet in synch %d', _wait_delay)
            time.sleep(_wait_delay)
            _wait_delay *= 1.5

        raise SDSDNSError(message="DNS view sync takes too long")

    # -------------------------------------
    def create(self, sync=True):
        """creates the DNS view"""
        if self.sds is None:
            raise SDSInitError(message="not connected")

        if self.dns_server is None:
            raise SDSDNSError(message="zone not linked to a DNS server")

        params = {
            'dnsview_name': self.name,
            'dns_id': self.dns_server.myid,
            **self.additional_params
        }

        self.prepare_class_params('dnsview', params)

        try:
            rjson = self.sds.query("dns_view_create",
                                   params=params)
        except SDSError as err:   # pragma: no cover
            raise SDSDNSError(message="create DNS view") from err

        if 'errno' in rjson:
            raise SDSDNSError(message="create DNS view"
                              f" {rjson['errmsg']}")

        rjson = rjson[0]
        if 'ret_oid' in rjson:
            self.myid = int(rjson['ret_oid'])

        if sync:
            time.sleep(.5)
            self.refresh()

    # -------------------------------------
    def refresh(self):
        """refresh content of the DNS view from the SDS"""
        if self.sds is None:
            raise SDSDNSError(message="not connected")

        if self.dns_server is None:
            raise SDSDNSError(message="view not linked to a server")

        if self.myid is None or self.myid == -1:
            self.set_additional_where_params(dns_id=self.dns_server.myid)

            view_id = self._get_id_by_name('dns_view_list',
                                           'dnsview',
                                           self.name)

            self.clean_additional_where_params()
        else:
            view_id = self.myid

        if view_id is None:
            raise SDSDNSError(message="non existant DNS view to refresh")

        self.myid = view_id
        rjson = self._wait_for_synch()

        if not rjson:   # pragma: no cover
            raise SDSDNSError(message="DNS server refresh error, len of array")

        rjson = rjson[0]

        for label in [
                'dns_class_name',
                'dnsview_name',
                'dnsview_recursion',
                'dnsview_allow_recursion',
                'dnsview_allow_query',
                'dnsview_allow_transfer',
                'dnsview_key_name',
                'dns_type',
                'dns_comment'
        ]:
            if label not in rjson:   # pragma: no cover
                raise SDSDNSError("parameter"
                                  + f" {label}"
                                  + " not found in DNS view")
            self.params[label] = rjson[label]

        if 'dnsview_class_parameters' in rjson:
            self.update_class_params(rjson['dnsview_class_parameters'])

    # -------------------------------------
    def delete(self, sync=True):
        """deletes the DNS view from the server"""
        if self.sds is None:
            raise SDSDNSError(message="not connected")

        if self.myid is None or self.myid == -1:
            raise SDSDNSError(message="missing DNS view id")

        try:
            logging.debug("delete")
            rjson = self.sds.query("dns_view_delete",
                                   params={
                                       'dnsview_id': self.myid,
                                       **self.additional_params
                                   })
            if 'errmsg' in rjson:  # pragma: no cover
                raise SDSDNSError(message="DNS view delete error, "
                                  + rjson['errmsg'])
        except SDSError as err:
            raise SDSDNSError(message="DNS view delete error") from err

        if sync:
            time.sleep(2)
            self._wait_for_synch(delete=True)

        self.myid = -1

    # -------------------------------------
    def __str__(self):
        """return the string notation of the DNS view object"""
        return_val = f"*VIEW* name={self.name}"

        if self.myid and self.myid != -1:
            return_val += f" [#{self.myid}]"

        if self.dns_server:
            return_val += f" server={self.dns_server.name}"

        if 'dnsview_recursion' in self.params:
            if self.params['dnsview_recursion'] == 'yes':
                return_val += " recurse"

        if 'dns_comment' in self.params:
            if self.params['dns_comment'] != '':
                return_val += f" comment='{self.params['dns_comment']}'"
        else:
            return_val += " not refreshed"

        return_val += str(super().__str__())

        return return_val
