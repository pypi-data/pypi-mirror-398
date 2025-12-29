"""CLI stories: every invocation a single beat."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Sequence
from typing import Any

import pytest
from click.testing import CliRunner, Result

import lib_cli_exit_tools

from bitranox_template_cli_app_config_log_mail import cli as cli_mod
from bitranox_template_cli_app_config_log_mail import __init__conf__


@dataclass(slots=True)
class CapturedRun:
    """Record of a single ``lib_cli_exit_tools.run_cli`` invocation.

    Attributes:
        command: Command object passed to ``run_cli``.
        argv: Argument vector forwarded to the command, when any.
        prog_name: Program name announced in the help output.
        signal_specs: Signal handlers registered by the runner.
        install_signals: ``True`` when the runner installed default signal handlers.
    """

    command: Any
    argv: Sequence[str] | None
    prog_name: str | None
    signal_specs: Any
    install_signals: bool


def _capture_run_cli(target: list[CapturedRun]) -> Callable[..., int]:
    """Return a stub that records lib_cli_exit_tools.run_cli invocations.

    Tests assert that the CLI delegates to lib_cli_exit_tools with the
    expected arguments; recording each call keeps those assertions readable.

    Args:
        target: Mutable list that will collect CapturedRun entries.

    Returns:
        Replacement callable for lib_cli_exit_tools.run_cli.
    """

    def _run(
        command: Any,
        argv: Sequence[str] | None = None,
        *,
        prog_name: str | None = None,
        signal_specs: Any = None,
        install_signals: bool = True,
    ) -> int:
        target.append(
            CapturedRun(
                command=command,
                argv=argv,
                prog_name=prog_name,
                signal_specs=signal_specs,
                install_signals=install_signals,
            )
        )
        return 42

    return _run


@pytest.mark.os_agnostic
def test_when_we_snapshot_traceback_the_initial_state_is_quiet(isolated_traceback_config: None) -> None:
    """Verify snapshot_traceback_state returns (False, False) initially."""
    assert cli_mod.snapshot_traceback_state() == (False, False)


@pytest.mark.os_agnostic
def test_when_we_enable_traceback_the_config_sings_true(isolated_traceback_config: None) -> None:
    """Verify apply_traceback_preferences enables traceback flags."""
    cli_mod.apply_traceback_preferences(True)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


@pytest.mark.os_agnostic
def test_when_we_restore_traceback_the_config_whispers_false(isolated_traceback_config: None) -> None:
    """Verify restore_traceback_state resets traceback flags to previous values."""
    previous = cli_mod.snapshot_traceback_state()
    cli_mod.apply_traceback_preferences(True)

    cli_mod.restore_traceback_state(previous)

    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_when_info_runs_with_traceback_the_choice_is_shared(
    monkeypatch: pytest.MonkeyPatch,
    isolated_traceback_config: None,
    preserve_traceback_state: None,
) -> None:
    """Verify traceback flag is active during info command then restored."""
    notes: list[tuple[bool, bool]] = []

    def record() -> None:
        notes.append(
            (
                lib_cli_exit_tools.config.traceback,
                lib_cli_exit_tools.config.traceback_force_color,
            )
        )

    monkeypatch.setattr(cli_mod.__init__conf__, "print_info", record)

    exit_code = cli_mod.main(["--traceback", "info"])

    assert exit_code == 0
    assert notes == [(True, True)]
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_when_main_is_called_it_delegates_to_run_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() delegates to lib_cli_exit_tools.run_cli with correct args."""
    ledger: list[CapturedRun] = []
    monkeypatch.setattr(lib_cli_exit_tools, "run_cli", _capture_run_cli(ledger))

    result = cli_mod.main(["info"])

    assert result == 42
    assert ledger == [
        CapturedRun(
            command=cli_mod.cli,
            argv=["info"],
            prog_name=__init__conf__.shell_command,
            signal_specs=None,
            install_signals=True,
        )
    ]


