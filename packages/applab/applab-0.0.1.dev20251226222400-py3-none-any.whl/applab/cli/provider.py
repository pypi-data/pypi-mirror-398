from cyclopts import App

provider_app = App(name="provider")


@provider_app.command
def ls(path, url):
    """
    This entire sentence
    is part of the short description and will
    have all the newlines removed.

    This is the beginning of the long description.


    """
    print(f"Downloading {url} to {path}.")


@provider_app.command
def info(path, url):
    """Upload a file."""
    print(f"Downloading {url} to {path}.")


@provider_app.command
def login(path, url):
    """Upload a file."""
    print(f"Downloading {url} to {path}.")
