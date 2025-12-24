"""
Comprehensive tests for the CLI module
"""

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse

from usenc.cli import add_default_params, add_encoder_params, main, process_encoding, smart_open
from usenc.encoders import ENCODERS


class TestSmartOpen:
    """Tests for the smart_open context manager"""

    def test_smart_open_with_none_uses_default_stream(self):
        """Test that smart_open with None uses the default stream"""
        mock_stream = io.BytesIO(b"test input")

        with smart_open(None, "rb", mock_stream) as f:
            assert f is mock_stream
            content = f.read()
            assert content == b"test input"

    def test_smart_open_with_file_path(self, tmp_path):
        """Test that smart_open opens and closes files"""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"file content")

        mock_stream = io.BytesIO()

        with smart_open(test_file, "rb", mock_stream) as f:
            assert f is not mock_stream
            content = f.read()
            assert content == b"file content"

    def test_smart_open_write_mode(self, tmp_path):
        """Test that smart_open can write to files"""
        test_file = tmp_path / "output.txt"
        mock_stream = io.BytesIO()

        with smart_open(test_file, "wb", mock_stream) as f:
            f.write(b"written content")

        assert test_file.read_bytes() == b"written content"

    def test_smart_open_does_not_close_default_stream(self):
        """Test that default stream is not closed"""
        mock_stream = io.BytesIO(b"test")

        with smart_open(None, "rb", mock_stream):
            pass

        # Stream should still be usable
        assert not mock_stream.closed
        mock_stream.read()  # Should not raise


class TestProcessEncoding:
    """Tests for the process_encoding function"""

    def test_process_encoding_encode_from_stdin_to_stdout(self, tmp_path):
        """Test encoding from stdin to stdout"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"hello world\ntest data\n")

        process_encoding(input_file, output_file, False, False, {}, "url", {})

        output_content = output_file.read_bytes().decode("utf-8")
        assert "hello%20world" in output_content
        assert "test%20data" in output_content

    def test_process_encoding_decode(self, tmp_path):
        """Test decoding mode"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"hello%20world\n")

        process_encoding(input_file, output_file, True, False, {}, "url", {})

        output_content = output_file.read_bytes().decode("utf-8")
        assert "hello world" in output_content

    def test_process_encoding_with_encoder_params(self, tmp_path):
        """Test encoding with encoder-specific parameters"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"hello-world\n")

        process_encoding(input_file, output_file, False, False, {}, "url", {"include": "-"})

        output_content = output_file.read_bytes().decode("utf-8")
        assert "hello%2Dworld" in output_content

    def test_process_encoding_multiple_lines(self, tmp_path):
        """Test encoding multiple lines"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"line 1\nline 2\nline 3\n")

        process_encoding(input_file, output_file, False, False, {}, "url", {})

        output_lines = output_file.read_bytes().decode("utf-8").splitlines()
        assert len(output_lines) == 3
        assert "line%201" in output_lines[0]
        assert "line%202" in output_lines[1]
        assert "line%203" in output_lines[2]

    def test_process_encoding_bulk(self, tmp_path):
        """Test encoding a whole file in bulk"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"line 1\nline 2\nline 3\n")

        process_encoding(input_file, output_file, False, True, {}, "url", {})

        output_lines = output_file.read_bytes().decode("utf-8").splitlines()
        print(output_lines)
        assert len(output_lines) == 1
        assert "line%201%0Aline%202%0Aline%203%0A" in output_lines[0]

    def test_process_encoding_empty_file(self, tmp_path):
        """Test encoding an empty file"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"")

        process_encoding(input_file, output_file, False, False, {}, "url", {})

        assert output_file.read_bytes() == b""


