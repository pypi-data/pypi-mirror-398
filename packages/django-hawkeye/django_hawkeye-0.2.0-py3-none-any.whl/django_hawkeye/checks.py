from django.core.checks import Error, Tags, Warning, register
from django.db import connection


@register(Tags.database)
def check_postgresql_version(app_configs, **kwargs):
    """
    Check that PostgreSQL version is 17+ (required for pg_textsearch).
    """
    errors = []

    if connection.vendor != "postgresql":
        errors.append(
            Error(
                "django-pg-textsearch requires PostgreSQL",
                hint=f"You are using {connection.vendor}. Switch to PostgreSQL 17+.",
                id="django_hawkeye.E001",
            )
        )
        return errors

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version_string = cursor.fetchone()[0]

            import re

            match = re.search(r"PostgreSQL (\d+)", version_string)
            if match:
                major_version = int(match.group(1))

                if major_version < 17:
                    errors.append(
                        Error(
                            f"PostgreSQL version {major_version} is not supported",
                            hint="pg_textsearch requires PostgreSQL 17 or later.",
                            id="django_hawkeye.E002",
                        )
                    )
    except Exception as e:
        errors.append(
            Warning(
                f"Could not determine PostgreSQL version: {e}",
                id="django_hawkeye.W001",
            )
        )

    return errors


def is_pg_textsearch_available():
    """
    Check if pg_textsearch extension is available and installed.

    Returns:
        bool: True if extension is installed
    """
    if connection.vendor != "postgresql":
        return False

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_textsearch')"
            )
            return cursor.fetchone()[0]
    except Exception:
        return False


def get_postgresql_version():
    """
    Get the major PostgreSQL version number.

    Returns:
        int or None: Major version number or None if not available
    """
    if connection.vendor != "postgresql":
        return None

    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version_num")
            version_num = int(cursor.fetchone()[0])
            return version_num // 10000
    except Exception:
        return None
