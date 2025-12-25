#
# pylint: enable=R0801

"""
SOLIDserver NOM interface object

mac address for doc = 00-00-5E-00-53-00/FF

"""

import ipaddress
import logging
import macaddress  # type: ignore

from SOLIDserverRest.Exception import (SDSError, SDSInitError)

from .class_params import ClassParams
from .nom_network_object import NomNetObject
from .sds import SDS


class NomPort(ClassParams):
    """ class to manipulate the SOLIDserver NOM port
        a port is composed of:
            - portid
            - mac
            - name
            - link to interface
            - link to other port
    """
    # -------------------------------------

    def __init__(self,
                 sds: SDS = None,
                 name: str = None,
                 mac_address: str = None,
                 network_object: NomNetObject = None,
                 class_params: dict = None):
        """init a NOM port:
            - sds: object SOLIDserver, could be set afterwards
        """

        self.network_object = None
        self.mac_address = None
        self.connected_port = 0
        self.aInterfaces = set()

        if not name:
            raise SDSError(
                message="name is required for network port")

        if not isinstance(network_object, NomNetObject):
            raise SDSError(
                message=f"netobj has not the correct type for {name}")

        super().__init__(sds, name)

        self.network_object = network_object
        self.set_mac_address(mac_address)

        if class_params is not None:
            logging.warning('class params on interface not yet supported')
            self.set_class_params(class_params)

    # -------------------------------------
    def set_mac_address(self, mac_address: str = None):
        """set a mac address for this port

        Args:
            mac_address (str)

        Raises:
            SDSError
        """
        if not isinstance(mac_address, str):
            raise SDSError(
                message=f"mac address has not the correct type for {self.name}")

        self.mac_address = macaddress.EUI48(str(mac_address))

    # -------------------------------------
    def clean_params(self):
        """ clean the object params """
        super().clean_params()

        self.network_object = None
        self.mac_address = None
        self.connected_port = 0
        self.aInterfaces = set()

    # -------------------------------------

    def create(self):
        """ create the network object port (and interface) """

        if self.sds is None:
            raise SDSError(message="not connected")

        # if object already created
        if self.myid > 0:
            return

        if self.network_object.myid <= 0:
            raise SDSError(
                message=f"netobj {self.network_object.name} should exists in real")

        params = {
            'nomnetobj_id': self.network_object.myid,
            **self.additional_params
        }

        if self.name is not None:
            params['nomiface_port_name'] = self.name
        else:
            raise SDSInitError(message="missing name to NOM interface")

        if self.mac_address:
            params['nomiface_port_mac'] = str(
                self.mac_address).replace('-', ':')

        self.prepare_class_params('nomnetobj', params)

        rjson = self.sds.query("nom_iface_create",
                               params=params)

        if 'errmsg' in rjson:
            raise SDSError(message="network object interface creation, "
                           + rjson['errmsg'])

        _ifaceid = int(rjson[0]['ret_oid'])
        nomif = NomInterface(sds=self.sds,
                             name=f'if-{self.name}',
                             port=self)
        nomif.myid = _ifaceid
        nomif.refresh()

        self.aInterfaces.add(int(_ifaceid))

        self.myid = int(nomif.params['nomport_id'])

        self.refresh()

    # -------------------------------------
    def refresh(self):
        """refresh content of the NOM port from the SDS"""

        if self.sds is None:
            raise SDSError(message="not connected")

        try:
            nomport_id = self._get_id(query="nom_port_list",
                                      key="nomport")
        except SDSError as err_descr:
            msg = "cannot get NOM port id"
            msg += " / " + str(err_descr)
            raise SDSError(msg) from err_descr

        params = {
            "nomport_id": nomport_id,
            **self.additional_params
        }

        rjson = self.sds.query("nom_port_info",
                               params=params)

        rjson = rjson[0]

        self.myid = int(rjson['nomport_id'])

        for label in ['nomport_id',
                      'nomport_name']:
            if label not in rjson:   # pragma: no cover
                raise SDSError(f"parameter {label} not found in NOM object")
            self.params[label] = rjson[label]

        if 'nomport_mac' in rjson:
            self.set_mac_address(rjson['nomport_mac'])

        if 'connected_port_id' in rjson:
            self.connected_port = int(rjson['connected_port_id'])

        # get the interfaces linked to this port
        params = {
            "WHERE": f"nomport_id={self.myid}"
        }

        # logging.info(params)
        rjson = self.sds.query("nom_iface_list",
                               params=params)
        self.aInterfaces = set()
        for iface in rjson:
            if iface['errno'] == '0':
                self.aInterfaces.add(int(iface['nomiface_id']))

        # if 'nomnetobj_class_parameters' in rjson:   # pragma: no cover
        #     self.update_class_params(rjson['nomnetobj_class_parameters'])

    # -------------------------------------
    def get_first_interface(self):
        """returns the first interface id linked to this port

        Returns:
            int: id of the interface
        """
        if len(self.aInterfaces) == 0:
            return None

        ifid = list(self.aInterfaces)[0]
        nomif = NomInterface(sds=self.sds,
                             name=f'if-{self.name}',
                             port=self)
        nomif.myid = ifid
        nomif.refresh()

        return nomif

    # -------------------------------------
    def delete(self):
        """deletes the NOM port and interface in the SDS"""
        if self.sds is None:
            logging.error("port does not have an SDS configured")
            return

        if self.myid == -1:
            logging.error("no port to delete on SDS")
            return

        noif = self.get_first_interface()
        while noif:
            # logging.info(noif)
            # self.aInterfaces.remove(noif.myid)
            noif.delete(recreate_port=False)

            if len(self.aInterfaces) > 0:
                self.refresh()
                noif = self.get_first_interface()
            else:
                noif = None

        self.clean_params()

    # -------------------------------------
    def set_connected_port(self, port=0):
        """if this port is connected to another one, set the id here

        Args:
            port (int): port id
        """
        self.connected_port = port

    # -------------------------------------
    def update(self):
        """ update the NOM port in SDS """

        # logging.info("update")
        if self.sds is None:
            raise SDSError(message="not connected")

        if self.myid <= 0:
            raise SDSError(
                message=f"port {self.name} should exists for update")

        params = {
            'nomiface_id': int(list(self.aInterfaces)[0]),

            **self.additional_params
        }

        if self.mac_address:
            params['nomiface_port_mac'] = str(
                self.mac_address).replace('-', ':')

        if self.connected_port:
            params['connected_port_id'] = int(self.connected_port)
        else:
            params['connected_port_id'] = 0

        self.prepare_class_params('nomnetobj', params)
        # logging.info(params)

        rjson = self.sds.query("nom_iface_update",
                               params=params)

        # logging.info(rjson)
        if 'errmsg' in rjson:  # pragma: no cover
            raise SDSError(message="NOM port update error, "
                           + rjson['errmsg'])

        self.refresh()

    # -------------------------------------
    def __str__(self):  # pragma: no cover
        """return the string notation of the NOM port"""

        return_val = "*NOM port* "

        if self.name:
            return_val += f"{self.name}"
        else:
            return_val += "NOT_SET"

        return_val += f" on {self.network_object.name}"

        return_val += f", mac={str(self.mac_address)}"

        if len(self.aInterfaces) > 0:
            return_val += ", interface id(s)=[" + \
                ", ".join(str(s) for s in self.aInterfaces) + "]"

        if self.connected_port > 0:
            return_val += f", connected to={self.connected_port}"

        return_val += self.str_params(exclude=['nomport_id',
                                               'nomport_name'])

        return_val += str(super().__str__())

        return return_val


