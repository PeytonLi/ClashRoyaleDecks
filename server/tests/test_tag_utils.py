"""Tests for player tag normalization and candidate resolution utilities."""

import pytest

from app.services.tag_utils import build_tag_candidates, normalize_tag_input


def test_normalize_tag_input_accepts_o_characters():
    normalized = normalize_tag_input("JOC9YVUL")
    assert normalized == "JOC9YVUL"


def test_normalize_tag_input_accepts_zero_characters():
    normalized = normalize_tag_input("J0C9YVUL")
    assert normalized == "J0C9YVUL"


def test_build_tag_candidates_keeps_input_and_adds_o_to_zero_variant():
    candidates = build_tag_candidates("JOC9YVUL")
    assert candidates == ["JOC9YVUL", "J0C9YVUL"]


def test_build_tag_candidates_keeps_zero_only_tag_once():
    candidates = build_tag_candidates("J0C9YVUL")
    assert candidates == ["J0C9YVUL"]


def test_normalize_tag_input_rejects_invalid_characters():
    with pytest.raises(ValueError):
        normalize_tag_input("JXC9YVUL")
