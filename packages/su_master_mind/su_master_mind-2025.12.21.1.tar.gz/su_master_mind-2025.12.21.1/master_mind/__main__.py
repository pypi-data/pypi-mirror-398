from pathlib import Path
from typing import List
import click
import sys
import importlib
import importlib.metadata
import logging
from .configuration import Configuration
from .utils import check_last_mastermind
from . import install
from packaging.version import parse as parse_version

logging.basicConfig(level=logging.INFO)

original_args = [arg for arg in sys.argv]
CLASS_NAMES = ["deepl", "rl", "llm", "adl", "rital"]


@click.group()
def main():
    pass


@main.group()
def courses():
    """Permet de gérer la liste des cours suivis"""
    pass


@click.argument("courses", type=click.Choice(CLASS_NAMES), nargs=-1)
@courses.command("add")
def courses_add(courses: List[str]):
    """Ajout de cours"""
    configuration = Configuration()
    configuration.courses.update(courses)
    configuration.save()
    print(  # noqa: T201
        "Don't forget to update the python packages with `master-mind update`"
    )


@click.argument("courses", type=click.Choice(CLASS_NAMES), nargs=-1)
@courses.command("rm")
def courses_rm(courses: List[str]):
    """Enlever un cours"""
    configuration = Configuration()
    for course in courses:
        configuration.courses.remove(course)
    configuration.save()


@courses.command("list")
def courses_list():
    """Liste des cours"""
    for course in Configuration().courses:
        print(course)  # noqa: T201


@click.option("--no-self-update", is_flag=True)
@main.command()
def update(no_self_update: bool):
    """Mettre à jour l'ensemble des modules pour les cours suivis"""
    if not no_self_update:
        check_last_mastermind(original_args)

    # Install all configured courses in a single command
    configuration = Configuration()
    install.install_courses(list(configuration.courses))

    print(  # noqa: T201
        "Don't forget to download the datasets with `master-mind download-datasets`"
    )


@main.command()
def download_datasets():
    """Mettre à jour l'ensemble des jeux de données pour les cours suivis"""
    import os

    # Ensure HuggingFace Hub is online for dataset downloads
    hf_hub_offline = os.environ.pop("HF_HUB_OFFLINE", None)

    try:
        configuration = Configuration()
        datasets = importlib.import_module("master_mind.datasets")

        for course in configuration.courses:
            logging.info("Installing resources for %s", course)
            getattr(datasets, course, lambda: None)()
    finally:
        # Restore original HF_HUB_OFFLINE setting
        if hf_hub_offline is not None:
            os.environ["HF_HUB_OFFLINE"] = hf_hub_offline


@main.group()
def rl():
    """Commandes spécifiques au module RL"""
    pass


@click.option("--hide", is_flag=True)
@click.option("--debug", is_flag=True)
@click.option("--error-handling", is_flag=True, help="Catch exceptions within agents")
@click.option(
    "--output",
    default=None,
    type=Path,
    help="Path for output JSON file (none = standard output)",
)
@click.option(
    "--no-check", is_flag=True, help="Do not check if master-mind is up to date"
)
@click.option(
    "--interaction",
    type=click.Choice(["none", "interactive", "map"]),
    help="Race interaction type (when debugging)",
)
@click.option(
    "--num-karts",
    type=int,
    help="Number of karts (must be greater than number of zip files)",
)
@click.option(
    "--max-paths",
    type=int,
    help="Limit on the number of paths for the environment",
)
@click.option(
    "--action-timeout",
    type=float,
    default=None,
    help="Maximum time in seconds allowed for each agent action (default: no timeout)",
)
@click.argument("file_or_modules", type=str, nargs=-1)
@rl.command("stk-race")
def rld_stk_race(
    no_check,
    hide,
    max_paths: int | None,
    debug,
    num_karts,
    file_or_modules,
    interaction,
    output,
    error_handling,
    action_timeout,
):
    """Race"""
    if not no_check:
        check_last_mastermind(original_args)

        version = parse_version(importlib.metadata.version("pystk2_gymnasium"))
        assert version >= parse_version("0.7.2") and version < parse_version(
            "0.8.0"
        ), f"Expected pytstk2-gymnasium version 0.7.*, got {version}. Please update."

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    from master_mind.rld.stk import race, InteractionMode

    if num_karts < 1 or len(file_or_modules) == 0:
        logging.error("At least one kart")
        sys.exit(1)

    race(
        hide,
        num_karts,
        file_or_modules,
        interaction=InteractionMode[(interaction or "NONE").upper()],
        output=output,
        max_paths=max_paths,
        error_handling=error_handling,
        action_timeout=action_timeout,
    )
