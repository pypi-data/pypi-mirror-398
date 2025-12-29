# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The entry point of the ElSabio CLI."""

# Standard library
from pathlib import Path

# Third party
import click

# Local
from elsabio.cli.core import Obj, exit_program
from elsabio.cli.tariff_analyzer.core import tariff_analyzer
from elsabio.config import LogHanderType, load_config
from elsabio.database import create_session_factory
from elsabio.exceptions import ConfigError
from elsabio.log import setup_logging
from elsabio.metadata import __releasedate__


@click.group(
    name='elsabio',
    context_settings={'help_option_names': ['-h', '--help'], 'max_content_width': 1000},
)
@click.option(
    '--config',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        resolve_path=True,
        path_type=Path,
    ),
    show_default=True,
    help=(
        'The path to the configuration file. If not specified the configuration will be loaded '
        'from these sources in descending order of relevance: '
        '1. stdin. '
        '2. A config file specified in environment variable ELSABIO_CONFIG_FILE. '
        '3. From the default config file location "~/.config/ElSabio/ElSabio.toml". '
        '4. From the secrets file specified in environment variable ELSABIO_SECRETS_FILE.'
    ),
)
@click.version_option(
    message=(
        f'%(prog)s, version: %(version)s, release date: {__releasedate__}, maintainer: Anton Lydell'
    )
)
@click.pass_context
def main(ctx: click.Context, config: Path | None) -> None:
    r"""Manage the ElSabio application"""

    ctx.ensure_object(dict)

    try:
        cm = load_config(path=config if config is None else config.expanduser().resolve())
    except ConfigError as e:
        error_msg = f'Error loading configuration!\n{e!s}'
        exit_program(error=True, ctx=ctx, message=error_msg)
    else:
        ctx.obj[Obj.CONFIG] = cm

    setup_logging(config=cm.logging, exclude={LogHanderType.FILE: ('web',)})

    db_cfg = cm.database
    ctx.obj[Obj.SESSION_FACTORY] = create_session_factory(
        url=db_cfg.url,
        autoflush=db_cfg.autoflush,
        expire_on_commit=db_cfg.expire_on_commit,
        create_database=False,
        connect_args=db_cfg.connect_args,
        **db_cfg.engine_config,
    )


for cmd in (tariff_analyzer,):
    main.add_command(cmd)

if __name__ == '__main__':
    main()
