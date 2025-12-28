import logging
import sys
import inspect
from typing import Optional, Any, Callable, Set, Tuple

from pygeai.cli.geai import main as geai
from pygeai.core.utils.console import Console


class Debugger:
    """
    A debugger for the GEAI application to trace and control execution flow.

    This class implements a custom debugging mechanism using Python's `sys.settrace` to intercept function calls
    and pause execution at specified breakpoints. Breakpoints can be set for specific modules or functions, allowing
    developers to inspect local variables, execute arbitrary code in the current context, and control program flow
    through an interactive command interface.
    """

    def __init__(self):
        self.setup_logging()
        self.breakpoints: Set[Tuple[Optional[str], Optional[str]]] = set()
        self.paused: bool = False
        logging.getLogger('geai').info("GEAI debugger started.")
        logging.getLogger('geai').info(f"geai module: {geai.__module__}")

    def setup_logging(self):
        logger = logging.getLogger('geai')
        logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    def add_breakpoint(self, module: Optional[str] = None, function_name: Optional[str] = None):
        """Add a breakpoint by module and/or function name."""
        self.breakpoints.add((module, function_name))
        logging.getLogger('geai').info(f"Breakpoint added: {module or '*'}:{function_name or '*'}")

    def trace_function(self, frame: sys._getframe, event: str, arg: Any) -> Callable:
        """Trace function calls to intercept execution."""
        if event != 'call':  # Only intercept function calls
            return self.trace_function

        module = frame.f_globals.get('__name__')
        function_name = frame.f_code.co_name

        # Check if the current frame matches a breakpoint
        for bp_module, bp_func in self.breakpoints:
            module_match = bp_module is None or bp_module == module
            func_match = bp_func is None or bp_func == function_name
            if module_match and func_match:
                logging.getLogger('geai').info(
                    f"Breakpoint hit at {module}.{function_name}"
                )
                self.paused = True
                self.handle_breakpoint(frame)
                self.paused = False
        return self.trace_function

    def handle_breakpoint(self, frame: sys._getframe):
        """Handle a breakpoint by prompting for interactive commands."""
        locals_info = {k: v for k, v in frame.f_locals.items()}
        logging.getLogger('geai').info(f"Local variables: {locals_info}")

        Console.write_stdout(f"\nPaused at {frame.f_globals.get('__name__')}.{frame.f_code.co_name}")
        Console.write_stdout("Enter commands to execute in the current context (type 'continue' to resume, 'quit' to exit, 'help' to display available commands):")
        while True:
            try:
                command = input("(geai-dbg) ")
                if command == 'continue' or command == 'c':
                    break
                elif command == 'quit' or command == "q":
                    logging.getLogger('geai').info("Debugger terminated by user.")
                    sys.exit(0)
                elif command == 'run' or command == 'r':
                    logging.getLogger('geai').info("Running program without further pauses.")
                    sys.settrace(None)  # Disable tracing to skip all breakpoints
                    break
                elif command == 'breakpoint-module' or command == 'bm':
                    logging.getLogger('geai').info("Adding breakpoint on module")
                    module_name = input("(geai-dbg) Enter module name (or press Enter for any module): ").strip()
                    module_name = module_name if module_name else None
                    self.add_breakpoint(module=module_name)
                elif command == 'breakpoint-function' or command == 'bf':
                    logging.getLogger('geai').info("Adding breakpoint on function name")
                    function_name = input("(geai-dbg) Enter function name (or press Enter for any function): ").strip()
                    function_name = function_name if function_name else None
                    module_name = input("(geai-dbg) Enter module name (optional, press Enter to skip): ").strip()
                    module_name = module_name if module_name else None
                    self.add_breakpoint(module=module_name, function_name=function_name)
                elif command == 'list-modules' or command == 'lm':
                    logging.getLogger('geai').info("Listing available modules")
                    modules = [m for m in sys.modules if m.startswith('pygeai')]
                    Console.write_stdout(f"Available modules: {modules}")
                elif command == 'help' or command == 'h':
                    Console.write_stdout("Available commands:")
                    Console.write_stdout("  continue, c: Resume execution until next breakpoint")
                    Console.write_stdout("  quit, q: Exit the debugger")
                    Console.write_stdout("  run, r: Run program without further pauses")
                    Console.write_stdout("  breakpoint-module, bm: Add a module breakpoint")
                    Console.write_stdout("  breakpoint-function, bf: Add a function breakpoint")
                    Console.write_stdout("  list-modules, lm: List available modules")
                    Console.write_stdout("  <Python code>: Execute arbitrary Python code in the current context")
                else:
                    logging.getLogger('geai').info(f"Executing interactive command: {command}")
                    try:
                        exec(command, frame.f_globals, frame.f_locals)
                    except Exception as e:
                        logging.getLogger('geai').error(f"Command execution failed: {e}")
            except EOFError:
                logging.getLogger('geai').info("Debugger terminated by user (EOF).")
                sys.exit(0)
            except KeyboardInterrupt:
                logging.getLogger('geai').info("Keyboard interrupt received. Continuing execution.")
                break

    def run(self):
        logging.getLogger('geai').info("Setting trace and running geai")
        sys.settrace(self.trace_function)
        try:
            geai()
        except Exception as e:
            logging.getLogger('geai').error(f"geai execution failed: {e}")
            raise
        finally:
            logging.getLogger('geai').info("Cleaning up trace")
            sys.settrace(None)


def main():
    dbg = Debugger()
    dbg.add_breakpoint(module='pygeai.cli.geai', function_name='main')
    dbg.run()


if __name__ == "__main__":
    main()