class TestAddEncoderParams:
    """Tests for the add_encoder_params function"""

    def test_add_encoder_params_for_url_encoder(self):
        """Test adding parameters for URL encoder"""
        parser = argparse.ArgumentParser()
        add_encoder_params(parser, "url")

        # Parse test args
        args = parser.parse_args(["--include", "abc", "--exclude", "xyz"])

        assert args.include == "abc"
        assert args.exclude == "xyz"

    def test_add_encoder_params_with_defaults(self):
        """Test that default values are set"""
        parser = argparse.ArgumentParser()
        add_encoder_params(parser, "url")

        args = parser.parse_args([])

        assert args.include == ""
        assert args.exclude == ""

    def test_add_encoder_params_nonexistent_encoder(self):
        """Test adding params for non-existent encoder does nothing"""
        parser = argparse.ArgumentParser()
        add_encoder_params(parser, "nonexistent")

        # Should not raise, just do nothing
        parser.parse_args([])

    def test_add_encoder_params_encoder_without_params(self):
        """Test encoder without params attribute"""
        parser = argparse.ArgumentParser()

        # Get initial actions (arguments) count
        initial_actions = len(parser._actions)

        # Create a mock encoder without params
        class MockEncoder:
            pass

        original_encoders = ENCODERS.copy()
        ENCODERS["mock"] = MockEncoder

        try:
            add_encoder_params(parser, "mock")

            # Verify no new arguments were added
            assert len(parser._actions) == initial_actions

            # Should parse successfully with no extra args
            args = parser.parse_args([])

            # Verify the mock encoder params were not added as attributes
            assert not hasattr(args, "include")
            assert not hasattr(args, "exclude")
        finally:
            # Restore original encoders
            ENCODERS.clear()
            ENCODERS.update(original_encoders)


class TestAddDefaultParams:
    """Tests for the add_default_params function"""

    def test_add_default_params_basic(self):
        """Test adding default parameters"""
        parser = argparse.ArgumentParser()
        add_default_params(parser)

        args = parser.parse_args(["url"])

        assert args.encoder == "url"
        assert args.decode is False
        assert args.input is None
        assert args.output is None

    def test_add_default_params_decode_flag(self):
        """Test decode flag"""
        parser = argparse.ArgumentParser()
        add_default_params(parser)

        args = parser.parse_args(["url", "-d"])
        assert args.decode is True

        args = parser.parse_args(["url", "--decode"])
        assert args.decode is True

    def test_add_default_params_input_output(self, tmp_path):
        """Test input and output file parameters"""
        parser = argparse.ArgumentParser()
        add_default_params(parser)

        input_file = tmp_path / "in.txt"
        output_file = tmp_path / "out.txt"

        args = parser.parse_args(["url", "-i", str(input_file), "-o", str(output_file)])

        assert args.input == input_file
        assert args.output == output_file

    def test_add_default_params_encoder_choices(self):
        """Test that encoder has choices from ENCODERS"""
        parser = argparse.ArgumentParser()
        add_default_params(parser)

        # Valid encoder should work
        args = parser.parse_args(["url"])
        assert args.encoder == "url"

        # Invalid encoder should raise
        with pytest.raises(SystemExit):
            parser.parse_args(["invalid_encoder"])


