#!/usr/bin/python3

import pathlib
import subprocess
from datetime import datetime
from enum import Enum
from typing import Annotated

import typer
import yaml


class Backend(str, Enum):
    codex = "codex"
    opencode = "opencode"
    gemini = "gemini"


class Mode(str, Enum):
    normal = "normal"
    yolo = "yolo"


def run(cwd, *args, **kwargs):
    """Shortcut to run a command in a given directory."""
    kwargs.setdefault("check", True)
    kwargs.setdefault("cwd", cwd)
    return subprocess.run(args, **kwargs)  # noqa: S603


def run_read(cwd, *args, **kwargs):
    """Shortcut to run a command in a given directory."""
    return run(cwd, *args, **kwargs, stdout=subprocess.PIPE).stdout.decode("utf-8")


def run_agent(cwd, instructions, backend, mode, model):
    if backend == "codex":
        cmd_args = ["codex", "--full-auto"]
        if model:
            cmd_args.extend(["--model", model])
        cmd_args.extend(["exec", instructions, "--skip-git-repo-check"])
        if mode == "yolo":
            cmd_args.append("--dangerously-bypass-approvals-and-sandbox")
        else:
            cmd_args.extend(["--sandbox", "danger-full-access"])
    elif backend == "opencode":
        if not model:
            model = "opencode/grok-code"
        cmd_args = [
            "opencode",
            "--model",
            model,
            "run",
            instructions,
        ]
    elif backend == "gemini":
        cmd_args = ["gemini"]
        if model:
            cmd_args.extend(["--model", model])
        if mode == "yolo":
            cmd_args.append("--yolo")
        else:
            cmd_args.extend(["--approval-mode", "auto_edit"])
        cmd_args.append(instructions)
    run(cwd, *cmd_args)


def inject_var(command):
    return command.replace("{module_dir}", ".")


def commit_if_change(cwd, step):
    changes = run_read(cwd, "git", "status", "--short")
    if not changes.strip():
        return
    run(cwd, "git", "add", ".")
    message = step["commit_if_change"]
    if message == True:  # noqa: E712
        message = step["name"]
    run(cwd, "git", "commit", "-m", message)


def run_workflow(workflow_dir, workflow, backend, mode, model):  # noqa: C901
    for step in workflow["steps"]:
        if step.get("ignore", False):
            continue
        cwd = inject_var(step["work_dir"]) if "work_dir" in step else "."
        now = datetime.now()
        str_now = now.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{str_now} Running step", step["name"])
        if "command" in step:
            command = inject_var(step["command"])
            run(cwd, "bash", "-lc", command)
        elif "instruction" in step:
            error = 0
            if "condition" in step:
                try:
                    command = inject_var(step["condition"])
                    run(cwd, "bash", "-lc", command)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    error = 1
            instruction = step["instruction"]
            if "files" in step:
                instruction += "\n\nHere are files added for context:\n"
                for file_name in step["files"]:
                    file = workflow_dir / file_name
                    if not file.exists():
                        print(f"File {file} does not exist.")
                        error = 1
                        continue
                    with open(file) as f:
                        instruction += f"\n# {file.name}\n```\n"
                        instruction += f.read()
                        instruction += "\n```\n"
            if not error:
                run_agent(cwd, instruction, backend, mode, model)
        if step.get("commit_if_change"):
            commit_if_change(cwd, step)


def main(
    instructions: Annotated[
        str,
        typer.Argument(
            help="Instruction to execute, required if instructions file or workflow is not provided",
        ),
    ] = "",
    backend: Backend = Backend.codex,
    mode: Mode = Mode.normal,
    instructions_file: Annotated[
        str,
        typer.Option(
            "--instructions-file",
            "-f",
            help="Instructions file, will override instructions argument,"
            " required if instructions or workflow is not provided",
        ),
    ] = "",
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-m",
            help="Model to use",
        ),
    ] = "",
    workflow: Annotated[
        str,
        typer.Option(
            "--workflow",
            "-w",
            help="Workflow to use, required if instructions_file or"
            " instructions is not provided, will override instructions"
            " or instructions_file",
        ),
    ] = "",
):
    if not (instructions_file or instructions or workflow):
        error = "Either instructions_file or instructions or workflow must be provided."
        raise ValueError(error)
    if workflow:
        workflow_dir = pathlib.Path(workflow).expanduser().resolve().parent
        with open(workflow) as file:
            workflow = yaml.safe_load(file)[0]
        run_workflow(workflow_dir, workflow, backend, mode, model)
    else:
        if instructions_file:
            with open(instructions_file) as file:
                instructions = file.read()
        run_agent(".", instructions, backend, mode, model)


def cli():
    typer.run(main)


if __name__ == "__main__":
    cli()
