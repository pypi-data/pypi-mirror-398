from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
import glob
import os
import subprocess

from .channel import Channel
from .config import Config, Resource, wrap_container, wrap_slurm
from .inout import local_log_paths, safe_job_name, write_cmd_log

class Step:
    """
    Declarative pipeline step with automatic sharding and channel wiring.
    """

    INPUTS: Dict[str, Any] = {}
    OUTPUTS: Dict[str, Optional[str]] = {}
    RESOURCE: Resource = Resource()
    CONFIG: Config = Config()
    PARAMS: Dict[str, Any] = {}

    def __init__(self, **overrides):
        # allow per-instance resource/config overrides
        self.resource = overrides.pop("resource", self.RESOURCE)
        self.config = overrides.pop("config", self.CONFIG)
        self.params: Dict[str, Any] = {**self.PARAMS, **overrides}

        # materialize channels with default values
        self._in_ch: Dict[str, Channel] = {k: Channel(k, v) for k, v in self.INPUTS.items()}
        self._out_ch: Dict[str, Channel] = {
            k: Channel(k, None, producers=[self]) for k in self.OUTPUTS.keys()
        }

    def __call__(self, *args, **kwargs) -> "Step":
        """
        Bind positional/keyword inputs to channels. Allows wiring via Channel objects.
        """
        bindings = self._bind_inputs(args, kwargs)
        for name, src in bindings.items():
            ch = self._in_ch[name]
            if isinstance(src, Channel):
                self._in_ch[name] = src
                src.consumers.append(self)
            else:
                ch.val = src
        return self

    def inputs(self) -> Dict[str, Any]:
        return {k: ch.val for k, ch in self._in_ch.items()}

    def outputs(self) -> Dict[str, Channel]:
        return self._out_ch

    def script(self) -> str:
        """Return the shell command for this step."""
        raise NotImplementedError

    # ------------------ Execution ------------------

    def execute(self):
        in_vals = self.inputs()
        shards = self._make_shards(in_vals)

        if len(shards) == 1:
            self._run_single(shards[0])
            return

        self._run_sharded(shards)

    def _make_shards(self, in_vals: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Sharding policy:
          * No list inputs -> single shard
          * All lists -> zip (aligned lengths)
          * Mix of lists/scalars -> broadcast scalars to max list length
        """
        list_keys = [k for k, v in in_vals.items() if isinstance(v, list)]
        if not list_keys:
            return [in_vals]

        lengths = {k: len(in_vals[k]) for k in list_keys}
        max_len = max(lengths.values())

        if len(list_keys) == len(in_vals):
            if len(set(lengths.values())) != 1:
                raise ValueError(f"Inconsistent input list lengths: {lengths}")
            return [{k: in_vals[k][i] for k in in_vals} for i in range(max_len)]

        expanded: Dict[str, List[Any]] = {}
        for k, v in in_vals.items():
            if isinstance(v, list):
                if len(v) != max_len:
                    raise ValueError(f"List input '{k}' length {len(v)} != expected {max_len}")
                expanded[k] = v
            else:
                expanded[k] = [v] * max_len

        return [{k: expanded[k][i] for k in expanded} for i in range(max_len)]

    def _bind_inputs(self, args, kwargs):
        names = list(self._in_ch.keys())
        values: Dict[str, Any] = {}

        for i, val in enumerate(args):
            if i >= len(names):
                raise TypeError(f"Too many positional args: expected at most {len(names)}")
            if names[i] in values:
                raise TypeError(f"Multiple values for '{names[i]}'")
            values[names[i]] = val

        for k, v in kwargs.items():
            if k not in names:
                raise TypeError(f"Unknown input '{k}'")
            if k in values:
                raise TypeError(f"Multiple values for '{k}'")
            values[k] = v

        for name in names:
            values.setdefault(name, self._in_ch[name].val)

        return values

    def _run_single(self, single_inputs: Dict[str, Any]):
        old_vals = {k: self._in_ch[k].val for k in single_inputs}
        try:
            for k, v in single_inputs.items():
                self._in_ch[k].val = v

            cmd = self.script()
            self._resolve_output_paths(single_inputs)
            self._run_cmd(cmd)
            self._finalize_output_paths()
        finally:
            for k, v in old_vals.items():
                self._in_ch[k].val = v

    def _run_sharded(self, shard_dicts: List[Dict[str, Any]]):
        workers = max(1, getattr(self.resource, "cpu", 1))
        results: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(self._run_child_shard, d) for d in shard_dicts]
            for fut in futs:
                results.append(fut.result())

        for name in self._out_ch:
            self._out_ch[name].val = [r[name] for r in results]

    def _run_child_shard(self, shard_inputs: Dict[str, Any]) -> Dict[str, Any]:
        child = self.__class__(**self.params)
        child.resource = self.resource
        child.config = self.config

        for name, ch in child._in_ch.items():
            ch.val = shard_inputs[name]

        cmd = child.script()
        child._resolve_output_paths(shard_inputs)
        child._run_cmd(cmd)
        child._finalize_output_paths()

        return {n: ch.val for n, ch in child._out_ch.items()}

    def _resolve_output_paths(self, context: Dict[str, Any]):
        """
        Resolve OUTPUT templates before running the command.
        Templates containing '*' are deferred until after execution.
        """
        ctx = {**self.params, **context}

        for name, tmpl in self.OUTPUTS.items():
            out_ch = self._out_ch[name]
            if out_ch.val is not None:
                continue

            if isinstance(tmpl, str):
                formatted = tmpl.format(**ctx)
                if "*" in formatted:
                    out_ch._pending_glob = formatted
                else:
                    out_ch.val = formatted
                continue

            if isinstance(tmpl, (list, tuple)):
                resolved: List[Optional[str]] = []
                pending_patterns: List[str] = []
                pending_indices: List[int] = []
                for i, part in enumerate(tmpl):
                    formatted = part.format(**ctx)
                    if "*" in formatted:
                        resolved.append(None)
                        pending_patterns.append(formatted)
                        pending_indices.append(i)
                    else:
                        resolved.append(formatted)

                if pending_patterns:
                    out_ch._pending_glob = pending_patterns
                    out_ch._pending_indices = pending_indices
                    out_ch.val = tuple(resolved)
                else:
                    out_ch.val = tuple(resolved)
                continue

    def _finalize_output_paths(self):
        """
        Replace pending glob templates with the actual file paths after execution.
        For patterns matching multiple files, store the list of matches.
        """
        for name, out_ch in self._out_ch.items():
            pending = getattr(out_ch, "_pending_glob", None)
            if not pending:
                continue

            if isinstance(pending, str):
                patterns = [pending]
                is_tuple = False
            else:
                patterns = list(pending)
                is_tuple = True

            resolved_values: List[Any] = []
            for pattern in patterns:
                hits = sorted(glob.glob(os.path.expanduser(pattern)))
                if len(hits) == 0:
                    raise FileNotFoundError(f"No files matched pattern '{pattern}' for output '{name}'")
                value: Any = hits[0] if len(hits) == 1 else hits
                resolved_values.append(value)

            if is_tuple:
                prev = out_ch.val if out_ch.val is not None else [None] * len(resolved_values)
                prev_list = list(prev)
                pending_indices = getattr(out_ch, "_pending_indices", list(range(len(resolved_values))))
                if len(pending_indices) != len(resolved_values):
                    raise RuntimeError("Mismatch between pending indices and matched files")
                for idx, match in zip(pending_indices, resolved_values):
                    prev_list[idx] = match
                out_ch.val = tuple(prev_list)
            else:
                out_ch.val = resolved_values[0]

            if hasattr(out_ch, "_pending_glob"):
                delattr(out_ch, "_pending_glob")
            if hasattr(out_ch, "_pending_indices"):
                delattr(out_ch, "_pending_indices")

    def _run_cmd(self, cmd: str):
        if not cmd:
            return
        cmd = wrap_container(cmd, self.config)
        if self.config.executor == "slurm":
            cmd = wrap_slurm(cmd, self)
        stdout_path, stderr_path = local_log_paths(safe_job_name(self.__class__.__name__))
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        write_cmd_log(cmd, self.config.flow_log)
        with open(stdout_path, "w") as fout, open(stderr_path, "w") as ferr:
            subprocess.run(cmd, shell=True, check=True, stdout=fout, stderr=ferr)


    @property
    def input_channels(self) -> List[Channel]:
        return list(self._in_ch.values())

    @property
    def output_channels(self) -> List[Channel]:
        return list(self._out_ch.values())

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
