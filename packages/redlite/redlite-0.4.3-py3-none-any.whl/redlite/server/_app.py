import os
import shutil
import json
from aiohttp import web
import aiohttp_cors
from urllib.parse import unquote, quote
from redlite.server import res
from redlite._util import redlite_data_dir
from .._util import read_data, read_meta, read_runs
from .._core import Run


class RunReader:
    """Defines how web service reads runs. Can be mocked for testing."""

    def __init__(self, base: str):
        self.base = base

    async def runs(self) -> list[Run]:
        """Reads all runs

        Returns:
            list: A list of runs found
        """
        return list(read_runs(self.base))

    async def data(self, name: str) -> list[dict]:
        """Reads data of the run.

        Args:
            name (str): Name of the run.

        Returns:
            list: A list of all datapoints for this run.
        """
        return list(read_data(self.base, name))

    async def meta(self, name: str) -> Run:
        """Reads metadata of the run.

        Args:
            name (str): Name of the run.

        Returns:
            dict: A dictionary containing run metadata.
        """
        return read_meta(self.base, name)


class Service:
    def __init__(self, reader: RunReader):
        self.reader = reader

    async def runs(self, request):
        runs = await self.reader.runs()
        return web.json_response(runs)

    async def data(self, request):
        name = request.match_info["name"]
        data = await self.reader.data(unquote(name))
        return web.json_response(data)

    async def meta(self, request):
        name = request.match_info["name"]
        meta = await self.reader.meta(unquote(name))
        return web.json_response(meta)


def get_app(reader: RunReader, *, skin="default"):

    async def index(_):
        return web.FileResponse(res(skin, "index.html"))

    @web.middleware
    async def spa_middleware(request, handler):
        try:
            return await handler(request)
        except web.HTTPException as ex:
            if ex.status == 404:
                return await index(request)
            raise

    app = web.Application()
    service = Service(reader)
    app.add_routes(
        [
            web.get("/api/runs.json", service.runs),
            web.get("/api/runs/{name}/meta.json", service.meta),
            web.get("/api/runs/{name}/data.json", service.data),
            web.get("/", index),
            web.static("/", res(skin)),
            web.get("", index),
        ]
    )

    cors = aiohttp_cors.setup(
        app,
        defaults={"*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")},
    )
    for route in list(app.router.routes()):
        cors.add(route)

    app.middlewares.append(spa_middleware)

    return app


def main(port: int = 8000, skin: str = "default"):
    base = redlite_data_dir()

    app = get_app(RunReader(base), skin=skin)

    web.run_app(app, port=port)


async def freeze(outdir: str, skin: str = "default"):

    def save(path, *, data):
        fname = outdir + "/" + path
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        with open(fname, "wb") as f:
            f.write(json.dumps(data).encode("utf-8"))

    base = redlite_data_dir()

    reader = RunReader(base)

    runs = await reader.runs()
    save("/api/runs.json", data=runs)
    for run in runs:
        name = quote(run["run"])
        meta = await reader.meta(run["run"])
        data = await reader.data(run["run"])
        save(f"/api/runs/{name}/meta.json", data=meta)
        save(f"/api/runs/{name}/data.json", data=data)

    skin_root = res(skin)
    for root, _, files in os.walk(skin_root):
        for fname in files:
            fname = os.path.join(root, fname)
            relname = os.path.relpath(fname, skin_root)
            target = os.path.join(outdir, relname)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(fname, target)


if __name__ == "__main__":
    main()
