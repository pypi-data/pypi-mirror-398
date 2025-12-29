"""CLI adapter wiring the behavior helpers into a rich-click interface.

Expose a stable command-line surface so tooling, documentation, and packaging
automation can be exercised while the richer logging helpers are being built.

Contents:
    * :data:`CLICK_CONTEXT_SETTINGS` – shared Click settings.
    * :func:`apply_traceback_preferences` – synchronises traceback configuration.
    * :func:`snapshot_traceback_state` / :func:`restore_traceback_state` – state management.
    * :func:`cli` – root command group wiring global options.
    * :func:`main` – entry point for console scripts and ``python -m`` execution.

System Role:
    The CLI is the primary adapter for local development workflows; packaging
    targets register the console script defined in :mod:`bitranox_template_cli_app_config_log_mail.__init__conf__`.
"""

from __future__ import annotations

import logging
from typing import Final, Optional, Sequence, Tuple

import rich_click as click
from lib_layered_config import Config

import lib_cli_exit_tools
import lib_log_rich.runtime
from click.core import ParameterSource

from . import __init__conf__
from .behaviors import emit_greeting, noop_main, raise_intentional_failure
from .config import get_config
from .config_deploy import deploy_configuration
from .config_show import display_config
from .enums import DeployTarget, OutputFormat
from .logging_setup import init_logging
from .mail import EmailConfig, load_email_config_from_dict, send_email, send_notification

#: Shared Click context flags so help output stays consistent across commands.
CLICK_CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}  # noqa: C408
#: Character budget used when printing truncated tracebacks.
TRACEBACK_SUMMARY_LIMIT: Final[int] = 500
#: Character budget used when verbose tracebacks are enabled.
TRACEBACK_VERBOSE_LIMIT: Final[int] = 10_000
TracebackState = Tuple[bool, bool]

logger = logging.getLogger(__name__)


def apply_traceback_preferences(enabled: bool) -> None:
    """Synchronise shared traceback flags with the requested preference.

    Args:
        enabled: ``True`` enables full tracebacks with colour.

    Example:
        >>> apply_traceback_preferences(True)
        >>> bool(lib_cli_exit_tools.config.traceback)
        True
    """
    lib_cli_exit_tools.config.traceback = bool(enabled)
    lib_cli_exit_tools.config.traceback_force_color = bool(enabled)


def snapshot_traceback_state() -> TracebackState:
    """Capture the current traceback configuration for later restoration.

    Returns:
        Tuple of ``(traceback_enabled, force_color)``.
    """
    return (
        bool(getattr(lib_cli_exit_tools.config, "traceback", False)),
        bool(getattr(lib_cli_exit_tools.config, "traceback_force_color", False)),
    )


def restore_traceback_state(state: TracebackState) -> None:
    """Reapply a previously captured traceback configuration.

    Args:
        state: Tuple returned by :func:`snapshot_traceback_state`.
    """
    lib_cli_exit_tools.config.traceback = bool(state[0])
    lib_cli_exit_tools.config.traceback_force_color = bool(state[1])


def _store_cli_context(
    ctx: click.Context,
    *,
    traceback: bool,
    config: Config,
    profile: Optional[str] = None,
) -> None:
    """Store CLI state in the Click context for subcommand access.

    Args:
        ctx: Click context associated with the current invocation.
        traceback: Whether verbose tracebacks were requested.
        config: Loaded layered configuration object for all subcommands.
        profile: Optional configuration profile name.
    """
    ctx.ensure_object(dict)
    ctx.obj["traceback"] = traceback
    ctx.obj["config"] = config
    ctx.obj["profile"] = profile


def _run_cli(argv: Optional[Sequence[str]]) -> int:
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
def cli(ctx: click.Context, traceback: bool, profile: Optional[str]) -> None:
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
    """Run the placeholder domain entry when callers opt into execution."""
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
def cli_config(ctx: click.Context, format: str, section: Optional[str], profile: Optional[str]) -> None:
    """Display the current merged configuration from all sources.

    Shows configuration loaded from defaults, application/user config files,
    .env files, and environment variables.

    Precedence: defaults -> app -> host -> user -> dotenv -> env
    """
    # Use config from context; reload if profile override specified
    if profile:
        config = get_config(profile=profile)
        effective_profile = profile
    else:
        config = ctx.obj["config"]
        effective_profile = ctx.obj.get("profile")

    output_format = OutputFormat(format.lower())
    extra = {"command": "config", "format": output_format.value, "profile": effective_profile}
    with lib_log_rich.runtime.bind(job_id="cli-config", extra=extra):
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
def cli_config_deploy(ctx: click.Context, targets: tuple[str, ...], force: bool, profile: Optional[str]) -> None:
    r"""Deploy default configuration to system or user directories.

    Creates configuration files in platform-specific locations:

    \b
    - app:  System-wide application config (requires privileges)
    - host: System-wide host config (requires privileges)
    - user: User-specific config (~/.config on Linux)

    By default, existing files are not overwritten. Use --force to overwrite.
    """
    effective_profile = profile if profile else ctx.obj.get("profile")
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


def main(argv: Optional[Sequence[str]] = None, *, restore_traceback: bool = True) -> int:
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


# =============================================================================
# Email Commands
# =============================================================================


