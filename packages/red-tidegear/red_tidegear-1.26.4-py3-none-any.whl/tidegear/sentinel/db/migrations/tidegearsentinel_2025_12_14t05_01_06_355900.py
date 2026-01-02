# SPDX-FileCopyrightText: 2025 cswimr <copyright@csw.im>
# SPDX-License-Identifier: MPL-2.0

from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import ForeignKey, Serial
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


ID = "2025-12-14T05:01:06:355900"
VERSION = "1.30.0"
DESCRIPTION = "change a column name; add auto-update for timestamps"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="TidegearSentinel", description=DESCRIPTION)

    manager.rename_column(
        table_class_name="PartialChannel",
        tablename="partial_channel",
        old_column_name="last_updated",
        new_column_name="updated_at",
        old_db_column_name="last_updated",
        new_db_column_name="updated_at",
        schema=None,
    )

    manager.rename_column(
        table_class_name="PartialGuild",
        tablename="partial_guild",
        old_column_name="last_updated",
        new_column_name="updated_at",
        old_db_column_name="last_updated",
        new_db_column_name="updated_at",
        schema=None,
    )

    manager.rename_column(
        table_class_name="PartialRole",
        tablename="partial_role",
        old_column_name="last_updated",
        new_column_name="updated_at",
        old_db_column_name="last_updated",
        new_db_column_name="updated_at",
        schema=None,
    )

    manager.rename_column(
        table_class_name="PartialUser",
        tablename="partial_user",
        old_column_name="last_updated",
        new_column_name="updated_at",
        old_db_column_name="last_updated",
        new_db_column_name="updated_at",
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
