from scar_sim.queue import Queue
from scar_sim.entity import Node, Arc, SimulationObject
from scar_sim.order import Order
from scar_sim.graph import Graph
import dill


class Simulation:
    def __init__(self):
        """
        Initializes a Simulation object to manage the overall simulation state, including objects, orders, event queue, and graph representations.
        """
        # Simulation objects
        self.objects = []
        self.orders = []

        # Stateful queue and graphs
        self.__queue__ = Queue()
        self.graph = Graph()

    def current_time(self) -> float:
        """
        Returns the current simulation time.

        Returns:

        - float: The current time in the simulation.
        """
        return self.__queue__.__current_time__

    def add_event(
        self,
        time_delta: float,
        func,
        args: tuple = tuple(),
        kwargs: dict = dict(),
    ) -> None:
        """
        Schedules a new event in the simulation's event queue.

        Required Arguments:

        - time_delta (float): The time delay after which the event should be executed. Must be non-negative.
        - func (callable): The function to be called when the event is processed.

        Optional Arguments:

        - args (tuple): Positional arguments to pass to the function when called.
            - Default: tuple()
        - kwargs (dict): Keyword arguments to pass to the function when called.
            - Default: dict()

        Returns:

        - None
        """
        self.__queue__.add(
            time_delta=time_delta, func=func, args=args, kwargs=kwargs
        )

    def add_object(self, obj: Node | Arc | Order) -> SimulationObject:
        """
        Adds a SimulationObject (Node, Arc, or Order) to the simulation.
        Assigns a unique ID to the object and updates relevant simulation structures.

        Required Arguments:

        - obj (Node | Arc | Order): The object to be added to the simulation.

        Raises:

        - ValueError: If the object is already part of a simulation.
        - ValueError: If the object type is not recognized (not Node, Arc, or Order).

        Returns:

        - SimulationObject: The added object with updated simulation references and IDs.
        """
        if obj.id is not None:
            raise ValueError("Object is already added to a simulation")
        if isinstance(obj, (Node, Arc, Order)):
            # Create a ref to this simulation in the object
            obj.__simulation__ = self
            # Set the object ID such that it is unique within this simulation
            obj.id = len(self.objects)
            self.objects.append(obj)
            if isinstance(obj, (Node, Arc)):
                # Add arcs and nodes to the graph and update graph structures
                self.graph.add_object(obj)
            elif isinstance(obj, Order):
                # Add orders to the order list and set an order_id specific to the stored order list
                obj.order_id = len(self.orders)
                self.orders.append(obj)
        else:
            raise ValueError("Object type not recognized for simulation")
        return obj

    def run(self, max_time: float):
        """
        Runs the simulation until the specified maximum time is reached.

        Required Arguments:

        - max_time (float): The maximum simulation time to run until.

        Returns:

        - None
        """
        self.__queue__.run(max_time=max_time)

    def export_state(self, filename: str | None = None) -> bytes | str:
        """
        Exports the current state of the simulation using dill serialization.

        Optional Arguments:

        - filename (str | None): The file path to save the serialized state. If None, the state is returned as bytes.
            - Default: None

        Returns:

        - bytes | str: The serialized state as bytes if filename is None, otherwise the filename where the state was saved.
        """
        if filename is not None:
            with open(filename, "wb") as f:
                dill.dump(self, f)
            return filename
        else:
            return dill.dumps(self)

    @staticmethod
    def import_state(
        data: bytes | None = None, filename: str | None = None
    ) -> "Simulation":
        """
        Imports a simulation state from dill serialized data or a file.
        If both data and filename are provided, the filename takes precedence.

        Required Arguments (one of):

        - data (bytes | None): The serialized simulation state as bytes.
        - filename (str | None): The file path to load the serialized state from.

        Raises:

        - ValueError: If neither data nor filename is provided.

        Returns:

        - Simulation: The imported Simulation object.

        """
        if filename is not None:
            with open(filename, "rb") as f:
                return dill.load(f)
        elif data is not None:
            return dill.loads(data)
        else:
            raise ValueError(
                "Either data or filename must be provided to import a simulation"
            )
