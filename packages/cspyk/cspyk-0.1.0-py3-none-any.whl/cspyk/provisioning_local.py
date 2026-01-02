import asyncio
import os
import pathlib
import signal
import sys
from typing import TYPE_CHECKING, Any

from jupyter_client.connect import KernelConnectionInfo, LocalPortCache
from jupyter_client.launcher import launch_kernel
from jupyter_client.localinterfaces import is_local_ip, local_ips
from jupyter_client.provisioning.provisioner_base import KernelProvisionerBase

class CSKernelProvisioner(KernelProvisionerBase):
    """Provisioner for CSPython kernels."""

    KERNEL_NAME = "cspython"
    process = None
    _exit_future = None
    pid = None
    pgid = None
    ip = None
    ports_cached = False
    cwd = None

    @property
    def has_process(self) -> bool:
        """Returns True if the kernel process is running."""
        # Implementation specific to CSPython kernel
        print("CSPYK: Checking if CSPython kernel process is running...")
        return self.process is not None
    
    async def poll(self) -> int | None:
        """Checks if the kernel process is still running."""
        # Implementation specific to CSPython kernel
        print("CSPYK: Polling CSPython kernel process status...")
        ret = 0
        if self.process:
            ret = self.process.poll()  # type:ignore[unreachable]
        return ret
    
    async def wait(self) -> int | None:
        """Waits for the kernel process to terminate."""
        # Implementation specific to CSPython kernel
        print("CSPYK: Waiting for CSPython kernel process to terminate...")
        ret = 0
        if self.process:
            # Use busy loop at 100ms intervals, polling until the process is
            # not alive.  If we find the process is no longer alive, complete
            # its cleanup via the blocking wait().  Callers are responsible for
            # issuing calls to wait() using a timeout (see kill()).
            while await self.poll() is None:  # type:ignore[unreachable]
                await asyncio.sleep(0.1)

            # Process is no longer alive, wait and clear
            ret = self.process.wait()
            # Make sure all the fds get closed.
            for attr in ["stdout", "stderr", "stdin"]:
                fid = getattr(self.process, attr)
                if fid:
                    fid.close()
            self.process = None  # allow has_process to now return False
        return ret 
    
    async def send_signal(self, signum: int) -> None:
        """Sends a signal to the kernel process."""
        # Implementation specific to CSPython kernel
        print(f"CSPYK: Sending signal {signum} to CSPython kernel process...")
        if self.process:
            if signum == signal.SIGINT and sys.platform == "win32":  # type:ignore[unreachable]
                from ..win_interrupt import send_interrupt

                send_interrupt(self.process.win32_interrupt_event)
                return

            # Prefer process-group over process
            if self.pgid and hasattr(os, "killpg"):
                try:
                    os.killpg(self.pgid, signum)
                    return
                except OSError:
                    pass  # We'll retry sending the signal to only the process below

            # If we're here, send the signal to the process and let caller handle exceptions
            self.process.send_signal(signum)
            return

    async def kill(self, restart: bool = False) -> None:
        """Kills the kernel process."""
        # Implementation specific to CSPython kernel
        print("CSPYK: Killing CSPython kernel process...")
        if self.process:
            if hasattr(signal, "SIGKILL"):  # type:ignore[unreachable]
                # If available, give preference to signalling the process-group over `kill()`.
                try:
                    await self.send_signal(signal.SIGKILL)
                    return
                except OSError:
                    pass
            try:
                self.process.kill()
            except OSError as e:
                print(f"CSPYK: Error killing CSPython kernel process: {e}")


    async def terminate(self, restart: bool = False) -> None:
        """Terminates the kernel process."""
        # Implementation specific to CSPython kernel
        print("CSPYK: Terminating CSPython kernel process...")
        if self.process:
            if hasattr(signal, "SIGTERM"):  # type:ignore[unreachable]
                # If available, give preference to signalling the process group over `terminate()`.
                try:
                    await self.send_signal(signal.SIGTERM)
                    return
                except OSError:
                    pass
            try:
                self.process.terminate()
            except OSError as e:
                print(f"CSPYK: Error terminating CSPython kernel process: {e}")

    @staticmethod
    def _tolerate_no_process(os_error: OSError) -> None:
        # In Windows, we will get an Access Denied error if the process
        # has already terminated. Ignore it.
        if sys.platform == "win32":
            if os_error.winerror != 5:
                err_message = f"Invalid Error, expecting error number to be 5, got {os_error}"
                raise ValueError(err_message)

        # On Unix, we may get an ESRCH error (or ProcessLookupError instance) if
        # the process has already terminated. Ignore it.
        else:
            from errno import ESRCH

            if not isinstance(os_error, ProcessLookupError) or os_error.errno != ESRCH:
                err_message = (
                    f"Invalid Error, expecting ProcessLookupError or ESRCH, got {os_error}"
                )
                raise ValueError(err_message)
            
    async def launch_kernel(self, cmd: list[str], **kwargs: Any) -> KernelConnectionInfo:
        """Launches the kernel process."""
        # Implementation specific to CSPython kernel
        print(f"CSPYK: Launching CSPython kernel with command: {cmd}")
        scrubbed_kwargs = CSKernelProvisioner._scrub_kwargs(kwargs)
        self.process = launch_kernel(cmd, **scrubbed_kwargs)
        pgid = None
        if hasattr(os, "getpgid"):
            try:
                pgid = os.getpgid(self.process.pid)
            except OSError:
                pass

        self.pid = self.process.pid
        self.pgid = pgid
        self.cwd = kwargs.get("cwd", pathlib.Path.cwd())
        return self.connection_info
    
    async def cleanup(self, restart: bool = False) -> None:
        """Cleans up resources after kernel termination."""
        # Implementation specific to CSPython kernel
        print("CSPYK: Cleaning up CSPython kernel resources...")
        if self.ports_cached and not restart:
            # provisioner is about to be destroyed, return cached ports
            lpc = LocalPortCache.instance()
            ports = (
                self.connection_info["shell_port"],
                self.connection_info["iopub_port"],
                self.connection_info["stdin_port"],
                self.connection_info["hb_port"],
                self.connection_info["control_port"],
            )
            for port in ports:
                if TYPE_CHECKING:
                    assert isinstance(port, int)
                lpc.return_port(port)
    
    async def shutdown_requested(self, restart: bool = False) -> None:
        """Handles shutdown requests for the kernel."""
        # Implementation specific to CSPython kernel
        print("CSPYK: Shutdown requested for CSPython kernel...")
        return None  # Placeholder implementation
    
    async def pre_launch(self, **kwargs: Any) -> dict[str, Any]:
        """Prepares for kernel launch."""
        # Implementation specific to CSPython kernel
        print("CSPYK: Preparing to launch CSPython kernel...")
        km = self.parent
        if km:
            if km.transport == "tcp" and not is_local_ip(km.ip):
                msg = (
                    "Can only launch a kernel on a local interface. "
                    f"This one is not: {km.ip}."
                    "Make sure that the '*_address' attributes are "
                    "configured properly. "
                    f"Currently valid addresses are: {local_ips()}"
                )
                raise RuntimeError(msg)
            # build the Popen cmd
            extra_arguments = kwargs.pop("extra_arguments", [])

            # write connection file / get default ports
            # TODO - change when handshake pattern is adopted
            if km.cache_ports and not self.ports_cached:
                lpc = LocalPortCache.instance()
                km.shell_port = lpc.find_available_port(km.ip)
                km.iopub_port = lpc.find_available_port(km.ip)
                km.stdin_port = lpc.find_available_port(km.ip)
                km.hb_port = lpc.find_available_port(km.ip)
                km.control_port = lpc.find_available_port(km.ip)
                self.ports_cached = True
            if "env" in kwargs:
                jupyter_session = kwargs["env"].get("JPY_SESSION_NAME", "")
                km.write_connection_file(jupyter_session=jupyter_session)
            else:
                km.write_connection_file()
            self.connection_info = km.get_connection_info()

            kernel_cmd = km.format_kernel_cmd(
                extra_arguments=extra_arguments
            )  # This needs to remain here for b/c
        else:
            extra_arguments = kwargs.pop("extra_arguments", [])
            kernel_cmd = self.kernel_spec.argv + extra_arguments

        return await super().pre_launch(cmd=kernel_cmd, **kwargs)
    
    def resolve_path(self, path_str: str) -> str | None:
        """Resolve path to given file."""
        path = pathlib.Path(path_str).expanduser()
        if not path.is_absolute() and self.cwd:
            path = (pathlib.Path(self.cwd) / path).resolve()
        if path.exists():
            return path.as_posix()
        return None

    @staticmethod
    def _scrub_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
        """Remove any keyword arguments that Popen does not tolerate."""
        keywords_to_scrub: list[str] = ["extra_arguments", "kernel_id"]
        scrubbed_kwargs = kwargs.copy()
        for kw in keywords_to_scrub:
            scrubbed_kwargs.pop(kw, None)
        return scrubbed_kwargs

    async def post_launch(self, **kwargs: Any) -> None:
        """Finalizes after kernel launch."""
        # Implementation specific to CSPython kernel
        print("CSPYK: Finalizing CSPython kernel launch...")
        return None  # Placeholder implementation
    
    async def get_provisioner_info(self) -> dict[str, Any]:
        """Returns information about the provisioner."""
        print("CSPYK: Getting provisioner information...")
        provisioner_info = await super().get_provisioner_info()
        provisioner_info.update({"pid": self.pid, "pgid": self.pgid, "ip": self.ip})
        return provisioner_info 

    async def load_provisioner_info(self, provisioner_info: dict) -> None:
        """Loads provisioner information."""
        # Implementation specific to CSPython kernel
        print("CSPYK: Loading provisioner information...")
        await super().load_provisioner_info(provisioner_info)
        self.pid = provisioner_info["pid"]
        self.pgid = provisioner_info["pgid"]
        self.ip = provisioner_info["ip"] 
    
    def get_shutdown_wait_time(self, recommended: float = 5.0) -> float:
        """Returns the wait time for shutdown."""
        print("CSPYK: Getting shutdown wait time...")
        return recommended  # Placeholder implementation
    
    def get_stable_start_time(self, recommended: float = 10.0) -> float:
        """Returns the stable start time for the kernel."""
        print("CSPYK: Getting stable start time...")
        return recommended  # Placeholder implementation    
    