class NomInterface(ClassParams):
    """ class to manipulate the SOLIDserver NOM interface """

    # -------------------------------------
    def __init__(self,
                 sds: SDS = None,
                 name: str = None,
                 port: NomPort = None,
                 class_params=None):
        """init a NOM interface:
        - sds: object SOLIDserver, could be set afterwards
        """

        if not name:
            raise SDSError(
                message=f"name is required for network interface")

        if not isinstance(port, NomPort):
            raise SDSError(
                message=f"port has not the correct type for {name}")

        self.clean_params()
        super().__init__(sds, name)

        self.ipv4 = None
        self.ipv6 = None
        self.vlan = 0

        self.port = port
        self.mac_address = None
        self.is_main = False

        if class_params is not None:
            logging.warning('class params on interface not yet supported')
            self.set_class_params(class_params)

    # -------------------------------------
    def clean_params(self):
        """ clean the object params """
        super().clean_params()

        self.mac_address = None
        self.vlan = 0
        self.is_main = False
        self.port = None
        self.ipv4 = None
        self.ipv6 = None

    # -------------------------------------
    def set_main(self, is_main: bool):
        """set this interface as main for the network object

        Args:
            is_main (bool): is this interface main
        """
        self.is_main = is_main

    # -------------------------------------
    def set_vlan(self, vlan: int):
        """set the vlan if not 0

        Args:
            vlan (int): vlan number 1-4096
        """
        self.vlan = int(vlan)

    # -------------------------------------
    def set_ip(self, ip):
        """set an IP for this interface, either v4 or v6 (not both)

        Args:
            ip (ip address): the ip as an ipaddress object or a string

        Raises:
            SDSError
            SDSInitError
        """
        if isinstance(ip, str):
            try:
                ip = ipaddress.ip_address(ip)
            except ValueError as exc:
                raise SDSError(
                    message=f"interface {self.name} requires a valid IP address, even as string") from exc

        if isinstance(ip, ipaddress.IPv4Address):
            if self.ipv6:
                raise SDSInitError(message="this interface has already IPv6")

            self.ipv4 = ip
            return

        if isinstance(ip, ipaddress.IPv6Address):
            if self.ipv4:
                raise SDSInitError(message="this interface has already IPv4")

            self.ipv6 = ip
            return

        raise SDSError(
            message=f"interface {self.name} requires a valid IP address")

    # -------------------------------------
    def set_mac_address(self, mac_address: str = None):
        """set the mac address for this interface

        Args:
            mac_address (str)

        Raises:
            SDSError
        """
        if not isinstance(mac_address, str):
            raise SDSError(
                message=f"mac address has not the correct type for {self.name}")

        self.mac_address = macaddress.EUI48(str(mac_address))

    # -------------------------------------
    def create(self):
        """ create the network object interface """

        if self.sds is None:
            raise SDSError(message="not connected")

        # if object already created
        if self.myid > 0:
            return

        if self.port.myid <= 0:
            raise SDSInitError(message="NOM port should exists")

        # if this interface is the first one attached to the port
        # we have to compare data to choose if we create or modify
        for _tmpifid in list(self.port.aInterfaces):
            # _tmpifid = list(self.port.aInterfaces)[0]
            _tmpif = NomInterface(sds=self.sds,
                                  name=self.name,
                                  port=self.port)
            _tmpif.myid = _tmpifid

            try:
                _tmpif.refresh()
            except SDSError:
                continue

            # logging.info('stock: '+str(_tmpif))
            # logging.info('new: '+str(self))

            b_need_update = False

            if _tmpif.name == self.name:
                if _tmpif.ipv4 == self.ipv4:
                    if _tmpif.ipv6 == self.ipv6:
                        if _tmpif.mac_address != self.mac_address:
                            b_need_update = True
                        if _tmpif.vlan != self.vlan:
                            b_need_update = True
            else:  # different name
                if _tmpif.mac_address == self.mac_address:
                    if _tmpif.vlan == self.vlan:
                        b_need_update = True

            if b_need_update:
                self.myid = _tmpifid
                # logging.info("update on create")
                self.update()
                return

            if _tmpif.vlan != self.vlan:
                if (_tmpif.name == self.name
                    and _tmpif.ipv4 == self.ipv4
                        and _tmpif.ipv6 == self.ipv6):
                    self.myid = _tmpifid
                    logging.info('***********************************')
                    self.update()
                    return
            else:
                if (_tmpif.name == self.name
                    and _tmpif.ipv4 == self.ipv4
                        and _tmpif.ipv6 == self.ipv6):
                    self.refresh()
                    return

                # logging.info("same vlan, name changed?")
                if _tmpif.name != self.name:
                    self.myid = _tmpifid
                    logging.info('***********************************')
                    self.update()
                    return

        # logging.info("create new interface")
        # logging.info(self)

        params = {
            'nomnetobj_id': self.port.network_object.myid,
            'nomiface_port_name': self.port.name,
            'nomiface_port_mac': str(self.port.mac_address).replace('-', ':'),
            **self.additional_params
        }

        if self.name is not None:
            params['nomiface_name'] = self.name
        else:
            raise SDSInitError(message="missing name to NOM interface")

        if self.mac_address:
            params['nomiface_mac'] = str(
                self.mac_address).replace('-', ':')

        params['nomiface_vlan_number'] = self.vlan

        if self.ipv4:
            params['nomiface_hostaddr'] = str(self.ipv4)
        elif self.ipv6:
            params['nomiface_hostaddr'] = str(self.ipv6)

        self.prepare_class_params('nomnetobj', params)

        # logging.info(params)
        rjson = self.sds.query("nom_iface_create",
                               params=params)

        # logging.info(rjson)
        if 'errmsg' in rjson:
            raise SDSError(message="network object interface creation, "
                           + rjson['errmsg'])

        self.params['nomiface_id'] = int(rjson[0]['ret_oid'])
        self.myid = int(self.params['nomiface_id'])
        self.port.aInterfaces.add(int(self.params['nomiface_id']))
        self.refresh()

    # -------------------------------------
    def get_id_by_fullname(self):
        """get the ID of the network interface,
           return None if non existant"""

        params = {
            "limit": 1,
            **self.additional_params
        }

        _where = f"nomnetobj_id={self.port.network_object.myid}"
        _where += f" AND nomiface_port_name='{self.port.name}'"
        if self.mac_address:
            _where += f" AND nomiface_mac='{str(self.mac_address).replace('-', ':')}'"
        if self.vlan > 0:
            _where += f" AND nomiface_vlan_number={self.vlan}"

        if self.ipv4:
            _where += f" AND nomiface_hostaddr='{self.ipv4}'"
        elif self.ipv6:
            _where += f" AND nomiface_hostaddr6='{self.ipv6}'"

        params.update({"WHERE": _where})

        try:
            rjson = self.sds.query('nom_iface_list',
                                   params=params)
        except SDSError as err_descr:
            msg = (f"cannot found NOM interface for"
                   f" {self.name}/{self.mac_address}/vlan {self.vlan}")
            msg += " / " + str(err_descr)
            raise SDSError(msg) from err_descr

        if rjson[0]['errno'] != '0':  # pragma: no cover
            logging.error(rjson)
            raise SDSError("errno raised on get network object")

        return rjson[0]['nomiface_id']

    # -------------------------------------
    def refresh(self):
        """refresh content of the NOM interface from the SDS"""
        if self.sds is None:
            raise SDSError(message="not connected")

        if self.myid > 0:
            nomif_id = self.myid
        else:
            try:
                nomif_id = self.get_id_by_fullname()
            except SDSError as err_descr:
                msg = "cannot get NOM interface id"
                msg += " / " + str(err_descr)
                raise SDSError(msg) from err_descr

        params = {
            "nomiface_id": nomif_id,
            **self.additional_params
        }

        rjson = self.sds.query("nom_iface_info",
                               params=params)

        rjson = rjson[0]

        self.myid = int(rjson['nomiface_id'])

        for label in ['nomiface_id',
                      'nomiface_fullname',
                      'nomiface_vlan_number',
                      'connected_port_id',
                      'connected_port_nomnetobj_id',
                      'ip_id',
                      'ip6_id',
                      'nomport_id']:
            if label not in rjson:   # pragma: no cover
                raise SDSError(f"parameter {label} not found in NOM object")
            self.params[label] = rjson[label]

        if 'nomnetobj_class_parameters' in rjson:   # pragma: no cover
            self.update_class_params(rjson['nomnetobj_class_parameters'])

        if 'nomiface_mac' in rjson and rjson['nomiface_mac'] != "":
            self.set_mac_address(rjson['nomiface_mac'])

        if 'nomiface_hostaddr' in rjson and rjson['nomiface_hostaddr'] != '':
            self.set_ip(rjson['nomiface_hostaddr'])

        elif 'nomiface_hostaddr6' in rjson and rjson['nomiface_hostaddr6'] != '':
            self.set_ip(rjson['nomiface_hostaddr6'])

        if 'nomiface_name' in rjson and rjson['nomiface_name'] != "":
            self.name = str(rjson['nomiface_name'])

        self.set_vlan(int(rjson['nomiface_vlan_number']))

        self.is_main = rjson['nomiface_main'] == 1

        if int(self.params['nomport_id']) != self.port.myid and self.port.myid == 0:
            self.port.myid = int(self.params['nomport_id'])

        self.port.refresh()

    # -------------------------------------
    def update(self):
        """ update the NOM interface in SDS """

        # logging.info("update")
        if self.sds is None:
            raise SDSError(message="not connected")

        params = {
            'nomiface_id': self.myid,
            'nomnetobj_id': self.port.network_object.myid,
            'nomiface_port_name': self.port.name,
            'nomiface_vlan_number': self.vlan,

            **self.additional_params
        }

        if self.name is not None:
            params['nomiface_name'] = self.name
        else:
            raise SDSInitError(message="missing name to NOM interface")

        if self.mac_address:
            params['nomiface_mac'] = str(
                self.mac_address).replace('-', ':')

        if self.ipv4:
            params['nomiface_hostaddr'] = str(self.ipv4)
        if self.ipv6:
            params['nomiface_hostaddr'] = str(self.ipv6)

        if self.is_main:
            params['nomiface_main'] = '1'
        else:
            params['nomiface_main'] = '0'

        self.prepare_class_params('nomnetobj', params)

        # logging.info(params)
        rjson = self.sds.query("nom_iface_update",
                               params=params)

        if 'errmsg' in rjson:  # pragma: no cover
            raise SDSError(message="NOM interface update error, "
                           + rjson['errmsg'])

        self.refresh()

    # -------------------------------------
    def delete(self, recreate_port=True):
        """deletes the NOM interface in the SDS"""
        if self.sds is None:
            raise SDSError(message="not connected")

        if self.myid == -1:
            raise SDSError("on NOM netobj interface delete")

        params = {
            'nomiface_id': self.myid,
            **self.additional_params
        }

        # logging.info(params)
        _r = self.sds.query("nom_iface_delete",
                            params=params)

        # update the port list
        if len(self.port.aInterfaces) > 1:
            self.port.aInterfaces.remove(int(self.myid))
        else:
            if recreate_port:
                self.port.aInterfaces = set()
                self.port.myid = 0
                self.port.create()
            else:
                self.port.clean_params()

        self.clean_params()

    # -------------------------------------
    def __str__(self):  # pragma: no cover
        """return the string notation of the NOM interface"""

        return_val = "*NOM interface* "

        return_val += str(super().__str__())

        if self.name:
            return_val += f", {self.name}"
        else:
            return_val += ", NOT_SET"

        return_val += f" on port {self.port.name}"

        if self.mac_address:
            return_val += f", mac={str(self.mac_address)}"
        else:
            return_val += f", port mac={str(self.port.mac_address)}"

        return_val += f", vlan={self.vlan}"

        if self.is_main:
            return_val += ", main interface"

        if self.ipv4:
            return_val += f", ipv4={self.ipv4}"
        if self.ipv6:
            return_val += f", ipv6={self.ipv6}"

        return_val += self.str_params(exclude=['nomiface_id',
                                               'name',
                                               'nomiface_port_name',
                                               'nomport_id',
                                               'nomiface_fullname',
                                               'nomiface_port_mac',
                                               'nomiface_vlan_number',
                                               'nomiface_ip6_addr',
                                               'nomnetobj_id',
                                               'ip_id',
                                               'ip6_id'])

        return return_val