class TestMain:
    """Tests for the main CLI function"""

    def test_main_help_message(self, capsys):
        """Test that --help shows help message"""
        with patch("sys.argv", ["usenc", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert "Encode URL parameters" in captured.out
            assert "Available encoders" in captured.out

    def test_main_encode_basic(self, tmp_path, capsys):
        """Test basic encoding via main"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"hello world\n")

        with patch("sys.argv", ["usenc", "url", "-i", str(input_file), "-o", str(output_file)]):
            main()

        output_content = output_file.read_bytes().decode("utf-8")
        assert "hello%20world" in output_content

    def test_main_decode_basic(self, tmp_path):
        """Test basic decoding via main"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"hello%20world\n")

        with patch(
            "sys.argv", ["usenc", "url", "-d", "-i", str(input_file), "-o", str(output_file)]
        ):
            main()

        output_content = output_file.read_bytes().decode("utf-8")
        assert "hello world" in output_content

    def test_main_with_encoder_params(self, tmp_path):
        """Test main with encoder-specific parameters"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"hello-world\n")

        with patch(
            "sys.argv",
            ["usenc", "url", "--include", "-", "-i", str(input_file), "-o", str(output_file)],
        ):
            main()

        output_content = output_file.read_bytes().decode("utf-8")
        assert "hello%2Dworld" in output_content

    def test_main_file_not_found(self, tmp_path, capsys):
        """Test error handling for missing input file"""
        input_file = tmp_path / "nonexistent.txt"
        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["usenc", "url", "-i", str(input_file), "-o", str(output_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "No such file or directory" in captured.err

    def test_main_stdin_stdout(self):
        """Test reading from stdin and writing to stdout"""
        mock_stdin = io.BytesIO(b"hello world\n")
        mock_stdout = io.BytesIO()

        # Create mock stdin/stdout objects with buffer attributes
        mock_stdin_obj = MagicMock()
        mock_stdin_obj.buffer = mock_stdin
        mock_stdout_obj = MagicMock()
        mock_stdout_obj.buffer = mock_stdout

        with patch("sys.argv", ["usenc", "url"]), patch("sys.stdin", mock_stdin_obj), patch(
            "sys.stdout", mock_stdout_obj
        ):
            main()

        output = mock_stdout.getvalue().decode("utf-8")
        assert "hello%20world" in output

    def test_main_multiple_lines(self, tmp_path):
        """Test processing multiple lines"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        lines = b"line1\nline2\nline3\n"

        input_file.write_bytes(lines)

        with patch("sys.argv", ["usenc", "url", "-i", str(input_file), "-o", str(output_file)]):
            main()

        output_lines = output_file.read_bytes()
        assert output_lines == lines


class TestCLIIntegration:
    """Integration tests for CLI workflows"""

    def test_encode_decode_roundtrip(self, tmp_path):
        """Test that encode then decode returns original"""
        original_file = tmp_path / "original.txt"
        encoded_file = tmp_path / "encoded.txt"
        decoded_file = tmp_path / "decoded.txt"

        test_content = b"hello world\ntest data\nspecial chars: !@#$%\n"
        original_file.write_bytes(test_content)

        # Encode
        with patch("sys.argv", ["usenc", "url", "-i", str(original_file), "-o", str(encoded_file)]):
            main()

        # Decode
        with patch(
            "sys.argv", ["usenc", "url", "-d", "-i", str(encoded_file), "-o", str(decoded_file)]
        ):
            main()

        # Compare
        assert decoded_file.read_bytes() == test_content

    def test_exclude_parameter_workflow(self, tmp_path):
        """Test using exclude parameter in workflow"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"path/to/file?query=value\n")

        # Encode but exclude /
        with patch(
            "sys.argv",
            ["usenc", "url", "--exclude", "/", "-i", str(input_file), "-o", str(output_file)],
        ):
            main()

        output = output_file.read_bytes().decode("utf-8")
        assert output == "path/to/file%3Fquery%3Dvalue\n"

    def test_keyboard_interrupt_handling(self, tmp_path, capsys):
        """Test that KeyboardInterrupt exits with code 130"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"test data\n")

        with patch(
            "sys.argv", ["usenc", "url", "-i", str(input_file), "-o", str(output_file)]
        ), patch("usenc.cli.process_encoding", side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # KeyboardInterrupt should exit with code 130
            assert exc_info.value.code == 130

    def test_generic_exception_handling(self, tmp_path, capsys):
        """Test that generic exceptions are caught and exit with code 1"""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_bytes(b"test data\n")

        with patch(
            "sys.argv", ["usenc", "url", "-i", str(input_file), "-o", str(output_file)]
        ), patch("usenc.cli.process_encoding", side_effect=RuntimeError("Something went wrong")):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Generic exceptions should exit with code 1
            assert exc_info.value.code == 1

            # Check error message was printed to stderr
            captured = capsys.readouterr()
            assert "Error: Something went wrong" in captured.err
