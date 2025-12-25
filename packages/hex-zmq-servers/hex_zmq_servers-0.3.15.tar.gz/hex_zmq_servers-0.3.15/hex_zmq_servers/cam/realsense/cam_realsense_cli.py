#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

from ..cam_base import HexCamClientBase

NET_CONFIG = {
    "ip": "127.0.0.1",
    "port": 12345,
    "realtime_mode": False,
    "deque_maxlen": 10,
    "client_timeout_ms": 200,
    "server_timeout_ms": 1_000,
    "server_num_workers": 4,
}


class HexCamRealsenseClient(HexCamClientBase):

    def __init__(
        self,
        net_config: dict = NET_CONFIG,
    ):
        HexCamClientBase.__init__(self, net_config)
        self._wait_for_working()

    def get_intri(self):
        intri_hdr, intri = self.request({"cmd": "get_intri"})
        return intri_hdr, intri
