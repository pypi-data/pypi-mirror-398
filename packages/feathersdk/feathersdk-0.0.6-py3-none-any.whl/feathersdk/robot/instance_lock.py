import os
import psutil
import signal
from filelock import FileLock, Timeout as _FLTimeoutError
import time


LOCK_FILE_PATH = "/feathersys/user_config/.robot_instance.lock"
PID_FILE_PATH = "/feathersys/user_config/.robot_instance.pid"
LOCK_TIMEOUT_SECONDS = 1.0
SIGTERM_TIMEOUT_SECONDS = 0.2
_FILE_LOCK_MODE = 0o666  # Need to explicitly set global r/w in case we're running as root, and non-root is checking

__LOCK_ACQUIRED = False

# Makes sure that if you fork this process, the lock is reset
def __onfork_reset_lock_acquired() -> None:
    global __LOCK_ACQUIRED
    __LOCK_ACQUIRED = False
os.register_at_fork(after_in_child=__onfork_reset_lock_acquired)


class InstanceLockError(Exception):
    """Base class for all instance lock errors."""
    pass

class FileLockTimeoutError(InstanceLockError):
    """Raised when the file lock times out."""
    def __init__(self, lock_file_path: str):
        self.lock_file_path = lock_file_path
        super().__init__(f"Failed to acquire file lock: {lock_file_path}. Check no other processes are running " \
                         "with Robot() instances, and remove the file with `rm {lock_file_path}`.")

class AlreadyHaveInstanceLockError(InstanceLockError):
    """Raised when the robot instance lock is already held by the current process."""
    def __init__(self):
        super().__init__("We already have the instance lock")

class DidNotHaveInstanceLockError(InstanceLockError):
    """Raised when the robot instance lock is not held by the current process."""
    def __init__(self):
        super().__init__("We do not have the instance lock")

class InvalidPIDFileError(InstanceLockError):
    """Raised when the PID in the PID file is invalid."""
    def __init__(self, pid_file_path: str):
        self.pid_file_path = pid_file_path
        super().__init__(f"Failed to parse PID from PID file: {pid_file_path}. Check no other processes are running " \
                         "with Robot() instances, and remove the file with `rm {pid_file_path}`.")

class FailedToAcquireInstanceLockError(InstanceLockError):
    """Raised when the instance lock cannot be obtained because another process has it."""
    def __init__(self, instance_pid: int, can_kill: bool):
        self.instance_pid = instance_pid
        self.can_kill = can_kill
        cannot_kill_msg = "" if can_kill else "\nNOTE: This process wouldn't have had permissions to kill the " \
            "previous instance. You'd have to either kill it manually or run this process as sudo."
        super().__init__(f"Another instance of the robot is already running. Use override_lock=True to override the " \
                         f"lock and kill the previous instance, or run `sudo kill -9 {instance_pid}` to kill the " \
                         f"previous instance.{cannot_kill_msg}")

class KillPermissionsError(InstanceLockError):
    """Raised when the current process doesn't have permissions to kill the previous instance."""
    def __init__(self, instance_pid: int):
        self.instance_pid = instance_pid
        super().__init__(f"This process doesn't have permissions to kill the previous instance {instance_pid}. You'd " \
                         "have to either kill it manually or run this process as sudo.")


