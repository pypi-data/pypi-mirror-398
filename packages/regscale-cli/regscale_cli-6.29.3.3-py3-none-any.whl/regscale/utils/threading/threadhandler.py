#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thread handler to create and start threads"""

from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from typing import Any, Callable, List, Optional, Tuple, Union


class ThreadManager:
    """
    Class to manage threads and tasks
    """

    def __init__(self, max_workers: int = 20):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = []

    def submit_task(self, func: Callable, *args, **kwargs) -> None:
        """
        Submit a task to the executor

        :param Callable func: Function to execute
        :rtype: None
        """
        future = self.executor.submit(func, *args, **kwargs)
        self.futures.append(future)

    def submit_tasks_from_list(self, func: Callable, items: List[Any], *args, **kwargs) -> None:
        """
        Submit multiple tasks to the executor, used for a list of items

        :param Callable func: Function to execute
        :param List[Any] items: List of items to process
        :rtype: None
        """
        for item in items:
            self.submit_task(func, item, *args, **kwargs)

    def execute_and_verify(
        self,
        timeout: int = None,
        check_for_failures: bool = True,
        terminate_after: bool = False,
        return_passed: bool = False,
    ) -> Union[List[Tuple[bool, Any]], List[Any]]:
        """
        Execute the tasks and verify if they were successful

        :param int timeout: Timeout for the tasks
        :param bool check_for_failures: Whether to check for failures, default True
        :param bool terminate_after: Whether to terminate the executor after the tasks are completed, default False
        :param bool return_passed: Whether to return only the passed tasks, default False
        :return: List of tuples with a bool indicating success & the result, or list of results if return_passed is True
        :rtype: Union[List[Tuple[bool, Any]], List[Any]]
        """
        results = []
        try:
            for future in as_completed(self.futures, timeout=timeout):
                try:
                    result = future.result()
                    results.append((True, result))
                except TimeoutError:
                    results.append((False, "Task timed out"))
                except Exception as e:
                    results.append((False, str(e)))
        finally:
            self.futures = []
            if terminate_after:
                self.shutdown()
        if check_for_failures:
            import logging

            logger = logging.getLogger(__name__)
            for success, result in results:
                if not success:
                    logger.error(f"Task failed with error: {result}")
        if return_passed:
            return [result for success, result in results if success]
        # clear the futures list
        return results

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the executor

        :param bool wait: Whether to wait for the tasks to complete
        :rtype: None
        """
        self.executor.shutdown(wait=wait)


def create_threads(process: Callable, args: Tuple, thread_count: int) -> None:
    """
    Function to create x threads using ThreadPoolExecutor

    :param Callable process: function for the threads to execute
    :param Tuple args: args for the provided process
    :param int thread_count: # of threads needed
    :rtype: None
    """
    max_threads = _determine_max_threads()
    if threads := min(thread_count, max_threads):
        # start the threads with the number of threads allowed
        with ThreadPoolExecutor(max_workers=threads) as executor:
            # iterate and start the threads that were requested
            for thread in range(threads):
                # assign each thread the passed process and args along with the thread number
                executor.submit(process, args, thread)


def thread_assignment(thread: int, total_items: int) -> list:
    """
    Function to iterate through items and returns a list the
    provided thread should be assigned and use during its execution

    :param int thread: current thread number
    :param int total_items: Total # of items to process with threads
    :return: List of items to process for the given thread
    :rtype: list
    """
    max_threads = _determine_max_threads()

    return [x for x in range(total_items) if x % max_threads == thread]


def _determine_max_threads(default: Optional[int] = 100) -> int:
    """
    Function to determine the max threads to use by checking the Application config

    :param Optional[int] default: The default max threads to use if the Application config is not set, defaults to 100
    :return: The max threads to use
    :rtype: int
    """
    from regscale.core.app.application import Application

    app = Application()
    if app.running_in_airflow:
        default = 20
    # set max threads
    max_threads = app.config.get("maxThreads", default)
    if not isinstance(max_threads, int):
        try:
            max_threads = int(max_threads)
        except (ValueError, TypeError):
            max_threads = default
    return max_threads
