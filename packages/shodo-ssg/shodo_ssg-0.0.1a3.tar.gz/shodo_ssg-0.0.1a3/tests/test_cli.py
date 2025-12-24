"""Tests for the CLI module."""

import re
from datetime import datetime, timezone
from shodo_ssg.cli import get_utc_timestamp, timestamp_command


def test_get_utc_timestamp_format():
    """Test that get_utc_timestamp returns correct ISO 8601 format"""
    result = get_utc_timestamp()

    # Check format: YYYY-MM-DDTHH:MM:SSZ
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
    assert re.match(
        pattern, result
    ), f"Timestamp {result} doesn't match ISO 8601 format"


def test_get_utc_timestamp_is_utc():
    """Test that timestamp ends with Z indicating UTC"""
    result = get_utc_timestamp()
    assert result.endswith("Z"), "Timestamp should end with Z for UTC"


def test_get_utc_timestamp_is_current():
    """Test that timestamp is approximately current time"""
    before = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = get_utc_timestamp()
    after = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Parse the results back to datetime
    before_dt = datetime.strptime(before, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    result_dt = datetime.strptime(result, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    after_dt = datetime.strptime(after, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    # Should be between before and after (within a few seconds)
    assert before_dt <= result_dt <= after_dt


def test_timestamp_command_prints_timestamp(capsys):
    """Test that timestamp_command prints to stdout"""
    timestamp_command()

    captured = capsys.readouterr()
    output = captured.out.strip()

    # Verify it printed something in the correct format
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
    assert re.match(pattern, output), f"Output {output} doesn't match ISO 8601 format"


def test_timestamp_command_output_matches_get_utc_timestamp(capsys):
    """Test that timestamp_command uses get_utc_timestamp"""
    # Get timestamp directly
    expected = get_utc_timestamp()

    # Get timestamp via command (within same second)
    timestamp_command()
    captured = capsys.readouterr()
    output = captured.out.strip()

    # Should be the same or within 1 second
    expected_dt = datetime.strptime(expected, "%Y-%m-%dT%H:%M:%SZ")
    output_dt = datetime.strptime(output, "%Y-%m-%dT%H:%M:%SZ")

    diff = abs((expected_dt - output_dt).total_seconds())
    assert diff <= 1, "Timestamps should be within 1 second of each other"
