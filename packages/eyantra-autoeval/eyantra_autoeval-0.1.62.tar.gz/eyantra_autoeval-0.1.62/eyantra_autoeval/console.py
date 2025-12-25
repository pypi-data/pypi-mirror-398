#!/usr/bin/env python3

# standard imports
import importlib
import json
import logging
import time
from datetime import datetime

# third-party imprts
import click
from rich import print
from rich.logging import RichHandler

FORMAT = "%(message)s"


@click.group()
def cli():
    pass


@click.command()
@click.option("--year", required=True, help="Year.")
@click.option("--theme", required=True, help="Theme Initials.")
@click.option("--task", required=True, help="Task Number.")
@click.option("--verbose", is_flag=True, help="Run in verbose mode.")
def evaluate(year, theme, task, verbose):
    """Dry run evaluation for a task."""
    print(
        f"Running evaluation scripts for [bold blue]{year}[/bold blue] "
        f"theme [bold blue]{theme}[/bold blue] for "
        f"task [bold blue]{task}[/bold blue]"
    )
    logging.basicConfig(
        level="DEBUG" if verbose else "INFO",
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    log = logging.getLogger("rich")

    evaluator = importlib.import_module(
        f"eyantra_autoeval.year.y{year}.{theme}.task{task}.evaluator"
    )

    start_time = time.time()
    try:
        log.debug("Calling appropriate evaluator")
        result = evaluator.evaluate()
    except Exception as err:
        log.error(err)
    end_time = time.time()

    result["meta"] = {}
    result["meta"]["evaluation_time"] = end_time - start_time

    log.debug(result)
    if result["generate"]:
        file_name = f"result-{year}-{theme}-{task}-{datetime.now().strftime('%Y%m%d')}.json"
        if "timestamp" in result:
            if not result["timestamp"]:
                file_name = "result.json"

        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=4)

cli.add_command(evaluate)
