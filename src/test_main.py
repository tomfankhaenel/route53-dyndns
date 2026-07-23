"""Functional tests for the route53-dyndns updater.

These tests exercise the pure helpers and the IP-discovery logic with all
network access mocked, so they can run in CI without AWS credentials or
internet access. They are the gate that decides whether a Renovate update is
allowed to be merged: if a dependency bump breaks this behaviour, the tests
fail and the pull request is never merged automatically.
"""
import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import main  # noqa: E402


def test_convert_to_record_set_format_escapes_wildcard():
    assert main.convert_to_record_set_format('*.example.com.') == '\\052.example.com.'


def test_convert_to_record_set_format_leaves_plain_name():
    assert main.convert_to_record_set_format('example.com.') == 'example.com.'


def test_parse_records_splits_and_strips():
    assert main.parse_records('a.example.com., *.example.com.') == [
        'a.example.com.',
        '*.example.com.',
    ]


def test_parse_records_handles_empty_and_none():
    assert main.parse_records(None) == []
    assert main.parse_records('') == []
    assert main.parse_records(' , ,') == []


def test_get_current_ip_primary_success():
    fake = mock.Mock()
    fake.raise_for_status.return_value = None
    fake.json.return_value = {'origin': '203.0.113.7'}
    with mock.patch.object(main.requests, 'get', return_value=fake) as get:
        assert main.get_current_ip() == '203.0.113.7'
        get.assert_called_once()


def test_get_current_ip_strips_multiple_origins():
    fake = mock.Mock()
    fake.raise_for_status.return_value = None
    fake.json.return_value = {'origin': '203.0.113.7, 10.0.0.1'}
    with mock.patch.object(main.requests, 'get', return_value=fake):
        assert main.get_current_ip() == '203.0.113.7'


def test_get_current_ip_uses_fallback_on_primary_failure():
    primary_error = main.requests.exceptions.RequestException('boom')
    fallback = mock.Mock()
    fallback.raise_for_status.return_value = None
    fallback.json.return_value = {'ip': '198.51.100.5'}

    calls = {'n': 0}

    def side_effect(url, timeout=30):
        calls['n'] += 1
        if calls['n'] == 1:
            raise primary_error
        return fallback

    with mock.patch.object(main.requests, 'get', side_effect=side_effect):
        assert main.get_current_ip() == '198.51.100.5'


def test_get_current_ip_returns_none_when_all_fail():
    with mock.patch.object(
        main.requests, 'get',
        side_effect=main.requests.exceptions.RequestException('down'),
    ):
        assert main.get_current_ip() is None


def test_update_route53_record_requires_credentials():
    with mock.patch.multiple(
        main,
        aws_access_key_id=None,
        aws_secret_access_key=None,
    ):
        assert main.update_route53_record('zone', 'name.', '1.2.3.4') is False


def test_update_route53_record_upserts(monkeypatch):
    client = mock.Mock()
    monkeypatch.setattr(main, 'aws_access_key_id', 'key')
    monkeypatch.setattr(main, 'aws_secret_access_key', 'secret')
    monkeypatch.setattr(main, 'region_name', 'eu-central-1')
    with mock.patch.object(main.boto3, 'client', return_value=client):
        assert main.update_route53_record('zone', 'name.', '1.2.3.4') is True
    args, kwargs = client.change_resource_record_sets.call_args
    change = kwargs['ChangeBatch']['Changes'][0]
    assert change['Action'] == 'UPSERT'
    assert change['ResourceRecordSet']['ResourceRecords'][0]['Value'] == '1.2.3.4'


if __name__ == '__main__':
    raise SystemExit(pytest.main([__file__, '-v']))
