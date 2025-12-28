"""Runner utility"""

import cProfile
import inspect
import io
import os
import pdb
import pstats
import re
import shutil
import signal
import sys
import time
from functools import singledispatch
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)

import cloudpickle as pickle
import dacite
from benedict import benedict
from jsonargparse import ArgumentParser, Namespace

from sukta import sem
from sukta.logging import LOG_LEVEL, Logger
from sukta.telemetry import Telemetry

T = TypeVar("T")


def cache(cache_dir, cache_name=None, cache_argnames=None):
    """provides a decorator to cache the results of any function.
    It pickles the return and stores it to reload if cached_path saved."""

    def decorator(func):
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        def wrapper(*args, **kwargs):
            cdir = Path(cache_dir)
            if cache_name is None:
                cname = func.__name__
            else:
                cname = cache_name
            if cache_argnames is not None:
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                all_args = bound_args.arguments
                cdir = cdir / "$".join(
                    f"{k}:{all_args.get(k, '')}" for k in cache_argnames
                )
            if not cname.endswith(".pkl"):
                cname += ".pkl"
            cdir.mkdir(parents=True, exist_ok=True)
            cache_path = cdir / cname
            if cache_path.exists():
                with open(cache_path, "rb") as f:
                    result = pickle.load(f)
                return result
            result = func(*args, **kwargs)
            with open(cache_path, "wb") as f:
                pickle.dump(result, f)
            return result

        return wrapper

    return decorator


# convert jsonargparse Namespace to dict recursively if needed
@singledispatch
def namespace2dict(namespace):
    return namespace


@namespace2dict.register(Namespace)
def _namespace2dict(namespace: Namespace) -> Dict:
    return {k: namespace2dict(v) for k, v in vars(namespace).items()}


class EnvConfig:
    """Utility class to configure common environment variables for different libraries."""

    @classmethod
    def jax(
        cls,
        preallocate: bool = False,
        mem_fraction: float = 0.75,
        alloc_on_demand: bool = False,
        device_id: int | Tuple[int, ...] | None = None,
    ):
        """configure common jax environment variables"""
        os.environ["XLA_PYTHON_CLIENT_MEM_FRACTION"] = f"{mem_fraction:.2f}"
        if alloc_on_demand:
            os.environ["XLA_PYTHON_CLIENT_ALLOCATOR"] = "platform"
        os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = str(preallocate).lower()
        xla_flags = os.environ.get("XLA_FLAGS", "")
        xla_flags += " --xla_gpu_triton_gemm_any=True"
        os.environ["XLA_FLAGS"] = xla_flags
        if device_id is not None:
            if isinstance(device_id, int):
                device_id = (device_id,)
            os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, device_id))
            if len(device_id) == 0:
                os.environ["JAX_PLATFORMS"] = "cpu"

    @classmethod
    def mujoco(
        cls, gl: Literal["egl", "osmesa", "glfw"] = "egl", gl_device_id: int = 0
    ):
        if "MUJOCO_GL" not in os.environ:
            os.environ["MUJOCO_GL"] = gl
            if gl == "egl":
                # warning: might not be supported on all cuda-driver versions
                os.environ["MUJOCO_EGL_DEVICE_ID"] = str(gl_device_id)


