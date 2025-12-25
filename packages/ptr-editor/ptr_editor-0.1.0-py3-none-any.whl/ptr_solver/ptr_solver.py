import json
import os
import shutil
import threading
from pathlib import Path
from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory

import spiceypy
from attrs import define, field
from loguru import logger as log
from planetary_coverage import TourConfig
from quick_spice_manager import SpiceManager

# from ptr_editor.generators.base import PtrElementGenerator


def _stream_reader(stream, stream_name: str, callback):
    """Read from a stream line by line in a thread and call callback for each line.

    Args:
        stream: The stream to read from (stdout or stderr)
        stream_name: Name of the stream for logging ("stdout" or "stderr")
        callback: Function to call for each line read
    """
    try:
        for line in iter(stream.readline, b""):
            if line:
                decoded_line = line.decode("utf-8").rstrip()
                callback(stream_name, decoded_line)
    except Exception as e:
        log.error(f"Error reading from {stream_name}: {e}")
    finally:
        stream.close()


def _log_ptwrapper_output(stream_name: str, line: str):
    """Log ptwrapper output to loguru with appropriate level.

    Args:
        stream_name: "stdout" or "stderr"
        line: The line to log
    """
    # Parse common ptwrapper patterns and log appropriately
    line_lower = line.lower()

    # Check for error patterns
    if "error" in line_lower or "failed" in line_lower or stream_name == "stderr":
        log.error(f"[ptwrapper:{stream_name}] {line}")
    # Check for warning patterns
    elif "warning" in line_lower or "warn" in line_lower:
        log.warning(f"[ptwrapper:{stream_name}] {line}")
    # Check for info patterns
    elif any(
        keyword in line_lower
        for keyword in ["info", "processing", "generating", "writing"]
    ):
        log.info(f"[ptwrapper:{stream_name}] {line}")
    # Everything else as debug
    else:
        log.debug(f"[ptwrapper:{stream_name}] {line}")


