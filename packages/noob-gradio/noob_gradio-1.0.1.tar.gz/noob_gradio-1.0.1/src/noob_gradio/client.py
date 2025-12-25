import json
import logging
import os
import uuid
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Literal

import aiofiles
import aiohttp

DEFAULT_TEMP_DIR = os.getenv("GRADIO_TEMP_DIR") or str(Path(gettempdir()) / "gradio")
logger = logging.getLogger(__name__)


class AppError(RuntimeError):
    pass


class NoSessionError(AppError):
    def __init__(self):
        super().__init__("HTTP session is not initialized, use 'async with' or 'connect()'")


def is_http_url_like(s: str):
    return s.startswith(("http://", "https://"))


def handle_file(filepath_or_url: str | Path):
    """Prepare a file input for Gradio API calls."""
    s = str(filepath_or_url)
    data = {"path": s, "meta": {"_type": "gradio.FileData"}}
    if is_http_url_like(s):
        return {**data, "orig_name": s.split("/")[-1], "url": s}
    elif Path(s).exists():
        return {**data, "orig_name": Path(s).name}
    else:
        raise ValueError(f"File {s} does not exist on local filesystem and is not a valid URL.")


class Client:
    """The client for interacting with a Gradio app."""
    def __init__(
        self,
        src: str | None = None,
        hf_token: str | None = None,
        headers: dict[str, str] | None = None,
        download_files: str | Path | Literal[False] = DEFAULT_TEMP_DIR,
        session: aiohttp.ClientSession | None = None,
    ):
        # Support both full URLs and repo names like "black-forest-labs/FLUX.1-schnell"
        self.base = self._resolve_base(src) if src else None
        self._provide_session = session is None
        self.session = session
        self.hf_token = hf_token
        self._space_cache = {}
        self.headers = headers or session.headers if session else {"User-Agent": "noob_gradio/1.0"}
        if self.hf_token:
            self.headers["x-hf-authorization"] = f"Bearer {self.hf_token}"
        self.download_dir = (
            Path(download_files)
            if isinstance(download_files, (str, Path))
            else None
        )
        if self.download_dir:
            self.download_dir.mkdir(parents=True, exist_ok=True)
            if not self.download_dir.is_dir():
                raise ValueError(f"Path: {self.download_dir} is not a directory.")

    def _resolve_base(self, src: str):
        if is_http_url_like(src):
            return src.rstrip("/")
        else:
            return (
                "https://"
                + src.lower().replace("/", "-").replace(".", "-")
                + ".hf.space"
            )

    async def connect(self):
        if self._provide_session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self._provide_session and self.session:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def _get_json(self, url: str) -> dict:
        if self.session is None:
            raise NoSessionError()
        async with self.session.get(url, headers=self.headers) as resp:
            if resp.status != 200:
                raise AppError(f"Failed to get JSON from {url}: {resp.status} {await resp.text()}")
            return await resp.json()

    async def _download_file(self, url: str):
        if not self.download_dir:
            return url
        if not self.session:
            raise NoSessionError()
        temp_dir = self.download_dir / uuid.uuid4().hex
        temp_dir.mkdir(exist_ok=True, parents=True)
        out_path = temp_dir / Path(url).name
        logger.debug(f"Downloading file from {url} to {out_path}")
        async with self.session.get(url, headers=self.headers) as r:
            if r.status != 200:
                raise AppError(f"Failed to download file from {url}: {r.status} {await r.text()}")
            data = await r.read()
        async with aiofiles.open(out_path, "wb") as f:
            await f.write(data)
        return str(out_path)

    async def _resolve_fn_index(self, api_name: str, base: str) -> int | None:
        # important to normalize api_name
        api_name = api_name.removeprefix("/")
        cache = self._space_cache.setdefault(base, {})
        if "fn_index_map" not in cache:
            cfg = await self._get_json(f"{base}/config")
            cache["fn_index_map"] = {
                dep["api_name"]: dep["id"]
                for dep in cfg.get("dependencies", [])
                if dep.get("api_name")
            }
            cache["param_constraints"] = {
                comp["props"]["label"]: {
                    "min": props.get("minimum"),
                    "max": props.get("maximum"),
                    "step": props.get("step"),
                }
                for comp in cfg.get("components", [])
                if (props := comp.get("props")) and "label" in props
            }
        return cache["fn_index_map"].get(api_name)

    async def _load_api_info(self, base: str) -> dict:
        cache = self._space_cache.setdefault(base, {})
        if "api_info" not in cache:
            cache["api_info"] = await self._get_json(f"{base}/gradio_api/info?serialize=False")
        return cache["api_info"]

    def _render_endpoints_info(
        self,
        name_or_index: str | int,
        endpoints_info: dict[str, list],
    ) -> str:
        parameter_info = endpoints_info["parameters"]
        parameter_names = [
            p.get("parameter_name") or p["label"] for p in parameter_info
        ]
        rendered_parameters = ", ".join(parameter_names)
        if rendered_parameters:
            rendered_parameters = rendered_parameters + ", "
        return_values = [p["label"] for p in endpoints_info["returns"]]
        rendered_return_values = ", ".join(return_values)
        if len(return_values) > 1:
            rendered_return_values = f"({rendered_return_values})"

        if isinstance(name_or_index, str):
            final_param = f'api_name="{name_or_index}"'
        elif isinstance(name_or_index, int):
            final_param = f"fn_index={name_or_index}"

        human_info = f"\n - predict({rendered_parameters}{final_param}) -> {rendered_return_values}\n"
        human_info += "    Parameters:\n"
        if parameter_info:
            for info in parameter_info:
                desc = (
                    f" ({info['python_type']['description']})"
                    if info["python_type"].get("description")
                    else ""
                )
                default_value = info.get("parameter_default")
                default_info = (
                    "(required)"
                    if not info.get("parameter_has_default", False)
                    else f"(not required, defaults to: {default_value})"
                )
                type_ = info["python_type"]["type"]
                if info.get("parameter_has_default", False) and default_value is None:
                    type_ += " | None"
                human_info += f"     - [{info['component']}] {info.get('parameter_name') or info['label']}: {type_} {default_info} {desc} \n"
        else:
            human_info += "     - None\n"
        human_info += "    Returns:\n"
        if endpoints_info["returns"]:
            for info in endpoints_info["returns"]:
                desc = (
                    f" ({info['python_type']['description']})"
                    if info["python_type"].get("description")
                    else ""
                )
                type_ = info["python_type"]["type"]
                human_info += f"     - [{info['component']}] {info['label']}: {type_}{desc} \n"
        else:
            human_info += "     - None\n"
        return human_info

    async def view_api(
        self,
        src: str | None = None,
        all_endpoints: bool | None = None,
        print_info: bool = True,
        return_format: Literal["dict", "str"] | None = None,
    ) -> dict | str | None:
        """View the API information of the Gradio app."""
        base = self._resolve_base(src) if src else self.base
        if base is None:
            raise ValueError("Client source URL is not set.")
        api_info = await self._load_api_info(base)
        num_named_endpoints = len(api_info["named_endpoints"])
        num_unnamed_endpoints = len(api_info["unnamed_endpoints"])
        if num_named_endpoints == 0 and all_endpoints is None:
            all_endpoints = True

        human_info = "Client.predict() Usage Info\n---------------------------\n"
        human_info += f"Named API endpoints: {num_named_endpoints}\n"

        for api_name, endpoint_info in api_info["named_endpoints"].items():
            human_info += self._render_endpoints_info(api_name, endpoint_info)

        if all_endpoints:
            human_info += f"\nUnnamed API endpoints: {num_unnamed_endpoints}\n"
            for fn_index, endpoint_info in api_info["unnamed_endpoints"].items():
                # When loading from json, the fn_indices are read as strings
                # because json keys can only be strings
                human_info += self._render_endpoints_info(int(fn_index), endpoint_info)
        elif num_unnamed_endpoints > 0:
            human_info += f"\nUnnamed API endpoints: {num_unnamed_endpoints}, to view, run Client.view_api(all_endpoints=True)\n"

        if print_info:
            print(human_info)
        if return_format == "str":
            return human_info
        elif return_format == "dict":
            return api_info

    async def _upload_local_file(self, filedict: dict, base: str):
        path = filedict.get("path")
        if not path:
            raise ValueError("filedict has no 'path' to upload")
        name = filedict.get("orig_name") or Path(path).name
        if self.session is None:
            raise NoSessionError()
        form = aiohttp.FormData()
        # field name must be 'files'
        form.add_field("files", await aiofiles.open(path, "rb"), filename=name, content_type="application/octet-stream")
        upload_url = f"{base}/gradio_api/upload"
        async with self.session.post(upload_url, headers=self.headers, data=form) as resp:
            result = await resp.json()
            if resp.status != 200:
                raise AppError(f"Upload failed {resp.status}: {result}")
        uploaded_path = result[0]
        logger.debug(f"Uploaded file to {uploaded_path}")
        return {"path": uploaded_path, "orig_name": name, "meta": {"_type": "gradio.FileData"}}

    def _validate_number(self, name: str, val: float, label: str, base: str):
        """Check if input is within expected min/max/step constraints."""
        c = self._space_cache.get(base, {}).get("param_constraints", {}).get(label)
        if not c:
            return
        min_v, max_v = c.get("min"), c.get("max")
        if min_v is not None and val < min_v:
            raise ValueError(f"Parameter '{name}' ({label}) is below minimum ({val} < {min_v})")
        if max_v is not None and val > max_v:
            raise ValueError(f"Parameter '{name}' ({label}) exceeds maximum ({val} > {max_v})")
        step_v = c.get("step")
        if step_v and isinstance(step_v, (int, float)) and step_v > 0:
            # step validation only for finite steps
            delta = abs((val - min_v) % step_v) if min_v is not None else val % step_v
            if delta not in (0, step_v):
                raise ValueError(f"Parameter '{name}' ({label}) is not aligned with step {step_v}")

    def _matches_type(self, value: Any, expected_pytype: Any) -> bool:
        t = expected_pytype.get("type") if isinstance(expected_pytype, dict) else str(expected_pytype)
        if not t:
            return True
        t = t.lower().split("(")[0]
        type_map = {
            "str": str,
            "int": int,
            "float": (int, float),
            "bool": bool,
            "list": (list, tuple),
            "sequence": (list, tuple),
            "tuple": (list, tuple),
            "dict": dict,
            "mapping": dict,
        }
        pytype = type_map.get(t)
        if pytype:
            return isinstance(value, pytype) and not (t in ("int", "float") and isinstance(value, bool))
        return type(value).__name__.lower() == t

    async def predict(
        self,
        *args,
        api_name: str,
        fn_index: int | None = None,
        src: str | None = None,
        headers: dict | None = None,
        **kwargs: Any,
    ) -> list[Any]:
        """Call the Gradio app's predict function with given inputs. Must be awaited to get results. Now supports src override per call."""
        if self.session is None:
            raise NoSessionError()
        if headers:
            # merge headers
            self.headers = {**self.headers, **headers}
        base = self._resolve_base(src) if src else self.base
        if not base:
            raise ValueError("Source URL or repo name must be provided in Client or predict() call.")
        api_info = await self._load_api_info(base)
        if fn_index is None:
            fn_index = await self._resolve_fn_index(api_name, base)
        if fn_index is None:
            raise AppError(f"Could not resolve fn_index for {api_name}")
        # Get expected parameter order
        params_list = []
        named = api_info.get("named_endpoints", {}) or {}
        if api_name in named:
            params_list = named[api_name].get("parameters", [])
        else:
            # backward-compatible: some spaces expose info keyed by fn_index with "inputs"
            params_entry = api_info.get(str(fn_index)) or {}
            params_list = params_entry.get("inputs", [])
        # collect canonical parameter names (parameter_name for new API, name for old)
        param_names = [p.get("parameter_name") or p.get("name") or f"arg{i}" for i, p in enumerate(params_list)]
        logger.debug(f"Expected parameters for {api_name} (fn_index={fn_index}): {param_names}")
        # Check for mixing args and kwargs for same parameter
        if args and kwargs:
            overlap = set(param_names[:len(args)]) & set(kwargs.keys())
            if overlap:
                raise TypeError(f"Got multiple values for parameters: {sorted(overlap)}")
        # raise on any unexpected kwargs
        unexpected = set(kwargs.keys()) - set(param_names)
        if unexpected:
            raise TypeError(f"Unexpected parameters for {api_name}: {sorted(unexpected)}")
        input_data = []
        args_iter = iter(args)
        for p in params_list:
            name = p.get("parameter_name") or p.get("name")
            has_default = p.get("parameter_has_default", True)
            default = p.get("parameter_default", None)
            expected = p.get("python_type") or p.get("type")
            try:
                # Try to get from positional args first
                val = next(args_iter)
            except StopIteration:
                # Fall back to kwargs or default
                if name in kwargs:
                    val = kwargs[name]
                else:
                    if not has_default:
                        raise ValueError(f"Missing required parameter: {name}") from None
                    input_data.append(default)
                    continue
            # Validate type
            if not self._matches_type(val, expected):
                expected_t = expected.get("type") if isinstance(expected, dict) else expected
                raise TypeError(
                    f"Parameter '{name}' expects type '{expected_t}' but got '{type(val).__name__}'",
                )
            # Validate numbers
            if isinstance(val, (int, float)):
                label = p.get("label")
                self._validate_number(name, val, label, base)
            # Handle file uploads
            if isinstance(val, dict) and val.get("meta", {}).get("_type") == "gradio.FileData":
                if "url" not in val:
                    val = await self._upload_local_file(val, base)
            input_data.append(val)
        logger.debug(f"Resolved input data: {input_data}")
        session_hash = uuid.uuid4().hex
        payload = {"fn_index": fn_index, "session_hash": session_hash, "data": input_data}
        join_url = f"{base}/gradio_api/queue/join"
        stream_url = f"{base}/gradio_api/queue/data?session_hash={session_hash}"
        async with self.session.post(join_url, json=payload) as resp:
            if resp.status != 200:
                raise AppError(f"Queue join failed: {resp.status} {await resp.text()}")
        data = {}
        async with self.session.get(stream_url, headers=self.headers) as resp:
            async for raw in resp.content:
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line.startswith("data:"):
                    continue
                try:
                    data: dict = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    logger.warning(f"{line} is not json")
                    continue
                msg = data.get("msg")
                if msg == "estimation":
                    logger.debug(f"Estimated wait: {data.get('rank_eta')}")
                elif msg == "process_starts":
                    logger.debug("Processing started...")
                elif msg == "process_completed":
                    success = data.get("success")
                    output = data.get("output", {})
                    if not success:
                        error_info = output.get("error")
                        if error_info and error_info != "null":
                            logger.debug(f"Processing failed: {error_info}")
                            raise AppError(error_info)
                        logger.debug(f"Processing failed: {data}")
                        raise AppError("Something went wrong in gradio app.")
                    result = output.get("data", [])
                    # download any files if download_files is not False
                    if self.download_dir:
                        for i, item in enumerate(result):
                            if isinstance(item, dict) and "url" in item:
                                local_path = await self._download_file(item["url"])
                                result[i] = local_path
                    logger.info("Processing completed successfully.")
                    return result
                elif msg == "close_stream":
                    raise AppError("Stream closed before completion.")
        raise AppError(f"No process_completed message received. Last data: {data}")
