"""Tests for Nix utility functions."""

from __future__ import annotations

from codec_cub.nix.encoder import is_bare_identifier


class TestIsBareIdentifier:
    """Test is_bare_identifier function."""

    def test_valid_simple_identifiers(self) -> None:
        """Test valid simple identifiers."""
        assert is_bare_identifier("foo") is True
        assert is_bare_identifier("bar") is True
        assert is_bare_identifier("_test") is True
        assert is_bare_identifier("_") is True

    def test_valid_identifiers_with_numbers(self) -> None:
        """Test valid identifiers containing numbers."""
        assert is_bare_identifier("foo123") is True
        assert is_bare_identifier("test_42") is True
        assert is_bare_identifier("_123") is True

    def test_valid_identifiers_with_dashes(self) -> None:
        """Test valid identifiers containing dashes."""
        assert is_bare_identifier("my-key") is True
        assert is_bare_identifier("test-key-123") is True
        assert is_bare_identifier("_my-test") is True

    def test_valid_identifiers_with_underscores(self) -> None:
        """Test valid identifiers with underscores."""
        assert is_bare_identifier("my_key") is True
        assert is_bare_identifier("test_key_123") is True
        assert is_bare_identifier("__private") is True

    def test_invalid_empty_string(self) -> None:
        """Test empty string is not a valid identifier."""
        assert is_bare_identifier("") is False

    def test_invalid_starts_with_number(self) -> None:
        """Test identifiers starting with numbers are invalid."""
        assert is_bare_identifier("123") is False
        assert is_bare_identifier("1foo") is False
        assert is_bare_identifier("2test") is False

    def test_invalid_starts_with_dash(self) -> None:
        """Test identifiers starting with dash are invalid."""
        assert is_bare_identifier("-foo") is False
        assert is_bare_identifier("-test") is False

    def test_invalid_special_characters(self) -> None:
        """Test identifiers with invalid special characters."""
        assert is_bare_identifier("foo bar") is False
        assert is_bare_identifier("test@key") is False
        assert is_bare_identifier("my.key") is False
        assert is_bare_identifier("foo!") is False
        assert is_bare_identifier("test$var") is False

    def test_invalid_whitespace(self) -> None:
        """Test identifiers with whitespace are invalid."""
        assert is_bare_identifier(" foo") is False
        assert is_bare_identifier("foo ") is False
        assert is_bare_identifier("foo bar") is False
        assert is_bare_identifier("\tfoo") is False
        assert is_bare_identifier("foo\n") is False

    def test_mixed_valid_combinations(self) -> None:
        """Test complex but valid identifiers."""
        assert is_bare_identifier("myVar123_test-key") is True
        assert is_bare_identifier("_internal_helper_v2") is True
        assert is_bare_identifier("build-system") is True
        assert is_bare_identifier("pkgs") is True
        assert is_bare_identifier("stdenv") is True

    def test_real_world_nix_identifiers(self) -> None:
        """Test real-world Nix identifiers.

        Examples taken from common Nix expressions.
        """
        assert is_bare_identifier("buildInputs") is True
        assert is_bare_identifier("nativeBuildInputs") is True
        assert is_bare_identifier("propagatedBuildInputs") is True
        assert is_bare_identifier("pname") is True
        assert is_bare_identifier("version") is True
        assert is_bare_identifier("src") is True
        assert is_bare_identifier("meta") is True
        assert is_bare_identifier("description") is True
        assert is_bare_identifier("license") is True
