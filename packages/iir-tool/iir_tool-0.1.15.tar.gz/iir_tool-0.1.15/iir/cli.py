import os
import sys
from importlib import metadata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

COMMAND_MAP = {
    "replace": "replace_text",
    "add-entry": "add_entry",
}
AVAILABLE_SUBCOMMANDS = sorted(
    [*COMMAND_MAP, "admin", "api", "dev-init", "dev-remove", "version"]
)


def main(argv=None):
    argv = list(argv) if argv is not None else sys.argv[1:]

    if not argv:
        sys.stderr.write(_usage())
        return 1

    subcommand, *rest = argv
    if subcommand == "--help":
        # Treat top-level help as a successful invocation (no Django init).
        sys.stdout.write(_usage())
        return 0
    if subcommand == "--version":
        print(f"iir {metadata.version('iir-tool')}")
        return 0
    if subcommand == "version":
        print(f"iir {metadata.version('iir-tool')}")
        return 0
    if subcommand == "dev-init":
        return dev_init()
    if subcommand == "dev-remove":
        return dev_remove()
    if subcommand == "admin":
        return admin_command(rest)
    if subcommand == "api":
        return api_command(rest)

    command = COMMAND_MAP.get(subcommand)
    if command is None:
        sys.stderr.write(f"Unknown subcommand: {subcommand}\n")
        sys.stderr.write(_usage())
        return 1

    # ★ 追加：Django プロジェクトルートを import path に追加
    sys.path.insert(0, str(PROJECT_ROOT))

    if _bootstrap_local_state() != 0:
        return 1
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "svr.settings")
    import django
    django.setup()

    from django.core.management import call_command
    call_command(command, *rest)
    return 0


def dev_init():
    from django.core.management.utils import get_random_secret_key

    data_dir = os.environ.get("DATA_DIR")
    if data_dir:
        data_path = Path(data_dir)
        if not data_path.exists():
            sys.stderr.write(f"DATA_DIR does not exist: {data_dir}\n")
            return 1
        if not data_path.is_dir():
            sys.stderr.write(f"DATA_DIR is not a directory: {data_dir}\n")
            return 1
        secret_path = data_path / ".env.secret"
        sqlite_path = data_path / "db.sqlite3"
    else:
        secret_path = _cwd_secret_path()
        sqlite_path = None
    if secret_path.exists():
        print("Already exists, nothing to do")
    else:
        secret = get_random_secret_key()
        secret_path.write_text(f'DJANGO_SECRET_KEY="{secret}"\n')
        print("Created .env.secret")
    if sqlite_path is not None:
        sqlite_path.touch(exist_ok=True)
    return 0


def dev_remove():
    secret_path = _cwd_secret_path()
    if not secret_path.exists():
        print("No .env.secret found")
        return 0
    secret_path.unlink()
    print("Removed .env.secret")
    return 0


def api_command(args):
    if not args:
        sys.stderr.write("Usage: iir api <subcommand> [options]\n")
        return 1

    subcommand, *rest = args
    if subcommand == "create-token":
        return create_token(rest)

    sys.stderr.write(f"Unknown api subcommand: {subcommand}\n")
    sys.stderr.write("Usage: iir api create-token <username>\n")
    return 1


def admin_command(args):
    if not args:
        sys.stderr.write("Usage: iir admin <subcommand> [options]\n")
        return 1

    subcommand, *rest = args
    if subcommand not in {"createsuperuser", "collectstatic", "migrate", "runserver"}:
        sys.stderr.write(f"Unknown admin subcommand: {subcommand}\n")
        sys.stderr.write(
            "Usage: iir admin createsuperuser|collectstatic|migrate|runserver [options]\n"
        )
        return 1

    sys.path.insert(0, str(PROJECT_ROOT))
    if subcommand == "migrate":
        return admin_migrate(rest)

    if _bootstrap_local_state() != 0:
        return 1
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "svr.settings")
    import django
    django.setup()

    if subcommand == "runserver":
        try:
            host, port = _parse_addrport(rest)
        except ValueError as exc:
            sys.stderr.write(f"{exc}\n")
            sys.stderr.write("Usage: iir admin runserver [addrport]\n")
            return 1

        import uvicorn

        uvicorn.run("svr.asgi:application", host=host, port=port)
        return 0

    from django.core.management import call_command
    call_command(subcommand, *rest)
    return 0


