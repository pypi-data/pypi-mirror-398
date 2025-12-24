import random

random.seed(42)


class SimulationObject:
    def __init__(self):
        """
        Initializes a SimulationObject with default attributes.

        This object forms the base class for all entities within the simulation framework.
        """
        self.id = None
        """ A unique identifier for the simulation object. Initially set to None."""
        self.__simulation__ = None
        """ A reference to the simulation instance that this object belongs to. Initially set to None."""


class SimulationEntity(SimulationObject):
    def __init__(
        self,
        processing_min_time: float = 0.0,
        processing_avg_time: float = 0.0,
        processing_sd_time: float = 0.0,
        processing_cashflow_per_unit: float = 0.0,
        metadata: dict = dict(),
    ):
        """
        Initializes a SimulationEntity with processing parameters and metadata.

        Required Arguments:

        - processing_min_time (float): The minimum processing time for the entity.
        - processing_avg_time (float): The average processing time for the entity.
        - processing_sd_time (float): The standard deviation of processing time for the entity.
        - processing_cashflow_per_unit (float): The cashflow per unit processed by the entity

        Optional Arguments:

        - metadata (dict): A dictionary of metadata associated with the entity.
            - This is injected into orders and can be used for tracking and analysis.
        """
        # Basic info
        super().__init__()
        self.entity_type = self.__class__.__name__
        # Split the entity type on uppercase letters and join with underscores
        self.cashflow_key = (
            "".join(
                [
                    "_" + letter.lower() if letter.isupper() else letter
                    for letter in self.entity_type
                ]
            ).lstrip("_")
            + "_cashflow"
        )
        self.metadata = metadata

        # Processing defaults
        self.__default_processing_min_time__ = processing_min_time
        self.__default_processing_avg_time__ = processing_avg_time
        self.__default_processing_sd_time__ = processing_sd_time
        self.__default_processing_cashflow_per_unit__ = (
            processing_cashflow_per_unit
        )

        # Live processing info
        self.processing_time_min = processing_min_time
        self.processing_time_avg = processing_avg_time
        self.processing_time_sd = processing_sd_time
        self.processing_cashflow_per_unit = processing_cashflow_per_unit

    def get_metadata(self, **kwargs) -> dict:
        """
        Retrieve the metadata dictionary for the entity, optionally augmented with additional key-value pairs.

        This method is deisnged to be useful by default but can be overridden in subclasses to provide custom metadata.

        Optional Arguments:

        - kwargs: Additional key-value pairs to include in the returned metadata dictionary.

        Returns:

        - dict: A dictionary containing the entity's metadata, augmented with any additional key-value pairs provided to this method.
        """
        # Return a copy of the metadata dictionary (in case it is modified later)
        return {**dict(self.metadata), **kwargs}

    def get_processing_time(self) -> float:
        """
        Calculates a random processing time based on the entity's processing parameters.

        This method can be overridden in subclasses to provide custom processing time calculations.

        Returns:

        - float: A processing time value, which is at least the minimum processing time and follows a normal distribution defined by the average and standard deviation.
        """
        return max(
            self.processing_time_min,
            random.gauss(self.processing_time_avg, self.processing_time_sd),
        )

    def change_processing_parameters(
        self,
        processing_min_time: float | None = None,
        processing_avg_time: float | None = None,
        processing_sd_time: float | None = None,
        processing_cashflow_per_unit: float | None = None,
    ) -> None:
        """
        Change the processing parameters of the entity.

        This would normally be expected to be scheduled as an event in the simulation to trigger something like a future disruption, maintenance, or upgrade.

        It updates the entity itself as well as the simulation graph if the entity is part of a simulation.

        Optional Arguments:

        - processing_min_time (float | None): New minimum processing time.
        - processing_avg_time (float | None): New average processing time.
        - processing_sd_time (float | None): New standard deviation of processing time.
        - processing_cashflow_per_unit (float | None): New cashflow per unit processed.

        Returns:

        - None
        """
        if processing_min_time is not None:
            self.processing_time_min = processing_min_time
        if processing_avg_time is not None:
            self.processing_time_avg = processing_avg_time
        if processing_sd_time is not None:
            self.processing_time_sd = processing_sd_time
        if processing_cashflow_per_unit is not None:
            self.processing_cashflow_per_unit = processing_cashflow_per_unit
        if self.__simulation__ is not None:
            self.__simulation__.graph.update_graphs(self)

    def reset_processing_parameters(self) -> None:
        """
        Resets the processing parameters of the entity to their default values.

        This would normally be expected to be scheduled as an event in the simulation to trigger the end of a disruption, maintenance, or upgrade.

        This method updates the entity itself as well as the simulation graph if the entity is part of a simulation.

        Returns:

        - None
        """
        self.change_processing_parameters(
            processing_min_time=self.__default_processing_min_time__,
            processing_avg_time=self.__default_processing_avg_time__,
            processing_sd_time=self.__default_processing_sd_time__,
            processing_cashflow_per_unit=self.__default_processing_cashflow_per_unit__,
        )

    def get_cashflow(self, units: int) -> float:
        """
        Calculate the cashflow for processing a given number of units through this entity.

        This method is designed to be useful by default but can be overridden in subclasses to provide custom cashflow calculations.

        Required Arguments:

        - units (int): The number of units being processed.
        """
        return self.processing_cashflow_per_unit * units


