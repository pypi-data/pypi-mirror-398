import subprocess
from pathlib import Path
from typing import Union, Optional, Any, Mapping, Sequence
from pydantic import BaseModel
import requests
from fastapi import Request, FastAPI, Response
import traceback
import json
import sys

PathLike = Union[str, Path]


def _to_flag_name(name: str) -> str:
    return "--" + name.replace("_", "-")


def _as_path_str(root_dir: Optional[PathLike], value: Any) -> str:
    if isinstance(value, Path):
        p = value
    elif isinstance(value, str) and ("/" in value or value.endswith((".gguf", ".safetensors", ".bin"))):
        p = Path(value)
    else:
        return str(value)

    if root_dir is None:
        return str(p)

    root = Path(root_dir)
    return str(p if p.is_absolute() else (root / p))


def _params_to_argv(root_dir: Optional[PathLike], params: Mapping[str, Any]) -> list[str]:
    argv: list[str] = []
    for key, value in params.items():
        flag = _to_flag_name(key)

        if value is True:
            argv.append(flag)
        elif value is False or value is None:
            continue
        elif isinstance(value, (list, tuple)):
            for item in value:
                argv += [flag, _as_path_str(root_dir, item)]
        else:
            argv += [flag, _as_path_str(root_dir, value)]
    return argv

def diffusion_handler(
        *,
        diffusion_model: PathLike | None = None,
        llm: PathLike | None = None,
        vae: PathLike | None = None,
        extra_args: Optional[Mapping[str, Any]] = None,
        raw_args: Sequence[str] = (),
        popen_kwargs: Optional[Mapping[str, Any]] = None,
        **params: Any,
) -> None:
    bin_path = "/workspace/stable-diffusion.cpp/build/bin/sd-server"
    root_dir = "/app"
    argv: list[str] = [str(bin_path)]

    if diffusion_model is not None:
        argv += ["--diffusion-model", _as_path_str(root_dir, diffusion_model)]
    if llm is not None:
        argv += ["--llm", _as_path_str(root_dir, llm)]
    if vae is not None:
        argv += ["--vae", _as_path_str(root_dir, vae)]

    # main params (kwargs) -> CLI
    argv += _params_to_argv(root_dir, params)

    # extra named args -> CLI
    if extra_args:
        argv += _params_to_argv(root_dir, extra_args)

    # exact raw passthrough (optional)
    argv += list(raw_args)

    defaults: dict[str, Any] = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    if popen_kwargs:
        defaults.update(dict(popen_kwargs))

    process = subprocess.Popen(argv, **defaults)
    for line in process.stdout:
        print(line, end='')
        if "listening on" in line:
            print("Model is loaded.")
            break

    class InferenceRequest(BaseModel):
        prompt: str
        negative_prompt: Optional[str] = ""
        width: Optional[int] = 1024
        height: Optional[int] = 1024
        guidance_scale: Optional[float] = 0.0   # "CFG"
        seed: Optional[int] = None


    def to_sd_cpp_payload(req):
        extra = {
            "negative_prompt": req.negative_prompt or "",
            "cfg_scale": req.guidance_scale or 0.0,
        }
        if req.seed is not None:
            extra["seed"] = req.seed
        prompt = (
            f"{req.prompt} "
            f"<sd_cpp_extra_args>{json.dumps(extra)}</sd_cpp_extra_args>"
        )
        return {
            "prompt": prompt,
            "size": f"{req.width}x{req.height}",
        }

    app = FastAPI()

    @app.get("/")
    async def root():
        # healthcheck localhost:8080 via requests
        try:
            response = requests.get("http://localhost:1234")

            if process.poll():
                exit(1)

            if response.status_code == 200:
                return "OK"
            else:
                response.status_code = 500
                return response.text()
        except requests.exceptions.RequestException as e:
            response.status_code = 500
            return response.text()

    @app.post("/infer")
    async def infer(request: InferenceRequest):
        response = requests.post("http://localhost:1234/v1/images/generations", json=to_sd_cpp_payload(request))
        img_str = response.json()['data'][0]['b64_json']
        return {"response": img_str}

    @app.exception_handler(Exception)
    async def debug_exception_handler(request: Request, exc: Exception):
        exc_type, exc_value, exc_tb = sys.exc_info()
        formatted_traceback = "".join(
            traceback.format_exception(exc_type, exc_value, exc_tb)
        )
        return Response(content=formatted_traceback, media_type="text/plain", status_code=500)

