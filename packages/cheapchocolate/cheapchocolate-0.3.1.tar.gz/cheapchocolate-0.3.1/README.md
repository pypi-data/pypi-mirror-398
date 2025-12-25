# 🍫 cheapchocolate v0.3.1

CheapChocolate is an simple imap client to receive you daily email.


## Installation

You can install directly in your `pip`:
```shell
pip install cheapchocolate
```

I recomend to use the [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer), so you can just use the command bellow and everything is installed:
```shell
uv add cheapchocolate
uv run cheapchocolate --version
```

But you can use everything as a tool, for example:
```shell
uvx cheapchocolate --version
```

## How to use

Set up your information in the `.env` file for your imap server, your user and password.
```shell
cheapchocolate start
```
> You can run `cheapchocolate start`, and it will create the file for you.

## See Also

- Github: https://github.com/bouli/cheapchocolate
- PyPI: https://pypi.org/project/cheapchocolate/

## License
This package is distributed under the [MIT license](https://opensource.org/license/MIT).
