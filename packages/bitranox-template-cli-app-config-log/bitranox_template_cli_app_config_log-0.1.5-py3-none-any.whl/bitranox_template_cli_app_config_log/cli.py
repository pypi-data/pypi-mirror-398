"""CLI adapter wiring the behavior helpers into a rich-click interface.

Exposes a stable command-line surface so tooling, documentation, and packaging
automation can be exercised while the richer logging helpers are being built.
By delegating to :mod:`bitranox_template_cli_app_config_log.behaviors` the transport stays
aligned with the Clean Code rules captured in
``docs/systemdesign/module_reference.md``.

This module contains:
    - :data:`CLICK_CONTEXT_SETTINGS`: shared Click settings ensuring consistent
      ``--help`` behavior across commands.
    - :func:`apply_traceback_preferences`: helper that synchronises the shared
      traceback configuration flags.
    - :func:`snapshot_traceback_state` / :func:`restore_traceback_state`: utilities
      for preserving and reapplying the global traceback preference.
    - :func:`cli`: root command group wiring the global options.
    - :func:`cli_main`: default action when no subcommand is provided.
    - :func:`cli_info`, :func:`cli_hello`, :func:`cli_fail`: subcommands covering
      metadata printing, success path, and failure path.
    - :func:`main`: composition helper delegating to ``lib_cli_exit_tools`` while
      honouring the shared traceback preferences.

Note:
    The CLI is the primary adapter for local development workflows; packaging
    targets register the console script defined in
    :mod:`bitranox_template_cli_app_config_log.__init__conf__`. Other transports
    (including ``python -m`` execution) reuse the same helpers so behaviour
    remains consistent regardless of entry point.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Final, Sequence

import rich_click as click

import lib_cli_exit_tools
import lib_log_rich.runtime
from click.core import ParameterSource
from lib_layered_config import Config

from . import __init__conf__
from .behaviors import emit_greeting, noop_main, raise_intentional_failure
from .config import get_config
from .config_deploy import deploy_configuration
from .config_show import display_config
from .enums import DeployTarget, OutputFormat
from .logging_setup import init_logging

#: Shared Click context flags so help output stays consistent across commands.
CLICK_CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}  # noqa: C408
#: Character budget used when printing truncated tracebacks.
TRACEBACK_SUMMARY_LIMIT: Final[int] = 500
#: Character budget used when verbose tracebacks are enabled.
TRACEBACK_VERBOSE_LIMIT: Final[int] = 10_000


@dataclass(frozen=True, slots=True)
class TracebackState:
    """Immutable snapshot of traceback configuration.

    Attributes:
        traceback_enabled: Whether verbose tracebacks are active.
        force_color: Whether color output is forced for tracebacks.
    """

    traceback_enabled: bool
    force_color: bool


@dataclass(slots=True)
class CliContext:
    """Typed context object for Click commands.

    Replaces untyped dict-based context with a structured dataclass,
    providing type safety for CLI state management.

    Attributes:
        traceback: Whether verbose tracebacks were requested.
        profile: Configuration profile name for environment isolation.
        config: Loaded layered configuration object for all subcommands.
    """

    traceback: bool = False
    profile: str | None = None
    config: Config | None = field(default=None)


logger = logging.getLogger(__name__)


def apply_traceback_preferences(enabled: bool) -> None:
    """Synchronise shared traceback flags with the requested preference.

    ``lib_cli_exit_tools`` inspects global flags to decide whether tracebacks
    should be truncated and whether colour should be forced. Updating both
    attributes together ensures the ``--traceback`` flag behaves the same for
    console scripts and ``python -m`` execution.

    Args:
        enabled: ``True`` enables full tracebacks with colour. ``False`` restores
            the compact summary mode.

    Example:
        >>> apply_traceback_preferences(True)
        >>> bool(lib_cli_exit_tools.config.traceback)
        True
        >>> bool(lib_cli_exit_tools.config.traceback_force_color)
        True
    """
    lib_cli_exit_tools.config.traceback = bool(enabled)
    lib_cli_exit_tools.config.traceback_force_color = bool(enabled)


def snapshot_traceback_state() -> TracebackState:
    """Capture the current traceback configuration for later restoration.

    Returns:
        TracebackState dataclass with current configuration.

    Example:
        >>> snapshot = snapshot_traceback_state()
        >>> isinstance(snapshot, TracebackState)
        True
    """
    return TracebackState(
        traceback_enabled=bool(getattr(lib_cli_exit_tools.config, "traceback", False)),
        force_color=bool(getattr(lib_cli_exit_tools.config, "traceback_force_color", False)),
    )


def restore_traceback_state(state: TracebackState) -> None:
    """Reapply a previously captured traceback configuration.

    Args:
        state: TracebackState dataclass returned by :func:`snapshot_traceback_state`.

    Example:
        >>> prev = snapshot_traceback_state()
        >>> apply_traceback_preferences(True)
        >>> restore_traceback_state(prev)
        >>> snapshot_traceback_state() == prev
        True
    """
    lib_cli_exit_tools.config.traceback = state.traceback_enabled
    lib_cli_exit_tools.config.traceback_force_color = state.force_color


def _store_cli_context(
    ctx: click.Context,
    *,
    traceback: bool,
    config: Config,
    profile: str | None = None,
) -> None:
    """Store CLI state in the Click context for subcommand access.

    Args:
        ctx: Click context associated with the current invocation.
        traceback: Whether verbose tracebacks were requested.
        config: Loaded layered configuration object for all subcommands.
        profile: Optional configuration profile name for environment isolation.
    """
    if isinstance(ctx.obj, CliContext):
        ctx.obj.traceback = traceback
        ctx.obj.profile = profile
        ctx.obj.config = config
    else:
        ctx.obj = CliContext(traceback=traceback, profile=profile, config=config)


def _run_cli(argv: Sequence[str] | None) -> int:
    """Execute the CLI via lib_cli_exit_tools with exception handling.

    Args:
        argv: Optional sequence of CLI arguments. None uses sys.argv.

    Returns:
        Exit code produced by the command.
    """
    try:
        return lib_cli_exit_tools.run_cli(
            cli,
            argv=list(argv) if argv is not None else None,
            prog_name=__init__conf__.shell_command,
        )
    except BaseException as exc:  # noqa: BLE001 - handled by shared printers
        tracebacks_enabled = bool(getattr(lib_cli_exit_tools.config, "traceback", False))
        apply_traceback_preferences(tracebacks_enabled)
        length_limit = TRACEBACK_VERBOSE_LIMIT if tracebacks_enabled else TRACEBACK_SUMMARY_LIMIT
        lib_cli_exit_tools.print_exception_message(trace_back=tracebacks_enabled, length_limit=length_limit)
        return lib_cli_exit_tools.get_system_exit_code(exc)


@click.group(
    help=__init__conf__.title,
    context_settings=CLICK_CONTEXT_SETTINGS,
    invoke_without_command=True,
)
@click.version_option(
    version=__init__conf__.version,
    prog_name=__init__conf__.shell_command,
    message=f"{__init__conf__.shell_command} version {__init__conf__.version}",
)
@click.option(
    "--traceback/--no-traceback",
    is_flag=True,
    default=False,
    help="Show full Python traceback on errors",
)
@click.option(
    "--profile",
    type=str,
    default=None,
    help="Load configuration from a named profile (e.g., 'production', 'test')",
)
@click.pass_context
def cli(ctx: click.Context, traceback: bool, profile: str | None) -> None:
    """Root command storing global flags and syncing shared traceback state.

    Loads configuration once with the profile and stores it in the Click context
    for all subcommands to access. Mirrors the traceback flag into
    ``lib_cli_exit_tools.config`` so downstream helpers observe the preference.

    Example:
        >>> from click.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(cli, ["hello"])
        >>> result.exit_code
        0
        >>> "Hello World" in result.output
        True
    """
    config = get_config(profile=profile)
    init_logging(config)
    _store_cli_context(ctx, traceback=traceback, config=config, profile=profile)
    apply_traceback_preferences(traceback)

    if ctx.invoked_subcommand is None:
        # No subcommand: show help unless --traceback was explicitly passed
        source = ctx.get_parameter_source("traceback")
        if source not in (ParameterSource.DEFAULT, None):
            cli_main()
        else:
            click.echo(ctx.get_help())


def cli_main() -> None:
    """Run the placeholder domain entry when callers opt into execution.

    Maintains compatibility with tooling that expects the original
    "do-nothing" behaviour by explicitly opting in via options (e.g.
    ``--traceback`` without subcommands).

    Note:
        Delegates to :func:`noop_main`.

    Example:
        >>> cli_main()
    """
    noop_main()


@cli.command("info", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_info() -> None:
    """Print resolved metadata so users can inspect installation details."""
    with lib_log_rich.runtime.bind(job_id="cli-info", extra={"command": "info"}):
        logger.info("Displaying package information")
        __init__conf__.print_info()


@cli.command("hello", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_hello() -> None:
    """Demonstrate the success path by emitting the canonical greeting."""
    with lib_log_rich.runtime.bind(job_id="cli-hello", extra={"command": "hello"}):
        logger.info("Executing hello command")
        emit_greeting()


@cli.command("fail", context_settings=CLICK_CONTEXT_SETTINGS)
def cli_fail() -> None:
    """Trigger the intentional failure helper to test error handling."""
    with lib_log_rich.runtime.bind(job_id="cli-fail", extra={"command": "fail"}):
        logger.warning("Executing intentional failure command")
        raise_intentional_failure()


@cli.command("config", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option(
    "--format",
    type=click.Choice([f.value for f in OutputFormat], case_sensitive=False),
    default=OutputFormat.HUMAN.value,
    help="Output format (human-readable or JSON)",
)
@click.option(
    "--section",
    type=str,
    default=None,
    help="Show only a specific configuration section (e.g., 'lib_log_rich')",
)
@click.option(
    "--profile",
    type=str,
    default=None,
    help="Override profile from root command (e.g., 'production', 'test')",
)
@click.pass_context
def cli_config(ctx: click.Context, format: str, section: str | None, profile: str | None) -> None:
    """Display the current merged configuration from all sources.

    Shows configuration loaded from:
    - Default config (built-in)
    - Application config (/etc/xdg/bitranox-template-cli-app-config-log/config.toml)
    - User config (~/.config/bitranox-template-cli-app-config-log/config.toml)
    - .env files
    - Environment variables (BITRANOX_TEMPLATE_CLI_APP_CONFIG_LOG_*)

    Precedence: defaults → app → host → user → dotenv → env

    When --profile is specified (at root or here), configuration is loaded from
    profile-specific subdirectories (e.g., ~/.config/slug/profile/<name>/config.toml).
    """
    # Use config from context; reload if profile override specified
    if profile:
        config = get_config(profile=profile)
        effective_profile = profile
    else:
        config = ctx.obj.config if isinstance(ctx.obj, CliContext) and ctx.obj.config else get_config()
        effective_profile = ctx.obj.profile if isinstance(ctx.obj, CliContext) else None

    output_format = OutputFormat(format.lower())
    extra = {"command": "config", "format": output_format.value, "profile": effective_profile}
    with lib_log_rich.runtime.bind(job_id="cli-config", extra=extra):
        # Skip info logging for JSON format to keep output machine-parseable
        if output_format != OutputFormat.JSON:
            logger.info("Displaying configuration", extra={"format": output_format.value, "section": section, "profile": effective_profile})
        display_config(config, format=output_format, section=section)


@cli.command("config-deploy", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option(
    "--target",
    "targets",
    type=click.Choice([t.value for t in DeployTarget], case_sensitive=False),
    multiple=True,
    required=True,
    help="Target configuration layer(s) to deploy to (can specify multiple)",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing configuration files",
)
@click.option(
    "--profile",
    type=str,
    default=None,
    help="Override profile from root command (e.g., 'production', 'test')",
)
@click.pass_context
def cli_config_deploy(ctx: click.Context, targets: tuple[str, ...], force: bool, profile: str | None) -> None:
    r"""Deploy default configuration to system or user directories.

    Creates configuration files in platform-specific locations:

    \b
    - app:  System-wide application config (requires privileges)
    - host: System-wide host config (requires privileges)
    - user: User-specific config (~/.config on Linux)

    By default, existing files are not overwritten. Use --force to overwrite.

    When --profile is specified (at root or here), configuration is deployed to
    profile-specific subdirectories (e.g., ~/.config/slug/profile/<name>/config.toml).

    Examples:
        \b
        # Deploy to user config directory
        $ bitranox-template-cli-app-config-log config-deploy --target user

        \b
        # Deploy to both app and user directories
        $ bitranox-template-cli-app-config-log config-deploy --target app --target user

        \b
        # Force overwrite existing config
        $ bitranox-template-cli-app-config-log config-deploy --target user --force

        \b
        # Deploy to production profile
        $ bitranox-template-cli-app-config-log config-deploy --target user --profile production
    """
    # Use subcommand profile if provided, otherwise fall back to root profile
    effective_profile = profile or (ctx.obj.profile if isinstance(ctx.obj, CliContext) else None)
    deploy_targets = tuple(DeployTarget(t.lower()) for t in targets)
    target_values = tuple(t.value for t in deploy_targets)
    extra = {"command": "config-deploy", "targets": target_values, "force": force, "profile": effective_profile}
    with lib_log_rich.runtime.bind(job_id="cli-config-deploy", extra=extra):
        logger.info("Deploying configuration", extra={"targets": target_values, "force": force, "profile": effective_profile})

        try:
            deployed_paths = deploy_configuration(targets=deploy_targets, force=force, profile=effective_profile)

            if deployed_paths:
                profile_msg = f" (profile: {effective_profile})" if effective_profile else ""
                click.echo(f"\nConfiguration deployed successfully{profile_msg}:")
                for path in deployed_paths:
                    click.echo(f"  ✓ {path}")
            else:
                click.echo("\nNo files were created (all target files already exist).")
                click.echo("Use --force to overwrite existing configuration files.")

        except PermissionError as exc:
            logger.error("Permission denied when deploying configuration", extra={"error": str(exc)})
            click.echo(f"\nError: Permission denied. {exc}", err=True)
            click.echo("Hint: System-wide deployment (--target app/host) may require sudo.", err=True)
            raise SystemExit(1)
        except Exception as exc:
            logger.error("Failed to deploy configuration", extra={"error": str(exc), "error_type": type(exc).__name__})
            click.echo(f"\nError: Failed to deploy configuration: {exc}", err=True)
            raise SystemExit(1)


def main(argv: Sequence[str] | None = None, *, restore_traceback: bool = True) -> int:
    """Execute the CLI with error handling and return the exit code.

    Provides the single entry point used by console scripts and
    ``python -m`` execution so that behaviour stays identical across transports.

    Args:
        argv: Optional sequence of CLI arguments. None uses sys.argv.
        restore_traceback: Whether to restore prior traceback configuration after execution.

    Returns:
        Exit code reported by the CLI run.
    """
    previous_state = snapshot_traceback_state()
    try:
        return _run_cli(argv)
    finally:
        if restore_traceback:
            restore_traceback_state(previous_state)
        if lib_log_rich.runtime.is_initialised():
            lib_log_rich.runtime.shutdown()
