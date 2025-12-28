


import typer


app = typer.Typer()

@app.command()
def test():
    print("Hallo")