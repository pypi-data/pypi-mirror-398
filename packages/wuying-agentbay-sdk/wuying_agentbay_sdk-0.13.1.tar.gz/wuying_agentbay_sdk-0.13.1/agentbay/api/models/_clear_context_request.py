# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
from __future__ import annotations

from darabonba.model import DaraModel


class ClearContextRequest(DaraModel):
    def __init__(
        self,
        authorization: str = None,
        id: str = None,
        login_region_id: str = None,
    ):
        self.authorization = authorization
        self.id = id
        self.login_region_id = login_region_id

    def validate(self):
        pass

    def to_map(self):
        result = dict()
        _map = super().to_map()
        if _map is not None:
            result = _map
        if self.authorization is not None:
            result["Authorization"] = self.authorization

        if self.id is not None:
            result["Id"] = self.id

        if self.login_region_id is not None:
            result["LoginRegionId"] = self.login_region_id

        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get("Authorization") is not None:
            self.authorization = m.get("Authorization")

        if m.get("Id") is not None:
            self.id = m.get("Id")

        if m.get("LoginRegionId") is not None:
            self.login_region_id = m.get("LoginRegionId")

        return self
