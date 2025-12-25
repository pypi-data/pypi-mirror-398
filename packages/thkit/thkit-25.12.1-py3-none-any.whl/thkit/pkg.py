import importlib
import subprocess
import sys
from pathlib import Path

from thkit.markup import TextDecor


#####ANCHOR: Packages tools
def check_package(
    package_name: str,
    auto_install: bool = False,
    git_repo: str | None = None,
    conda_channel: str | None = None,
):
    """Check if the required packages are installed."""
    try:
        importlib.import_module(package_name)
    except ImportError:
        if auto_install:
            install_package(package_name, git_repo, conda_channel)
        else:
            raise ImportError(
                f"Required package `{package_name}` is not installed. Please install it.",
            )
    return


def install_package(
    package_name: str,
    git_repo: str | None = None,
    conda_channel: str | None = None,
) -> None:
    """Install the required package.

    Args:
        package_name (str): package name
        git_repo (str): git path for the package. Default: None. E.g., http://somthing.git
        conda_channel (str): conda channel for the package. Default: None. E.g., conda-forge

    Notes:
        - Default using: `pip install -U {package_name}`
        - If `git_repo` is provided: `pip install -U git+{git_repo}`
        - If `conda_channel` is provided: `conda install -c {conda_channel} {package_name}`
    """
    if git_repo:
        cmd = ["pip", "install", "-U", f"git+{git_repo}"]
    elif conda_channel:
        cmd = ["conda", "install", "-c", conda_channel, package_name, "-y"]
    else:
        cmd = ["pip", "install", "-U", package_name]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to install `{package_name}`: {e}")
    return


def dependency_info(packages=["numpy", "polars", "thkit", "ase"]) -> str:
    """Get the dependency information.

    Args:
        packages (list[str]): list of package names

    Note:
        Use `importlib` instead of `__import__` for clarity.
    """
    w = [12, 13, None]  # widths for formatting
    lines = [TextDecor(" Dependencies ").fill_center(fill="-", length=70)]
    for pkg in packages:
        try:
            mm = importlib.import_module(pkg)
            ver = getattr(mm, "__version__", "unknown").split("+")[0]
            path = getattr(mm, "__path__", ["unknown path"])[0]
            lines.append(f"{pkg:>{w[0]}}  {ver:<{w[1]}} {Path(path).as_posix()}")
        except ImportError:
            lines.append(f"{pkg:>{w[0]}}  {'unknown':<{w[1]}} ")
        except Exception:
            lines.append(f"{pkg:>{w[0]}}  {'':<{w[1]}} unknown version or path")
    ### Python version
    lines.append(
        f"{'python':>{w[0]}}  {sys.version.split(' ')[0]:<{w[1]}} {Path(sys.executable).as_posix()}"
    )
    return "\n".join(lines) + "\n"
