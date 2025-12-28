#!/bin/env python3

# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import os
import logging

from licomp_doubleopen.config import module_name
from licomp_doubleopen.config import module_url
from licomp_doubleopen.config import doubleopen_url
from licomp_doubleopen.config import licomp_doubleopen_version
from licomp_doubleopen.config import my_supported_api_version
from licomp_doubleopen.config import disclaimer

from licomp.interface import Licomp
from licomp.interface import Provisioning
from licomp.interface import UseCase
from licomp.interface import CompatibilityStatus

SCRIPT_DIR = os.path.dirname(__file__)
MATRIX_FILE_NAME = 'doubleopen-bindist.json'
MATRIX_DIR = os.path.join(SCRIPT_DIR, 'data')
MATRIX_FILE = os.path.join(MATRIX_DIR, MATRIX_FILE_NAME)

class LicompDoubleOpen(Licomp):

    def __init__(self):
        Licomp.__init__(self)
        self.provisionings = [Provisioning.BIN_DIST]
        self.usecases = [UseCase.LIBRARY]
        logging.debug(f'Reading JSON file: {MATRIX_FILE}')

        with open(MATRIX_FILE) as fp:
            self.matrix = json.load(fp)
            self.licenses = self.matrix['licenses']

        self.ret_statuses = {
            "yes": CompatibilityStatus.COMPATIBLE,
            "no": CompatibilityStatus.INCOMPATIBLE,
        }

    def name(self):
        return module_name

    def url(self):
        return module_url

    def data_url(self):
        return doubleopen_url

    def version(self):
        return licomp_doubleopen_version

    def supported_api_version(self):
        return my_supported_api_version

    def supported_licenses(self):
        return list(self.licenses.keys())

    def supported_usecases(self):
        return self.usecases

    def supported_provisionings(self):
        return self.provisionings

    def disclaimer(self):
        return disclaimer

    def _status_to_licomp_status(self, status):
        return self.ret_statuses[status]

    def _outbound_inbound_compatibility(self,
                                        outbound,
                                        inbound,
                                        usecase,
                                        provisioning,
                                        modified):
        compat_object = self.licenses[outbound][inbound]
        compat = compat_object['compatibility']
        reasons = compat_object['comment']
        if reasons == []:
            reasons = None
        compat_value = self.ret_statuses[compat]
        return self.outbound_inbound_reply(compat_value, reasons)