@pytest.mark.os_agnostic
def test_when_cli_runs_without_arguments_help_is_printed(
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
) -> None:
    """Verify CLI with no arguments displays help text."""
    calls: list[str] = []

    def remember() -> None:
        calls.append("called")

    monkeypatch.setattr(cli_mod, "noop_main", remember)

    result = cli_runner.invoke(cli_mod.cli, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert calls == []


@pytest.mark.os_agnostic
def test_when_main_receives_no_arguments_cli_main_is_exercised(
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
    isolated_traceback_config: None,
) -> None:
    """Verify main with no args exercises CLI and shows help."""
    calls: list[str] = []
    outputs: list[str] = []

    def remember() -> None:
        calls.append("called")

    monkeypatch.setattr(cli_mod, "noop_main", remember)

    def fake_run_cli(
        command: Any,
        argv: Sequence[str] | None = None,
        *,
        prog_name: str | None = None,
        signal_specs: Any = None,
        install_signals: bool = True,
    ) -> int:
        args = [] if argv is None else list(argv)
        result: Result = cli_runner.invoke(command, args)
        if result.exception is not None:
            raise result.exception
        outputs.append(result.output)
        return result.exit_code

    monkeypatch.setattr(lib_cli_exit_tools, "run_cli", fake_run_cli)

    exit_code = cli_mod.main([])

    assert exit_code == 0
    assert calls == []
    assert outputs and "Usage:" in outputs[0]


@pytest.mark.os_agnostic
def test_when_traceback_is_requested_without_command_the_domain_runs(
    monkeypatch: pytest.MonkeyPatch,
    cli_runner: CliRunner,
) -> None:
    """Verify --traceback without command runs noop_main."""
    calls: list[str] = []

    def remember() -> None:
        calls.append("called")

    monkeypatch.setattr(cli_mod, "noop_main", remember)

    result = cli_runner.invoke(cli_mod.cli, ["--traceback"])

    assert result.exit_code == 0
    assert calls == ["called"]
    assert "Usage:" not in result.output


@pytest.mark.os_agnostic
def test_when_traceback_flag_is_passed_the_full_story_is_printed(
    isolated_traceback_config: None,
    capsys: pytest.CaptureFixture[str],
    strip_ansi: Callable[[str], str],
) -> None:
    """Verify --traceback displays full exception traceback on failure."""
    exit_code = cli_mod.main(["--traceback", "fail"])

    plain_err = strip_ansi(capsys.readouterr().err)

    assert exit_code != 0
    assert "Traceback (most recent call last)" in plain_err
    assert "RuntimeError: I should fail" in plain_err
    assert "[TRUNCATED" not in plain_err
    assert lib_cli_exit_tools.config.traceback is False
    assert lib_cli_exit_tools.config.traceback_force_color is False


@pytest.mark.os_agnostic
def test_when_hello_is_invoked_the_cli_smiles(cli_runner: CliRunner) -> None:
    """Verify hello command outputs Hello World greeting."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["hello"])

    assert result.exit_code == 0
    assert "Hello World" in result.output


@pytest.mark.os_agnostic
def test_when_fail_is_invoked_the_cli_raises(cli_runner: CliRunner) -> None:
    """Verify fail command raises RuntimeError."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["fail"])

    assert result.exit_code != 0
    assert isinstance(result.exception, RuntimeError)


@pytest.mark.os_agnostic
def test_when_info_is_invoked_the_metadata_is_displayed(cli_runner: CliRunner) -> None:
    """Verify info command displays project metadata."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["info"])

    assert result.exit_code == 0
    assert f"Info for {__init__conf__.name}:" in result.output
    assert __init__conf__.version in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_it_displays_configuration(cli_runner: CliRunner) -> None:
    """Verify config command displays configuration."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    # With default config (all commented), output may be empty or show only log messages


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_json_format_it_outputs_json(cli_runner: CliRunner) -> None:
    """Verify config --format json outputs JSON."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json"])

    assert result.exit_code == 0
    # Use result.stdout to avoid async log messages from stderr
    assert "{" in result.stdout


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_nonexistent_section_it_fails(cli_runner: CliRunner) -> None:
    """Verify config with nonexistent section returns error."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--section", "nonexistent_section_that_does_not_exist"])

    assert result.exit_code != 0
    assert "not found or empty" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_mocked_data_it_displays_sections(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    mock_config_factory: Any,
    clear_config_cache: None,
) -> None:
    """Verify config displays sections from mocked configuration."""
    test_data = {
        "test_section": {
            "setting1": "value1",
            "setting2": 42,
        }
    }
    mock_config = mock_config_factory(test_data)

    def get_mock(**_kwargs: Any) -> Any:
        return mock_config

    # Patch get_config in cli module where it's imported and used
    monkeypatch.setattr(cli_mod, "get_config", get_mock)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    assert "test_section" in result.output
    assert "setting1" in result.output
    assert "value1" in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_json_format_and_section_it_shows_section(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    mock_config_factory: Any,
    clear_config_cache: None,
) -> None:
    """Verify JSON format displays specific section content."""
    test_data = {
        "email": {
            "smtp_hosts": ["smtp.test.com:587"],
            "from_address": "test@example.com",
        }
    }
    mock_config = mock_config_factory(test_data)

    def get_mock(**_kwargs: Any) -> Any:
        return mock_config

    # Patch get_config in cli module where it's imported and used
    monkeypatch.setattr(cli_mod, "get_config", get_mock)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json", "--section", "email"])

    assert result.exit_code == 0
    assert "email" in result.output
    assert "smtp_hosts" in result.output
    assert "smtp.test.com:587" in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_json_format_and_nonexistent_section_it_fails(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    mock_config_factory: Any,
    clear_config_cache: None,
) -> None:
    """Verify JSON format with nonexistent section returns error."""
    test_data = {
        "email": {
            "smtp_hosts": ["smtp.test.com:587"],
        }
    }
    mock_config = mock_config_factory(test_data)

    def get_mock(**_kwargs: Any) -> Any:
        return mock_config

    # Patch get_config in cli module where it's imported and used
    monkeypatch.setattr(cli_mod, "get_config", get_mock)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--format", "json", "--section", "nonexistent"])

    assert result.exit_code != 0
    assert "not found or empty" in result.stderr


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_section_showing_complex_values(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    mock_config_factory: Any,
    clear_config_cache: None,
) -> None:
    """Verify human format with section containing lists and dicts."""
    test_data = {
        "email": {
            "smtp_hosts": ["smtp1.test.com:587", "smtp2.test.com:587"],
            "from_address": "test@example.com",
            "metadata": {"key1": "value1", "key2": "value2"},
            "timeout": 60.0,
        }
    }
    mock_config = mock_config_factory(test_data)

    def get_mock(**_kwargs: Any) -> Any:
        return mock_config

    # Patch get_config in cli module where it's imported and used
    monkeypatch.setattr(cli_mod, "get_config", get_mock)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--section", "email"])

    assert result.exit_code == 0
    assert "[email]" in result.output
    assert "smtp_hosts" in result.output
    assert '["smtp1.test.com:587", "smtp2.test.com:587"]' in result.output or "smtp1.test.com:587" in result.output
    assert "metadata" in result.output
    assert '"test@example.com"' in result.output
    assert "60.0" in result.output


