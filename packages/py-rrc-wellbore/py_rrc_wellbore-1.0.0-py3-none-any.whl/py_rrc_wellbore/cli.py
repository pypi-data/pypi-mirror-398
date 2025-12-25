import typer

app = typer.Typer()

@app.command()
def main():
    """
    Console script for py_rrc_wellbore.
    """
    typer.echo("Replace this message by putting your code into py_rrc_wellbore.cli.main")

if __name__ == "__main__":
    app()
