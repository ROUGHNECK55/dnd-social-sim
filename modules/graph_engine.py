import json
import os
import networkx as nx
from typing import List, Dict, Any, Optional

class WorldGraph:
    def __init__(self):
        # Ephemeral initialization - start blank
        self.graph = nx.DiGraph()
        self.ontology = {
            "node_types": ["Character", "Location", "Faction", "Item", "Concept", "Event"],
            "edge_types": ["Knows", "Located_In", "Member_Of", "Owner_Of", "Related_To", "Happened_At"]
        }

    def export_to_json(self) -> str:
        """Returns the current graph state as a JSON string."""
        data = {
            "ontology": self.ontology,
            "graph": nx.node_link_data(self.graph)
        }
        return json.dumps(data, indent=2)

    def import_from_json(self, json_str: str) -> tuple[bool, str]:
        """Replaces current state with data from JSON string."""
        try:
            data = json.loads(json_str)
            if "ontology" in data:
                self.ontology = data["ontology"]
            
            if "graph" in data:
                self.graph = nx.node_link_graph(data["graph"])
                return True, f"Successfully loaded {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges."
            else:
                 return False, "Invalid JSON: missing 'graph' key."
        except Exception as e:
            return False, f"Import Error: {e}"

    def update_ontology(self, node_types: List[str] = None, edge_types: List[str] = None):
        """Updates the allowed node and edge types."""
        if node_types:
            self.ontology["node_types"] = node_types
        if edge_types:
            self.ontology["edge_types"] = edge_types

    def add_node(self, name: str, type: str, description: str = "", **kwargs) -> bool:
        """Adds or updates a node. Returns True if successful."""
        if type not in self.ontology["node_types"]:
            print(f"Error: Invalid node type '{type}'. Allowed: {self.ontology['node_types']}")
            return False
        
        self.graph.add_node(name, type=type, description=description, **kwargs)
        return True

    def delete_node(self, name: str):
        """Deletes a node and its edges."""
        if self.graph.has_node(name):
            self.graph.remove_node(name)

    def add_edge(self, source: str, target: str, type: str, weight: int = 1, **kwargs) -> bool:
        """Adds or updates an edge. Returns True if successful."""
        if not self.graph.has_node(source) or not self.graph.has_node(target):
            print(f"Error: One or both nodes '{source}', '{target}' do not exist.")
            return False
        
        if type not in self.ontology["edge_types"]:
            print(f"Error: Invalid edge type '{type}'. Allowed: {self.ontology['edge_types']}")
            return False

        self.graph.add_edge(source, target, type=type, weight=weight, **kwargs)
        return True

    def get_context(self, query_entities: List[str], depth: int = 1) -> Dict[str, Any]:
        """
        Retrieves context sub-graph for a list of entities.
        Returns a dictionary of relevant nodes and edges.
        """
        relevant_nodes = set(query_entities)
        
        # Simple expansion: Get neighbors
        for entity in query_entities:
            if self.graph.has_node(entity):
                # Outgoing
                relevant_nodes.update(self.graph.successors(entity))
                # Incoming
                relevant_nodes.update(self.graph.predecessors(entity))
        
        # Filter strictly to existing nodes
        relevant_nodes = {n for n in relevant_nodes if self.graph.has_node(n)}
        
        items = {}
        for node in relevant_nodes:
            items[node] = self.graph.nodes[node]
            
        relationships = []
        subgraph = self.graph.subgraph(relevant_nodes)
        for u, v, data in subgraph.edges(data=True):
            relationships.append({
                "source": u,
                "target": v,
                "type": data.get("type", "related"),
                "data": data
            })

        return {
            "nodes": items,
            "edges": relationships
        }

    def get_all_nodes(self):
        """Returns all nodes with their data."""
        return dict(self.graph.nodes(data=True))

    def get_all_edges(self):
        """Returns all edges with their data."""
        return list(self.graph.edges(data=True))
