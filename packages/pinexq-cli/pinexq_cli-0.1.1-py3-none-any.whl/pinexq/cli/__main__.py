from typing import Optional
import signal
import logging

from dotenv import load_dotenv

from pinexq.cli.cmd.cli import pinexq

log = logging.getLogger(__name__)

load_dotenv()

def signal_handler(_sig, _frame):
    print('Aborting')
    exit(0)

def main(argv: Optional[list[str]] = None) -> None:
    signal.signal(signal.SIGINT, signal_handler)
    # Delegate to Typer app
    # If argv is None, Typer uses sys.argv automatically
    if argv is None:
        pinexq(prog_name="pinexq")
    else:
        pinexq(args=argv, prog_name="pinexq")


if __name__ == "__main__":
    main()
