"""Mixin class for objects that can be solved using PTR solver."""

from __future__ import annotations
from pathlib import Path

from ptr_solver.ptr_solver import PtrSolution
import spiceypy
from loguru import logger as log


class PtrSolvableMixin:
    """
    Mixin for objects that can be solved using the PTR solver.

    This mixin provides the `solve()` method that uses the CachedPtrSolver
    to solve the object. The object must implement `to_xml()` method and
    have `ref`, `start`, and `end` attributes for logging purposes.

    It also provides context manager support to automatically load and unload
    the generated CK kernel when used with a `with` statement.

    Example:
        >>> class MyBlock(
        ...     PtrSolvableMixin
        ... ):
        ...     ref = "OBS"
        ...     start = "2024-01-01T00:00:00"
        ...     end = "2024-01-01T01:00:00"
        ...
        ...     def to_xml(
        ...         self,
        ...     ):
        ...         return "<block>...</block>"
        >>> block = MyBlock()
        >>> result = (
        ...     block.solve()
        ... )
        >>>
        >>> # Use as context manager to auto-load/unload kernel
        >>> with (
        ...     block as ck_path
        ... ):
        ...     # Kernel is loaded and available in SPICE pool
        ...     # Do SPICE operations here
        ...     pass
        >>> # Kernel is automatically unloaded when exiting context
    """

    def _solvable_ptr_(self) -> str:
        msg = "Classes using PtrSolvableMixin must implement _solvable_ptr_() method"
        raise NotImplementedError(msg)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._currently_loaded_ck = None

    def solve(
        self, mk="5_1_150lb_23_1_a3", *, use_cache: bool = True
    ) -> PtrSolution:
        """
        Solve the object using the PTR solver.

        Returns:
            The solver result containing solved pointing information.

        Raises:
            AttributeError: If the object doesn't have a `to_xml()` method.
        """
        from ptr_solver.cached_solver import CachedPtrSolver

        # Log with available attributes
        ref = getattr(self, "ref", "Unknown")
        start = getattr(self, "start", "Unknown")
        end = getattr(self, "end", "Unknown")

        log.debug(
            f"Solving {self.__class__.__name__} {ref} with start {start} and end {end}",
        )

        solver = CachedPtrSolver(
            self._solvable_ptr_(), use_cache=use_cache, metakernel=mk
        )
        return solver.solve()

    def generate(self):
        """
        Generate the CK kernel for this object.

        This method solves the object and returns the path to the generated
        CK kernel file.

        Returns:
            Path to the generated CK kernel file.
        """
        result = self.solve()
        return Path(result)

    # Context management
    def __enter__(self):
        """
        Enter context manager - load the generated CK kernel into SPICE pool.

        Returns:
            Path to the loaded CK kernel file.
        """
        # Generate and get the kernel path
        ck = self.generate()
        log.debug(f"Loading kernel {ck}")
        spiceypy.furnsh(str(ck))
        self._currently_loaded_ck = ck
        return ck

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit context manager - unload the CK kernel from SPICE pool.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_value: Exception value if an exception was raised.
            traceback: Traceback if an exception was raised.

        Returns:
            None (does not suppress exceptions)
        """
        # Unload the kernel when exiting the context
        if self._currently_loaded_ck:
            log.debug(f"Unloading kernel {self._currently_loaded_ck}")
            spiceypy.unload(str(self._currently_loaded_ck))
            self._currently_loaded_ck = None
