import os
import time
import uuid as uuid_lib

import typer

app = typer.Typer(help="Utility commands")


def _uuid7() -> str:
    """Generate UUID v7 (time-sortable)."""
    timestamp_ms = int(time.time() * 1000)
    rand_bytes = os.urandom(10)

    # 48 bits of timestamp
    uuid_bytes = timestamp_ms.to_bytes(6, "big")
    # 4 bits version (7) + 12 bits random
    uuid_bytes += bytes([(0x70 | (rand_bytes[0] & 0x0F)), rand_bytes[1]])
    # 2 bits variant (10) + 62 bits random
    uuid_bytes += bytes([(0x80 | (rand_bytes[2] & 0x3F))] + list(rand_bytes[3:10]))

    hex_str = uuid_bytes.hex()
    return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:]}"


@app.command()
def uuid(
    v7: bool = typer.Option(False, "--v7", help="Generate UUID v7 (time-sortable)"),
    count: int = typer.Option(1, "--count", "-n", help="Number of UUIDs to generate"),
):
    """Generate UUIDs."""
    for _ in range(count):
        if v7:
            print(_uuid7())
        else:
            print(uuid_lib.uuid4())
