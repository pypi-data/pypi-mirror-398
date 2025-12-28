"""Profiling helpers for codec-cub formats.

Usage:
    python -m scripts.profiling [options]
Options:
    -r, --runs <int>           Number of times to run to get a mean result. Default: 1
    -c, --codecs <list>        Specific codecs to profile (default: all).
    -t, --time-unit <str>      Time unit for display: s (seconds), ms (milliseconds), us (microseconds). Default: us
    --report <str>             Choose to print out a report on a specific codec.
    -d, --debug                Show error column for failed codecs.
    --detailed                 Show min/max columns in addition to avg/median.

Description:
    This script profiles the read and write performance of various codecs
    supported by codec-cub. It measures the time taken to serialize and
    deserialize a sample data structure multiple times and reports the results
    in a formatted table.
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from contextlib import suppress
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import timeit
from typing import TYPE_CHECKING, Any

from profiler_cub.core import CodeProfiler
from profiler_cub.display import display_all
from profiler_cub.models import ProfileConfig, SortMode
from rich.align import Align
from rich.console import Console
from rich.table import Table
from rich.text import Text

from funcy_bear.tools.gradient import ColorGradient, DefaultColorConfig
from scripts._helpers import ALL_CODECS, CodecData, ProfileResult, SetupReturn, _codec_definitions, _CodecRunner, touch

if TYPE_CHECKING:
    from collections.abc import Sequence

console = Console()


def profile_codecs(
    arguments: Namespace,
    codec_map: dict[str, _CodecRunner],
    sample_data: CodecData,
) -> list[ProfileResult]:
    """Profile read/write speeds for the available codecs.

    Args:
        data: Dictionary payload to profile.
        arguments: Parsed command-line arguments.

    Returns:
        A list of ProfileResult instances, one per codec.
    """
    runs: int = arguments.runs
    created_files: list[Path] = []
    results: list[ProfileResult] = []

    for codec in codec_map.values():
        result = ProfileResult(name=codec.name, runs=runs)
        codec.file_path.parent.mkdir(parents=True, exist_ok=True)
        touch(codec.file_path, exist_ok=True)
        prepared_data: Any = codec.prepare(sample_data)

        def write_func() -> None:
            codec.write(prepared_data)  # noqa: B023

        try:
            result.write_times = timeit.repeat(stmt=write_func, repeat=runs, number=1)
            result.total_write_seconds = sum(result.write_times)
            codec.write_handler.write(prepared_data)
            result.read_times = timeit.repeat(stmt=codec.read, repeat=runs, number=1)
            result.total_read_seconds = sum(result.read_times)
            result.size_bytes = codec.size
            created_files.append(codec.file_path)
        except Exception as e:
            result.error = str(e)
        finally:
            codec.close()
        results.append(result)

    return results


def _format_baseline(multiplier: float) -> Text | str:
    baseline = 1.0
    double_slower = 2.0
    ten_times_slower = 10.0

    if multiplier == baseline:
        return Text("1.00x", style="dim yellow")
    if multiplier < baseline:
        pct_faster: float = (baseline - multiplier) * 100
        return Text(f"↑ {pct_faster:.0f}%", style="bold green")
    if multiplier < double_slower:
        pct_slower: float = (multiplier - baseline) * 100
        return Text(f"↓ {pct_slower:.0f}%", style="dim yellow")
    if multiplier < ten_times_slower:
        return Text(f"↓ {multiplier:.2f}x", style="yellow")
    return Text(f"↓ {multiplier:.2f}x", style="red")


def visualization(arguments: Namespace, results: list[ProfileResult]) -> None:
    time_unit: Any = arguments.time_unit
    unit_symbol: str = {"s": "s", "ms": "ms", "us": "μs"}[time_unit]

    table = Table()
    table.add_column("Codec", style="cyan", no_wrap=True)
    table.add_column(f"W Med ({unit_symbol})", justify="right")
    if arguments.detailed:
        table.add_column(f"W Avg ({unit_symbol})", justify="right")
        table.add_column(f"W Min ({unit_symbol})", justify="right")
        table.add_column(f"W Max ({unit_symbol})", justify="right")
    table.add_column(f"R Med ({unit_symbol})", justify="right")
    if arguments.detailed:
        table.add_column(f"R Avg ({unit_symbol})", justify="right")
        table.add_column(f"R Min ({unit_symbol})", justify="right")
        table.add_column(f"R Max ({unit_symbol})", justify="right")
    table.add_column("W MB/s", justify="right")
    table.add_column("R MB/s", justify="right")
    table.add_column("Bytes", justify="right", width=5)
    table.add_column("Speed (W)", justify="right")
    table.add_column("Speed (R)", justify="right")
    if arguments.debug:
        table.add_column("Error", style="red")

    valid_write: list[float] = [r.write_per_run_ms for r in results if r.error is None]
    valid_read: list[float] = [r.read_per_run_ms for r in results if r.error is None]
    valid_sizes: list[int] = [r.size_bytes for r in results if r.error is None]

    fastest_write: float = min(valid_write) if valid_write else 0.0
    slowest_write: float = max(valid_write) if valid_write else 0.0
    fastest_read: float = min(valid_read) if valid_read else 0.0
    slowest_read: float = max(valid_read) if valid_read else 0.0
    smallest_size: int = min(valid_sizes) if valid_sizes else 0
    largest_size: int = max(valid_sizes) if valid_sizes else 0

    gradient = ColorGradient(reverse=True)

    baseline: ProfileResult | None = next((r for r in results if r.name == "text"), None)

    for result in results:
        write_avg: str = f"{result.write_avg:.4f}"
        write_median_val: str = f"{result.write_median:.4f}"
        write_min_val: str = f"{result.write_min:.4f}"
        write_max_val: str = f"{result.write_max:.4f}"
        read_avg: str = f"{result.read_avg:.4f}"
        read_median_val: str = f"{result.read_median:.4f}"
        read_min_val: str = f"{result.read_min:.4f}"
        read_max_val: str = f"{result.read_max:.4f}"
        write_tp: str = f"{result.write_throughput_mbs:.2f}"
        read_tp: str = f"{result.read_throughput_mbs:.2f}"
        size_val = str(result.size_bytes)

        result._write_color = gradient.map_to_rgb(fastest_write, slowest_write, result.write_per_run_ms)
        result._read_color = gradient.map_to_rgb(fastest_read, slowest_read, result.read_per_run_ms)
        result._size_color = gradient.map_to_rgb(smallest_size, largest_size, result.size_bytes)
        baseline_write_str: str | Text = "-"
        baseline_read_str: str | Text = "-"

        if baseline and result.error is None:
            if baseline.write_per_run_ms > 0:
                write_multiplier: float = result.write_per_run_ms / baseline.write_per_run_ms
                baseline_write_str = _format_baseline(write_multiplier)

            if baseline.read_per_run_ms > 0:
                read_multiplier: float = result.read_per_run_ms / baseline.read_per_run_ms
                baseline_read_str = _format_baseline(read_multiplier)

        row: list[str | Text] = [result.name, Text(write_median_val, style=result._write_color)]
        if arguments.detailed:
            row.extend([write_avg, write_min_val, write_max_val])

        row.append(Text(read_median_val, style=result._read_color))
        if arguments.detailed:
            row.extend([read_avg, read_min_val, read_max_val])

        row.extend([write_tp, read_tp, Text(size_val, style=result._size_color), baseline_write_str, baseline_read_str])
        if arguments.debug:
            row.append(result.error or "")
        table.add_row(*row)
    console.print(Align.center(table))
    if arguments.report != "none":
        result: ProfileResult | None = next((r for r in results if r.name == arguments.report), None)
        if result is None:
            return
        report(result, unit_symbol)


def report(result: ProfileResult, unit_symbol: str) -> None:
    console.print(f"[bold underline]Detailed Report for {result.name} Codec[/bold underline]")
    console.print(f"Total Write Time: {result.total_write_seconds:.6f} seconds")
    console.print(f"Total Read Time: {result.total_read_seconds:.6f} seconds")

    console.print(Text(f"Write Median: {result.write_median:.2f} {unit_symbol}", style=result._write_color))
    console.print(f"Min Write Time: {result.write_min:.2f} {unit_symbol}")
    console.print(f"Max Write Time: {result.write_max:.2f} {unit_symbol}")

    console.print(Text(f"Read Median: {result.read_median:.2f} {unit_symbol}", style=result._read_color))
    console.print(f"Min Read Time: {result.read_min:.2f} {unit_symbol}")
    console.print(f"Max Read Time: {result.read_max:.2f} {unit_symbol}")

    console.print(f"Write Time Std Dev: {result.write_std_dev:.2f} {unit_symbol}")
    console.print(f"Read Time Std Dev: {result.read_std_dev:.2f} {unit_symbol}")
    console.print(f"Write Time Variance: {result.write_variance:.2f} {unit_symbol}²")
    console.print(f"Read Time Variance: {result.read_variance:.2f} {unit_symbol}²")
    console.print(f"Write Throughput: {result.write_throughput_mbs:.2f} MB/s")
    console.print(f"Read Throughput: {result.read_throughput_mbs:.2f} MB/s")
    console.print(f"Slowest Reads: {[f'{t * result._time_multiplier:.2f}' for t in result.slowest_reads]}")
    console.print(f"Fastest Reads: {[f'{t * result._time_multiplier:.2f}' for t in result.fastest_reads]}")
    console.print(f"Slowest Writes: {[f'{t * result._time_multiplier:.2f}' for t in result.slowest_writes]}")
    console.print(f"Fastest Writes: {[f'{t * result._time_multiplier:.2f}' for t in result.fastest_writes]}")
    console.print(Text(f"File Size: {result.size_bytes} bytes", style=result._size_color))


def get_args(args: list[str]) -> Namespace:
    parser = ArgumentParser(description="Profile codec-cub codecs for read/write performance.")
    parser.add_argument("-r", "--runs", type=int, default=1, help="Number of times to run to get a mean result.")
    parser.add_argument(
        "-c",
        "--codecs",
        type=str,
        nargs="+",
        default=None,
        help="Specific codecs to profile (default: all).",
    )
    parser.add_argument(
        "-t",
        "--time-unit",
        type=str,
        choices=["s", "ms", "us"],
        default="us",
        help="Time unit for display: s (seconds), ms (milliseconds), us (microseconds). Default: us",
    )
    parser.add_argument(
        "--report",
        type=str,
        choices=ALL_CODECS,
        default="none",
        help="Choose to print out a report on a specific codec.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Show full detailed columns in the report.",
    )

    parser.add_argument("-d", "--debug", action="store_true", help="Show error column for failed codecs.")
    parser.add_argument("--detailed", action="store_true", help="Show min/max columns in addition to avg/median.")

    return parser.parse_args(args)


config = ProfileConfig(
    module_name="codec_cub",
    stats_file=Path("codec_cub_profile.stats"),
    module_map={
        "general": {"general"},
        "file lock": {"general.file_lock"},
        "json": {"jsons"},
        "jsonl": {"jsonl"},
        "yaml": {"yaml"},
        "toml": {"toml"},
        "xml": {"xml"},
        "msgpack": {"message_pack"},
        "nix": {"nix"},
        "toon": {"toon"},
        "text": {"text"},
    },
)


def create_temp_dir() -> Path:
    """Create a temporary directory for profiling files.

    Returns:
        Path to the created temporary directory.
    """
    temp_dir: TemporaryDirectory[str] = TemporaryDirectory(prefix="codec-cub-")
    Path(temp_dir.name).mkdir(parents=True, exist_ok=True)
    return Path(temp_dir.name)


def setup_items(base_dir: Path, codecs: Sequence[str] | None = None) -> SetupReturn:
    """Get a mapping of codec names to their corresponding _CodecRunner instances.

    Args:
        base_dir: Base directory for codec files.

    Returns:
        A dictionary mapping codec names to _CodecRunner instances.
    """
    sample_data: CodecData = {
        "name": "Codec Cub",
        "version": 1.0,
        "features": ["json", "yaml", "toml", "xml", "msgpack", "nix", "toon", "text"],
        "active": True,
        "settings": {"indent": 4, "ensure_ascii": False, "sort_keys": True},
        "items": [{"id": i, "value": f"Item {i}"} for i in range(10)],
    }
    codec_map: dict[str, _CodecRunner] = _codec_definitions(base_dir)
    if codecs is not None:
        codec_map = {name: codec_map[name] for name in codecs if name in codec_map}
    return SetupReturn(codec_map=codec_map, sample_data=sample_data)


def main(args: list[str] | None = None) -> None:
    """Run profiling and display results."""
    if args is None:
        args = sys.argv[1:]

    arguments: Namespace = get_args(args)

    base_dir: Path = create_temp_dir()

    def setup_fn() -> SetupReturn:
        items: SetupReturn = setup_items(base_dir, arguments.codecs)
        items.runs = arguments.runs
        return items

    def workload_fn(setup_vars: SetupReturn) -> tuple[Path, dict[str, _CodecRunner], CodecData]:
        """Function to perform workload for profiling.

        Args:
            codec_map: Mapping of codec names to _CodecRunner instances.
            data: Data to be processed.
            runs: Number of runs for profiling.

        Returns:
            Tuple of base directory and codec map.
        """
        codec_map = setup_vars.codec_map
        data = setup_vars.sample_data
        runs = setup_vars.runs

        for codec in codec_map.values():
            prepared_data: Any = codec.prepare(data)

            for _ in range(runs):
                codec.write_handler.write(prepared_data)
                codec.read()
        return base_dir, codec_map, data

    results: list[ProfileResult] | None = None

    def cleanup_temp_dir(temp_dir: Path, codec_map: dict[str, _CodecRunner], sample_data: CodecData) -> None:
        """Cleanup the temporary directory.

        Args:
            temp_dir: Path to the temporary directory.
        """
        nonlocal results
        results = profile_codecs(arguments, codec_map, sample_data)

        for codec in codec_map.values():
            codec.close()
        with suppress(Exception):
            if temp_dir.exists() and temp_dir.is_dir():
                shutil.rmtree(temp_dir)

    if not arguments.full:
        setup_vars: SetupReturn = setup_fn()
        results = profile_codecs(
            arguments,
            setup_vars.codec_map,
            setup_vars.sample_data,
        )
        visualization(arguments, results)

    else:
        color_config = DefaultColorConfig()
        color_config.update_thresholds(mid=0.7)
        color_gradient = ColorGradient(config=color_config, reverse=True)
        profiler = CodeProfiler(
            pkg_name="codec_cub",
            module_map=config.module_map,
            threshold_ms=config.threshold_ms,
            iterations=arguments.runs,
        )
        profiler.run(
            workload_fn=workload_fn,
            stats_file=config.stats_file,
            setup_fn=setup_fn,
            teardown_fn=cleanup_temp_dir,
        )
        display_all(
            profiler=profiler,
            top_n=100,
            console=console,
            color_gradient=color_gradient,
            sort_mode=SortMode.TOTAL_TIME,
            dependency_search="tomlkit",
            display_callback=visualization,
            callback_kwargs={"arguments": arguments, "results": results},
        )


if __name__ == "__main__":
    main()
