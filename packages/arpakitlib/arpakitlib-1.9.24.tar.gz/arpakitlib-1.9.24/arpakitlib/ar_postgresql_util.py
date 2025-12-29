# arpakit

from shlex import quote

from arpakitlib.ar_run_cmd_util import run_cmd
from arpakitlib.ar_type_util import raise_for_type


def make_postgresql_db_dump(
        *,
        user: str,
        host: str = "127.0.0.1",
        db_name: str,
        port: int = 5432,
        out_filepath: str = "db_dump.sql",
        password: str | None = None,
) -> str:
    raise_for_type(user, str)
    raise_for_type(host, str)
    raise_for_type(db_name, str)
    raise_for_type(port, int)
    raise_for_type(out_filepath, str)

    env_prefix = ""
    if password:
        env_prefix = f"PGPASSWORD={quote(password)} "

    command = (
        f"{env_prefix}"
        f"pg_dump "
        f"-U {quote(user)} "
        f"-h {quote(host)} "
        f"-p {port} "
        f"-f {quote(out_filepath)} "
        f"{quote(db_name)}"
    )

    res = run_cmd(command)
    res.raise_for_bad_return_code()

    return out_filepath


def __example():
    pass


if __name__ == '__main__':
    __example()
