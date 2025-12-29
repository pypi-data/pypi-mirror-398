# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The CLI `elsabio-web` is used to launch the ElSabio web application."""

# Standard library
import os
import subprocess
from pathlib import Path

# Third party
import click

# Local
from elsabio import __releasedate__
from elsabio.app._pages import Pages
from elsabio.config import CONFIG_FILE_ENV_VAR


@click.command(
    name='elsabio-web',
    context_settings={
        'help_option_names': ['-h', '--help'],
        'max_content_width': 1000,
        'ignore_unknown_options': True,
    },
)
@click.option(
    '--page',
    '-p',
    type=click.Choice([p.name for p in Pages], case_sensitive=False),
    help='Run a specific page of the app. If not specified the main application is run.',
)
@click.option(
    '--config',
    '-c',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True, path_type=Path),
    help=(
        'The ElSabio config file to use with the application. If specified it will override '
        'the environment variable ELSABIO_CONFIG_FILE. Useful if a specific page should be '
        'run with a different config file from the main application.'
    ),
)
@click.argument('streamlit_options', nargs=-1, type=click.UNPROCESSED)
@click.version_option(
    message=(
        f'%(prog)s, version: %(version)s, release date: {__releasedate__}, maintainer: Anton Lydell'
    )
)
def main(page: str, config: Path, streamlit_options: tuple[str, ...]) -> None:
    """Run the ElSabio Streamlit app.

    \b
    Configuring Streamlit
    ---------------------
    Streamlit can be configured with config files, environment variables or command line options.
    Below is a list of the configuration options in order in which they will override each
    other:

    1 : Command line options.

    2 : Environment variables with names of the config options prefixed by STREAMLIT, e.g. STREAMLIT_SERVER_PORT

    3 : A local config file located in the current working directory at "./.streamlit/config.toml".

    4 : A global config file located in the user's home directory at: "~/.streamlit/config.toml"

    See also the Streamlit documentation on configuration for more details:
    https://docs.streamlit.io/library/advanced-features/configuration#view-all-configuration-options

    \b
    Examples
    --------
    Initialize the ElSabio database and create an admin user:
        $ elsabio-web --page init

    \b
    Run the ElSabio main app and pass on command line options to Streamlit:
        $ elsabio-web --theme.base dark --server.headless true
    """

    root_path = Path(__file__).parent
    path = str(root_path / Pages[page]) if page else str(root_path / 'main.py')

    if config:
        os.environ[CONFIG_FILE_ENV_VAR] = str(config.expanduser())

    run_cmd = ['python', '-m', 'streamlit', 'run', path]
    run_cmd.extend(streamlit_options)

    click.echo('Launching Streamlit ...')
    subprocess.run(run_cmd)  # noqa: S603, PLW1510


if __name__ == '__main__':
    main()
