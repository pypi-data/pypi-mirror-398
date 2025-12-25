import contextlib
import os
from tqdm import tqdm
import duoname
from datetime import datetime, timezone
from ._core import (
    NamedModel,
    NamedDataset,
    NamedMetric,
    Storage,
    Run,
)
from ._jsonl_storage import JsonlStorage
from ._dummy_storage import DummyStorage
from ._util import (
    DatasetRunningDigest,
    redlite_data_dir,
    format_score_summary,
    ScoreAccumulator,
    read_meta,
    read_data,
)
from ._lock import incr_run_count
from typing import Iterator, Callable
from ._core import log


__all__ = ["run", "parallel_run", "rescore"]


def run(
    *,
    model: NamedModel,
    dataset: NamedDataset,
    metric: NamedMetric,
    name: str | None = None,
    max_samples=0,
) -> Run:
    """Runs experiment, using the given `model`, `dataset`, and `metric`.

    - **model** (`NamedModel`): Model.
    - **dataset** (`NamedDataset`): Dataset.
    - **metric** (`NamedMetric`): Metric.
    - **name** (`str`, optional): The name of the run. It will automatically get a
            numeric suffix to ensure global uniqueness.
            If not provided, a unique name will be auto-generated.
    - **max_samples** (`int`, optional): Allows one to limit the number of samples
            in the run. Value of zero (the default) means "run the whole dataset".

    Returns the run metadata as a `dict` object. See Run docs for the structure.

    Sample usage:
    ```python
    model = MyModel(...)
    dataset = MyDataset(...)
    metric = MyMetric(...)

    run(model=model, dataset=dataset, metric=metric)
    ```
    """
    started = datetime.now(tz=timezone.utc)

    data_with_digest = DatasetRunningDigest(dataset, max_samples=max_samples)
    score_accumulator = ScoreAccumulator()

    if name is None:
        name = _generate_name()
    run_count = incr_run_count()
    runname = f"{name}-{run_count}"

    print(f"RedLite run {runname}:")
    print(f"\tmodel  : {model.name}")
    print(f"\tdataset: {dataset.name}")
    print(f"\tmetric : {metric.name}")

    with _storage(runname) as storage:  # type: Storage
        for item in tqdm(data_with_digest):
            actual = model(item["messages"])
            score = metric(item["expected"], actual)
            storage.save(item, actual, score)
            score_accumulator(score)

        completed = datetime.now(tz=timezone.utc)

        this_run: Run = dict(
            run=storage.name,
            dataset=dataset.name,
            split=dataset.split,
            dataset_labels=dataset.labels,
            data_digest=data_with_digest.hexdigest,
            metric=metric.name,
            model=model.name,
            max_samples=max_samples,
            started=started.isoformat(),
            completed=completed.isoformat(),
            duration=(completed - started).total_seconds(),
            score_summary=score_accumulator.summary,
        )

        storage.save_meta(**this_run)

        print()
        print(f"\tData digest: {this_run['data_digest']}")
        print(f"\tScore summary: {format_score_summary(this_run['score_summary'])}")
        print()
        return this_run


def rescore(
    *,
    run: str,
    metric: NamedMetric,
    name: str | None = None,
    dry: bool = False,
) -> Run:
    """Uses a prior experiment and re-runs it with a different metric.

    Model answers will not be re-computed, but each answer will be re-evaluated
    with the new metric. This is normally very fast.

    - **run** (`str`): The parent run.
    - **metric** (`NamedMetric`): Metric.
    - **name** (`str`, optional): The name of the run. It will automatically get a
            numeric suffix to ensure global uniqueness.
            If not provided, a unique name will be auto-generated.
    - **dry** (`bool`, optional): If set to `True`, does not write new run data to the disk.
            Only displays the aggregated metric on the screen. Useful for developing and
            debugging metrics.

    Returns the experiment metadata as `dict` object. See `Run` docs for the structure.

    Sample usage:
    ```python
    metric = MyNewMetric(...)

    rescore(run="tired-tiger-32", metric=metric)
    ```
    """
    started = datetime.now(tz=timezone.utc)

    score_accumulator = ScoreAccumulator()

    if name is None:
        name = _generate_name()
    if dry:
        run_count = 9999
    else:
        run_count = incr_run_count()
    runname = f"{name}-{run_count}"

    print(f"RedLite rescore {run} as {runname}:")
    print(f"\tmetric : {metric.name}")

    this_run = read_meta(redlite_data_dir(), run)

    with _storage(runname, dry) as storage:  # type: Storage
        for item in tqdm(read_data(redlite_data_dir(), run)):
            actual = item["actual"]
            score = metric(item["expected"], actual)
            storage.save(item, actual, score)
            score_accumulator(score)

        completed = datetime.now(tz=timezone.utc)

        this_run.update(
            dict(
                run=storage.name,
                started=started.isoformat(),
                completed=completed.isoformat(),
                duration=(completed - started).total_seconds(),
                score_summary=score_accumulator.summary,
                metric=metric.name,
            )
        )

        storage.save_meta(**this_run)

        print()
        print(f"\tScore summary: {format_score_summary(this_run['score_summary'])}")
        if dry:
            print("\tWARNING: dry run - results not saved!")
        print()
        return this_run


