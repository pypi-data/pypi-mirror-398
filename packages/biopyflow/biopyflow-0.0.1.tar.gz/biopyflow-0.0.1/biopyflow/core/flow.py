from __future__ import annotations

import inspect
from collections import deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Dict, List, Optional, Set
import copy

from .step import Step
from .config import Config
from .config import Resource
from .inout import make_flow_log


class Flow:
    """
    DAG executor that wires Step dependencies via their channels.
    """

    CONFIG: Config = Config(runtime="local", executor="local", flow_log=make_flow_log("flow"))
    RESOURCE: Resource = Resource(cpu=1, mem=4, time=2)

    def __init__(self):
        self.steps: List[Step] = []
        self.graph: Dict[Step, List[Step]] = {}
        self._initialized = False

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if isinstance(value, Step) and getattr(self, "_initialized", False):
            self._register_step(value)

    def _register_step(self, step: Step):
        if step not in self.steps:
            self.steps.append(step)

    def _update_config(self):
        for step in self.steps:
            if step.config is None:
                step.config = copy.deepcopy(self.CONFIG)
            else:
                #loop through step.config attributes
                # and update with self.CONFIG attributes 
                # if config of each step is None
                for attr, value in self.CONFIG.__dict__.items():
                    if getattr(step.config, attr) is None:
                        setattr(step.config, attr, value)

    def _update_resource(self):
        for step in self.steps:
            if step.resource is None:
                step.resource = copy.deepcopy(self.RESOURCE)
            else:
                #loop through step.resource attributes
                # and update with self.RESOURCE attributes 
                # if resource of each step is None
                for attr, value in self.RESOURCE.__dict__.items():
                    if getattr(step.resource, attr) is None:
                        setattr(step.resource, attr, value)

    def finalize(self):
        self._initialized = True
        for _, val in inspect.getmembers(self):
            if isinstance(val, Step):
                self._register_step(val)
        self._build_dag()
        self._update_config()
        self._update_resource()

    def _build_dag(self):
        """Build adjacency information using producers recorded on channels."""

        self.graph = {s: [] for s in self.steps}
        self.upstream: Dict[Step, Set[Step]] = {s: set() for s in self.steps}

        for step in self.steps:
            for in_ch in step.input_channels:
                for producer in in_ch.producers:
                    if producer is step:
                        continue
                    self.upstream[step].add(producer)
                    if step not in self.graph[producer]:
                        self.graph[producer].append(step)
                        
    def _topological_sort(self) -> List[Step]:
        """Return steps in topologically sorted order.

        Uses self.graph (adjacency list) and self.upstream (dependency sets).
        Raises:
            ValueError: if a cycle is detected.
        """

        # Compute in-degree (number of upstream dependencies) for each step
        in_degree = {step: len(self.upstream[step]) for step in self.steps}
        # Queue starts with all nodes that have no incoming edges
        queue = deque(step for step in self.steps if in_degree[step] == 0)
        order: List[Step] = []
        while queue:
            step = queue.popleft()
            order.append(step)
            # For each node downstream of this step, decrement in-degree
            for downstream in self.graph[step]:
                in_degree[downstream] -= 1
                if in_degree[downstream] == 0:
                    queue.append(downstream)
        # If some nodes weren't processed, there's a cycle
        if len(order) != len(self.steps):
            raise ValueError("Cycle detected in step graph; topological sort not possible.")
        return order

        

    def show_dag(self):
        print("Pipeline DAG:")
        for src, dsts in self.graph.items():
            if dsts:
                for dst in dsts:
                    print(f"  {src.__class__.__name__} → {dst.__class__.__name__}")
            else:
                print(f"  {src.__class__.__name__} → [no downstream step]")

    def run(self, max_workers: Optional[int] = None):
        """
        Execute the DAG respecting dependencies.
        """
        if not getattr(self, "_initialized", False) or not hasattr(self, "upstream"):
            self.finalize()

        remaining: Dict[Step, Set[Step]] = {
            s: set(self.upstream.get(s, set())) for s in self.steps
        }
        children = self.graph
        ready = deque([s for s in self.steps if not remaining[s]])

        if not max_workers or max_workers <= 1:
            while ready:
                step = ready.popleft()
                step.execute()
                for child in children.get(step, ()):
                    remaining[child].discard(step)
                    if not remaining[child]:
                        ready.append(child)
            if any(remaining.values()):
                raise RuntimeError("Some steps could not be scheduled (cycle?)")
            return

        submitted: Dict = {}
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            while ready or submitted:
                while ready:
                    step = ready.popleft()
                    fut = ex.submit(step.execute)
                    submitted[fut] = step

                done, _ = wait(list(submitted.keys()), return_when=FIRST_COMPLETED)
                for fut in done:
                    step = submitted.pop(fut)
                    fut.result()
                    for child in children.get(step, ()):
                        if step in remaining[child]:
                            remaining[child].discard(step)
                            if not remaining[child]:
                                ready.append(child)

        if any(remaining.values()):
            raise RuntimeError("Some steps could not be scheduled (cycle?)")