@pytest.mark.os_agnostic
def test_when_config_shows_all_sections_with_complex_values(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    mock_config_factory: Any,
    clear_config_cache: None,
) -> None:
    """Verify human format showing all sections with lists and dicts."""
    test_data = {
        "email": {
            "smtp_hosts": ["smtp.test.com:587"],
            "tags": {"environment": "test", "version": "1.0"},
        },
        "logging": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
        },
    }
    mock_config = mock_config_factory(test_data)

    def get_mock(**_kwargs: Any) -> Any:
        return mock_config

    # Patch get_config in cli module where it's imported and used
    monkeypatch.setattr(cli_mod, "get_config", get_mock)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    assert "[email]" in result.output
    assert "[logging]" in result.output
    assert "smtp_hosts" in result.output
    assert "handlers" in result.output
    assert "tags" in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_without_target_it_fails(cli_runner: CliRunner) -> None:
    """Verify config-deploy without --target option fails."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_it_deploys_configuration(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy creates configuration files."""
    from pathlib import Path

    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Path]:
        return [deployed_path]

    monkeypatch.setattr(cli_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"])

    assert result.exit_code == 0
    assert "Configuration deployed successfully" in result.output
    assert str(deployed_path) in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_finds_no_files_to_create_it_informs_user(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy reports when no files are created."""
    from pathlib import Path

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Path]:
        return []

    monkeypatch.setattr(cli_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"])

    assert result.exit_code == 0
    assert "No files were created" in result.output
    assert "--force" in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_encounters_permission_error_it_handles_gracefully(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy handles PermissionError gracefully."""

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Any]:
        raise PermissionError("Permission denied")

    monkeypatch.setattr(cli_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "app"])

    assert result.exit_code != 0
    assert "Permission denied" in result.stderr
    assert "sudo" in result.stderr.lower()