@contextlib.contextmanager
def _storage(runname: str, dry=False) -> Iterator[Storage]:
    if dry:
        yield DummyStorage()
        return

    base = os.path.join(redlite_data_dir(), runname)
    if os.path.isdir(base):
        raise RuntimeError(f"Unexpectedly, directory {base} exists!")
    os.makedirs(base, exist_ok=True)

    log.info(f"Started run {runname}")
    with JsonlStorage.open(runname, base) as s:
        yield s


def _generate_name():
    return duoname.duoname()


NamedModelProducer = Callable[[], NamedModel]
NamedMetricProducer = Callable[[], NamedMetric]

_worker_model: NamedModel | None = None
_worker_metric: NamedMetric | None = None


def _worker_init(model_producer: NamedModelProducer, metric_producer: NamedMetricProducer) -> None:
    global _worker_model
    global _worker_metric

    try:
        _worker_model = model_producer()
        _worker_metric = metric_producer()
    except Exception as e:
        raise RuntimeError(f"Worker initialization failed: {str(e)}")


def _worker_task(item) -> tuple[dict, str, float]:
    try:
        assert _worker_model is not None
        assert _worker_metric is not None
        actual = _worker_model(item["messages"])
        score = _worker_metric(item["expected"], actual)
        return item, actual, score
    except Exception as e:
        raise RuntimeError(f"Worker task failed: {str(e)}")


def parallel_run(
    *,
    model_producer: NamedModelProducer,
    dataset: NamedDataset,
    metric_producer: NamedMetricProducer,
    name: str | None = None,
    max_samples=0,
    num_workers: int = 64,
) -> Run:
    from multiprocessing import Pool

    """Runs experiment using parallel workers, using the given `model`, `dataset`, and `metric`.

    This function is similar to `run()`, but uses multiple parallel workers
    to process the dataset faster. Each worker creates its own instance of the model
    and metric by calling the provided `model_producer` and `metric_producer` functions.

    - **model_provider** (`NamedModelProvider`): a function taht returns model instance.
    - **dataset** (`NamedDataset`): Dataset.
    - **metric_provider** (`NamedMetricProvider`): a function taht returns metric instance.
    - **name** (`str`, optional): The name of the run. It will automatically get a
            numeric suffix to ensure global uniqueness.
            If not provided, a unique name will be auto-generated.
    - **max_samples** (`int`, optional): Allows one to limit the number of samples
            in the run. Value of zero (the default) means "run the whole dataset".
    - **num_workers** (`int`, optional): Number of parallel workers to use. Default is 64.

    Returns the run metadata as a `dict` object. See Run docs for the structure.

    Sample usage:
    ```python
    model_provider = lambda: MyModel(...)
    dataset = MyDataset(...)
    metric_provider = lambda: MyMetric(...)

    parallel_run(model_provider=model_provider, dataset=dataset, metric_provider=metric_provider, num_workers=128)
    ```
    """
    started = datetime.now(tz=timezone.utc)

    data_with_digest = DatasetRunningDigest(dataset, max_samples=max_samples)
    score_accumulator = ScoreAccumulator()

    if name is None:
        name = _generate_name()
    run_count = incr_run_count()
    runname = f"{name}-{run_count}"

    _worker_model = model_producer()
    _worker_metric = metric_producer()

    print(f"RedLite run {runname}:")
    print(f"\tmodel  : {_worker_model.name}")
    print(f"\tdataset: {dataset.name}")
    print(f"\tmetric : {_worker_metric.name}")

    with _storage(runname) as storage:  # type: Storage
        with Pool(num_workers, initializer=_worker_init, initargs=(model_producer, metric_producer)) as pool:
            for item, actual, score in tqdm(
                pool.imap_unordered(_worker_task, data_with_digest), total=len(data_with_digest)
            ):
                storage.save(item, actual, score)
                score_accumulator(score)

    completed = datetime.now(tz=timezone.utc)

    this_run: Run = dict(
        run=storage.name,
        dataset=dataset.name,
        split=dataset.split,
        dataset_labels=dataset.labels,
        data_digest=data_with_digest.hexdigest,
        metric=_worker_metric.name,
        model=_worker_model.name,
        max_samples=max_samples,
        started=started.isoformat(),
        completed=completed.isoformat(),
        duration=(completed - started).total_seconds(),
        score_summary=score_accumulator.summary,
    )

    storage.save_meta(**this_run)

    print()
    print(f"\tData digest: {this_run['data_digest']}")
    print(f"\tScore summary: {format_score_summary(this_run['score_summary'])}")
    print()
    return this_run
