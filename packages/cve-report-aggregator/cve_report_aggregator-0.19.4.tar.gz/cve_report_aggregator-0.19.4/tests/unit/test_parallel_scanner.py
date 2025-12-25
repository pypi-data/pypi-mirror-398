"""Unit tests for parallel scanner module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cve_report_aggregator.core.exceptions import ScannerExecutionError
from cve_report_aggregator.processing.parallel_scanner import get_optimal_workers, parallel_scan_files


class TestGetOptimalWorkers:
    """Tests for get_optimal_workers function."""

    def test_returns_specified_max_workers(self):
        """Test that specified max_workers is returned."""
        assert get_optimal_workers(4) == 4
        assert get_optimal_workers(8) == 8
        assert get_optimal_workers(1) == 1

    def test_returns_auto_detect_for_invalid_input(self):
        """Test that auto-detection is used for invalid input."""
        # When max_workers <= 0, function auto-detects based on CPU count
        result_zero = get_optimal_workers(0)
        result_negative = get_optimal_workers(-5)
        # Should be between 1 and 8 (auto-detected)
        assert 1 <= result_zero <= 8
        assert 1 <= result_negative <= 8

    @patch("os.cpu_count", return_value=4)
    def test_auto_detects_workers_from_cpu_count(self, mock_cpu_count):
        """Test auto-detection based on CPU count."""
        # Formula: min(cpu_count, 8)
        # With 4 CPUs: min(4, 8) = 4
        assert get_optimal_workers(None) == 4

    @patch("os.cpu_count", return_value=1)
    def test_auto_detects_minimum_workers_single_cpu(self, mock_cpu_count):
        """Test auto-detection with single CPU returns minimum."""
        # Formula: min(1, 8) = 1
        assert get_optimal_workers(None) == 1

    @patch("os.cpu_count", return_value=None)
    def test_handles_cpu_count_unavailable(self, mock_cpu_count):
        """Test graceful handling when CPU count is unavailable."""
        # Should default to 1 when cpu_count() returns None
        assert get_optimal_workers(None) == 1


class TestParallelScanFiles:
    """Tests for parallel_scan_files function."""

    @pytest.fixture
    def mock_scan_func(self):
        """Create a mock scan function that returns predictable output paths."""

        def scan_func(input_file: Path, output_dir: Path, verbose: bool = False) -> Path:
            return output_dir / f"{input_file.stem}_scanned.json"

        return scan_func

    @pytest.fixture
    def temp_files(self, tmp_path):
        """Create temporary test files."""
        files = []
        for i in range(3):
            file_path = tmp_path / f"test_{i}.json"
            file_path.write_text(f'{{"test": {i}}}')
            files.append(file_path)
        return files

    def test_single_file_processing(self, tmp_path, mock_scan_func):
        """Test processing single file without parallelization overhead."""
        input_files = [tmp_path / "test.json"]
        input_files[0].write_text('{"test": 1}')
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        results = parallel_scan_files(
            files=input_files,
            scan_func=mock_scan_func,
            output_dir=output_dir,
            verbose=False,
            max_workers=1,
        )

        assert len(results) == 1
        assert results[0][0] == input_files[0]
        assert results[0][1] == output_dir / "test_scanned.json"

    def test_multiple_file_parallel_processing(self, tmp_path, temp_files, mock_scan_func):
        """Test parallel processing of multiple files."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        results = parallel_scan_files(
            files=temp_files,
            scan_func=mock_scan_func,
            output_dir=output_dir,
            verbose=False,
            max_workers=2,
        )

        assert len(results) == 3
        # Verify all input files were processed
        input_files_in_results = {result[0] for result in results}
        assert input_files_in_results == set(temp_files)
        # Verify all output files follow expected naming
        for result in results:
            assert result[1].parent == output_dir
            assert result[1].name.endswith("_scanned.json")

    def test_scan_function_receives_correct_parameters(self, tmp_path):
        """Test that scan function is called with correct parameters."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"test": 1}')
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_func = MagicMock(return_value=output_dir / "result.json")

        parallel_scan_files(
            files=[input_file],
            scan_func=mock_func,
            output_dir=output_dir,
            verbose=True,
            max_workers=1,
        )

        # Function is called with positional args (file_path, output_dir, verbose)
        mock_func.assert_called_once_with(input_file, output_dir, True)

    def test_error_handling_single_file(self, tmp_path):
        """Test error handling when single file scan fails."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"test": 1}')
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        def failing_scan_func(input_file: Path, output_dir: Path, verbose: bool = False) -> Path:
            raise RuntimeError("Scan failed")

        # Single-file optimization path doesn't wrap exceptions
        with pytest.raises(RuntimeError) as exc_info:
            parallel_scan_files(
                files=[input_file],
                scan_func=failing_scan_func,
                output_dir=output_dir,
                verbose=False,
                max_workers=1,
            )

        assert "Scan failed" in str(exc_info.value)

    def test_partial_failure_continues_with_results(self, tmp_path, temp_files):
        """Test that partial failures continue with successful results."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        def partially_failing_scan_func(input_file: Path, output_dir: Path, verbose: bool = False) -> Path:
            # Fail on first file, succeed on others
            if "test_0" in input_file.name:
                raise RuntimeError("Scan failed for test_0")
            output_file = output_dir / f"{input_file.stem}_scanned.json"
            output_file.touch()
            return output_file

        # Should NOT raise - continues with partial results
        results = parallel_scan_files(
            files=temp_files,
            scan_func=partially_failing_scan_func,
            output_dir=output_dir,
            verbose=False,
            max_workers=2,
        )

        # Should have 2 successful results (test_1 and test_2)
        assert len(results) == 2
        # Results are tuples of (input_path, output_path)
        output_names = [output_path.name for _, output_path in results]
        assert "test_1_scanned.json" in output_names
        assert "test_2_scanned.json" in output_names

    def test_all_files_fail(self, tmp_path, temp_files):
        """Test error handling when all file scans fail."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        def always_failing_scan_func(input_file: Path, output_dir: Path, verbose: bool = False) -> Path:
            raise RuntimeError(f"Failed to scan {input_file.name}")

        with pytest.raises(ScannerExecutionError) as exc_info:
            parallel_scan_files(
                files=temp_files,
                scan_func=always_failing_scan_func,
                output_dir=output_dir,
                verbose=False,
                max_workers=2,
            )

        error_message = str(exc_info.value)
        assert "Failed to scan all 3 files" in error_message
        # All three files should be in the error message
        assert "test_0.json" in error_message
        assert "test_1.json" in error_message
        assert "test_2.json" in error_message

    def test_empty_file_list(self, tmp_path, mock_scan_func):
        """Test handling of empty file list."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        results = parallel_scan_files(
            files=[],
            scan_func=mock_scan_func,
            output_dir=output_dir,
            verbose=False,
            max_workers=2,
        )

        assert results == []

    def test_custom_operation_name(self, tmp_path, mock_scan_func):
        """Test that custom operation name is used in progress display."""
        input_file = tmp_path / "test.json"
        input_file.write_text('{"test": 1}')
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Should not raise an exception - operation name is used internally
        results = parallel_scan_files(
            files=[input_file],
            scan_func=mock_scan_func,
            output_dir=output_dir,
            verbose=True,
            max_workers=1,
            operation_name="Custom Scanning Operation",
        )

        assert len(results) == 1

    def test_respects_max_workers_limit(self, tmp_path, temp_files):
        """Test that max_workers parameter is respected."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Track concurrent execution
        active_workers = []
        max_concurrent = [0]

        def tracking_scan_func(input_file: Path, output_dir: Path, verbose: bool = False) -> Path:
            import threading
            import time

            thread_id = threading.current_thread().ident
            active_workers.append(thread_id)
            max_concurrent[0] = max(max_concurrent[0], len(set(active_workers)))
            time.sleep(0.01)  # Small delay to ensure overlap
            return output_dir / f"{input_file.stem}_scanned.json"

        results = parallel_scan_files(
            files=temp_files,
            scan_func=tracking_scan_func,
            output_dir=output_dir,
            verbose=False,
            max_workers=2,
        )

        assert len(results) == 3
        # Should not exceed max_workers
        assert max_concurrent[0] <= 2

    def test_verbose_mode_outputs_progress(self, tmp_path, temp_files, mock_scan_func, capsys):
        """Test that verbose mode produces output."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Note: Rich progress uses stderr for output
        results = parallel_scan_files(
            files=temp_files,
            scan_func=mock_scan_func,
            output_dir=output_dir,
            verbose=True,
            max_workers=2,
        )

        assert len(results) == 3
        # Can't easily test Rich output, but verify no exceptions


class TestParallelProcessItems:
    """Tests for parallel_process_items function."""

    def test_empty_items_list(self):
        """Test handling of empty items list."""
        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        def process_func(item, verbose=False):
            return item * 2

        results = parallel_process_items(
            items=[],
            process_func=process_func,
            verbose=False,
            max_workers=2,
        )

        assert results == []

    def test_single_item_processing(self):
        """Test processing single item without parallelization overhead."""
        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        def process_func(item, verbose=False):
            return item * 2

        results = parallel_process_items(
            items=[5],
            process_func=process_func,
            verbose=False,
            max_workers=1,
        )

        assert results == [10]

    def test_multiple_items_parallel_processing(self):
        """Test parallel processing of multiple items."""
        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        def process_func(item, verbose=False):
            return item * 2

        results = parallel_process_items(
            items=[1, 2, 3, 4, 5],
            process_func=process_func,
            verbose=False,
            max_workers=2,
        )

        assert len(results) == 5
        assert set(results) == {2, 4, 6, 8, 10}

    def test_process_function_receives_verbose_flag(self):
        """Test that process function receives verbose parameter."""
        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        received_args = []

        def process_func(item, verbose=False):
            received_args.append((item, verbose))
            return item

        parallel_process_items(
            items=[1],
            process_func=process_func,
            verbose=True,
            max_workers=1,
        )

        assert len(received_args) == 1
        assert received_args[0] == (1, True)

    def test_error_handling_raises_exception(self):
        """Test that processing errors are raised."""
        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        def failing_process_func(item, verbose=False):
            if item == 2:
                raise RuntimeError(f"Failed to process item {item}")
            return item * 2

        # Errors are wrapped in a generic Exception
        with pytest.raises(Exception) as exc_info:
            parallel_process_items(
                items=[1, 2, 3],
                process_func=failing_process_func,
                verbose=False,
                max_workers=2,
            )

        error_message = str(exc_info.value)
        assert "Failed to process" in error_message
        assert "item 2" in error_message

    def test_custom_operation_name(self):
        """Test that custom operation name is used."""
        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        def process_func(item, verbose=False):
            return item

        # Should not raise exception - operation name is used internally
        results = parallel_process_items(
            items=[1, 2],
            process_func=process_func,
            verbose=True,
            max_workers=2,
            operation_name="Custom Processing",
        )

        assert len(results) == 2

    def test_respects_max_workers(self):
        """Test that max_workers parameter is respected."""
        import threading
        import time

        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        active_workers = []
        max_concurrent = [0]

        def tracking_process_func(item, verbose=False):
            thread_id = threading.current_thread().ident
            active_workers.append(thread_id)
            max_concurrent[0] = max(max_concurrent[0], len(set(active_workers)))
            time.sleep(0.01)
            return item * 2

        results = parallel_process_items(
            items=[1, 2, 3, 4, 5],
            process_func=tracking_process_func,
            verbose=False,
            max_workers=2,
        )

        assert len(results) == 5
        # Should not exceed max_workers
        assert max_concurrent[0] <= 2

    def test_verbose_mode(self):
        """Test verbose mode produces no exceptions."""
        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        def process_func(item, verbose=False):
            return item * 2

        results = parallel_process_items(
            items=[1, 2, 3],
            process_func=process_func,
            verbose=True,
            max_workers=2,
        )

        assert len(results) == 3


class TestParallelScanFilesVerboseMode:
    """Tests for verbose mode in parallel_scan_files."""

    def test_error_handling_verbose_mode(self, tmp_path):
        """Test error handling with verbose mode enabled."""
        files = [tmp_path / "test1.json", tmp_path / "test2.json"]
        for f in files:
            f.write_text('{"test": 1}')

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        def failing_scan_func(input_file: Path, output_dir: Path, verbose: bool = False) -> Path:
            raise RuntimeError(f"Failed to scan {input_file.name}")

        with pytest.raises(ScannerExecutionError) as exc_info:
            parallel_scan_files(
                files=files,
                scan_func=failing_scan_func,
                output_dir=output_dir,
                verbose=True,  # Enable verbose mode
                max_workers=2,
            )

        error_message = str(exc_info.value)
        assert "Failed to scan" in error_message


class TestParallelProcessItemsVerboseMode:
    """Tests for verbose mode in parallel_process_items."""

    def test_single_item_verbose(self):
        """Test single item processing with verbose mode."""
        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        def process_func(item, verbose=False):
            assert verbose is True
            return item * 2

        results = parallel_process_items(
            items=[5],
            process_func=process_func,
            verbose=True,
            max_workers=1,
        )

        assert results == [10]

    def test_multiple_items_verbose(self):
        """Test multiple items processing with verbose mode."""
        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        def process_func(item, verbose=False):
            return item * 2

        results = parallel_process_items(
            items=[1, 2, 3],
            process_func=process_func,
            verbose=True,
            max_workers=2,
        )

        assert len(results) == 3
        assert set(results) == {2, 4, 6}

    def test_error_handling_verbose_mode(self):
        """Test error handling with verbose mode enabled."""
        from cve_report_aggregator.processing.parallel_scanner import parallel_process_items

        def failing_process_func(item, verbose=False):
            raise RuntimeError(f"Failed to process {item}")

        with pytest.raises(Exception) as exc_info:
            parallel_process_items(
                items=[1, 2, 3],
                process_func=failing_process_func,
                verbose=True,
                max_workers=2,
            )

        error_message = str(exc_info.value)
        assert "Failed to process" in error_message
