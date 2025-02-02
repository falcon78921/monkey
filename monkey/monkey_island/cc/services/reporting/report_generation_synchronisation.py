import logging

# TODO: Switch to threading.lock and test. Calling gevent.patch_all() is supposed to monkeypatch
#       threading to be compatible with gevent/greenlets.
from gevent.lock import BoundedSemaphore

logger = logging.getLogger(__name__)

# These are pseudo-singletons - global Locks. These locks will allow only one thread to generate
# a report at a time.
# Report generation can be quite slow if there is a lot of data, and the UI queries the Root
# service often; without
# the locks, these requests would accumulate, overload the server, eventually causing it to crash.
logger.debug("Initializing report generation locks.")
__report_generating_lock = BoundedSemaphore()
__regular_report_generating_lock = BoundedSemaphore()


def safe_generate_reports():
    # Entering the critical section; Wait until report generation is available.
    __report_generating_lock.acquire()
    try:
        report = safe_generate_regular_report()
    finally:
        # Leaving the critical section.
        __report_generating_lock.release()
    return report


def safe_generate_regular_report():
    # Local import to avoid circular imports
    from monkey_island.cc.services.reporting.report import ReportService

    try:
        __regular_report_generating_lock.acquire()
        report = ReportService.generate_report()
    finally:
        __regular_report_generating_lock.release()
    return report


def is_report_being_generated():
    # From https://docs.python.org/2/library/threading.html#threading.Semaphore.acquire:
    # When invoked with blocking set to false, do not block.
    #   If a call without an argument would block, return false immediately;
    #   otherwise, do the same thing as when called without arguments, and return true.
    is_report_being_generated_right_now = not __report_generating_lock.acquire(blocking=False)
    if not is_report_being_generated_right_now:
        # We're not using the critical resource; we just checked its state.
        __report_generating_lock.release()
    return is_report_being_generated_right_now
