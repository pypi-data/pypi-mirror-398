# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

"""Piccolo engine and registry configuration."""

import os

from piccolo.conf.apps import AppRegistry
from piccolo.engine.sqlite import SQLiteEngine

if not (path := os.getenv("DB_PATH")):
    msg = "DB_PATH environment variable not set!"
    raise ValueError(msg)

DB = SQLiteEngine(path=path)

APP_REGISTRY = AppRegistry(apps=["tidegear.sentinel.db.piccolo_app"])
