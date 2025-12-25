from __future__ import annotations

import os
import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import click
from schemathesis import SCHEMATHESIS_VERSION, cli
from schemathesis.core import Specification, SpecificationKind
from schemathesis.engine import events
from schemathesis.engine.recorder import Interaction, ScenarioRecorder

from tracecov import CoverageMap, HttpInteraction, HttpRequest, HttpResponse, terminal

COVERAGE_REPORT_TITLE = "Schema Coverage Report"
DEFAULT_HTML_REPORT_PATH = "./schema-coverage.html"
ENABLE_PROFILING = os.environ.get("SCHEMATHESIS_COVERAGE_PROFILE", "").lower() in ("1", "true", "yes", "on")


class ExtensionError(Exception):
    def __init__(self, inner: BaseException) -> None:
        self.inner = inner


def _transform_headers(headers: dict[str, list[str]]) -> dict[str, str]:
    return {key: value[0] for key, value in headers.items()}


def group_interactions_by_method_path(recorder: ScenarioRecorder) -> dict[tuple[str, str], list[Interaction]]:
    """Group interactions by method and path template."""
    groups = defaultdict(list)

    for case_id, case_node in recorder.cases.items():
        case = case_node.value
        interaction = recorder.interactions.get(case_id)
        if interaction:
            groups[(case.method, case.operation.full_path)].append(interaction)
        else:
            # Could only happen with some hard-to-trigger network errors
            ...  # pragma: no cover

    return groups


T = TypeVar("T")


def profile(name: str) -> Callable:
    """Decorator that profiles collector operations if profiling is enabled."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if not ENABLE_PROFILING:
            return func

        @wraps(func)
        def wrapper(self: cli.EventHandler, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            result = func(self, *args, **kwargs)
            elapsed = time.perf_counter() - start
            self.profile_log.append(f"Collector.{name}: {elapsed:.6f}s")
            self.collector_total_time += elapsed
            return result

        return wrapper

    return decorator


def safe_collector(name: str) -> Callable:
    """Decorator that catches exceptions from collector operations."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self: cli.EventHandler, *args: Any, **kwargs: Any) -> Any:
            try:
                return func(self, *args, **kwargs)
            except BaseException as e:  # pragma: no cover
                self.coverage_errors.append(f"Error in {name}: {str(e)}")
                raise ExtensionError(e) from None

        return wrapper

    return decorator