def get_robot_instance_lock(
    override_lock: bool = False, 
    strict: bool = True, 
    timeout: float = LOCK_TIMEOUT_SECONDS
) -> None:
    """Get the lock for the robot instance.

    Ensures that only one instance of the robot is running at a time. Does this by creating a file lock in the
    /feathersys/user_config directory. Lock file is named ".robot_instance.lock", and obtaining the lock allows a
    process to interact with the PID_FILE_PATH file which contains the PID of the running instance.

    If the pid file exists but the process is not running, the pid file will be removed and we will write our own PID
    to it. If the process is still running, we will raise an error (unless override_lock is True, in which case we will 
    kill the previous instance then write our own PID to the pid file).

    NOTE: You will require correct permissions to kill the previous instance. Either sudo, or the current user must
    have permissions to kill the previous instance.

    Args:
        override_lock: If True, will override the lock, killing the previous instance and allowing a new one to run. If
            False, will raise an error if the previous instance is still running.
        strict: If True, will raise an error if we attempt to acquire the lock while we already have it. Otherwise,
            doing so would succeed quietly.
        timeout: The timeout in seconds to wait for the file lock to be acquired.
    """
    os.makedirs(os.path.dirname(LOCK_FILE_PATH), exist_ok=True)
    
    global __LOCK_ACQUIRED
    if __LOCK_ACQUIRED:
        if strict:
            raise AlreadyHaveInstanceLockError()
        else:
            print("We already have the instance lock")
            return

    # In case we ever decide to change what we write to the PID file, this is a helper function to do so
    def _write_pid_file() -> None:
        global __LOCK_ACQUIRED
        with open(PID_FILE_PATH, 'w') as f:
            f.write(str(os.getpid()))
        __LOCK_ACQUIRED = True
        print("Successfully acquired robot instance lock")

    # Attempt to gain the lock by creating the lock file with current PID
    try:
        with FileLock(LOCK_FILE_PATH, timeout=timeout, mode=_FILE_LOCK_MODE):
            if not os.path.exists(PID_FILE_PATH):
                print(f"No PID file {PID_FILE_PATH} found, writing our own PID")
                _write_pid_file()
                return
            
            # Otherwise, read the PID to see if that process is still running
            pid = _parse_pid_from_pid_file()
            
            # If the process is not running, remove the PID file and replace it with our own. Doesn't need special perms
            if not _is_process_running(pid):
                os.remove(PID_FILE_PATH)
                print(f"Removed PID file {PID_FILE_PATH} because previous instance {pid} is not running")
                _write_pid_file()
                return
            
            # If the process is us, raise an error
            if pid == os.getpid():
                if strict:
                    raise AlreadyHaveInstanceLockError()
                __LOCK_ACQUIRED = True
                print("WARNING: somehow __LOCK_ACQUIRED was false but we own the lock!")
                return
            
            # Check if we have permissions to kill the previous instance
            try:
                os.kill(pid, 0)
                can_kill = True
            except (OSError, PermissionError):
                can_kill = False
            
            # The process is still running. If override_lock is False, raise an error
            if not override_lock:
                raise FailedToAcquireInstanceLockError(pid, can_kill)
            
            # If we can't kill the previous instance, raise an error
            if not can_kill:
                raise KillPermissionsError(pid)
            
            # We can kill the previous instance. Attempt to send a SIGTERM
            os.kill(pid, signal.SIGTERM)
            print(f"Sent SIGTERM to previous instance {pid}, waiting up to {SIGTERM_TIMEOUT_SECONDS} seconds to exit")

            init_time = time.time()
            while time.time() - init_time < SIGTERM_TIMEOUT_SECONDS:
                if not _is_process_running(pid):
                    print(f"Previous instance {pid} has exited")
                    break
                time.sleep(0.01)
            else:
                # Sigterm timed out, send SIGKILL
                print(f"Previous instance {pid} did not exit within {SIGTERM_TIMEOUT_SECONDS} seconds, sending SIGKILL")
                os.kill(pid, signal.SIGKILL)
                # Wait a bit for the process to become a zombie, then check
                time.sleep(0.1)
            
            # Make sure previous instance is actually dead (not just a zombie)
            if _is_process_running(pid):
                # Process is still running (not a zombie), which shouldn't happen after SIGKILL
                raise RuntimeError(f"Previous instance {pid} is somehow still alive after sigkill")
            else:
                print(f"Previous instance {pid} has been terminated")
            
            # Write our own PID to the pid file
            _write_pid_file()
    
    except _FLTimeoutError:
        raise FileLockTimeoutError(LOCK_FILE_PATH)


def release_robot_instance_lock(timeout: float = LOCK_TIMEOUT_SECONDS) -> None:
    """Release the robot instance lock

    Args:
        timeout: The timeout in seconds to wait for the file lock to be acquired.
    """
    global __LOCK_ACQUIRED
    if not __LOCK_ACQUIRED:
        raise DidNotHaveInstanceLockError()
    
    os.makedirs(os.path.dirname(LOCK_FILE_PATH), exist_ok=True)
    
    with FileLock(LOCK_FILE_PATH, timeout=timeout, mode=_FILE_LOCK_MODE):
        # Make sure we have the lock
        if not os.path.exists(PID_FILE_PATH) or _parse_pid_from_pid_file() != os.getpid():
            raise DidNotHaveInstanceLockError()
        
        # We have it, remove the PID file
        os.remove(PID_FILE_PATH)
        __LOCK_ACQUIRED = False
        print("Successfully released robot instance lock")


def is_robot_instance_locked() -> bool:
    """Check if the robot instance lock is held by the current process"""
    return __LOCK_ACQUIRED


def _is_process_running(pid: int) -> bool:
    """Check if a process is actually running (not a zombie)."""
    if not psutil.pid_exists(pid):
        return False
    
    try:
        # Check if process is a zombie - zombies are considered "dead" for our purposes
        if psutil.Process(pid).status() == psutil.STATUS_ZOMBIE:
            return False
        return True
    except psutil.NoSuchProcess:  # Process doesn't exist, shouldn't ever happen since we check pid_exists first
        return False
    except psutil.AccessDenied:
        # Can't access process info, but it exists - assume it's running
        return True


def _parse_pid_from_pid_file() -> int:
    """Get the PID of the running robot instance. Assumes file exists and we have the file lock"""
    with open(PID_FILE_PATH, 'r') as f:
        file_str = f.read()
    try:
        return int(file_str.strip())
    except ValueError:
        raise InvalidPIDFileError(PID_FILE_PATH)