class Runner:
    EnvConfig = EnvConfig

    def __init__(
        self,
        root_dir: Path = Path("./runs"),
        experiment: Optional[str] = None,
        override: bool = False,
        overwrite: bool = False,
        run_params: Any = {},
        auto_sort: bool = True,
        log_name: str = "run",
        log_level: LOG_LEVEL = "INFO",
        exit_fns: Sequence[Callable] | None = None,
        telemetry: bool = True,
        debug: bool = False,
    ):
        exp_params = (experiment,) if experiment is not None else ()
        if isinstance(run_params, list) or isinstance(run_params, tuple):
            exp_params = (*exp_params, *run_params)
        else:
            exp_params = (*exp_params, run_params)
        self.exp_params = exp_params
        self.auto_sort = auto_sort
        self.run_dir = sem.ResultManager.create_default_path(
            root_dir, exp_params, auto_sort=auto_sort
        )
        if overwrite:
            # remove the run_dir if it exists
            if self.run_dir.exists():
                shutil.rmtree(self.run_dir)

        if not override:
            assert not self.run_dir.exists(), (
                f"Run directory {self.run_dir} already exists"
            )
        self.log_name = log_name
        self.log_level = log_level
        self._exit_fns = exit_fns or []

        self.log = Logger.getLogger(self.log_name, self.run_dir, level=self.log_level)

        repo = root_dir / experiment
        if telemetry:
            self.telemetry = Telemetry(
                repo=repo,
                experiment=experiment,
            )
            self.exit_hook(self.telemetry.close)
        else:
            self.telemetry = None
        self.debug = debug

    def get_experiment_dir(self, root_dir: Path):
        """
        utility method to allow specifying slower drives to store checkpoints etc., if needed
        """
        return sem.ResultManager.create_default_path(
            root_dir, self.exp_params, auto_sort=self.auto_sort
        )

    def __enter__(self):
        signal.signal(signal.SIGINT, self.handle_stop_signals)
        signal.signal(signal.SIGTERM, self.handle_stop_signals)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for fn in self._exit_fns:
            fn()
        if exc_type is not None:
            self.log.exception("An exception occurred")
            if self.debug:
                pdb.post_mortem(traceback)

    def handle_stop_signals(self, signum, frame):
        self.log.warning("Received signal %s, stopping...", signal.Signals(signum).name)
        sys.exit(1)

    @classmethod
    def default_parser(
        cls,
        parser: Optional[ArgumentParser] = None,
        run_dir: Path = "./runs",
        experiment: Optional[str] = None,
        log_name: str = "run",
        log_level: LOG_LEVEL = "INFO",
        debug: bool = False,
        override: bool = False,
        overwrite: bool = False,
        telemetry: bool = True,
    ) -> ArgumentParser:
        """Create a default argument parser for Runner, or add to an existing one."""
        parser = parser or ArgumentParser()
        parser.add_argument("--debug", type=bool, default=debug)
        parser.add_argument("--override", type=bool, default=override)
        parser.add_argument("--overwrite", type=bool, default=overwrite)
        parser.add_argument("--telemetry", type=bool, default=telemetry)
        parser.add_argument("--run_dir", type=Path, default=run_dir)
        parser.add_argument("--experiment", type=Optional[str], default=experiment)
        parser.add_argument("--log_name", type=str, default=log_name)
        parser.add_argument(
            "--desc",
            type=str,
            default=None,
            help="use to provide a memorable description for the experiment",
        )
        parser.add_argument(
            "--log_level",
            type=LOG_LEVEL,
            default=log_level,
        )
        return parser

    @classmethod
    def from_args(
        cls,
        args: Namespace,
        run_params: Any = {},
        exit_fns: Sequence[Callable] | Callable | None = None,
    ) -> "Runner":
        """Create a Runner instance from command line arguments."""
        if isinstance(exit_fns, Callable):
            exit_fns = [exit_fns]
        runner = cls(
            root_dir=args.run_dir,
            experiment=args.experiment,
            override=args.override,
            overwrite=args.overwrite,
            log_name=args.log_name,
            log_level=args.log_level,
            debug=args.debug,
            run_params=run_params,
            exit_fns=exit_fns,
            telemetry=args.telemetry,
        )
        return runner

    def save_args(self, parser: ArgumentParser, args: Namespace):
        """Save the command line arguments to a yaml file in the run directory."""
        with open(self.run_dir / "args.yaml", "w", encoding="utf-8") as f:
            f.write(parser.dump(args))
        if args.desc is not None:
            with open(self.run_dir / "desc.txt", "w", encoding="utf-8") as f:
                f.write(args.desc)

    def save_dict_as_yaml(self, data_name: str, data: Dict):
        """Save a dictionary as a yaml file in the run directory."""
        assert "." not in data_name, ".yaml is automatically appended"
        assert data_name != "args", "args.yaml is reserved for storing run arguments"
        with open(self.run_dir / f"{data_name}.yaml", "w", encoding="utf-8") as f:
            f.write(benedict(data).to_yaml())

    def exit_hook(self, fn: Callable):
        """Register a function to be called when the Runner exits."""
        self._exit_fns.append(fn)

    @classmethod
    def load_args(cls, path) -> Dict:
        """Load command line arguments from a yaml file."""
        return benedict.from_yaml(path)

    @classmethod
    def dataclass_from_dict(
        cls,
        data_class: Type[T],
        data: dacite.data.Data,
        config: dacite.Config | None = None,
    ) -> T:
        if isinstance(data, Namespace):
            data = namespace2dict(data)
        return dacite.from_dict(data_class, data, config)

    def set_trace(self):
        """Set a breakpoint using pdb."""
        pdb.set_trace()

    @staticmethod
    def parse_cstr(cstr):
        """Parse configuration-string (e.g. serialized hyperparameters) to dictionary."""
        replaces, restores = {}, {}
        for c in ["_", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            sp_chr = f"||{chr(ord('A') + ord(c) - ord('0'))}||"
            replaces[f"\\{c}"] = sp_chr
            restores[sp_chr] = c

        def replace(s: str) -> str:
            for k, v in replaces.items():
                s = s.replace(k, v)
            return s

        def restore(s: str) -> str:
            for k, v in restores.items():
                s = s.replace(k, v)
            return s

        cstr = replace(cstr)
        chunks = cstr.split("_")  # simple underscore to split chunks
        d = {}
        for chunk in chunks:
            if "$" in chunk:
                k, v = chunk.split("$", 1)
                k, v = restore(k), restore(v)
                d[k] = v
            else:
                match = re.match(r"([a-zA-Z\|]+)(.*)", chunk)
                if match:
                    k, v = match.groups()
                    k, v = restore(k), restore(v)
                    try:
                        if "." in v or "e" in v.lower():
                            d[k] = float(v)
                        else:
                            d[k] = int(v)
                    except (ValueError, TypeError):
                        # if conversion fails, test if it's a flag parameter
                        if len(v) == 0:
                            d[k] = True  # flag parameter
                        else:
                            d[k] = v  # keep as string
        return d

    @staticmethod
    def serialize_cstr(cdict: Dict) -> str:
        """Serialize a dictionary to a configuration-string."""
        cstr = ""
        for k, v in cdict.items():
            k = str(k).replace("_", r"\_")
            if isinstance(v, bool) and v is True:
                cstr += f"_{k}"
            else:
                if isinstance(v, float):
                    v = "{:e}".format(v)
                    v = re.sub(
                        r"([eE][+-]?)0+", r"\1", v
                    )  # remove leading zeros in exponent
                    v = re.sub(r"\.0+([eE])", r"\1", v)  # remove .0 in float
                v = str(v).replace("_", r"\_")
                cstr += f"_{k}${v}"
        if cstr.startswith("_"):
            cstr = cstr[1:]
        return cstr


class Profile:
    """Context manager that profiles a section of code"""

    def __init__(self, name: str, sort_by="cumulative"):
        self.name = name

        self.profiler = cProfile.Profile()
        self.sort_by = sort_by
        self.start_time = None

    def __enter__(self):
        self.profiler.enable()
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        total_time = time.time() - self.start_time
        self.profiler.disable()
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats(self.sort_by)
        ps.print_stats()
        print(f"Profile [{self.name}]:\n{s.getvalue()}")
        print(f"Profile [{self.name}] took {total_time:.3f} seconds")


class Timer:
    """Context manager that times a section of code"""

    def __init__(self, name: str = "", logger: Optional[Logger] = None):
        self.name = name
        self.logger = logger
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        total_time = time.time() - self.start_time
        total_time = Logger.num2pstr(total_time, ".3f")
        name = self.name or "root"
        msg = "[{name}] took {total_time}s"
        if self.logger is not None:
            self.logger.info(msg, name=name, total_time=total_time)
        else:
            print(msg.format(name=name, total_time=total_time))
