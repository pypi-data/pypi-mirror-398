from scar_sim.entity import Arc, Node, SimulationObject


class Order(SimulationObject):
    def __init__(
        self,
        origin_node: Node,
        destination_node: Node,
        units: int,
        planned_path: list[int],
    ):
        """
        Initializes an Order object representing a shipment from an origin to a destination.

        Required Arguments:

        - origin_node (Node): The starting node for the order.
        - destination_node (Node): The ending node for the order.
        - units (int): The number of units in the order.
        - planned_path (list[int]): The planned path for the order as a list of graph IDs.
        """
        super().__init__()
        self.origin_node = origin_node
        self.destination_node = destination_node
        self.units = units

        # History of the Order's progress
        self.history = []

        # Simulation and miscellaneous state
        self.__simulation__ = None
        self.__current_object__ = self.origin_node
        self.__started__ = False
        self.__prev_time__ = 0.0

        # Note: Planned path is in terms of graph IDs and not in terms of simulation ids
        self.__set_planned_path__(planned_path, initial=True)
        self.__current_path_idx__ = 0

    def start(self) -> None:
        """
        Starts the Order's processing within the simulation.

        Raises an error if the Order has already been started.

        This method schedules the first event in the Order's lifecycle, transitioning it to the "started" status.

        Returns:

        - None
        """
        if self.__started__:
            raise ValueError("Order has already been started")
        self.__started__ = True
        self.__prev_time__ = self.__simulation__.current_time()
        self.__next__(status="started")

    def set_current_cashflow(self, cashflow: int | float) -> None:
        """
        Sets the cashflow for the most recent history entry of the Order.

        While designed to be used internally, this method can be overridden for custom cashflow handling.

        Required Arguments:

        - cashflow (int | float): The cashflow amount to set for the current history entry.
        """
        self.history[-1]["cashflow"] = cashflow

    def inject_metadata(self) -> dict:
        """
        Inject metadata about the Order into the history log entry when called. This is called by the __next__ method without arguments when logging history.

        This method can be overridden to provide custom metadata such as time, order ID, customer info, product info, etc.

        By default, this returns the current simulation time in integer form as 'time'.
        """
        return {
            "time": int(self.__simulation__.current_time()),
        }

    def consider_reroute(self) -> tuple[bool, list[int]]:
        """
        Consider whether to reroute the Order at its current location.

        This method can be overridden to provide custom rerouting logic based on current simulation state, congestion, delays, etc.

        This method will not have any inputs, but can access the Order's current state.

        By default, this placeholder does not reroute and returns (False, None).
        """
        return (False, list())

    def __set_planned_path__(
        self, planned_path: list[int], initial=False
    ) -> None:
        """
        An internal method to set the planned path for the Order.

        This is expected to be called internally when the Order is created and when rerouting is performed.

        Required Arguments:

        - planned_path (list[int]): The new planned path as a list of graph IDs.
        - initial (bool): Whether this is the initial setting of the planned path. Defaults to False.

        Raises:

        - ValueError: If the new path does not match the current path up to the current location (when not initial).
        - AssertionError: If the planned path does not start at the origin node or end at the destination node.
            - Note: More specifically, the planned path must start with the origin node's inbound graph ID and end with the destination node's inbound graph ID.

        Returns:
        - None
        """
        if not initial:
            if (
                planned_path[: self.__current_path_idx__ + 1]
                != self.__planned_path__[: self.__current_path_idx__ + 1]
            ):
                raise ValueError(
                    "New path must match current path up to current location"
                )
        assert (
            planned_path[0] == self.origin_node.inbound_graph_id
        ), "Planned path must start at origin node"
        assert (
            planned_path[-1] == self.destination_node.inbound_graph_id
        ), "Planned path must end at destination node"
        self.__planned_path__ = planned_path

    def __next__(self, status: str) -> None:
        """
        An internal method to progress the Order to the next status in its lifecycle.

        This method is expected to be stored as an event in the simulation's event queue and fired off at the appropriate times.

        Required Arguments:

        - status (str): The current status of the Order. Must be one of "started", "shipped", "arrived", or "completed".

        Raises:

        - ValueError: If the status is unknown or if the current object does not match the expected type for the status transition.

        Returns:

        - None
        """
        # Log this item into the Order history
        self.history.append(
            {
                "time": self.__simulation__.current_time(),
                "time_delta": round(
                    self.__simulation__.current_time() - self.__prev_time__, 3
                ),
                "order_id": self.id,
                "current_obj_id": self.__current_object__.id,
                "meta": self.__current_object__.get_metadata(
                    **self.inject_metadata()
                ),
                "status": status,
                "cashflow": 0.0,
            }
        )
        self.__current_path_idx__ += 1
        self.__prev_time__ = self.__simulation__.current_time()

        if status == "started":
            # Validate that we are at a Node that can process orders
            if not isinstance(self.__current_object__, Node):
                raise ValueError("Current object must be a Node when started")
            # Perform any logic at the origin node to process the order (i.e., remove from capacity)
            self.__current_object__.order_placed(self)
            # Set up for shipping
            next_status = "shipped"
        elif status == "shipped":
            # If the current object is a Node, we need to ship the order (i.e., remove from inventory)
            if isinstance(self.__current_object__, Node):
                self.__current_object__.order_shipped(self)

            # Pay for processing an order when it is shipped from a node
            self.set_current_cashflow(
                self.__current_object__.get_cashflow(units=self.units)
            )
            # Given the planned path, set the current object to the next planned Arc
            next_graph_id = self.__planned_path__[self.__current_path_idx__]
            self.__current_object__ = self.__simulation__.graph.arc_obj_graph[
                self.__current_object__.outbound_graph_id
            ][next_graph_id]
            # Determine the next node given this arc (allowing for symmetic arcs)
            if (
                self.__current_object__.origin_node.inbound_graph_id
                == next_graph_id
            ):
                self.__next_node__ = self.__current_object__.origin_node
            else:
                self.__next_node__ = self.__current_object__.destination_node
            next_status = "arrived"
        elif status == "arrived":
            if not isinstance(self.__current_object__, Arc):
                raise ValueError("Current object must be an Arc when arriving")
            # Pay for the transportation when a unit arrives at the destination node
            self.set_current_cashflow(
                self.__current_object__.get_cashflow(units=self.units)
            )
            # Set the current object to the next Node (supports symmetric arcs)
            self.__current_object__ = self.__next_node__
            if not isinstance(self.__current_object__, Node):
                raise ValueError("Next object must be a Node when arriving")
            # Consider rerouting the order
            should_reroute, new_path = self.consider_reroute()
            if should_reroute:
                self.__set_planned_path__(new_path)
            if isinstance(self.__current_object__, Node):
                # Only fire off the order arrived event if we are at a Node and a reroute has not changed the path away from this Node
                # Fire off the order arrived event at the Node for processing (i.e., add to inventory)
                if len(self.__planned_path__) == self.__current_path_idx__:
                    # We are at the end of the path
                    self.__current_object__.order_arrived(self)
                elif (
                    self.__planned_path__[self.__current_path_idx__ + 1]
                    == self.__current_object__.outbound_graph_id
                ):
                    self.__current_object__.order_arrived(self)
            next_status = (
                "completed"
                if self.__current_object__.id == self.destination_node.id
                else "shipped"
            )
        elif status == "completed":
            # Validate that we are at a Node that can receive Orders
            if not isinstance(self.__current_object__, Node):
                raise ValueError("Current object must be a Node when completed")
            # Fire off the order completed event at the Node for processing (i.e., add to capacity)
            self.__current_object__.order_completed(self)
            # When called with "completed", we do not schedule any further events
            return
        else:
            raise ValueError(f"Unknown status: {status}")

        self.__simulation__.add_event(
            time_delta=(
                self.__current_object__.get_processing_time()
                if next_status != "completed"
                else 0.0
            ),
            func=self.__next__,
            kwargs={"status": next_status},
        )
