"""
Implementation for the callback that manages communication with EdgeFirst Studio
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

import threading
from queue import Queue, Empty
import time

from edgefirst.validator.evaluators.callbacks import PlotsCallback, CallbacksList

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import Evaluator


class StudioProgress:
    """
    Deploy standard validation from the existing evaluator objects
    but also provide communication to EdgeFirst Studio to report
    the progress and the final metrics and evaluation of the model
    performance.

    Parameters
    ----------
    evaluator: Evaluator
        This object handles running validation by iterating through
        the dataset samples and run model inference to calculate the
        validation metrics at the end of the process.
    """

    def __init__(self, evaluator: Evaluator):
        self.evaluator = evaluator
        plots_callback = PlotsCallback(
            studio_publisher=evaluator.stage_tracker.studio_publisher,
            parameters=self.evaluator.parameters,
            stage_tracker=self.evaluator.stage_tracker)
        self.callbacks = CallbacksList([plots_callback])

        # Non-blocking queue + single background worker thread to execute callbacks
        # Bounded queue prevents unbounded memory growth;
        # if full we fallback to sync execution.
        self._queue: Queue = Queue(maxsize=1000)
        self._stop_event = threading.Event()
        self._last_update = 0
        # NOTE: Increasing this interval results in the functions not being
        # called.
        self._update_interval = 0.0001  # Minimum seconds between updates.
        self._worker = threading.Thread(target=self._worker_loop,
                                        name="studio-callback-worker",
                                        daemon=True)
        self._worker.start()

    def _worker_loop(self):
        """
        Background worker that executes
        callback functions from the queue.
        """
        while True:
            try:
                fn, kwargs = self._queue.get(timeout=0.5)
            except Empty:
                if self._stop_event.is_set() and self._queue.empty():
                    break
                continue
            try:
                try:
                    fn(**kwargs)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    print(f"Exception in callback worker: {exc}")
                    traceback.print_exc()
            finally:
                try:
                    self._queue.task_done()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

    def _dispatch(self, method_name: str, /, **kwargs):
        """
        Enqueue a callback method for asynchronous execution.
        If the queue is full, execute synchronously as a best-effort
        fallback to avoid dropping important updates.

        Parameters
        ----------
        method_name: str
            The name of the callback method to invoke.
        **kwargs: dict
            The keyword arguments to pass to the callback method.
        """
        fn = getattr(self.callbacks, method_name)
        # Always process begin/end/error events
        critical = method_name in ('on_test_begin',
                                   'on_test_end',
                                   'on_test_error')
        current_time = time.monotonic()
        if critical or (current_time -
                        self._last_update) >= self._update_interval:
            try:
                self._queue.put_nowait((fn, kwargs))
                self._last_update = current_time
            except Exception:  # pylint: disable=broad-exception-caught
                if critical:
                    # Only fall back to sync for critical updates.
                    try:
                        fn(**kwargs)
                    except Exception:  # pylint: disable=broad-exception-caught
                        traceback.print_exc()

    def _drain_and_stop(self, timeout: float = 10.0):
        """
        Wait for queued tasks to finish
        and stop the background worker.

        Parameters
        ----------
        timeout: float
            The maximum time to wait for the worker to stop.
        """
        # Wait for tasks to be processed
        try:
            self._queue.join()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        self._stop_event.set()
        self._worker.join(timeout=timeout)

    def group_evaluation(self, epoch: int = 0, reset: bool = True):
        """
        Runs model validation on all samples in the dataset.

        Parameters
        ----------
        epoch: int
            This is the training epoch number. This
            parameter is internal for ModelPack usage.
            Standalone validation does not use this parameter.
        reset: bool
            This is an optional parameter that controls the reset state.
            By default, it will reset at the end of validation to erase
            the data in the containers.
        """
        save_image = bool(self.evaluator.parameters.validation.visualize or
                          self.evaluator.parameters.validation.tensorboard)

        logs = {
            "total": len(self.evaluator.dataset)
        }

        i = 0
        try:
            self._dispatch("on_test_begin", logs=logs)
            for instance in self.evaluator.instance_collector():
                i += 1
                self._dispatch("on_test_batch_begin", step=i, logs=logs)
                if self.evaluator.parameters.validation.display >= 0:
                    if (self.evaluator.counter <
                            self.evaluator.parameters.validation.display):
                        save_image = True
                        self.evaluator.counter += 1
                    else:
                        save_image = False

                self.evaluator.single_evaluation(
                    instance, epoch=epoch, save_image=save_image)
                self._dispatch("on_test_batch_end", step=i, logs=logs)
            metrics, plots = self.end(epoch=epoch, reset=reset)

            if (self.evaluator.parameters.model.common.with_boxes and
                    self.evaluator.parameters.model.common.with_masks):
                logs["multitask"] = metrics
                logs["plots"] = plots
                logs["timings"] = metrics.timings

            elif self.evaluator.parameters.model.common.with_boxes:
                logs["detection"] = metrics
                logs["plots"] = plots
                logs["timings"] = metrics.timings

            elif self.evaluator.parameters.model.common.with_masks:
                logs["segmentation"] = metrics
                logs["plots"] = plots
                logs["timings"] = metrics.timings

            self._dispatch("on_test_end", logs=logs)
            # Ensure queued callback tasks complete before returning from
            # evaluation
            self._drain_and_stop()

        except Exception as e:
            self._dispatch("on_test_error", step=i, error=e, logs=logs)
            # Ensure error callback is processed and worker stopped
            self._drain_and_stop()
            error = traceback.format_exc()
            print(error)
            raise e

    def end(self, epoch: int = 0, reset: bool = True):
        """
        Calculate final metrics and publish the results into
        EdgeFirst Studio.

        Parameters
        ----------
        epoch: int
            This is the training epoch number. This
            parameter is internal for ModelPack usage.
            Standalone validation does not use this parameter.
        reset: bool
            This is an optional parameter that controls the reset state.
            By default, it will reset at the end of validation to erase
            the data in the containers.

        Returns
        -------
        Tuple[Metrics, Metrics]
            This returns the detection and segmentation metrics for
            multitask. Otherwise, for single tasks, only one or
            the other is returned.
        """
        # Ensure any pending callback tasks are flushed
        # before final metrics are posted
        try:
            self._queue.join()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return self.evaluator.end(epoch=epoch, reset=reset)
