# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2022-10-10 16:20:01 alex>
#
# pylint: enable=R0801


"""
SOLIDserver NOM folder

"""

# import binascii
# import ipaddress
import logging
# import re
import time

# from packaging.version import Version, parse
from SOLIDserverRest.Exception import (SDSError, SDSInitError, SDSEmptyError)

from .class_params import ClassParams
from .space import Space


class NomFolder(ClassParams):
    """ class to manipulate the SOLIDserver Network Object Manager folder """

    # -------------------------------------
    def __init__(self, sds=None,  # pylint: enable=too-many-arguments
                 name=None,
                 parent=None,
                 class_params=None):
        """init a NOM folder object:
        - sds: object SOLIDserver, could be set afterwards
        """

        self.space = None
        self.parent = None
        self.description = None

        self.clean_params()

        super().__init__(sds, name)
        # self.set_sds(sds)

        if parent:
            self.set_parent(parent)

        if class_params is not None:
            self.set_class_params(class_params)

    # -------------------------------------
    def clean_params(self):
        """ clean the object params """
        super().clean_params()

        self.space = None
        self.parent = None
        self.description = ""

    # -------------------------------------
    def set_parent(self, parent):
        """ set a parent folder for this subfolder """
        if parent and not isinstance(parent, NomFolder):
            raise SDSError(
                message=f"parent folder {parent} not of type NomFolder")

        self.parent = parent

    # -------------------------------------
    def set_description(self, descr: str) -> None:
        """ set the description on the folder"""
        if descr != '':
            self.description = descr

    # -------------------------------------
    def create(self):
        """ create the folder """

        if self.sds is None:
            raise SDSError(message="not connected")

        # if object already created
        if self.myid > 0:
            return

        params = {
            **self.additional_params
        }

        if self.name is not None:
            params['nomfolder_name'] = self.name
        else:
            raise SDSInitError(message="missing name to NOM folder")

        if self.parent:
            params['parent_nomfolder_id'] = self.parent.myid

        if self.description != '':
            params['nomfolder_description'] = self.description

        if self.space:
            params['nomfolder_site_name'] = self.space.name

        self.prepare_class_params('nomfolder', params)

        rjson = self.sds.query("nom_folder_create",
                               params=params)

        if 'errmsg' in rjson:
            raise SDSError(message="folder creation, "
                           + rjson['errmsg'])

        self.params['nomfolder_id'] = int(rjson[0]['ret_oid'])
        self.myid = int(self.params['nomfolder_id'])

        self.refresh()

    # -------------------------------------
    def get_id_by_fullname(self, fullname):
        """get the ID of the folder with parent path,
           return None if non existant"""

        params = {
            "limit": 1,
            **self.additional_params
        }
        params.update({"WHERE": f"nomfolder_path='{fullname}'"})

        try:
            rjson = self.sds.query('nom_folder_list',
                                   params=params)
        except SDSError as err_descr:
            msg = f"cannot found NOM folder by full name {fullname}"
            msg += " / " + str(err_descr)
            raise SDSError(msg) from err_descr

        if rjson[0]['errno'] != '0':  # pragma: no cover
            raise SDSError("errno raised on get folder")

        return rjson[0]['nomfolder_id']

    # -------------------------------------
    def refresh(self):
        """refresh content of the NOM folder from the SDS"""

        if self.sds is None:
            raise SDSError(message="not connected")

        if self.myid == -1:
            try:
                if self.parent:
                    parents_name = self.parent.get_parent_name_hierarchy()
                    nomfolder_id = self.get_id_by_fullname(
                        fullname=f"{parents_name}{self.name}")
                else:
                    nomfolder_id = self.get_id_by_fullname(
                        fullname=f"{self.name}")
            except SDSError as err_descr:
                msg = "cannot get NOM folder id"
                msg += " / " + str(err_descr)
                raise SDSError(msg) from err_descr
        else:
            nomfolder_id = self.myid

        params = {
            "nomfolder_id": nomfolder_id,
            **self.additional_params
        }

        rjson = self.sds.query("nom_folder_info",
                               params=params)

        rjson = rjson[0]
        # logging.info(rjson)

        self.myid = int(rjson['nomfolder_id'])

        for label in ['nomfolder_id',
                      'nomfolder_description',
                      'nomfolder_class_name',
                      'nomfolder_nb_netobj']:
            if label not in rjson:   # pragma: no cover
                raise SDSError(f"parameter {label} not found in NOM folder")
            self.params[label] = rjson[label]

        self.name = rjson['nomfolder_name']

        if rjson['nomfolder_class_name'] != '':
            self.set_class_name(rjson['nomfolder_class_name'])

        if rjson['nomfolder_description'] != '':
            self.set_description(rjson['nomfolder_description'])

        if rjson['parent_nomfolder_path'] != '':
            self.parent = NomFolder(
                sds=self.sds, name=rjson['parent_nomfolder_path'])
            self.parent.refresh()

        if not self.space and rjson['nomfolder_site_name'] != '#':
            self.bind_spacename(rjson['nomfolder_site_name'])

        if 'nomfolder_class_parameters' in rjson:   # pragma: no cover
            self.update_class_params(rjson['nomfolder_class_parameters'])

    # -------------------------------------
    def bind_spacename(self, spacename):
        """ associate the folder with a space by name"""
        self.space = Space(self.sds, name=spacename)
        try:
            self.space.refresh()
        except SDSError as e:
            self.space = None
            logging.error("Folder cannot be associated"
                          " with unexistent space (%s)",
                          spacename)
            raise SDSError("space not found") from e

    def bind_space(self, space):
        """ associate the folder with a space"""

        if not isinstance(space, Space):
            raise SDSError("bind not provided space object")

        self.space = space

    # -------------------------------------
    def delete(self):
        """deletes the NOM folder in the SDS"""
        if self.sds is None:
            raise SDSError(message="not connected")

        if self.myid == -1:
            raise SDSError("on NOM folder delete")

        params = {
            'nomfolder_id': self.myid,
            **self.additional_params
        }

        self.sds.query("nom_folder_delete",
                       params=params)

        # check if not present
        b_error = False
        try:
            time.sleep(1)
            self.refresh()
            b_error = True
        except SDSError:
            pass

        if b_error:
            raise SDSError("folder not empty, still exists after delete")

        self.clean_params()

    # -------------------------------------
    def update(self):
        """ update the NOM folder in SDS """

        if self.sds is None:
            raise SDSError(message="not connected")

        if self.name is None or self.name == '':
            raise SDSError(message="requires a name")

        params = {
            'nomfolder_id': self.myid,
            'nomfolder_name': str(self.name),
            **self.additional_params
        }

        if self.description != '':
            params['nomfolder_description'] = self.description

        if self.space != '':
            params['nomfolder_site_name'] = self.space.name

        self.prepare_class_params('nomfolder', params)

        rjson = self.sds.query("nom_folder_update",
                               params=params)

        if 'errmsg' in rjson:  # pragma: no cover
            raise SDSError(message="NOM folder update error, "
                           + rjson['errmsg'])

        self.refresh()

    # -------------------------------------

    def set_param(self, param=None, value=None, exclude=None, name=None):
        """ set a specific param on the NOM folder object """
        super().set_param(param,
                          value,
                          exclude=['nomfolder_id'],
                          name='name')

    # -------------------------------------

    def get_parent_name_hierarchy(self) -> str:
        """ return a string of the full parent path"""
        if self.parent:
            parent_name = self.parent.get_parent_name_hierarchy()
            return f"{parent_name}{self.name}/"

        return f"{self.name}/"

    # -------------------------------------
    def list(self, offset=0, page=25, limit=0, collected=0):
        """return the list of folder in NOM"""

        params = {
            'limit': page,
            'offset': offset,
            'ORDERBY': 'nomfolder_path'
        }

        if limit > 0:
            if page > limit:
                params['limit'] = limit

        try:
            rjson = self.sds.query("nom_folder_list",
                                   params=params)
        except SDSEmptyError:
            return None

        if 'errmsg' in rjson:  # pragma: no cover
            raise SDSError(message="NOM folder list, "
                           + rjson['errmsg'])

        afolders = []
        for _s in rjson:
            # print(_s)

            _r = {
                'id': _s['nomfolder_id'],
                'name': _s['nomfolder_name'],
                'parent': '',
                'description': _s['nomfolder_description'],
                'class': _s['nomfolder_class_name'],
                'object': _s['nomfolder_nb_netobj']
            }

            if _s['parent_nomfolder_name'] != '#':
                _r['parent'] = _s['parent_nomfolder_name']

            if 'nomfolder_class_parameters' in _s:
                self.update_class_params(_s['nomfolder_class_parameters'])
                self.filter_private_class_params()

                _pcp = self.get_class_params(private=True)
                if len(_pcp) > 0:
                    _r['meta'] = _pcp
                else:
                    _r['meta'] = {}

                _r['tree_level'] = int(_s['nomfolder_level'])

            afolders.append(_r)

        # no limit, we should get all the records
        if len(rjson) == page:
            if limit == 0 or (collected + page) < limit:
                newfolders = self.list(offset + page,
                                       page=page,
                                       limit=limit,
                                       collected=(len(afolders)
                                                  + collected))
                if newfolders is not None:
                    afolders += newfolders

        if limit and len(afolders) > limit:
            afolders = afolders[:limit]

        return afolders

    # -------------------------------------
    def __str__(self):  # pragma: no cover
        """return the string notation of the NOM Folder object"""

        return_val = "*NOM folder* "

        if self.parent:
            parents_name = self.parent.get_parent_name_hierarchy()
            return_val += f"{parents_name}"

        if self.name:
            return_val += f"{self.name}"
        else:
            return_val += "no_name"

        if self.space is not None:
            return_val += f" space={self.space.name}"

        if self.description:
            return_val += f" \"{self.description}\""

        return_val += self.str_params(exclude=['nomfolder_id',
                                               'name'])

        return_val += str(super().__str__())

        return return_val
