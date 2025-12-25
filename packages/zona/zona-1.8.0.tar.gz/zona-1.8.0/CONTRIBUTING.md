# Contributing

Zona's upstream repository is hosted on [git.ficd.sh](https://git.ficd.sh),
which is a self-hosted Forgejo instance. The server does **not** have open
registration. (preferred)

I'm _very_ unlikely to create an account for people I don't know, so
contributing via email is preferred. If you're new to this workflow, check out
[get-send-email.io](https://git-send-email.io/) for a friendly tutorial.

Please send your patches to [daniel@ficd.sh](mailto:daniel@ficd.sh), and prefix
the subject line with `[zona] [PATCH]`. I will review your patch and respond
over email. You'll be notified if your patch is applied, and whether I've made
changes to it.

## Environment

Zona uses [`uv`](https://docs.astral.sh/uv/) to manage the Python environment.
After cloning the project, you can use `uv sync` to set it up.
`uv run zona <args>` runs the development version. It shouldn't conflict with
the globally installed version.

We also use the [`just`](https://just.systems/man/en/) command runner for
convenience. Please check `just --list` to see the available recipes.

## Docker

The Dockerfile and associated `just` recipes are for the CI image, meant for
linting, building, and releasing Zona. Zona is **not** pre-installed, and the
repository must be cloned _inside_ the image.

## Linting

Please use the `ruff` configuration defined in
[`pyproject.toml`](./pyproject.toml) to enforce consistent style. Also take care
that the `basedpyright` check passes. I recommend using `just` to run the lint
recipe: `just lint`.
