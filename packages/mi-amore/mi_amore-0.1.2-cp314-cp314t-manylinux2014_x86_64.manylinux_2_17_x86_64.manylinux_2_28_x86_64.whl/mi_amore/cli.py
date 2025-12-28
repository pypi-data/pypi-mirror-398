import typer

from mi_amore.minimize import minimize


app = typer.Typer()


@app.command()
def run(on_func: list[str]):
    cubes_on = []

    for input in on_func:
        cube = []
        for char in input:
            match char:
                case "1":
                    cube += [0, 1]
                case "0":
                    cube += [1, 0]
                case "-":
                    cube += [1, 1]
                case _:
                    raise ValueError(f"Invalid character {char} only 1, 0, - are allowed")

        cubes_on.append(cube)
    n_binary = len(on_func[0])
    result = minimize(n_binary, [], cubes_on, [[]], 0)

    for res in result:
        print(res)