def admin_migrate(args):
    if args:
        sys.stderr.write("Usage: iir admin migrate\n")
        return 1

    state_dir = _state_dir()
    if state_dir is None:
        return 1

    sys.stdout.write(f"Using state directory: {state_dir}\n")

    env_path = state_dir / ".env.secret"
    sys.stdout.write(f"Loading env file: {env_path}\n")
    if not env_path.exists():
        sys.stderr.write("Error: .env.secret not found in state directory.\n")
        sys.stderr.write("Please run `iir dev-init` first.\n")
        return 1

    _load_secret_from_path(env_path)
    if not os.environ.get("DJANGO_SECRET_KEY"):
        sys.stderr.write("Error: DJANGO_SECRET_KEY is not set.\n")
        return 1

    db_engine = os.environ.get("DB_ENGINE", "sqlite").lower()
    if db_engine == "sqlite" and not os.environ.get("SQLITE_PATH"):
        os.environ.setdefault("SQLITE_PATH", str(state_dir / "db.sqlite3"))

    sys.stdout.write("Running database migrations...\n")

    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "svr.settings")
    import django
    django.setup()

    from django.core.management import call_command
    try:
        call_command("migrate")
    except Exception as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    sys.stdout.write("Migration completed successfully.\n")
    return 0


def create_token(args):
    if len(args) != 1:
        sys.stderr.write("Usage: iir api create-token <username>\n")
        return 1

    username = args[0]

    sys.path.insert(0, str(PROJECT_ROOT))
    if _bootstrap_local_state() != 0:
        return 1
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "svr.settings")
    import django
    django.setup()

    from django.contrib.auth import get_user_model
    from rest_framework.authtoken.models import Token

    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        sys.stderr.write(f"User does not exist: {username}\n")
        return 1

    token, _ = Token.objects.get_or_create(user=user)
    sys.stdout.write(f"{token.key}\n")
    return 0


def _cwd_secret_path():
    return Path.cwd() / ".env.secret"


def _load_secret_from_cwd():
    if os.environ.get("DJANGO_SECRET_KEY"):
        return

    secret_path = _cwd_secret_path()
    if not secret_path.exists():
        return

    for line in secret_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not stripped.startswith("DJANGO_SECRET_KEY="):
            continue
        _, value = stripped.split("=", 1)
        if value:
            os.environ["DJANGO_SECRET_KEY"] = value
        return


def _set_sqlite_path():
    db_engine = os.environ.get("DB_ENGINE", "sqlite").lower()
    if db_engine == "sqlite":
        os.environ.setdefault("SQLITE_PATH", str(Path.cwd() / "db.sqlite3"))


def _bootstrap_local_state():
    state_dir = None
    if not os.environ.get("DJANGO_SECRET_KEY"):
        state_dir = _state_dir()
        if state_dir is None:
            return 1
        secret_path = state_dir / ".env.secret"
        if secret_path.exists():
            for line in secret_path.read_text().splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if not stripped.startswith("DJANGO_SECRET_KEY="):
                    continue
                _, value = stripped.split("=", 1)
                if value:
                    os.environ["DJANGO_SECRET_KEY"] = value
                break

    db_engine = os.environ.get("DB_ENGINE", "sqlite").lower()
    if db_engine == "sqlite" and not os.environ.get("SQLITE_PATH"):
        if state_dir is None:
            state_dir = _state_dir()
            if state_dir is None:
                return 1
        os.environ.setdefault("SQLITE_PATH", str(state_dir / "db.sqlite3"))
    return 0


def _load_secret_from_path(secret_path):
    for line in secret_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not stripped.startswith("DJANGO_SECRET_KEY="):
            continue
        _, value = stripped.split("=", 1)
        if value:
            os.environ["DJANGO_SECRET_KEY"] = value
        break


def _state_dir():
    data_dir = os.environ.get("DATA_DIR")
    if not data_dir:
        return Path.cwd()

    data_path = Path(data_dir)
    if not data_path.exists():
        sys.stderr.write(f"DATA_DIR does not exist: {data_dir}\n")
        return None
    if not data_path.is_dir():
        sys.stderr.write(f"DATA_DIR is not a directory: {data_dir}\n")
        return None
    return data_path


def _parse_addrport(args):
    if not args:
        return "127.0.0.1", 8000
    if len(args) != 1:
        raise ValueError("runserver accepts at most one addr:port argument")

    addrport = args[0]
    if addrport.isdigit():
        return "127.0.0.1", int(addrport)

    if ":" not in addrport:
        raise ValueError("addrport must be in the form host:port")

    host, port_str = addrport.rsplit(":", 1)
    if not host:
        raise ValueError("addrport must include a host")
    if not port_str.isdigit():
        raise ValueError("port must be a number")
    return host, int(port_str)


def _usage():
    available = ", ".join(AVAILABLE_SUBCOMMANDS)
    return (
        "Usage: iir <subcommand> [options]\n"
        f"Subcommands: {available}\n"
    )


if __name__ == "__main__":  # pragma: no cover - manual execution guard
    sys.exit(main())
