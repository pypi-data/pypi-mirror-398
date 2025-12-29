"""Nox file."""

import nox

nox.options.error_on_external_run = True
nox.options.default_venv_backend = "uv"


def uv_install(session: nox.Session) -> None:
    """Install dependencies using uv."""
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )


@nox.session(tags=["tests"])
def tests(session: nox.Session) -> None:
    """Testing."""
    uv_install(session)

    session.run("coverage", "run", "-m", "pytest")
    session.run("coverage", "report")


@nox.session(tags=["quality"])
def quality(session: nox.Session) -> None:
    """Quality checks."""
    uv_install(session)

    session.run(
        "ruff", "check", "src", "tests", "noxfile.py", "--fix", "--exit-non-zero-on-fix"
    )
    session.run("pyproject-fmt", "pyproject.toml")

    session.run("mypy", "src")
