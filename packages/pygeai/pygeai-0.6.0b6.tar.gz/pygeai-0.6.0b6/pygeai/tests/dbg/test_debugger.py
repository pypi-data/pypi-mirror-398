from unittest import TestCase
from unittest.mock import patch, MagicMock
from pygeai.dbg.debugger import Debugger


class TestDebugger(TestCase):
    """
    python -m unittest pygeai.tests.dbg.test_debugger.TestDebugger
    """

    def setUp(self):
        # Mock logging to avoid actual log output during tests
        self.logging_patch = patch('pygeai.dbg.debugger.logging')
        self.mock_logging = self.logging_patch.start()
        self.mock_logger = MagicMock()
        self.mock_logging.getLogger.return_value = self.mock_logger

        # Mock Console to avoid actual stdout writes
        self.console_patch = patch('pygeai.dbg.debugger.Console')
        self.mock_console = self.console_patch.start()
        self.mock_console.write_stdout = MagicMock()

    def tearDown(self):
        self.logging_patch.stop()
        self.console_patch.stop()

    def test_debugger_init(self):
        debugger = Debugger()
        self.assertEqual(len(debugger.breakpoints), 0)
        self.assertFalse(debugger.paused)
        self.mock_logger.info.assert_called()
        self.assertTrue(any("GEAI debugger started" in str(call) for call in self.mock_logger.info.call_args_list))

    def test_add_breakpoint_module_only(self):
        debugger = Debugger()
        debugger.add_breakpoint(module="pygeai.cli.geai")
        self.assertEqual(len(debugger.breakpoints), 1)
        self.assertIn(("pygeai.cli.geai", None), debugger.breakpoints)
        self.mock_logger.info.assert_called()
        self.assertTrue(any("Breakpoint added: pygeai.cli.geai:*" in str(call) for call in self.mock_logger.info.call_args_list))

    def test_add_breakpoint_function_only(self):
        debugger = Debugger()
        debugger.add_breakpoint(function_name="main")
        self.assertEqual(len(debugger.breakpoints), 1)
        self.assertIn((None, "main"), debugger.breakpoints)
        self.mock_logger.info.assert_called()
        self.assertTrue(any("Breakpoint added: *:main" in str(call) for call in self.mock_logger.info.call_args_list))

    def test_add_breakpoint_both(self):
        debugger = Debugger()
        debugger.add_breakpoint(module="pygeai.cli.geai", function_name="main")
        self.assertEqual(len(debugger.breakpoints), 1)
        self.assertIn(("pygeai.cli.geai", "main"), debugger.breakpoints)
        self.mock_logger.info.assert_called()
        self.assertTrue(any("Breakpoint added: pygeai.cli.geai:main" in str(call) for call in self.mock_logger.info.call_args_list))

    def test_trace_function_no_breakpoint(self):
        debugger = Debugger()
        # Reset mock to ignore initialization logs
        self.mock_logger.reset_mock()
        mock_frame = MagicMock()
        mock_frame.f_globals = {"__name__": "pygeai.cli.geai"}
        mock_frame.f_code.co_name = "main"
        result = debugger.trace_function(mock_frame, "call", None)
        self.assertEqual(result, debugger.trace_function)
        self.assertFalse(debugger.paused)
        self.mock_logger.info.assert_not_called()  # No breakpoint hit log after reset

    def test_trace_function_breakpoint_hit_module_only(self):
        debugger = Debugger()
        debugger.add_breakpoint(module="pygeai.cli.geai")
        self.mock_logger.reset_mock()
        mock_frame = MagicMock()
        mock_frame.f_globals = {"__name__": "pygeai.cli.geai"}
        mock_frame.f_code.co_name = "some_function"
        with patch('builtins.input', return_value="continue"):
            result = debugger.trace_function(mock_frame, "call", None)
            self.assertEqual(result, debugger.trace_function)
            self.mock_logger.info.assert_called()
            self.assertTrue(any("Breakpoint hit at pygeai.cli.geai.some_function" in str(call) for call in
                                self.mock_logger.info.call_args_list))

    def test_trace_function_breakpoint_hit_function_only(self):
        debugger = Debugger()
        debugger.add_breakpoint(function_name="main")
        self.mock_logger.reset_mock()
        mock_frame = MagicMock()
        mock_frame.f_globals = {"__name__": "some.module"}
        mock_frame.f_code.co_name = "main"
        with patch('builtins.input', return_value="continue"):
            result = debugger.trace_function(mock_frame, "call", None)
            self.assertEqual(result, debugger.trace_function)
            self.mock_logger.info.assert_called()
            self.assertTrue(
                any("Breakpoint hit at some.module.main" in str(call) for call in self.mock_logger.info.call_args_list))

    def test_trace_function_non_call_event(self):
        debugger = Debugger()
        self.mock_logger.reset_mock()
        mock_frame = MagicMock()
        result = debugger.trace_function(mock_frame, "return", None)
        self.assertEqual(result, debugger.trace_function)
        self.mock_logger.info.assert_not_called()  # No logging for non-call events

    def test_run_with_exception(self):
        debugger = Debugger()
        with patch('sys.settrace') as mock_settrace:
            with patch('pygeai.dbg.debugger.geai', side_effect=Exception("Test error")):
                try:
                    debugger.run()  # run() might not catch the exception in test environment
                except Exception:
                    pass  # Ignore the exception since we expect it to be logged
                self.mock_logger.error.assert_called()
                self.assertTrue(any("geai execution failed" in str(call) for call in self.mock_logger.error.call_args_list))
                self.assertTrue(any("Test error" in str(call) for call in self.mock_logger.error.call_args_list))
                mock_settrace.assert_called()  # Called at least once to set trace

    def test_run_successful(self):
        debugger = Debugger()
        with patch('sys.settrace') as mock_settrace:
            with patch('pygeai.dbg.debugger.geai') as mock_geai:
                debugger.run()
                mock_geai.assert_called_once()
                mock_settrace.assert_called()  # Called at least once to set trace
                self.mock_logger.info.assert_called()
                self.assertTrue(any("Setting trace and running geai" in str(call) for call in self.mock_logger.info.call_args_list))
                self.assertTrue(any("Cleaning up trace" in str(call) for call in self.mock_logger.info.call_args_list))