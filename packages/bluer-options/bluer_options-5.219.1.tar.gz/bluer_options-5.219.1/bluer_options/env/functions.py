from typing import Any
import os
from dotenv import load_dotenv

# https://chatgpt.com/c/683d39ac-34a8-8005-b780-71a6d2253ea9
try:
    from importlib.resources import files, as_file
except ImportError:
    # for Python < 3.9
    from importlib_resources import files, as_file


def get_env(name: str, default: Any = "") -> Any:
    output = os.getenv(
        name,
        default,
    )

    if isinstance(default, bool):
        return output == "1"

    # order is critical
    for output_type in [int, float]:
        if isinstance(default, output_type):
            try:
                return output_type(output)
            except:
                return default

    return output


def load_config(
    package_name: str,
    verbose: bool = False,
):
    if "." in package_name:
        package_name = package_name.split(".")[0]

    resource = files(package_name).joinpath("config.env")
    with as_file(resource) as env_filename:
        if verbose:
            print(f"loading {env_filename}.")

        assert load_dotenv(
            env_filename
        ), f"package_name: {package_name}, env_filename: {env_filename}"


def load_env(
    package_name: str,
    verbose: bool = False,
):
    if "." in package_name:
        package_name = package_name.split(".")[0]

    with as_file(files(package_name)) as package_path:
        env_filename = os.path.join(
            os.path.dirname(package_path),
            ".env",
        )

        if verbose:
            print(f"loading {env_filename}.")

        load_dotenv(env_filename)
