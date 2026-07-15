import json
import platform
from pathlib import Path

import psycopg

import labrecall
from labrecall.app import app


def main() -> None:
    static_dir = Path(labrecall.__file__).parent / "static"
    assert (static_dir / "index.html").is_file()
    print(
        json.dumps(
            {
                "architecture": platform.machine(),
                "application": app.title,
                "psycopg_version": psycopg.__version__,
                "static_assets": sorted(path.name for path in static_dir.iterdir()),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