@cli.command("send-email", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option("--to", "recipients", multiple=True, required=True, help="Recipient email address (can specify multiple)")
@click.option("--subject", required=True, help="Email subject line")
@click.option("--body", default="", help="Plain-text email body")
@click.option("--body-html", default="", help="HTML email body (sent as multipart with plain text)")
@click.option("--from", "from_address", default=None, help="Override sender address (uses config default if not specified)")
@click.option("--attachment", "attachments", multiple=True, type=click.Path(exists=True, path_type=str), help="File to attach (can specify multiple)")
@click.pass_context
def cli_send_email(
    ctx: click.Context,
    recipients: tuple[str, ...],
    subject: str,
    body: str,
    body_html: str,
    from_address: Optional[str],
    attachments: tuple[str, ...],
) -> None:
    """Send an email using configured SMTP settings."""
    from pathlib import Path

    config: Config = ctx.obj["config"]

    with lib_log_rich.runtime.bind(job_id="cli-send-email", extra={"command": "send-email", "recipients": list(recipients), "subject": subject}):
        try:
            email_config = _load_and_validate_email_config(config)
            attachment_paths = [Path(p) for p in attachments] if attachments else None

            logger.info(
                "Sending email",
                extra={
                    "recipients": list(recipients),
                    "subject": subject,
                    "has_html": bool(body_html),
                    "attachment_count": len(attachments) if attachments else 0,
                },
            )

            result = send_email(
                config=email_config,
                recipients=list(recipients),
                subject=subject,
                body=body,
                body_html=body_html,
                from_address=from_address,
                attachments=attachment_paths,
            )

            if result:
                click.echo("\nEmail sent successfully!")
                logger.info("Email sent via CLI", extra={"recipients": list(recipients)})
            else:
                click.echo("\nEmail sending failed.", err=True)
                raise SystemExit(1)

        except ValueError as exc:
            logger.error("Invalid email parameters", extra={"error": str(exc)})
            click.echo(f"\nError: Invalid email parameters - {exc}", err=True)
            raise SystemExit(1)
        except FileNotFoundError as exc:
            logger.error("Attachment file not found", extra={"error": str(exc)})
            click.echo(f"\nError: Attachment file not found - {exc}", err=True)
            raise SystemExit(1)
        except RuntimeError as exc:
            logger.error("SMTP delivery failed", extra={"error": str(exc)})
            click.echo(f"\nError: Failed to send email - {exc}", err=True)
            raise SystemExit(1)
        except Exception as exc:
            logger.error("Unexpected error sending email", extra={"error": str(exc), "error_type": type(exc).__name__}, exc_info=True)
            click.echo(f"\nError: Unexpected error - {exc}", err=True)
            raise SystemExit(1)


@cli.command("send-notification", context_settings=CLICK_CONTEXT_SETTINGS)
@click.option("--to", "recipients", multiple=True, required=True, help="Recipient email address (can specify multiple)")
@click.option("--subject", required=True, help="Notification subject line")
@click.option("--message", required=True, help="Notification message (plain text)")
@click.pass_context
def cli_send_notification(
    ctx: click.Context,
    recipients: tuple[str, ...],
    subject: str,
    message: str,
) -> None:
    """Send a simple plain-text notification email."""
    config: Config = ctx.obj["config"]

    with lib_log_rich.runtime.bind(job_id="cli-send-notification", extra={"command": "send-notification", "recipients": list(recipients), "subject": subject}):
        try:
            email_config = _load_and_validate_email_config(config)

            logger.info("Sending notification", extra={"recipients": list(recipients), "subject": subject})

            result = send_notification(
                config=email_config,
                recipients=list(recipients),
                subject=subject,
                message=message,
            )

            if result:
                click.echo("\nNotification sent successfully!")
                logger.info("Notification sent via CLI", extra={"recipients": list(recipients)})
            else:
                click.echo("\nNotification sending failed.", err=True)
                raise SystemExit(1)

        except ValueError as exc:
            logger.error("Invalid notification parameters", extra={"error": str(exc)})
            click.echo(f"\nError: Invalid notification parameters - {exc}", err=True)
            raise SystemExit(1)
        except RuntimeError as exc:
            logger.error("SMTP delivery failed", extra={"error": str(exc)})
            click.echo(f"\nError: Failed to send notification - {exc}", err=True)
            raise SystemExit(1)
        except Exception as exc:
            logger.error("Unexpected error sending notification", extra={"error": str(exc), "error_type": type(exc).__name__}, exc_info=True)
            click.echo(f"\nError: Unexpected error - {exc}", err=True)
            raise SystemExit(1)


def _load_and_validate_email_config(config: Config) -> EmailConfig:
    """Extract and validate email config from the provided Config object.

    Args:
        config: Already-loaded layered configuration object.

    Returns:
        EmailConfig with validated SMTP configuration.

    Raises:
        SystemExit: When SMTP hosts are not configured (exit code 1).
    """
    email_config = load_email_config_from_dict(config.as_dict())

    if not email_config.smtp_hosts:
        logger.error("No SMTP hosts configured")
        click.echo("\nError: No SMTP hosts configured. Please configure email.smtp_hosts in your config file.", err=True)
        click.echo("See: bitranox-template-cli-app-config-log-mail config-deploy --target user", err=True)
        raise SystemExit(1)

    return email_config
