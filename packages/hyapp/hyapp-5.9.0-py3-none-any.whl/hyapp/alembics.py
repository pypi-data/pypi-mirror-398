from __future__ import annotations

import alembic
import alembic.operations
import alembic.script


def process_revision_directives(context, revision, directives) -> None:
    """Prefix alembic migration revisions with a consecutive number"""
    migration_script = directives[0]
    assert isinstance(migration_script, alembic.operations.MigrationScript)

    head_revision = alembic.script.ScriptDirectory.from_config(context.config).get_current_head()
    if head_revision is None:
        new_rev_id = 1
    else:
        last_rev_id = int(head_revision.split("_", 1)[0].lstrip("0"))
        new_rev_id = last_rev_id + 1

    old_rev_id = migration_script.rev_id or ""
    migration_script.rev_id = f"{new_rev_id:04}_{old_rev_id[:6]}"
