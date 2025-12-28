import asyncio
import contextlib
import logging
from typing import Coroutine, overload

class TwiTaskManager:

    def __init__(self, tasks: list[Coroutine] = [], loop: asyncio.AbstractEventLoop = None):
        '''
        Twilight's event loop wrapper.
        Allows to manage async tasks with creating a loop and running it forever

        :param tasks: List of coroutines should be ran on the start of the loop
        :type tasks: list[Coroutine]

        :param loop: Already created loop if it exist
        :type loop: asyncio.AbstractEventLoop
        '''
        self.logger = logging.getLogger(name="loop-manager")
        self._tasks: list[asyncio.Task] = tasks
        self._loop: asyncio.AbstractEventLoop = asyncio.get_event_loop() if loop is None else loop
    
    def get_loop(self):
        '''Returns a loop if it was created'''
        if self._loop:
            return self._loop
        self.logger.warning("Event loop was not created")
    
    def run(self, stop_when: str = asyncio.FIRST_EXCEPTION):
        '''
        Run the event loop until all task will be completed or first_exception will be caught

        :param stop_when: Let the loop manager know when it should stop (ALL_COMPLETED / FIRST_COMPLETED / FIRST_EXCEPTION)
        :type stop_when: str
        '''
        self.logger.debug(f"Loop was started with {len(self._tasks)} tasks")

        while self._tasks:
            self._loop.create_task(self._tasks.pop(0))
        
        _all_tasks = asyncio.all_tasks(self._loop)

        try:
            while _all_tasks:
                _done, _ = self._loop.run_until_complete(
                    asyncio.wait(_all_tasks, return_when=stop_when)
                )

                for _result in _done:
                    try:
                        _result.result()
                    except Exception as exc:
                        self.logger.critical(f"Task {_result.get_coro().__name__} retuned the exception: {exc}", exc_info=True)

                _all_tasks = asyncio.all_tasks(self._loop)

        except KeyboardInterrupt:
            self.logger.warning("KeyboardInterrupt recieved, shutting down...")
            self.stop(_all_tasks)

        finally:
            self.close()

    def stop(self, tasks: list[asyncio.Task] = None):
        '''
        Force stop with cancelling all the tasks

        :param tasks: List of currently created tasks in the event loop
        :type tasks: list[asyncio.Task]
        '''
        self.logger.debug("Stopping all tasks...")
        self.cancel_tasks(tasks)
        self.logger.debug("Tasks was stopped")

    def cancel_tasks(self, tasks: list[asyncio.Task] = None, targets: Coroutine | list[Coroutine] = None):

        if tasks is None:
            tasks = asyncio.all_tasks(self._loop)

        #TODO: Cancelling the certain tasks, not the all ones

        #if targets is None:
        #    tasks_to_cancel = asyncio.gather(*tasks)
        #else:
        #    _tasks_to_gather = set()
        #    for _task in tasks:
        #        for _target in targets:
        #            if _task.get_coro() == _target:
        #                _tasks_to_gather.add(_task)
        #    tasks_to_cancel = asyncio.gather(*_tasks_to_gather)
        
        tasks_to_cancel = asyncio.gather(*tasks)
        tasks_to_cancel.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            self._loop.run_until_complete(
                asyncio.wait_for(
                    tasks_to_cancel,
                    timeout=10
                )
            )

    def close(self):
        '''
        Closing the current event loop
        '''
        if self._loop.is_running():
            self.logger.debug("Loop will be closed")
            self._loop.close()
    
    @overload
    def add_task(self, tasks: list[Coroutine]):
        ...
    
    @overload
    def add_task(self, task: Coroutine):
        ...
    
    def add_task(self, tasks: Coroutine | list[Coroutine]):
        '''
        Adds the task to the event loop

        :param tasks: Coroutine or list of coroutine functions to be added in event loop
        :type tasks: Coroutine | list[Coroutine]
        '''

        _tasks = tasks if isinstance(tasks, list) else [tasks]

        for _task in _tasks:
            if asyncio.iscoroutinefunction(_task):
                _task = _task()
            elif not asyncio.iscoroutine(_task):
                raise TypeError("Task should be coroutine or coroutine function")
            
            if self._loop and self._loop.is_running():
                self._loop.create_task(_task)
                self.logger.debug(f"Task {_task.__name__} was added to the running event loop")
            else:
                self._tasks.append(_task)
                self.logger.debug(f"Task {_task.__name__} was added to the event loop")
