import sys
from pathlib import Path
from typing import LiteralString

from pydantic import BaseModel, Field, PositiveFloat, PositiveInt, ValidationError
from pydantic_settings import CliApp, CliPositionalArg, CliSubCommand

from .monitor import ProcessMonitor
from .utils import visualize_metric


class Monitor(BaseModel):
    """Monitor specific process resource usage."""

    pid: CliPositionalArg[PositiveInt] = Field(description="Process PID.")
    interval: PositiveFloat = Field(1.0, description="Monitoring interval in seconds.")

    def cli_cmd(self):
        pm = ProcessMonitor(self.pid, interval=self.interval)
        pm.start()


class Plot(BaseModel):
    """Visualize process resource usage from a csv file."""

    file: CliPositionalArg[Path] = Field(description="Path to the csv file.")

    def cli_cmd(self):
        visualize_metric(self.file)


class Cli(BaseModel):
    """A process system resource usage monitor."""

    monitor: CliSubCommand[Monitor] = Field(
        description="Monitor process resource usage."
    )
    plot: CliSubCommand[Plot] = Field(description="Plot process resource usage.")

    def cli_cmd(self):
        CliApp.run_subcommand(self)

    @staticmethod
    def custom_messages(val_err: ValidationError) -> LiteralString:
        msgs = []
        for err in val_err.errors():
            msgs.append(
                f"- {err['loc'][1].upper()}: {err['msg']}, but got '{err['input']}'"  # type: ignore
            )
        return "\n".join(msgs)


def main():
    try:
        CliApp.run(Cli)
    except ValidationError as e:
        print(f"Argument parsing error:\n{Cli.custom_messages(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
