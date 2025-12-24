from scar_sim.entity import Node, Arc
from scgraph import Graph as SCGraph
from typing import Literal


class Graph:
    def __init__(self):
        """
        Initializes a Graph object to manage nodes and arcs within the simulation.
        """
        self.time_graph = []
        """Initializes the time graph as a list of dictionaries. This maps index based graph IDs to time values."""
        self.cashflow_graph = []
        """Initializes the cashflow graph as a list of dictionaries. This maps index based graph IDs to cashflow values. Cashflows are stored as negative values since we are trying to minimize costs (which are negative cashflows)."""
        self.arc_obj_graph = []
        """Initializes the arc object graph as a list of dictionaries. This maps index based graph IDs to Arc objects."""

    def update_graphs(self, obj: Arc | Node):
        """
        Updates the graph representations with the provided Arc or Node object.

        This should be called when an Arc or Node's processing parameters are changed to ensure the graph representations remain accurate.

        Any cashflow that is positive will be treated as zero since cashflows in the graph are only used to represent costs (negative cashflows).

        If an arc is symmetric, the graph will be updated in both directions.

        Required Arguments:

        - obj (Arc | Node): The Arc or Node object to update the graphs with.

        Returns:

        - None
        """
        if isinstance(obj, Arc):
            self.time_graph[obj.origin_node.outbound_graph_id][
                obj.destination_node.inbound_graph_id
            ] = max(float(obj.processing_time_avg), 0)
            self.cashflow_graph[obj.origin_node.outbound_graph_id][
                obj.destination_node.inbound_graph_id
            ] = max(-float(obj.processing_cashflow_per_unit), 0)
            self.arc_obj_graph[obj.origin_node.outbound_graph_id][
                obj.destination_node.inbound_graph_id
            ] = obj
            if obj.is_symmetric:
                self.time_graph[obj.destination_node.outbound_graph_id][
                    obj.origin_node.inbound_graph_id
                ] = max(float(obj.processing_time_avg), 0)
                self.cashflow_graph[obj.destination_node.outbound_graph_id][
                    obj.origin_node.inbound_graph_id
                ] = max(-float(obj.processing_cashflow_per_unit), 0)
                self.arc_obj_graph[obj.destination_node.outbound_graph_id][
                    obj.origin_node.inbound_graph_id
                ] = obj
        elif isinstance(obj, Node):
            self.time_graph[obj.inbound_graph_id] = {
                obj.outbound_graph_id: max(float(obj.processing_time_avg), 0)
            }
            self.cashflow_graph[obj.inbound_graph_id] = {
                obj.outbound_graph_id: max(
                    -float(obj.processing_cashflow_per_unit), 0
                )
            }

    def add_object(self, obj: Node | Arc) -> Node | Arc:
        """
        Adds a Node or Arc object to the graph representations.

        Nodes are actually represented as two nodes in the graph (inbound and outbound) connected by an arc that models processing time and cashflow.

        Graphs are updated accordingly.

        Required Arguments:

        - obj (Node | Arc): The Node or Arc object to add to the graphs.
        """
        if isinstance(obj, Node):
            obj.inbound_graph_id = len(self.time_graph)
            obj.outbound_graph_id = obj.inbound_graph_id + 1
            self.time_graph += [dict(), dict()]
            self.cashflow_graph += [dict(), dict()]
            self.arc_obj_graph += [dict(), dict()]
        if isinstance(obj, Node | Arc):
            self.update_graphs(obj)
        return obj

    def get_path_weight(
        self, path: list[int], graph: Literal["cashflow", "time"]
    ) -> float:
        """
        Given a path (list of graph IDs), calculates the total weight of the path based on the specified graph type.

        Required Arguments:

        - path (list[int]): A list of graph IDs representing the path.
        - graph (Literal['cashflow', 'time']): The type of graph to use for weight calculation.

        Returns:

        - float: The total weight of the path.
            - Note: Since cashflows are stored as negative values, the returned cashflow weight will be adjusted back to its original sign for consistency.
        """
        graph_obj = (
            self.cashflow_graph if graph == "cashflow" else self.time_graph
        )
        weight_sum = 0.0
        for i in range(len(path) - 1):
            origin = path[i]
            destination = path[i + 1]
            weight_sum += graph_obj[origin][destination]
        return weight_sum if graph == "time" else -weight_sum

    def get_optimal_path(
        self,
        origin_node: Node,
        destination_node: Node,
        graph: Literal["cashflow", "time"],
    ) -> list[int]:
        """
        Calculates the optimal path between the specified origin and destination nodes based on the specified graph type.

        Required Arguments:

        - origin_node (Node): The starting node for the path.
        - destination_node (Node): The ending node for the path.
        - graph (Literal['cashflow', 'time']): The type of graph to use for path calculation.

        Returns:

        - list[int]: A list of graph IDs representing the optimal path.
        """
        graph_obj = (
            self.cashflow_graph if graph == "cashflow" else self.time_graph
        )
        return SCGraph.dijkstra_makowski(
            graph_obj,
            origin_node.inbound_graph_id,
            destination_node.inbound_graph_id,
        )["path"]

    def get_route_options(
        self, origin_node: Node, destination_node: Node
    ) -> dict:
        """
        Calculates route options between the specified origin and destination nodes.

        Required Arguments:

        - origin_node (Node): The starting node for the route.
        - destination_node (Node): The ending node for the route.

        Returns:

        - dict: A dictionary containing route options for minimum cashflow and minimum time paths, each with their respective path, time, and cashflow values.
            - Example:
            ```
            {
                "min_cashflow":{
                    'path': [...],
                    'time': ...,
                    'cashflow': ...
                },
                "min_time":{
                    'path': [...],
                    'time': ...,
                    'cashflow': ...
                }
            }
            ```
        """
        min_time_path = self.get_optimal_path(
            origin_node, destination_node, "time"
        )
        min_cashflow_path = self.get_optimal_path(
            origin_node, destination_node, "cashflow"
        )
        return {
            "min_cashflow": {
                "path": min_cashflow_path,
                "time": self.get_path_weight(min_cashflow_path, "time"),
                "cashflow": self.get_path_weight(min_cashflow_path, "cashflow"),
            },
            "min_time": {
                "path": min_time_path,
                "time": self.get_path_weight(min_time_path, "time"),
                "cashflow": self.get_path_weight(min_time_path, "cashflow"),
            },
        }
