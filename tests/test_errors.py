from src.errors import BuildError, SynthesisStep


def test_build_error_message_includes_context():
    err = BuildError(
        SynthesisStep.MAP_CHUNK,
        "connection reset",
        project_name="my-proj",
        detail="/path/a.md",
    )
    s = str(err)
    assert "map_chunk" in s
    assert "my-proj" in s
    assert "/path/a.md" in s
