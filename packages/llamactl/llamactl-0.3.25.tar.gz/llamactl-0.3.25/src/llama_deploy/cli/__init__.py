import warnings

from llama_deploy.cli.commands.auth import auth
from llama_deploy.cli.commands.deployment import deployments
from llama_deploy.cli.commands.dev import dev
from llama_deploy.cli.commands.env import env_group
from llama_deploy.cli.commands.init import init
from llama_deploy.cli.commands.pkg import pkg
from llama_deploy.cli.commands.serve import serve

from .app import app

# Disable warnings in llamactl CLI, and specifically silence the Pydantic
# UnsupportedFieldAttributeWarning about `validate_default` on Field().
warnings.simplefilter("ignore")
warnings.filterwarnings(
    "ignore",
    message=r"The 'validate_default' attribute .* has no effect.*",
)


# Main entry point function (called by the script)
def main() -> None:
    app()


__all__ = [
    "app",
    "deployments",
    "auth",
    "serve",
    "init",
    "env_group",
    "pkg",
    "dev",
]


if __name__ == "__main__":
    app()