class Node(SimulationEntity):
    def __init__(self, **kwargs):
        """
        Initializes a Node entity with processing parameters and metadata.

        Nodes represent points in the simulation where activity occurs, such as facilities or junctions.

        In the underlying graph representation, each node is represented by two nodes (inbound and outbound) connected by an arc that models processing time and cashflow.

        Two additional attributes are initialized to None:

        - inbound_graph_id: The graph ID for the inbound representation of the node.
        - outbound_graph_id: The graph ID for the outbound representation of the node.

        Required Arguments:

        - kwargs: Keyword arguments passed to the SimulationEntity __init__ function.
        """
        super().__init__(**kwargs)
        # Technically each node is made up of two nodes in the graph
        # Connected by an arc that represents processing time and cashflow at the node
        self.inbound_graph_id = None
        self.outbound_graph_id = None

    def order_arrived(self, order):
        """
        A placeholder method to handle logic when an order arrives at this node.
        This can be overridden in subclasses to implement specific behavior.

        Requires:

        - order (Order): The order that has arrived.

        Returns:

        - None
        """

    def order_placed(self, order):
        """
        A placeholder method to handle logic when an order is placed at this node.
        This can be overridden in subclasses to implement specific behavior.

        Requires:

        - order (Order): The order that has been placed.

        Returns:

        - None
        """

    def order_shipped(self, order):
        """
        A placeholder method to handle logic when an order is shipped from this node.
        This can be overridden in subclasses to implement specific behavior.

        Requires:

        - order (Order): The order that has been shipped.

        Returns:

        - None
        """

    def order_completed(self, order):
        """
        A placeholder method to handle logic when an order is completed at this node.
        This can be overridden in subclasses to implement specific behavior.

        Requires:

        - order (Order): The order that has been completed.

        Returns:

        - None
        """


class Arc(SimulationEntity):
    def __init__(
        self,
        origin_node: Node,
        destination_node: Node,
        is_symmetric: bool = True,
        **kwargs,
    ):
        """
        Initializes an Arc entity connecting two nodes with processing parameters and metadata.

        Arcs represent connections between nodes in the simulation, modeling the flow of entities such as orders or goods.

        Required Arguments:

        - origin_node (Node): The node where the arc originates.
        - destination_node (Node): The node where the arc terminates.
        - kwargs: Additional keyword arguments passed to the SimulationEntity __init__ function.

        Optional Arguments:

        - is_symmetric (bool): Indicates whether the arc is symmetric, meaning the processing parameters apply equally in both directions.
            - Default: True
        """
        super().__init__(**kwargs)
        self.is_symmetric = is_symmetric
        self.origin_node = origin_node
        self.destination_node = destination_node
