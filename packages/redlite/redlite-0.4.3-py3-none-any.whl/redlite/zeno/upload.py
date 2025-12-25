from .._util import redlite_data_dir, read_runs, read_data
from .._core import MissingDependencyError
import collections
import os

__all__ = ["upload"]


try:
    from zeno_client import ZenoClient, ZenoMetric
    import pandas as pd
except ImportError as err:
    raise MissingDependencyError("Please install zeno_client library") from err


Task = collections.namedtuple("Task", ["dataset", "split", "data_digest", "metric"])


def read_tasks(root: str):
    """Reads all runs and builds task-level aggregation."""
    by_task = collections.defaultdict(list)

    def run_task(run):
        return Task(run["dataset"], run["split"], run["data_digest"], run["metric"])

    for run in read_runs(root):
        by_task[run_task(run)].append(run)

    for task, runs in by_task.items():
        # group by model here
        by_model = collections.defaultdict(list)
        for run in runs:
            by_model[run["model"]].append(run)

        # take only the last model's run into account
        latest_runs = []
        for model_runs in by_model.values():
            model_runs = sorted(model_runs, key=lambda x: x["completed"])
            latest_runs.append(model_runs[-1])

        yield task, latest_runs


def upload(*, api_key: str | None = None, zeno_project: str = "redlite") -> None:
    """Uploads all runs to Zeno."""
    base_dir = redlite_data_dir()
    tasks = dict(read_tasks(base_dir))
    if len(tasks) == 0:
        print("No tasks found. Please run some benchmarks, then upload")

    if api_key is None:
        api_key = os.environ.get("ZENO_API_KEY")
    if api_key is None:
        raise RuntimeError("ZENO_API_KEY not found")

    # Initialize a client with our API key.
    client = ZenoClient(api_key=api_key)

    run_by_model = {}
    all_models = set()
    for task, runs in tasks.items():
        for run in runs:
            run_by_model[task, run["model"]] = run["run"]
            all_models.add(run["model"])

    project = client.create_project(
        name=zeno_project,
        view="chatbot",
        metrics=[
            ZenoMetric(name="score", type="mean", columns=["score"]),
        ],
    )

    datasets = []
    null_datasets = {}
    for task_id, (task, runs) in enumerate(tasks.items()):
        run_name = runs[0]["run"]  # all runs contain the same data,
        # does not matter which one we send out
        df = pd.DataFrame(read_data(base_dir, run_name)).drop("score", axis=1).drop("actual", axis=1)
        df["gid"] = f"{task_id}-" + df["id"]
        df["task_id"] = task_id
        df["dataset"] = task.dataset
        df["split"] = task.split
        df["metric"] = task.metric
        df["data_digest"] = task.data_digest
        datasets.append(df)

        null_df = df.copy(deep=True)
        null_df = null_df[["id", "gid"]]
        null_df["actual"] = "**not run**"
        null_df["score"] = "**not run**"
        null_datasets[task] = null_df

    df = pd.concat(datasets)
    print("Uploading tasks")
    project.upload_dataset(df, id_column="gid", data_column="messages", label_column="expected")

    for model in sorted(all_models):
        sys = []
        for task_id, (task, runs) in enumerate(tasks.items()):
            run_name = run_by_model.get((task, model))
            if run_name is None:  # no runs for this combination of model and task
                print(
                    f"Warning: no runs for model {model} on task {task}. "
                    + 'Fabricating "**not run**" response and score of 0.0'
                )
                sys.append(null_df[task])
            else:
                df_sys = pd.DataFrame(read_data(base_dir, run_name))
                df_sys = df_sys[["id", "actual", "score"]]
                df_sys["gid"] = f"{task_id}-" + df_sys["id"]
                sys.append(df_sys)

        df_sys = pd.concat(sys)
        print(f"Uploading model {model}")
        project.upload_system(df_sys, name=model.replace("/", "__"), id_column="gid", output_column="actual")

    print(
        f"\nUploaded {len(tasks)} tasks and {len(all_models)} models to Zeno. "
        + "Go to https://hub.zenoml.com/ to view your data."
    )
