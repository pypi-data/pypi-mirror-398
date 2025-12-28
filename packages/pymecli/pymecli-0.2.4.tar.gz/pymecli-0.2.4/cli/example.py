import typer

app = typer.Typer()


@app.command()
def hello(
    name: str = typer.Argument(
        "from My CLI!",
        help="Name of the person to greet",
    ),
):
    print(f"Hello {name}!")


@app.command()
def goodbye(
    name: str = typer.Argument(
        "from My CLI!",
        help="Name of the person to goodbye",
    ),
    formal: bool = typer.Option(
        False,
        "--formal",
        "-f",
        help="是否为正式场合回答",
    ),
):
    if formal:
        print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        print(f"Bye {name}!")
