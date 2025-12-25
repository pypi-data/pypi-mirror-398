#
# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2022-01-14 11:55:52 alex>
#

"""
SOLIDserver space management

get an existing space:
    space = sdsadv.Space(sds=sds, name="Local")
    space.refresh()

create a new space:
    space = sdsadv.Space(sds, name="test")
    space.create()

"""

import logging
# import math
# import pprint
import urllib

from SOLIDserverRest.Exception import SDSInitError, SDSError
from SOLIDserverRest.Exception import SDSEmptyError, SDSSpaceError
# from SOLIDserverRest.Exception import SDSNetworkError

from .class_params import ClassParams


class Space(ClassParams):
    """ class to manipulate the SOLIDserver spaces """

    # -------------------------------------
    def __init__(self, sds=None,
                 name="Local",
                 class_params=None):
        """init the space object:
        - sds: object SOLIDserver, could be set afterwards
        - name: space name, default Local
        """

        super().__init__(sds, name)

        # self.name = name
        # self.sds = sds

        self.parent = None
        self.description = None

        self.params = {
            'site_is_template': None,
            'site_id': None,
            'tree_level': None,
            'site_name': None,
            'site_description': None,
            'parent_site_id': None,
            'parent_site_name': None,
            'site_class_name': None,
            'parent_site_class_name': None,
            'row_enabled': None,
            'multistatus': None,
        }

        if class_params is not None:
            self.set_class_params(class_params)

    # -------------------------------------
    def clean_params(self):
        """ clean the object params """
        super().clean_params()

        self.parent = None
        self.description = None

    # -------------------------------------
    def set_parent(self, parent):
        if not parent:
            raise SDSSpaceError("no parent space provided")

        if not isinstance(parent, Space):
            raise SDSSpaceError("no valid parent space provided")

        self.parent = parent

    # -------------------------------------
    def set_parent_byname(self, parent_name: str) -> None:
        if not parent_name:
            raise SDSSpaceError("no parent space name provided")

        parent = Space(sds=self.sds,
                       name=parent_name)
        parent.refresh()

        self.set_parent(parent)

    # -------------------------------------
    def set_description(self, descr=None) -> None:
        if not descr:
            raise SDSSpaceError("no description provided")

        if not isinstance(descr, str):
            raise SDSSpaceError("no valid description provided")

        self.description = descr

    # -------------------------------------
    def create(self):
        """creates the space in the SDS"""
        if self.sds is None:
            raise SDSSpaceError(message="not connected")

        space_id = None
        try:
            space_id = self._get_id_by_name('ip_site_list', 'site', self.name)
        except SDSError:
            None  # pylint: disable=W0104

        # space_id = self._get_siteid_by_name(self.name)
        if space_id is not None:
            raise SDSSpaceError(message="already existant space")

        params = {
            'site_name': self.name,
            **self.additional_params
        }

        if self.parent:
            params['parent_site_id'] = self.parent.myid

        if self.description:
            params['site_description'] = self.description

        self.prepare_class_params('site', params)

        try:
            rjson = self.sds.query("ip_site_create",
                                   params=params)
        except SDSError:   # pragma: no cover
            logging.error("create space")

        if len(rjson) != 1:   # pragma: no cover
            raise SDSSpaceError(message="space creation error,"
                                + " array not recognized")
        if 'ret_oid' not in rjson[0]:   # pragma: no cover
            raise SDSSpaceError(message="space creation error, id not found")

        self.params['site_id'] = int(rjson[0]['ret_oid'])
        self.refresh()

    # -------------------------------------
    def delete(self):
        """deletes the space in the SDS"""
        if self.sds is None:
            raise SDSSpaceError(message="not connected")

        if self.myid <= 0:
            space_id = self._get_id_by_name('ip_site_list', 'site', self.name)
        else:
            space_id = self.myid

        try:
            rjson = self.sds.query("ip_site_delete",
                                   params={
                                       'site_id': space_id,
                                       **self.additional_params
                                   })
            if 'errmsg' in rjson:  # pragma: no cover
                raise SDSSpaceError(message="space delete error, "
                                    + rjson['errmsg'])
        except SDSError as sdse:   # pragma: no cover
            raise SDSSpaceError(message="space delete error") from sdse

        self.clean_params()

    # -------------------------------------
    def refresh(self):
        """refresh content of the object from the SDS"""
        if self.sds is None:
            raise SDSInitError(message="not connected")

        if self.myid <= 0:
            space_id = self._get_id_by_name('ip_site_list', 'site', self.name)
        else:
            space_id = self.myid

        if space_id is None:
            raise SDSEmptyError(message="non existant space")

        rjson = self.sds.query("ip_site_info",
                               params={
                                   "site_id": space_id,
                                   **self.additional_params
                               })

        if not rjson:   # pragma: no cover
            raise SDSSpaceError(message="space refresh error, len of array")

        rjson = rjson[0]

        for label in ['site_is_template',
                      'site_id',
                      'tree_level',
                      'site_name',
                      'site_description',
                      'parent_site_id',
                      'parent_site_name',
                      'site_class_name',
                      'parent_site_class_name',
                      'row_enabled',
                      'multistatus']:
            if label not in rjson:   # pragma: no cover
                raise SDSError(f"parameter {label} not found in space")
            self.params[label] = rjson[label]

        self.myid = int(self.params['site_id'])

        self.set_name(self.params['site_name'])
        self.params.pop('site_name')

        if self.params['site_description'] and self.params['site_description'] != '':
            self.set_description(self.params['site_description'])
            self.params.pop('site_description')

        if self.params['site_class_name'] and self.params['site_class_name'] != '':
            self.set_class_name(self.params['site_class_name'])
            self.params.pop('site_class_name')

        if self.params['parent_site_name'] and self.params['parent_site_name'] != '#':
            if not self.parent:
                self.set_parent_byname(self.params['parent_site_name'])
                self.params.pop('parent_site_name')

        if 'site_class_parameters' in rjson:
            self.update_class_params(rjson['site_class_parameters'])
            self.filter_private_class_params()

    # -------------------------------------
    def update(self):
        """ update the space in SDS """

        if self.sds is None:
            raise SDSSpaceError(message="not connected")

        if self.myid == -1:
            raise SDSSpaceError(
                message="object not initialized, need refresh or create")

        params = {
            'site_id': self.myid,
            'site_name': self.name,
            **self.additional_params
        }

        if self.description:
            params['site_description'] = self.description

        self.prepare_class_params('site', params)

        # logging.info(params)

        try:
            rjson = self.sds.query("ip_site_update",
                                   params=params)
        except SDSError:   # pragma: no cover
            logging.error("update space")

        # print(rjson)
        if len(rjson) != 1:   # pragma: no cover
            raise SDSSpaceError(message="update error, "
                                + rjson['errmsg'])
        if 'ret_oid' not in rjson[0]:   # pragma: no cover
            raise SDSSpaceError(message="space update error, id not found")

        self.refresh()

    # -------------------------------------
    def list_spaces(self, offset=0, page=25, limit=0, collected=0):
        """return the list of spaces"""
        # print(
        #     f"call offset={offset} page={page} limit={limit} collected={collected}")

        params = {
            'limit': page,
            'offset': offset,
        }

        params['WHERE'] = 'site_is_template=0'
        params['ORDERBY'] = 'tree_path'

        if limit > 0:
            if page > limit:
                params['limit'] = limit

        try:
            rjson = self.sds.query("ip_site_list",
                                   params=params)
        except SDSEmptyError:
            return None

        if 'errmsg' in rjson:  # pragma: no cover
            raise SDSSpaceError(message="space list, "
                                + rjson['errmsg'])

        aspaces = []
        for _s in rjson:
            # print(_s)

            _r = {
                'id': _s['site_id'],
                'name': _s['site_name'],
                'parent': '',
                'description': _s['site_description'],
                'class': _s['site_class_name']

            }

            if _s['parent_site_name'] != '#':
                _r['parent'] = _s['parent_site_name']

            if 'site_class_parameters' in _s:
                self.update_class_params(_s['site_class_parameters'])
                self.filter_private_class_params()

                _pcp = self.get_class_params(private=True)
                if len(_pcp) > 0:
                    _r['meta'] = _pcp
                else:
                    _r['meta'] = {}

                _r['tree_level'] = int(_s['tree_level'])

            aspaces.append(_r)

        # no limit, we should get all the records
        if len(rjson) == page:
            if limit == 0 or (collected + page) < limit:
                newspaces = self.list_spaces(offset + page,
                                             page=page,
                                             limit=limit,
                                             collected=(len(aspaces)
                                                        + collected))
                if newspaces is not None:
                    aspaces += newspaces

        if limit and len(aspaces) > limit:
            aspaces = aspaces[:limit]

        return aspaces

    # -------------------------------------
    def __str__(self):
        """return the string notation of the space object"""
        return_val = f"*space* name={self.name}"

        if self.myid != -1:
            return_val += f" id={self.myid}"

        if self.description is not None and self.description != "":
            return_val += f" \"{self.description}\""

        if self.parent is not None:
            return_val += f" parent={self.parent.name}"

        return_val += str(super().__str__())

        return return_val
