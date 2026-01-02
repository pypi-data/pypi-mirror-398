# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.columns.column_types import ForeignKey, Integer, Serial, Timestamptz, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.indexes import IndexMethod
from piccolo.table import Table


class Moderation(Table, tablename="moderation", schema=None):
    id = Serial(
        null=False,
        primary_key=True,
        unique=False,
        index=False,
        index_method=IndexMethod.btree,
        choices=None,
        db_column_name="id",
        secret=False,
    )


class PartialGuild(Table, tablename="partial_guild", schema=None):
    id = Serial(
        null=False,
        primary_key=True,
        unique=False,
        index=True,
        index_method=IndexMethod.btree,
        choices=None,
        db_column_name=None,
        secret=False,
    )


class PartialRole(Table, tablename="partial_role", schema=None):
    id = Serial(
        null=False,
        primary_key=True,
        unique=False,
        index=True,
        index_method=IndexMethod.btree,
        choices=None,
        db_column_name=None,
        secret=False,
    )


ID = "2025-09-26T09:29:17:713551"
VERSION = "1.28.0"
DESCRIPTION = "Support setting roles as moderation targets"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="TidegearSentinel", description=DESCRIPTION)

    manager.add_table(
        class_name="PartialRole",
        tablename="partial_role",
        schema=None,
        columns=None,
    )

    manager.add_column(
        table_class_name="PartialRole",
        tablename="partial_role",
        column_name="id",
        db_column_name="id",
        column_class_name="Serial",
        column_class=Serial,
        params={
            "null": False,
            "primary_key": True,
            "unique": False,
            "index": True,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    manager.add_column(
        table_class_name="PartialRole",
        tablename="partial_role",
        column_name="guild_id",
        db_column_name="guild_id",
        column_class_name="ForeignKey",
        column_class=ForeignKey,
        params={
            "references": PartialGuild,
            "on_delete": OnDelete.cascade,
            "on_update": OnUpdate.cascade,
            "target_column": None,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    manager.add_column(
        table_class_name="PartialRole",
        tablename="partial_role",
        column_name="role_id",
        db_column_name="role_id",
        column_class_name="Integer",
        column_class=Integer,
        params={
            "default": 0,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": True,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    manager.add_column(
        table_class_name="PartialRole",
        tablename="partial_role",
        column_name="last_known_name",
        db_column_name="last_known_name",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 100,
            "default": "Unknown Role",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    manager.add_column(
        table_class_name="PartialRole",
        tablename="partial_role",
        column_name="last_updated",
        db_column_name="last_updated",
        column_class_name="Timestamptz",
        column_class=Timestamptz,
        params={
            "default": TimestamptzNow(),
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    manager.add_column(
        table_class_name="Moderation",
        tablename="moderation",
        column_name="target_role_id",
        db_column_name="target_role_id",
        column_class_name="ForeignKey",
        column_class=ForeignKey,
        params={
            "references": PartialRole,
            "on_delete": OnDelete.cascade,
            "on_update": OnUpdate.cascade,
            "target_column": None,
            "null": True,
            "primary_key": False,
            "unique": False,
            "index": True,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    manager.alter_column(
        table_class_name="Change",
        tablename="change",
        column_name="moderation_id",
        db_column_name="moderation_id",
        params={"references": Moderation},
        old_params={"references": Moderation},
        column_class=ForeignKey,
        old_column_class=ForeignKey,
        schema=None,
    )

    return manager