@pytest.mark.os_agnostic
def test_when_config_deploy_supports_multiple_targets(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy accepts multiple --target options."""
    from pathlib import Path
    from bitranox_template_cli_app_config_log_mail.enums import DeployTarget

    path1 = tmp_path / "config1.toml"
    path2 = tmp_path / "config2.toml"
    path1.touch()
    path2.touch()

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Path]:
        target_values = [t.value if isinstance(t, DeployTarget) else t for t in targets]
        assert len(target_values) == 2
        assert "user" in target_values
        assert "host" in target_values
        return [path1, path2]

    monkeypatch.setattr(cli_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user", "--target", "host"])

    assert result.exit_code == 0
    assert str(path1) in result.output
    assert str(path2) in result.output


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_with_profile_it_passes_profile(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy passes profile to deploy_configuration."""
    from pathlib import Path

    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured_profile: list[str | None] = []

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Path]:
        captured_profile.append(profile)
        return [deployed_path]

    monkeypatch.setattr(cli_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user", "--profile", "production"])

    assert result.exit_code == 0
    assert captured_profile == ["production"]
    assert "(profile: production)" in result.output


@pytest.mark.os_agnostic
def test_when_config_is_invoked_with_profile_it_passes_profile_to_get_config(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    mock_config_factory: Any,
    clear_config_cache: None,
) -> None:
    """Verify config command passes --profile to get_config."""
    captured_profiles: list[str | None] = []
    test_data = {"test_section": {"key": "value"}}
    mock_config = mock_config_factory(test_data)

    def get_mock(*, profile: str | None = None, **_kwargs: Any) -> Any:
        captured_profiles.append(profile)
        return mock_config

    # Patch get_config in cli module where it's imported and used
    monkeypatch.setattr(cli_mod, "get_config", get_mock)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config", "--profile", "staging"])

    assert result.exit_code == 0
    assert "staging" in captured_profiles


@pytest.mark.os_agnostic
def test_when_config_is_invoked_without_profile_it_passes_none(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    mock_config_factory: Any,
    clear_config_cache: None,
) -> None:
    """Verify config command passes None when no --profile specified."""
    captured_profiles: list[str | None] = []
    test_data = {"test_section": {"key": "value"}}
    mock_config = mock_config_factory(test_data)

    def get_mock(*, profile: str | None = None, **_kwargs: Any) -> Any:
        captured_profiles.append(profile)
        return mock_config

    # Patch get_config in cli module where it's imported and used
    monkeypatch.setattr(cli_mod, "get_config", get_mock)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config"])

    assert result.exit_code == 0
    assert None in captured_profiles


@pytest.mark.os_agnostic
def test_when_config_deploy_is_invoked_without_profile_it_passes_none(
    cli_runner: CliRunner,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify config-deploy passes None when no --profile specified."""
    from pathlib import Path

    deployed_path = tmp_path / "config.toml"
    deployed_path.touch()
    captured_profiles: list[str | None] = []

    def mock_deploy(*, targets: Any, force: bool = False, profile: str | None = None) -> list[Path]:
        captured_profiles.append(profile)
        return [deployed_path]

    monkeypatch.setattr(cli_mod, "deploy_configuration", mock_deploy)

    result: Result = cli_runner.invoke(cli_mod.cli, ["config-deploy", "--target", "user"])

    assert result.exit_code == 0
    assert captured_profiles == [None]
    assert "(profile:" not in result.output


@pytest.mark.os_agnostic
def test_when_an_unknown_command_is_used_a_helpful_error_appears(cli_runner: CliRunner) -> None:
    """Verify unknown command shows No such command error."""
    result: Result = cli_runner.invoke(cli_mod.cli, ["does-not-exist"])

    assert result.exit_code != 0
    assert "No such command" in result.output


@pytest.mark.os_agnostic
def test_when_restore_is_disabled_the_traceback_choice_remains(
    isolated_traceback_config: None,
    preserve_traceback_state: None,
) -> None:
    """Verify restore_traceback=False keeps traceback flags enabled."""
    cli_mod.apply_traceback_preferences(False)

    cli_mod.main(["--traceback", "hello"], restore_traceback=False)

    assert lib_cli_exit_tools.config.traceback is True
    assert lib_cli_exit_tools.config.traceback_force_color is True


# ======================== Email Command Tests ========================


@pytest.mark.os_agnostic
def test_when_send_email_is_invoked_without_smtp_hosts_it_fails(
    cli_runner: CliRunner,
) -> None:
    """When SMTP hosts are not configured, send-email should exit with error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-email",
            "--to",
            "recipient@test.com",
            "--subject",
            "Test",
            "--body",
            "Hello",
        ],
    )

    assert result.exit_code == 1
    assert "No SMTP hosts configured" in result.output


