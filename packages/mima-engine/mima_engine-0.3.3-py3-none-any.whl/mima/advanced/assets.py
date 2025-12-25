import csv
import logging
from pathlib import Path
from typing import Any, TypeAlias

from mima.standalone.tiled_map import MapManager

CSVContent: TypeAlias = list[dict[str, str]]
LOG = logging.getLogger(__name__)


class AssetManager(MapManager):
    def __init__(self) -> None:
        super().__init__()

        self._csvs: dict[str, CSVContent] = {}

    def _load_file(self, fp: Path, skip_invalid: bool = False) -> None:
        if str(fp) in self._loaded_paths:
            return

        _, suf = fp.parts[-1].rsplit(".")

        if suf.lower() == "png":
            self._load_image(fp)
        elif suf.lower() == "csv":
            self._load_csv(fp)
        else:
            super()._load_file(fp, skip_invalid)

    def _load_csv(self, path: Path) -> str:
        name = Path(path).parts[-1].rsplit(".", 1)[0]
        if name in self._csvs:
            return name

        with path.open("r") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=",")
            self._csvs[name] = [r for r in reader]

        self._loaded_paths[str(path)] = name

        return name

    def get_csv(self, name: str | Path) -> CSVContent:
        name = str(name)
        if name in self._csvs:
            return self._csvs[name]
        if name in self._loaded_paths:
            return self._csvs[self._loaded_paths[name]]

        LOG.info("CSV '%s' not found. Attempting to read from disk ...", name)
        self._load_csv(Path(name))

        return self._csvs[self._loaded_paths[name]]