@cli.handler()
class TracecovHandler(cli.EventHandler):
    show_missing: list[str] | None

    def __init__(self, *args: Any, **params: Any) -> None:
        self.format = params["coverage_format"]
        self.report_path = params["coverage_report_path"]
        self.no_report = params["coverage_no_report"]
        self.skip_covered = params["coverage_skip_covered"]
        self.skip_empty = params["coverage_skip_empty"]
        show_missing = params["coverage_show_missing"]
        self.profile_log: list[str] = []
        self.collector_total_time = 0.0
        if isinstance(show_missing, str):
            value = {
                "parameters": "parameter",
            }[show_missing]
            self.show_missing = [value]
        else:
            self.show_missing = None
        if params.get("no_color"):
            self.colored_report = False
        else:
            self.colored_report = True
        self.coverage_map: CoverageMap | None = None
        self.coverage_errors: list[str] = []
        self.specification: Specification | None = None

    @profile("create")
    @safe_collector("create_collector")
    def create_coverage_map(self, schema: dict[str, Any], base_path: str) -> CoverageMap:
        return CoverageMap.from_dict(schema, base_path=base_path)

    @profile("record_schemathesis_interactions")
    @safe_collector("process_batch")
    def process_batch(self, method: str, path: str, batch: list[HttpInteraction]) -> None:
        assert self.coverage_map is not None
        self.coverage_map.record_schemathesis_interactions(method, path, batch)

    @profile("generate_text_report")
    @safe_collector("generate_text_report")
    def generate_text_report(self, width: int) -> str:
        assert self.coverage_map is not None
        return self.coverage_map.generate_text_report(
            width=width,
            colored=self.colored_report,
            skip_covered=self.skip_covered,
            skip_empty=self.skip_empty,
            show_missing=self.show_missing,
        )

    @profile("generate_report")
    @safe_collector("generate_report")
    def generate_report(self, title: str | None = None) -> str:
        assert self.coverage_map is not None
        return self.coverage_map.generate_report(title=title)

    @safe_collector("record_error")
    def record_error(self, method: str, path: str, message: str) -> None:
        assert self.coverage_map is not None
        self.coverage_map.record_error(method, path, message)

    def handle_event(self, ctx: cli.ExecutionContext, event: events.ExecutionEvent) -> None:
        if isinstance(event, cli.LoadingFinished):
            self.specification = event.specification
            if event.specification.kind == SpecificationKind.OPENAPI:
                try:
                    self.coverage_map = self.create_coverage_map(event.schema, base_path=event.base_path)
                except ExtensionError:
                    pass
        elif (
            isinstance(event, events.NonFatalError)
            and self.coverage_map is not None
            and event.label is not None
            and event.label.startswith(("GET ", "PUT ", "POST ", "DELETE ", "OPTIONS ", "HEAD ", "PATCH ", "TRACE "))
        ):
            method, path = event.label.split(" ", maxsplit=1)
            try:
                self.record_error(method, path, event.info.message)
            except ExtensionError:  # pragma: no cover
                pass
        elif isinstance(event, events.ScenarioFinished) and self.coverage_map is not None:
            grouped_interactions = group_interactions_by_method_path(event.recorder)
            for (method, path), interactions in grouped_interactions.items():
                batch = [
                    HttpInteraction(
                        request=HttpRequest(
                            method=method,
                            url=interaction.request.uri,
                            body=interaction.request.body,
                            headers=_transform_headers(interaction.request.headers),
                        ),
                        response=HttpResponse(
                            status_code=interaction.response.status_code,
                            elapsed=interaction.response.elapsed,
                        )
                        if interaction.response
                        else None,
                        timestamp=interaction.timestamp,
                    )
                    for interaction in interactions
                ]
                try:
                    self.process_batch(method, path, batch)
                except ExtensionError:
                    pass
        elif isinstance(event, events.EngineFinished):
            if self.coverage_map is not None:
                try:
                    if not self.no_report:
                        if self.format == "text":
                            width = _report_section(ctx)
                            report = self.generate_text_report(width)
                            ctx.add_summary_line(report)
                        if self.format == "html":
                            report = self.generate_report(title=f"Schemathesis {SCHEMATHESIS_VERSION}")
                            path = self.report_path or DEFAULT_HTML_REPORT_PATH
                            with open(path, "w") as fd:
                                fd.write(report)
                            ctx.add_summary_line(f"Schema Coverage report: {path}")
                except ExtensionError:
                    pass

                if self.coverage_errors:
                    width = terminal.get_width()
                    ctx.add_summary_line(click.style(" Coverage Errors ".center(width, "-"), bold=True, fg="red"))
                    ctx.add_summary_line("")
                    for error in self.coverage_errors:
                        ctx.add_summary_line(click.style(f"- {error}", fg="red"))

                if ENABLE_PROFILING:
                    width = terminal.get_width()
                    ctx.add_summary_line("")
                    ctx.add_summary_line(click.style(" Coverage Profiling ".center(width, "-"), bold=True))
                    for entry in self.profile_log:
                        ctx.add_summary_line(entry)
                    ctx.add_summary_line(f"Total collector time: {self.collector_total_time:.6f}s")
            else:
                assert self.specification is not None
                width = _report_section(ctx)
                title = click.style("Error", bold=True)
                ctx.add_summary_line(click.style(f"{title}: {self.specification.name} is not supported", fg="red"))


def _report_section(context: cli.ExecutionContext) -> int:
    width = terminal.get_width()
    context.add_summary_line(click.style(f" {COVERAGE_REPORT_TITLE} ".center(width, "_"), bold=True))
    context.add_summary_line("")
    return width