@pytest.mark.os_agnostic
def test_when_send_email_is_invoked_with_valid_config_it_sends(
    cli_runner: CliRunner,
    tmp_path: Any,
) -> None:
    """When SMTP is configured, send-email should successfully send."""
    from unittest.mock import patch, MagicMock

    # Create test config with SMTP settings
    config_path = tmp_path / "test_config.toml"
    config_path.write_text('[email]\nsmtp_hosts = ["smtp.test.com:587"]\nfrom_address = "sender@test.com"\n')

    with patch("bitranox_template_cli_app_config_log_mail.cli.get_config") as mock_get_config:
        with patch("smtplib.SMTP"):
            # Mock config
            mock_config_obj = MagicMock()
            mock_config_obj.as_dict.return_value = {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
            mock_get_config.return_value = mock_config_obj

            result: Result = cli_runner.invoke(
                cli_mod.cli,
                [
                    "send-email",
                    "--to",
                    "recipient@test.com",
                    "--subject",
                    "Test Subject",
                    "--body",
                    "Test body",
                ],
            )

            assert result.exit_code == 0
            assert "Email sent successfully" in result.output


@pytest.mark.os_agnostic
def test_when_send_email_receives_multiple_recipients_it_accepts_them(
    cli_runner: CliRunner,
) -> None:
    """When multiple --to flags are provided, send-email should accept them."""
    from unittest.mock import patch, MagicMock

    with patch("bitranox_template_cli_app_config_log_mail.cli.get_config") as mock_get_config:
        with patch("smtplib.SMTP"):
            mock_config_obj = MagicMock()
            mock_config_obj.as_dict.return_value = {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
            mock_get_config.return_value = mock_config_obj

            result: Result = cli_runner.invoke(
                cli_mod.cli,
                [
                    "send-email",
                    "--to",
                    "user1@test.com",
                    "--to",
                    "user2@test.com",
                    "--subject",
                    "Test",
                    "--body",
                    "Hello",
                ],
            )

            assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_when_send_email_includes_html_body_it_sends(
    cli_runner: CliRunner,
) -> None:
    """When HTML body is provided, send-email should include it."""
    from unittest.mock import patch, MagicMock

    with patch("bitranox_template_cli_app_config_log_mail.cli.get_config") as mock_get_config:
        with patch("smtplib.SMTP"):
            mock_config_obj = MagicMock()
            mock_config_obj.as_dict.return_value = {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
            mock_get_config.return_value = mock_config_obj

            result: Result = cli_runner.invoke(
                cli_mod.cli,
                [
                    "send-email",
                    "--to",
                    "recipient@test.com",
                    "--subject",
                    "Test",
                    "--body",
                    "Plain text",
                    "--body-html",
                    "<h1>HTML</h1>",
                ],
            )

            assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_when_send_email_has_attachments_it_sends(
    cli_runner: CliRunner,
    tmp_path: Any,
) -> None:
    """When attachments are provided, send-email should include them."""
    from unittest.mock import patch, MagicMock

    # Create test attachment
    attachment = tmp_path / "test.txt"
    attachment.write_text("Test content")

    with patch("bitranox_template_cli_app_config_log_mail.cli.get_config") as mock_get_config:
        with patch("smtplib.SMTP"):
            mock_config_obj = MagicMock()
            mock_config_obj.as_dict.return_value = {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
            mock_get_config.return_value = mock_config_obj

            result: Result = cli_runner.invoke(
                cli_mod.cli,
                [
                    "send-email",
                    "--to",
                    "recipient@test.com",
                    "--subject",
                    "Test",
                    "--body",
                    "See attachment",
                    "--attachment",
                    str(attachment),
                ],
            )

            assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_when_send_email_smtp_fails_it_reports_error(
    cli_runner: CliRunner,
) -> None:
    """When SMTP connection fails, send-email should show error message."""
    from unittest.mock import patch, MagicMock

    with patch("bitranox_template_cli_app_config_log_mail.cli.get_config") as mock_get_config:
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = ConnectionError("Cannot connect")

            mock_config_obj = MagicMock()
            mock_config_obj.as_dict.return_value = {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "sender@test.com",
                }
            }
            mock_get_config.return_value = mock_config_obj

            result: Result = cli_runner.invoke(
                cli_mod.cli,
                [
                    "send-email",
                    "--to",
                    "recipient@test.com",
                    "--subject",
                    "Test",
                    "--body",
                    "Hello",
                ],
            )

            assert result.exit_code == 1
            assert "Error" in result.output


@pytest.mark.os_agnostic
def test_when_send_notification_is_invoked_without_smtp_hosts_it_fails(
    cli_runner: CliRunner,
) -> None:
    """When SMTP hosts are not configured, send-notification should exit with error."""
    result: Result = cli_runner.invoke(
        cli_mod.cli,
        [
            "send-notification",
            "--to",
            "admin@test.com",
            "--subject",
            "Alert",
            "--message",
            "System notification",
        ],
    )

    assert result.exit_code == 1
    assert "No SMTP hosts configured" in result.output


@pytest.mark.os_agnostic
def test_when_send_notification_is_invoked_with_valid_config_it_sends(
    cli_runner: CliRunner,
) -> None:
    """When SMTP is configured, send-notification should successfully send."""
    from unittest.mock import patch, MagicMock

    with patch("bitranox_template_cli_app_config_log_mail.cli.get_config") as mock_get_config:
        with patch("smtplib.SMTP"):
            mock_config_obj = MagicMock()
            mock_config_obj.as_dict.return_value = {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "alerts@test.com",
                }
            }
            mock_get_config.return_value = mock_config_obj

            result: Result = cli_runner.invoke(
                cli_mod.cli,
                [
                    "send-notification",
                    "--to",
                    "admin@test.com",
                    "--subject",
                    "Alert",
                    "--message",
                    "System notification",
                ],
            )

            assert result.exit_code == 0
            assert "Notification sent successfully" in result.output


@pytest.mark.os_agnostic
def test_when_send_notification_receives_multiple_recipients_it_accepts_them(
    cli_runner: CliRunner,
) -> None:
    """When multiple --to flags are provided, send-notification should accept them."""
    from unittest.mock import patch, MagicMock

    with patch("bitranox_template_cli_app_config_log_mail.cli.get_config") as mock_get_config:
        with patch("smtplib.SMTP"):
            mock_config_obj = MagicMock()
            mock_config_obj.as_dict.return_value = {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "alerts@test.com",
                }
            }
            mock_get_config.return_value = mock_config_obj

            result: Result = cli_runner.invoke(
                cli_mod.cli,
                [
                    "send-notification",
                    "--to",
                    "admin1@test.com",
                    "--to",
                    "admin2@test.com",
                    "--subject",
                    "Alert",
                    "--message",
                    "System notification",
                ],
            )

            assert result.exit_code == 0


@pytest.mark.os_agnostic
def test_when_send_notification_smtp_fails_it_reports_error(
    cli_runner: CliRunner,
) -> None:
    """When SMTP connection fails, send-notification should show error message."""
    from unittest.mock import patch, MagicMock

    with patch("bitranox_template_cli_app_config_log_mail.cli.get_config") as mock_get_config:
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = ConnectionError("Cannot connect")

            mock_config_obj = MagicMock()
            mock_config_obj.as_dict.return_value = {
                "email": {
                    "smtp_hosts": ["smtp.test.com:587"],
                    "from_address": "alerts@test.com",
                }
            }
            mock_get_config.return_value = mock_config_obj

            result: Result = cli_runner.invoke(
                cli_mod.cli,
                [
                    "send-notification",
                    "--to",
                    "admin@test.com",
                    "--subject",
                    "Alert",
                    "--message",
                    "System notification",
                ],
            )

            assert result.exit_code == 1
            assert "Error" in result.output