@define
class PtrSolution:
    """Context manager for PTR solution CK files.

    Manages loading and unloading of CK kernels into the SPICE kernel pool.
    Can be used as a context manager to automatically handle kernel lifecycle.

    Example:
        >>> solution = solve_attitude(ptr_content)
        >>> with solution:
        ...     # CK kernel is loaded and available in SPICE pool
        ...     # Do SPICE operations here
        ...     pass
        >>> # Kernel is automatically unloaded when exiting context

        >>> # Or manually control loading/unloading
        >>> solution.load()
        >>> # Do SPICE operations
        >>> solution.unload()
    """

    ck_file: Path = field(converter=Path)
    errors: list = field(factory=list)
    _is_loaded: bool = field(init=False, default=False)

    def __fspath__(self) -> str:
        return str(self.ck_file)

    def load_ck(self) -> None:
        """Load the CK kernel into the SPICE kernel pool."""
        if self._is_loaded:
            log.warning(f"Kernel {self.ck_file} is already loaded")
            return

        if not self.ck_file.exists():
            msg = f"CK file {self.ck_file} does not exist"
            raise FileNotFoundError(msg)

        log.debug(f"Loading kernel {self.ck_file}")
        spiceypy.furnsh(str(self.ck_file))
        self._is_loaded = True

    def unload_ck(self) -> None:
        """Unload the CK kernel from the SPICE kernel pool."""
        if not self._is_loaded:
            log.warning(f"Kernel {self.ck_file} is not currently loaded")
            return

        log.debug(f"Unloading kernel {self.ck_file}")
        spiceypy.unload(str(self.ck_file))
        self._is_loaded = False

    def __enter__(self):
        """Enter context manager - load the CK kernel into SPICE pool.

        Returns:
            self: The PtrSolution instance for convenient access.
        """
        self.load_ck()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit context manager - unload the CK kernel from SPICE pool.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_value: Exception value if an exception was raised.
            traceback: Traceback if an exception was raised.

        Returns:
            None (does not suppress exceptions)
        """
        self.unload_ck()


# module, severity, text, time
def parse_ptwrapper_log(
    logs: list[dict],
    raise_if_error=False,
) -> tuple[list[dict], list[dict], list[dict]]:
    errors = []
    warnings = []
    for item in logs:
        if item.get("severity") == "ERROR":
            log.error(f"{item['module']} - {item['text']} @{item['time']}")
            errors.append(item)
            if raise_if_error:
                msg = "Error in log!"
                raise ValueError(msg)
        elif item.get("severity") == "WARNING":
            log.warning(f"{item['module']} - {item['text']} @{item['time']}")
            warnings.append(item)

    return errors, warnings, logs


def solve_attitude_via_ptwrapper(
    ptr_content: str,
    metakernel: str | Path | TourConfig,
    out_folder: str | Path = Path("./"),
    ck_name: str = "result.ck",
    dt: float = 5,
    
    raise_on_missing_ck=True,
    cleanup=True,
) -> PtrSolution:
    if not isinstance(metakernel, TourConfig) and not Path(metakernel).exists():
        msg = "No MK file at {mk}"
        raise FileNotFoundError(msg)

    log.debug(f"Solving ptr with text \n {ptr_content}")

    out_folder = Path(out_folder)
    out_folder.mkdir(exist_ok=True, parents=True)
    # out_ck = out_foder / ck_name

    # outdir = Path("output")
    # outdir.mkdir(exist_ok=True)
    # log.debug(f" Output dir for ptwrapper is set to {outdir}")
    with TemporaryDirectory(delete=cleanup) as dir:
        dir = Path(dir)
        ptr_file = dir / "input.ptr"
        with ptr_file.open(mode="w") as file:
            file.write(ptr_content)

        if isinstance(metakernel, TourConfig):
            log.debug("Retrieving the mk from a tour config, might be incomplete.")
            # metakernel.load_kernels()
            meta = metakernel.kernels[0]
            mkname = dir / "input_metakernel.tm"
            with meta as m:
                shutil.copy(str(m), mkname)

            metakernel = mkname

        # -pw \ no using -pw for now
        command = f"ptwrapper  -m {metakernel} -p {ptr_file} -t {dt} -w {dir}"

        log.debug(f"Executing {command}")

        # if not cleanup:
        #     command += " -nc"

        current = Path.cwd()
        try:
            log.debug(f"Moving to work dir {dir}")
            os.chdir(dir)

            # Start process with pipes for stdout and stderr
            # bufsize=0 for unbuffered (immediate output capture in binary mode)
            process = Popen(
                command,
                stdout=PIPE,
                stderr=PIPE,
                shell=True,
                bufsize=0,
            )

            # Start threads to read stdout and stderr
            stdout_thread = threading.Thread(
                target=_stream_reader,
                args=(process.stdout, "stdout", _log_ptwrapper_output),
                daemon=True,
            )
            stderr_thread = threading.Thread(
                target=_stream_reader,
                args=(process.stderr, "stderr", _log_ptwrapper_output),
                daemon=True,
            )

            stdout_thread.start()
            stderr_thread.start()

            # Wait for process to complete
            return_code = process.wait()

            # Wait for threads to finish reading all output
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)

            if return_code != 0:
                msg = f"ptwrapper exited with non-zero return code: {return_code}"
                log.error(msg)
                log.error(f"Command line was: {command}")
                raise RuntimeError(msg)

        except Exception as e:
            log.error(f"An error occurred during execution of ptwrapper: {e}")
            raise
        finally:  # whatever happens just go back
            os.chdir(current)

        in_ck = dir / "juice_sc_input_v01.bc"
        in_ptr = dir / "input_resolved.ptx"
        in_log = dir / "input_osve_log.json"
        in_power = dir / "input_power.csv"

        if not Path(in_ck).exists():
            if raise_on_missing_ck:
                msg = (
                    f"CK file {in_ck} not found. "
                    "Something went wrong with the generation in ptwrapper."
                )
                raise FileNotFoundError(
                    msg,
                )
            log.error(
                f"CK file {in_ck} not found. "
                "Something went wrong with the generation in ptwrapper.",
            )
            out_ck = None

        with Path(in_log).open() as logf:
            log_json = json.load(logf)

        errors, _warnings, _logs = parse_ptwrapper_log(log_json)

        fname = Path(ck_name).with_suffix("")

        out_ck: str | Path = out_folder / ck_name
        out_ptr: str | Path = out_folder / f"{fname}_results.ptr"
        out_log: str | Path = out_folder / f"{fname}_log.json"
        out_power: str | Path = out_folder / f"{fname}_input_power.csv"

        shutil.move(in_ck, out_ck)
        shutil.move(in_ptr, out_ptr)
        shutil.move(in_log, out_log)
        try:
            shutil.move(in_power, out_power)
        except Exception as e:
            log.warning(f"Error moving power file: {e}. Maybe ptwrapper was run without -pw")

    return PtrSolution(ck_file=out_ck, errors=errors)

    # return in_ck, in_ptr, in_log, [errors, warnings, logs]


def solve_attitude(
    ptr: str,
    out_folder: str | Path = Path("./"),
    ck_name: str = "ckfile.ck",
    metakernel: str = "5_1_150lb_23_1_a3",
    dt: int = 5,
    raise_on_missing_ck: bool = True,
    cleanup: bool = True,
) -> PtrSolution:
    """Solve attitude using ptwrapper.

    Args:
        ptr: PTR content as string
        out_folder: Output folder for results
        ck_name: Name for the output CK file
        metakernel: Metakernel identifier or path
        dt: Time step for attitude computation in seconds
        raise_on_missing_ck: Whether to raise an error if CK file is not generated
        cleanup: Whether to cleanup temporary files after processing

    Returns:
        PtrSolution containing the path to the CK file and any errors
    """
    log.debug(f"Solving attitude with metakernel {metakernel}")
    man = SpiceManager(mk=metakernel)

    return solve_attitude_via_ptwrapper(
        ptr,
        metakernel=man.tour_config,
        out_folder=out_folder,
        ck_name=ck_name,
        dt=dt,
        raise_on_missing_ck=raise_on_missing_ck,
        cleanup=cleanup,
    )
