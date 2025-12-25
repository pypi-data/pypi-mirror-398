import hashlib
import json
import os
import math
from collections.abc import Iterable, Iterator, Sized
from ._core import NamedDataset, DatasetItem, ScoreSummary, Run

__all__ = [
    "DatasetRunningDigest",
    "parse_duration",
    "format_duration",
    "redlite_data_dir",
]


def _serialize(obj: dict | DatasetItem | list | str | int | float) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")


class DatasetRunningDigest(Sized, Iterable[DatasetItem]):
    """Helper object to compute data digest."""

    def __init__(self, dataset: NamedDataset, max_samples=0):
        self._digest = b"\x00" * 32
        self._dataset = dataset
        self._max_samples = max_samples

    def __iter__(self) -> Iterator[DatasetItem]:
        count = 0
        for item in self._dataset:
            yield item
            record_digest = hashlib.sha256(
                _serialize({"id": item["id"], "messages": item["messages"], "expected": item["expected"]}),
                usedforsecurity=False,
            ).digest()
            self._digest = bytes(a ^ b for a, b in zip(self._digest, record_digest))
            count += 1
            if self._max_samples > 0 and count >= self._max_samples:
                break

    def __len__(self):
        return len(self._dataset) if self._max_samples == 0 else min(len(self._dataset), self._max_samples)

    @property
    def hexdigest(self) -> str:
        return self._digest.hex()


def object_digest(object: list | dict | str | int | float) -> str:
    """Computes SHA digest of any JSON-serializable object"""
    _hash = hashlib.sha256(usedforsecurity=False)
    _hash.update(_serialize(object))
    return _hash.hexdigest()


def format_duration(seconds: float) -> str:
    """Formats duration to a compact human-readable string, e.g. "1d 4h 27m 14.5s".

    - **seconds** (`float`): Time duration in seconds.

    Returns string, representing the same duration as a human-readable value, for example "1d 4h 27m 14.5s".
    """

    out = []
    minutes = math.floor(seconds // 60)
    seconds -= minutes * 60
    out.append(f"{round(seconds, 2)}s")
    if minutes > 0:
        hours = minutes // 60
        minutes -= hours * 60
        out.append(f"{minutes}m")
        if hours > 0:
            days = hours // 24
            hours -= days * 24
            out.append(f"{hours}h")
            if days > 0:
                out.append(f"{days}d")
    return " ".join(reversed(out))


def parse_duration(duration: str) -> float:
    """Parses human-readable duration into float number, representing seconds.

    - **duration** (`str`): Duration string, for example: "1h 24m 33s".

    Returns `float` value representing the same duration in seconds.
    """
    seconds = 0.0
    minutes = 0.0
    hours = 0.0
    days = 0.0
    for x in reversed(duration.split()):
        if x[-1] == "s":
            seconds = float(x[:-1])
        elif x[-1] == "m":
            minutes = float(x[:-1])
        elif x[-1] == "h":
            hours = float(x[:-1])
        elif x[-1] == "d":
            days = float(x[:-1])
        else:
            raise ValueError(f"Invalid duration string: [{duration}]")
    return seconds + minutes * 60 + hours * 60 * 60 + days * 24 * 60 * 60


def format_score_summary(summary: ScoreSummary) -> str:
    return f"{round(summary['mean'], 3)} (#{summary['count']}, {round(summary['min'], 3)}-{round(summary['max'], 3)})"


def redlite_data_dir() -> str:
    """Returns the location of RedLite data directory.

    Returns location of the RedLite data directory.
    """
    return os.environ.get("REDLITE_DATA_DIR", os.path.expanduser("~/.cache/redlite"))


class ScoreAccumulator:
    """Helper object that computes metric statistics"""

    def __init__(self):
        self._min = 100000  # FIXME?
        self._max = 0.0
        self._acc = 0.0
        self._count = 0

    def __call__(self, score: float) -> None:
        """Adds another score to the statistics.

        - **score** (`float`): Score data point.
        """
        self._acc += score
        self._min = min(self._min, score)
        self._max = max(self._max, score)
        self._count += 1

    @property
    def summary(self) -> ScoreSummary:
        """Computes and returns statistics.

        Returns plain dict containing `count`, `mean`, `min`, and `max` values.
        """
        mean = 0.0 if self._count == 0 else self._acc / self._count
        return dict(
            count=self._count,
            mean=mean,
            min=self._min,
            max=self._max,
        )


def read_runs(base: str) -> Iterator[Run]:
    """Iterator that reads all runs' metadata.

    - **base** (`str`): Directory where runs are stored.

    Returns `Iterator[dict]` yielding metadata dict for each discovered run.
    """
    if not os.path.isdir(base):
        return

    for name in os.listdir(base):
        meta_name = os.path.join(base, name, "meta.json")
        if not os.path.isfile(meta_name):
            continue

        with open(meta_name, encoding="utf-8") as f:
            meta = json.load(f)

        data_name = os.path.join(base, name, "data.jsonl")
        if not os.path.isfile(data_name):
            continue

        yield _fixup_meta(meta)


def read_data(base: str, name: str) -> Iterator[dict]:
    """Iterator that reads run data.

    - **base** (`str`): Directory where runs are stored.
    - **name** (`str`): Name of the run.

    Returns `Iterator[dict]` yielding dataset records.
    """
    meta_name = os.path.join(base, name, "meta.json")
    if not os.path.isfile(meta_name):
        return

    data_name = os.path.join(base, name, "data.jsonl")
    if not os.path.isfile(data_name):
        return

    with open(data_name, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def read_meta(base: str, name: str) -> Run:
    """Reads run metadata.

    - **base (`str`): Directory where runs are stored.
    - **name (`str`): Name of the run.

    Returns a dictionary containing run metadata.
    """
    meta_name = os.path.join(base, name, "meta.json")
    if not os.path.isfile(meta_name):
        raise FileNotFoundError()

    data_name = os.path.join(base, name, "data.jsonl")
    if not os.path.isfile(data_name):
        raise FileNotFoundError()

    with open(meta_name, "r", encoding="utf-8") as f:
        return _fixup_meta(json.load(f))


def _fixup_meta(meta: dict) -> Run:
    """
    Legacy code generated formatted duration. Now we leave it as seconds (float).

    Similarly, have added "split" key, and renamed "name" to "run".
    """
    if type(meta["duration"]) is str:
        meta["duration"] = parse_duration(meta["duration"])
    if "name" in meta:
        meta["run"] = meta.pop("name")
    if "split" not in meta:
        meta["split"] = "test"
    return meta  # type: ignore [return-value]


def sha_digest(object: dict | list | int | float | str) -> str:
    """
    Computes SHA256 digest of a JSON-serializable object
    """
    sha256 = hashlib.sha256(usedforsecurity=False)
    sha256.update(json.dumps(object, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return sha256.hexdigest()
