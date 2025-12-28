#!/usr/bin/env python
# Copyright (C) 2025 Tasos Alvas <tasos.alvas@qwertyuiopia.com>
# SPDX-License-Identifier: AGPL-3.0-or-later
"""SpdIU Download and installation tasks."""

import json
import shutil

import urllib.request
from zipfile import ZipFile, BadZipFile

from invoke import task, Collection

from .. import util
from ..util import path


ns = Collection("get")


# Github-related methods and tasks
def github_json(c, target=None):
    """Query the Github API for a project."""
    try:
        cfg = c.config.spdiu
        api_url = f"https://api.github.com/repos/{cfg.release.project}"

        if target:
            api_url += "/" + target

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Shattered Pixel Dungeon Invoke Utility",
        }
        req = urllib.request.Request(api_url, headers=headers)

        with urllib.request.urlopen(req) as r:
            response = json.loads(r.read().decode("utf-8"))

        return response

    except Exception as e:
        print(f"Github API Error: {e}")
        return []


def print_package(c, release: dict):
    """Print package information for a dict returned by strip_release."""
    cfg = c.config.spdiu

    title = f"{cfg.i.package} Latest package from {cfg.release.project}"

    print("\n|||>" + (len(title) - 6) * "-" + "<|||")
    print(title)
    print(f"  Tag name: {release['tag_name']}")
    print(f"  Name: {release['name']}")
    print(f"  Published at: {release['published_at']}")

    # Single package available
    if release.get("package"):
        print(f"{cfg.i.package} Link for {release['package']} discovered.")

    elif type(release["download"]) is list:
        print("Multiple candidates available:")
        for p in release["download"]:
            print(f"{cfg.i.package} {p}")

    else:
        print("No appropriate download link detected.")


def strip_release(c, release_json, silent=False):
    """Grab the values we care about from a Github API response.

    Returns a dict of "name", "tag_name", "published_at", "download", "package".

    The "download" key can be "", a list of urls, or an unambiguous url.
    A "package" key is only set if there is an unambiguous single package.
    """
    cfg = c.config.spdiu

    fields = ("name", "tag_name", "published_at")
    summary = {k: release_json[k] for k in fields}

    # filter links by any relevant values i    Accepts a regular en config until one is left.
    links = [i["browser_download_url"] for i in release_json["assets"]]
    wants = (
        cfg.release.extension,
        cfg.release.platform,
        cfg.release.version,
        cfg.release.tag_name,
    )

    download = ""
    for condition in [i for i in wants if i is not None]:
        links = [i for i in links if condition in i]

        if len(links) == 1:
            download = links[0]
            summary["download"] = download
            summary["package"] = download.split("/")[-1]
            return summary

    summary["download"] = links
    return summary


@task
def latest(c):
    """Get information on the latest release from the Github API.

    Prints what it discovers to the terminal, and returns a package dict.
    """
    cfg = c.config.spdiu
    if not cfg.release.gh_use_api:
        print("Can't get latest releases without the project's github info.")
        print("Use release_template to configure the installation instead.")
        return []

    package = strip_release(c, github_json(c, "releases/latest"))

    print_package(c, package)
    return package


@task
def releases(c, search=""):
    """List releases. -s, --search to filter results that match it.

    Looks for a supplied pattern in the asset download urls of each release,
    and filters the result to only the releases containing links that match.

    TODO: Currently only gets one page, pagination planned.
    """
    cfg = c.config.spdiu

    if not cfg.release.gh_use_api:
        print("Can't get latest releases without the project's github info.")
        print("Use release_template to configure the installation instead.")
        return []

    r_data = github_json(c, "releases")

    result = []
    for r in r_data:
        found = False
        for asset in r.get("assets", []):
            if search in asset["browser_download_url"]:
                found = True

        if found:
            result.append(strip_release(c, r))

    matching = f' matching pattern "{search}"' if search else ""
    print(f"{len(result)} {cfg.i.int}, releases found{matching}")

    for package in result:
        print_package(c, package)

    return result


@task
def install(c, version=None):
    """Download the game and install it. 'siu -h' this for more options.

    -v, --version [release] to request a version.
    If a version is not supplied and not pinned in config, it gets the latest.

    See spdiu.yaml.example for configuring the task to download different SPD forks.
    """
    cfg = c.config.spdiu
    version = version if version else cfg.release.version
    platform = cfg.release.platform
    ext = cfg.release.extension

    packages = path(c, cfg.dirs.package)
    packages.mkdir(parents=True, exist_ok=True)

    install_path = path(c, cfg.dirs.game)

    # Get latest from gh
    if cfg.release.gh_use_api and not version:
        rel = latest(c)
        d_url = rel["download"]
        d_name = rel["package"]

    # Get a version from gh
    elif cfg.release.gh_use_api:
        rel = releases(c, version)

        if len(rel) == 1:
            d_url = rel[0]["download"]
            d_name = rel[0]["package"]

        elif not rel:
            print(f'No matches found for "{version}"')
            return

        else:
            print("Multiple matches found, please narrow your search terms")
            return

    # Manually generate a download link from release_template.
    else:
        print(f"{cfg.i.str} Project is not hosted on github, templating manually:")
        # Don't put arbitrary code in your user config, mkay?
        tpl = cfg.release.template

        tag_name = cfg.release.tag_name  # noqa: F841
        project = cfg.release.project  # noqa: F841

        d_url = eval('f"' + tpl + '"')
        d_name = d_url.split("/")[-1]
        print(d_url)

    package_path = packages / d_name

    # Get ready to download
    def progress_hook(blocks, block_size, total):
        current_mb = blocks * block_size / 1024**2
        total_mb = total / 1024**2
        percentage = current_mb / total_mb

        chars = 30
        full = int(chars * percentage) * "="
        bar = full.ljust(chars, "-")

        print(f" |>{bar}<| {current_mb:.2f}MB out of {total_mb:.2f}MB", end="\r")

    # Downloading
    if package_path.exists():
        print(f"{d_name} already exists in {cfg.dirs.package}.")

    elif ext == "jar" and (install_path / d_name).exists():
        print("This jar file is already installed, nothing to do.")
        return

    else:
        print(f"Downloading {d_name}...")

        try:
            urllib.request.urlretrieve(d_url, package_path, progress_hook)

        except urllib.error.HTTPError:
            print(f"404: {d_url} not found.")
            return

        except urllib.error.ContentTooShortError:
            package_path.unlink()
            print("Transfer failed, try again.")
            return

        print("Package downloaded. Great success!")

    # Pre-installation checks
    if install_path.exists():
        print("WARNING: Destination already exists.")
        print(install_path)

        delete_ok = input("Are you sure you want to delete it? (y/N)")
        if delete_ok.strip().lower() == "y":
            util.remove(install_path)

        else:
            print("Well, come back when you're ready.")
            return

    # Installation, varying by package
    print(f"Installing {d_name}...")
    install_path.mkdir(parents=True, exist_ok=True)

    if ext == "zip":
        with ZipFile(package_path, "r") as z:
            try:
                z.extractall(install_path)
                print("Zip package extracted to the game folder.")

            except BadZipFile:
                package_path.unlink()
                print("Zip file is unreadable. Removed it, try again.")

        # Python's zipfile doesn't preserve permissions when extracting
        if platform.lower() == "linux":
            binary = install_path / cfg.game.cmd
            binary.chmod(0o755)

    elif ext == "jar":
        shutil.move(package_path, install_path)
        print("Jar package copied to the game folder.")

    print(f"{d_name} was successfully installed. Have a nice day!")


ns.add_task(releases)
ns.add_task(latest)
ns.add_task(install)
