"""
Integration tests for the CLI module.
"""

from pathlib import Path

from structure_viewer.cli import main, parse_args


class TestParseArgs:
    """Tests for argument parsing."""

    def test_default_directory(self) -> None:
        """Test default directory is current directory."""
        args = parse_args([])
        assert args.directory == "."

    def test_custom_directory(self) -> None:
        """Test specifying a custom directory."""
        args = parse_args(["/some/path"])
        assert args.directory == "/some/path"

    def test_depth_option(self) -> None:
        """Test depth option."""
        args = parse_args(["-d", "3"])
        assert args.depth == 3

        args = parse_args(["--depth", "5"])
        assert args.depth == 5

    def test_format_option(self) -> None:
        """Test format option."""
        args = parse_args(["-f", "json"])
        assert args.format == "json"

        args = parse_args(["--format", "yaml"])
        assert args.format == "yaml"

    def test_exclude_option(self) -> None:
        """Test exclude option can be repeated."""
        args = parse_args(["-e", "*.log", "-e", "tmp"])
        assert args.exclude == ["*.log", "tmp"]

    def test_include_ext_option(self) -> None:
        """Test include extension option."""
        args = parse_args(["-I", "py", "-I", "js"])
        assert args.include_ext == ["py", "js"]

    def test_exclude_ext_option(self) -> None:
        """Test exclude extension option."""
        args = parse_args(["-E", "pyc", "-E", "log"])
        assert args.exclude_ext == ["pyc", "log"]

    def test_all_hidden_option(self) -> None:
        """Test show hidden option."""
        args = parse_args(["-a"])
        assert args.show_hidden is True

        args = parse_args(["--all"])
        assert args.show_hidden is True

    def test_no_color_option(self) -> None:
        """Test no-color option."""
        args = parse_args(["--no-color"])
        assert args.no_color is True

    def test_quiet_option(self) -> None:
        """Test quiet option."""
        args = parse_args(["-q"])
        assert args.quiet is True

    def test_stats_option(self) -> None:
        """Test stats option."""
        args = parse_args(["-s"])
        assert args.stats is True


class TestMain:
    """Integration tests for the main function."""

    def test_basic_execution(self, temp_project: Path, capsys) -> None:
        """Test basic CLI execution."""
        exit_code = main([str(temp_project), "--no-color"])

        assert exit_code == 0

        captured = capsys.readouterr()
        assert temp_project.name in captured.out
        assert "src/" in captured.out

    def test_json_output(self, temp_project: Path, capsys) -> None:
        """Test JSON output format."""
        exit_code = main([str(temp_project), "-f", "json"])

        assert exit_code == 0

        captured = capsys.readouterr()
        # Should be valid JSON
        import json
        data = json.loads(captured.out)
        assert "name" in data

    def test_depth_limit(self, temp_nested_dir: Path, capsys) -> None:
        """Test depth limiting via CLI."""
        exit_code = main([str(temp_nested_dir), "-d", "1", "--no-color"])

        assert exit_code == 0

        captured = capsys.readouterr()
        # Should contain level1 but not deep.txt
        assert "level1" in captured.out
        assert "deep.txt" not in captured.out

    def test_stats_output(self, temp_project: Path, capsys) -> None:
        """Test statistics output."""
        exit_code = main([str(temp_project), "-s", "--no-color"])

        assert exit_code == 0

        captured = capsys.readouterr()
        assert "directories" in captured.out
        assert "files" in captured.out

    def test_quiet_mode(self, temp_project: Path, capsys) -> None:
        """Test quiet mode shows only directories."""
        exit_code = main([str(temp_project), "-q", "--no-color"])

        assert exit_code == 0

        captured = capsys.readouterr()
        # Should not contain file names
        assert "README.md" not in captured.out
        # Should contain directory names
        assert "src/" in captured.out

    def test_nonexistent_directory(self, capsys) -> None:
        """Test error handling for non-existent directory."""
        exit_code = main(["/nonexistent/path/12345"])

        assert exit_code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_include_extensions(self, temp_mixed_extensions: Path, capsys) -> None:
        """Test filtering by extension."""
        exit_code = main([str(temp_mixed_extensions), "-I", "py", "--no-color"])

        assert exit_code == 0

        captured = capsys.readouterr()
        assert "script.py" in captured.out
        assert "style.css" not in captured.out

    def test_exclude_extensions(self, temp_mixed_extensions: Path, capsys) -> None:
        """Test excluding extensions."""
        exit_code = main([str(temp_mixed_extensions), "-E", "txt", "-E", "json", "--no-color"])

        assert exit_code == 0

        captured = capsys.readouterr()
        assert "script.py" in captured.out
        assert "notes.txt" not in captured.out
