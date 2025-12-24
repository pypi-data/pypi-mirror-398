from heapq import heappop, heappush
from scar_sim.utils import hard_round


class Queue:
    def __init__(self, log_events: bool = False, precision: int = 4):
        """
        Initializes a priority queue for managing simulation events.

        Optional Arguments:

        - log_events (bool): If True, logs each event processed for debugging or analysis. Default is False.
        - precision (int): The number of decimal places to round time values to, ensuring numerical stability.
            - Default: 4
        """
        self.__queue__ = []
        self.__current_time__ = 0.0
        self.__log__ = []
        self.__event_dict__ = {}
        self.__event_id__ = 0
        self.__log_events__ = log_events
        self.__precision__ = precision

    def add(
        self,
        time_delta: float,
        func,
        args: tuple = tuple(),
        kwargs: dict = dict(),
    ) -> None:
        """
        Schedules a new event in the queue to be executed after a specified time delta.

        Required Arguments:

        - time_delta (float): The time delay after which the event should be executed. Must be non-negative.
        - func (callable): The function to be called when the event is processed.

        Optional Arguments:

        - args (tuple): Positional arguments to pass to the function when called.
            - Default: tuple()
        - kwargs (dict): Keyword arguments to pass to the function when called.
            - Default: dict()
        """
        if time_delta < 0:
            raise ValueError("Cannot schedule events in the past")
        self.__event_id__ += 1
        self.__event_dict__[self.__event_id__] = (
            self.__event_id__,
            func,
            args,
            kwargs,
        )
        next_time = hard_round(
            self.__current_time__ + time_delta, self.__precision__
        )
        heappush(self.__queue__, (next_time, self.__event_id__))

    def process(self) -> None:
        """
        Processes the next event in the queue, updating the current time and executing the associated function.

        Logs the event if logging is enabled.

        Raises:

        - IndexError: If there are no events to process in the queue.

        Returns:

        - None
        """
        if not self.__queue__:
            raise IndexError("No events to process in the queue")
        self.__current_time__, event_id = heappop(self.__queue__)
        event_id, func, args, kwargs = self.__event_dict__.pop(event_id)
        func(*args, **kwargs)

        if self.__log_events__:
            self.__log__.append(
                {
                    "event_id": event_id,
                    "time": self.__current_time__,
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs,
                }
            )

    def run(self, max_time: float) -> None:
        """
        Runs the event queue, processing events in chronological order until the specified maximum time is reached.

        Once the simulation is complete, the current time is set to max_time to ensure future events are scheduled correctly.

        Required Arguments:

        - max_time (float): The maximum simulation time at which to stop processing events.

        Raises:

        - ValueError: If max_time is less than the current simulation time.

        Returns:

        - None
        """
        if max_time < self.__current_time__:
            raise ValueError(
                "max_time cannot be less than the current simulation time"
            )
        while self.__queue__ and self.__queue__[0][0] <= max_time:
            self.process()
        self.__current_time__ = max_time
