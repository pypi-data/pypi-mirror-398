"""Tests for DocstringBuilder."""

from __future__ import annotations

from codec_cub.pythons.builders import DocstringBuilder


def test_summary_only() -> None:
    """Test docstring with only a summary."""
    doc: DocstringBuilder = DocstringBuilder().summary("Get the user name.")

    result: str = doc.render()
    assert result == "Get the user name."


def test_summary_and_description() -> None:
    """Test docstring with summary and description."""
    doc = (
        DocstringBuilder()
        .summary("Get the user name.")
        .description("This function retrieves the user's full name from the database.")
    )

    result = doc.render()

    assert "Get the user name." in result
    assert "This function retrieves the user's full name from the database." in result


def test_with_args() -> None:
    """Test docstring with arguments."""
    doc = (
        DocstringBuilder()
        .summary("Create a new user.")
        .arg("name", "User's full name")
        .arg("age", "User's age in years")
        .arg("email", "User's email address")
    )

    result = doc.render()

    assert "Create a new user." in result
    assert "Args:" in result
    assert "name: User's full name" in result
    assert "age: User's age in years" in result
    assert "email: User's email address" in result


def test_with_returns() -> None:
    """Test docstring with return value."""
    doc = DocstringBuilder().summary("Calculate sum.").returns("The sum of all numbers")

    result = doc.render()

    assert "Calculate sum." in result
    assert "Returns:" in result
    assert "The sum of all numbers" in result


def test_with_raises() -> None:
    """Test docstring with exceptions."""
    doc = (
        DocstringBuilder()
        .summary("Open a file.")
        .raises("FileNotFoundError", "If the file doesn't exist")
        .raises("PermissionError", "If lacking read permissions")
    )

    result = doc.render()

    assert "Open a file." in result
    assert "Raises:" in result
    assert "FileNotFoundError: If the file doesn't exist" in result
    assert "PermissionError: If lacking read permissions" in result


def test_with_yields() -> None:
    """Test docstring with yields section."""
    doc = DocstringBuilder().summary("Generate numbers.").yields("Next number in sequence")

    result = doc.render()

    assert "Generate numbers." in result
    assert "Yields:" in result
    assert "Next number in sequence" in result


def test_with_examples() -> None:
    """Test docstring with examples."""
    doc = DocstringBuilder().summary("Add two numbers.").example(">>> add(2, 3)\n5").example(">>> add(-1, 1)\n0")

    result = doc.render()

    assert "Add two numbers." in result
    assert "Examples:" in result
    assert ">>> add(2, 3)" in result
    assert "5" in result
    assert ">>> add(-1, 1)" in result
    assert "0" in result


def test_with_notes() -> None:
    """Test docstring with notes."""
    doc = (
        DocstringBuilder()
        .summary("Process data.")
        .note("This function is deprecated.")
        .note("Use process_data_v2 instead.")
    )

    result = doc.render()

    assert "Process data." in result
    assert "Note:" in result
    assert "This function is deprecated." in result
    assert "Use process_data_v2 instead." in result


def test_complete_docstring() -> None:
    """Test a complete docstring with all sections."""
    doc = (
        DocstringBuilder()
        .summary("Factory function to get a storage backend by name.")
        .description("Returns the appropriate storage class based on the backend name.")
        .arg("storage", "Storage backend name")
        .returns("Storage backend class")
        .raises("ValueError", "If storage backend is unknown")
        .example('>>> get_storage("json")\n<class JsonStorage>')
    )

    result = doc.render()

    assert "Factory function to get a storage backend by name." in result
    assert "Returns the appropriate storage class based on the backend name." in result
    assert "Args:" in result
    assert "storage: Storage backend name" in result
    assert "Returns:" in result
    assert "Storage backend class" in result
    assert "Raises:" in result
    assert "ValueError: If storage backend is unknown" in result
    assert "Examples:" in result
    assert '>>> get_storage("json")' in result


def test_empty_docstring() -> None:
    """Test empty docstring builder."""
    doc = DocstringBuilder()

    result = doc.render()

    assert result == ""


def test_str_method() -> None:
    """Test __str__ method."""
    doc = DocstringBuilder().summary("Test function.")

    assert str(doc) == "Test function."


def test_repr_method() -> None:
    """Test __repr__ method."""
    doc = DocstringBuilder().summary("Test function.")

    assert repr(doc) == "DocstringBuilder(summary='Test function.')"


def test_isinstance_check() -> None:
    """Test that DocstringBuilder can be detected via isinstance()."""
    doc = DocstringBuilder()

    assert isinstance(doc, DocstringBuilder)
    # Verify it has the expected interface
    assert hasattr(doc, "render")
    assert callable(doc.render)


def test_fluent_chaining() -> None:
    """Test that all methods return Self for chaining."""
    doc = DocstringBuilder()

    result = (
        doc.summary("Test")
        .description("Description")
        .arg("x", "param")
        .returns("value")
        .raises("Error", "when")
        .yields("item")
        .example("code")
        .note("note")
    )

    assert result is doc
