from typing import Annotated
from pathlib import Path
import typer
import logging

from polyhattrick.client import polyhattrick_client

app = typer.Typer()
login_app = typer.Typer()
app.add_typer(login_app, name="login")

match_app = typer.Typer()
app.add_typer(match_app, name="match")
live_app = typer.Typer()
match_app.add_typer(live_app, name="live")

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "client.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

client = polyhattrick_client.PolyhattrickClient("prod")


@login_app.command("authenticate")
def authenticate():
    response = client.authenticate()
    print(
        f"Please follow this URL to grant polyhattrick access to read your data. Then, run `login exchange [TOKEN]`:\n{response}"
    )


@login_app.command("exchange")
def exchange(pin: Annotated[str, typer.Argument()]):
    client.exchange_tokens(pin)


@live_app.command("watch")
def watch():
    try:
        res = client.get_live_result()
        if res:
            print(res)
    except Exception as e:
        logging.error("Unable to get live result.", exc_info=True)
        return ""


def main():
    app()


if __name__ == "__main__":
    main()
