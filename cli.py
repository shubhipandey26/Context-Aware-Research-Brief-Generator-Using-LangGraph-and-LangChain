
import json, typer
from .workflow import build_and_run

cli = typer.Typer(help="Research Brief CLI")

@cli.command()
def run(topic: str, depth: int = 1, follow_up: bool = False, user_id: str = "local_user"):
    out = build_and_run(topic=topic, depth=depth, user_id=user_id, follow_up=follow_up)
    print(json.dumps(out, indent=2, default=str))

if __name__ == "__main__":
    cli()
