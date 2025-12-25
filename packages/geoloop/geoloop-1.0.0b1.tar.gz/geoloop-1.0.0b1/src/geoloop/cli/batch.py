import json
from pathlib import Path

import typer

from geoloop.bin.Runbatch import run_batch_from_json

batch_app = typer.Typer(help="Batch processing commands for geoloop.")


@batch_app.command("run")
def batch_run(batchfile: Path = typer.Argument(..., help="Path to batch JSON file.")):
    """Run a batch JSON file."""
    run_batch_from_json(str(batchfile))


@batch_app.command("create")
def batch_create(
    output: Path = typer.Argument(..., help="Where to save the new batch JSON file."),
    stochastic_run: list[str] = typer.Option([], help="Runmain config files."),
    single_run: list[str] = typer.Option([], help="SingleRunSim config files."),
    process_lithology: list[str] = typer.Option([], help="Lithology config files."),
    calculate_loadprofile: list[str] = typer.Option(
        [], help="Loadprofile config files."
    ),
    calculate_flowdata: list[str] = typer.Option([], help="FlowData config files."),
    plot: list[str] = typer.Option([], help="Plotmain config files."),
):
    """
    Create a batch JSON non-interactively.

    Example:
        geoloop batch create batch.json --stochastic-run a.json --plot p.json
    """

    commands = []

    for file in stochastic_run:
        commands.append({"command": "Runmain", "args": file})

    for file in single_run:
        commands.append({"command": "SingleRunSim", "args": file})

    for file in process_lithology:
        commands.append({"command": "Lithology", "args": file})

    for file in calculate_loadprofile:
        commands.append({"command": "Loadprofile", "args": file})

    for file in calculate_flowdata:
        commands.append({"command": "FlowData", "args": file})

    for file in plot:
        commands.append({"command": "Plotmain", "args": file})

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"commands": commands}, indent=2))

    typer.secho(f"Batch file created: {output}", fg=typer.colors.GREEN)


@batch_app.command("wizard")
def batch_wizard():
    """
    Interactive wizard to build a batch JSON file.
    """

    typer.echo("Welcome to the Geoloop Batch Wizard!")
    typer.echo("Let's build your batch sequence.\n")

    commands = []
    while True:
        typer.echo("\nSelect command to add:")
        choice = typer.prompt(
            "Options: stochastic-run, single-run, process-lithology, calculate-loadprofile, calculate-flowdata, plot, done",
            type=str,
        )

        if choice.lower() == "done":
            break

        valid = {
            "stochastic-run": "Runmain",
            "single-run": "SingleRunSim",
            "process-lithology": "Lithology",
            "calculate-loadprofile": "Loadprofile",
            "calculate-flowdata": "FlowData",
            "plot": "Plotmain",
        }

        if choice.lower() not in valid:
            typer.secho("Invalid command type!", fg=typer.colors.RED)
            continue

        filepath = typer.prompt("Enter path to the config JSON file:")

        commands.append({"command": valid[choice.lower()], "args": filepath})

        typer.secho("Command added!\n", fg=typer.colors.GREEN)

    output_file = typer.prompt("Where should the batch JSON be saved?")
    output = Path(output_file)

    output.write_text(json.dumps({"commands": commands}, indent=2))

    typer.secho(f"\nBatch file saved: {output}", fg=typer.colors.GREEN)
