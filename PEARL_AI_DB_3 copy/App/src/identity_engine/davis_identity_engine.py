class DAVISIdentityEngine:
    """DAVIS Identity Engine for managing identity metrics across three lanes."""
    def __init__(self):
        self.geometric_lane = {}
        self.semantic_lane = {}
        self.procedural_lane = {}

    def update_geometric_metrics(self, pearl_id: str, metrics: dict):
        """Updates geometric identity metrics for a given PEARL_ID."""
        self.geometric_lane[pearl_id] = {**self.geometric_lane.get(pearl_id, {}), **metrics}
        print(f"Updated geometric metrics for {pearl_id}: {metrics}")
        return self.geometric_lane[pearl_id]

    def update_semantic_metrics(self, pearl_id: str, metrics: dict):
        """Updates semantic identity metrics for a given PEARL_ID."""
        self.semantic_lane[pearl_id] = {**self.semantic_lane.get(pearl_id, {}), **metrics}
        print(f"Updated semantic metrics for {pearl_id}: {metrics}")
        return self.semantic_lane[pearl_id]

    def update_procedural_metrics(self, pearl_id: str, metrics: dict):
        """Updates procedural identity metrics for a given PEARL_ID."""
        self.procedural_lane[pearl_id] = {**self.procedural_lane.get(pearl_id, {}), **metrics}
        print(f"Updated procedural metrics for {pearl_id}: {metrics}")
        return self.procedural_lane[pearl_id]

    def get_identity_metrics(self, pearl_id: str):
        """Retrieves all identity metrics for a given PEARL_ID."""
        return {
            "geometric": self.geometric_lane.get(pearl_id),
            "semantic": self.semantic_lane.get(pearl_id),
            "procedural": self.procedural_lane.get(pearl_id),
        }

