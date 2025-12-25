from ._util import redlite_data_dir, read_runs, read_data


def stats(model: str, dataset: str):
    data_dir = redlite_data_dir()

    if model is None or dataset is None:
        print_available(data_dir)
        return -1

    runs = [run for run in read_runs(data_dir) if run["model"] == model and run["dataset"] == dataset]
    if len(runs) < 2:
        print(f"Found {len(runs)} runs for model={model} dataset={dataset}. Need 2 or more runs to compute statistics.")
        print()
        print_available(data_dir)
        return -1

    N = len(runs)
    datapoints: dict[tuple[str, str], list[float]] = {}
    for run in runs:
        name = run["run"]
        for datum in read_data(data_dir, name):
            id_ = datum["id"]
            datapoints.setdefault(id_, []).append(datum["score"])

    datapoints = {k: v for k, v in datapoints.items() if len(v) == N}
    if len(datapoints) == 0:
        print(f"No datapoints with {N} scores found")
        return -1

    # mean and stddev/stderr
    scores: list[list[float]] = [list() for _ in range(N)]
    for v in datapoints.values():
        for i in range(N):
            scores[i].append(v[i])
    run_averages = [sum(s) / len(s) for s in scores]
    mean_score = sum(run_averages) / N
    stddev_across_runs = (sum((x - mean_score) ** 2 for x in run_averages) / (N - 1)) ** 0.5

    # majority vote (assumes scores are 0/1)
    majority_votes = []
    for v in datapoints.values():
        c = sum(v)
        majority_votes.append(1 if c > N / 2 else 0)
    mean_score_majority = sum(majority_votes) / len(majority_votes)

    # pass@N
    pass_at_N = sum(1 for v in datapoints.values() if sum(v) > 0) / len(datapoints)

    print(f"Model: {model}")
    print(f"Dataset: {dataset}")
    print(f"Num runs: {N}")
    print(f"Score: {mean_score:.3f}±{stddev_across_runs:.3f}")
    print(f"Majority vote score: {mean_score_majority:.3f}")
    print(f"Pass@{N}: {pass_at_N:.3f}")
    return 0


def print_available(data_dir):
    multi_runs = {}

    for run in read_runs(data_dir):
        model = run["model"]
        dataset = run["dataset"]
        multi_runs.setdefault((model, dataset), []).append(run)

    multi_runs = {k: v for k, v in multi_runs.items() if len(v) > 1}
    models = set(x[0] for x in multi_runs.keys())
    datasets = set(x[1] for x in multi_runs.keys())

    if len(models) == 0 or len(datasets) == 0:
        print("No model+dataset with multiple runs found")
        return

    print("Available models:")
    for model in sorted(models):
        print(f"  {model}")
    print()

    print("Available datasets:")
    for dataset in sorted(datasets):
        print(f"  {dataset}")
    print()

    print("Model+dataset pairs with multiple runs:")
    for (model, dataset), runs in sorted(multi_runs.items()):
        print(f"  {model} on {dataset}: {len(runs)} runs")
    print()
