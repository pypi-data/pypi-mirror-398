import time


def wait_task_executed(qtapp, widget, timeout=10):
    t0 = time.time()
    while qtapp.hasPendingEvents() or not widget.task_done:
        qtapp.processEvents()
        if timeout is not None and (time.time() - t0) > timeout:
            raise TimeoutError("Execution failed")
        time.sleep(0.5)
