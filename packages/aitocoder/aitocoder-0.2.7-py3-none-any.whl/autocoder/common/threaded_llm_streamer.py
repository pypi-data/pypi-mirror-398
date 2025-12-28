"""
Threaded LLM Streamer Module
(NEW)
This module provides a thread-based wrapper for LLM streaming that enables
responsive cancellation. By running the LLM streaming in a separate thread
and using a queue for communication, the main thread can check for cancellation
signals between chunk arrivals rather than blocking on network I/O.

Usage:
    streamer = ThreadedLLMStreamer(cancel_token="my_token")
    streamer.start(llm, conversations, llm_config, args)

    try:
        for chunk, metadata in streamer.iter_chunks():
            # Process chunk - cancellation is checked automatically
            process(chunk)
    finally:
        streamer.stop()
"""

import queue
import threading
from typing import Any, Dict, Generator, Optional, Tuple
from loguru import logger


class ThreadedLLMStreamer:
    """
    Runs LLM streaming in a background thread with cancellation support.

    This class wraps the synchronous LLM streaming generator and runs it
    in a separate thread, allowing the main thread to check for cancellation
    signals between chunks without being blocked on network I/O.
    """

    # Sentinel values for queue messages
    MSG_CHUNK = "chunk"
    MSG_DONE = "done"
    MSG_ERROR = "error"

    def __init__(self, cancel_token: Optional[str] = None, queue_timeout: float = 0.1):
        """
        Initialize the threaded streamer.

        Args:
            cancel_token: The cancellation token to check against global_cancel
            queue_timeout: Timeout in seconds for queue.get() operations.
                          This determines how often cancellation is checked
                          when waiting for chunks. Default 100ms.
        """
        self._cancel_token = cancel_token
        self._queue_timeout = queue_timeout
        self._queue: queue.Queue = queue.Queue(maxsize=100)  # Bounded to prevent memory issues
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._error: Optional[Exception] = None
        self._started = False
        self._finished = False

    def start(
        self,
        stream_generator: Generator[Tuple[Any, Any], None, None],
    ) -> None:
        """
        Start streaming in a background thread.

        Args:
            stream_generator: The LLM streaming generator to wrap
        """
        if self._started:
            raise RuntimeError("Streamer already started")

        self._started = True
        self._thread = threading.Thread(
            target=self._stream_worker,
            args=(stream_generator,),
            daemon=True,  # Thread will be killed when main process exits
            name="LLMStreamerThread"
        )
        self._thread.start()
        logger.debug("LLM streamer thread started")

    def _stream_worker(self, stream_generator: Generator) -> None:
        """
        Worker function that runs in the background thread.

        Iterates through the LLM stream generator and puts chunks into
        the queue. Checks stop_event periodically to allow early termination.
        """
        try:
            for chunk, metadata in stream_generator:
                # Check if we should stop
                if self._stop_event.is_set():
                    logger.debug("LLM streamer thread received stop signal")
                    break

                # Put chunk in queue (blocks if queue is full)
                try:
                    self._queue.put(
                        (self.MSG_CHUNK, chunk, metadata),
                        timeout=1.0  # Don't block forever if queue is full
                    )
                except queue.Full:
                    # If queue is full and stop is requested, exit
                    if self._stop_event.is_set():
                        break
                    # Otherwise, try again
                    continue

            # Signal completion
            self._queue.put((self.MSG_DONE, None, None))

        except Exception as e:
            logger.error(f"Error in LLM streamer thread: {e}")
            self._error = e
            try:
                self._queue.put((self.MSG_ERROR, e, None))
            except Exception:
                pass  # Queue might be broken, just log and exit
        finally:
            self._finished = True
            logger.debug("LLM streamer thread finished")

    def iter_chunks(self) -> Generator[Tuple[Any, Any], None, None]:
        """
        Generator that yields chunks from the LLM stream.

        This method checks for cancellation between queue reads, providing
        responsive interrupt handling even when the LLM is slow to respond.

        Yields:
            Tuple of (chunk_content, metadata) from the LLM stream

        Raises:
            CancelRequestedException: If cancellation is requested
            Exception: If the LLM stream encounters an error
        """
        from autocoder.common.global_cancel import global_cancel

        if not self._started:
            raise RuntimeError("Streamer not started. Call start() first.")

        while True:
            # Check for cancellation BEFORE blocking on queue
            global_cancel.check_and_raise(token=self._cancel_token)

            try:
                # Wait for next chunk with timeout
                msg_type, data, metadata = self._queue.get(timeout=self._queue_timeout)

                if msg_type == self.MSG_DONE:
                    # Stream completed normally
                    logger.debug("LLM stream completed")
                    break
                elif msg_type == self.MSG_ERROR:
                    # Stream encountered an error
                    logger.error(f"LLM stream error: {data}")
                    raise data
                else:
                    # Normal chunk - yield it
                    yield data, metadata

            except queue.Empty:
                # No chunk available within timeout
                # Loop back to check cancellation again
                continue

    def stop(self) -> None:
        """
        Signal the streaming thread to stop and wait for it to finish.

        This method is safe to call multiple times and from any thread.
        """
        if not self._started:
            return

        logger.debug("Stopping LLM streamer thread")
        self._stop_event.set()

        # Drain the queue to unblock the worker if it's waiting on put()
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass

        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            if self._thread.is_alive():
                logger.warning("LLM streamer thread did not stop cleanly")

    def is_running(self) -> bool:
        """Check if the streamer thread is still running."""
        return self._started and not self._finished

    def get_error(self) -> Optional[Exception]:
        """Get any error that occurred in the streaming thread."""
        return self._error

    def __enter__(self) -> "ThreadedLLMStreamer":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures cleanup."""
        self.stop()
