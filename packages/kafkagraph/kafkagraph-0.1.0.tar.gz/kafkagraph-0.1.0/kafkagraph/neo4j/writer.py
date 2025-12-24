from neo4j import GraphDatabase
from collections import defaultdict

class Neo4jWriter:
    def __init__(self, cfg):
        self.driver = GraphDatabase.driver(
            cfg["uri"], auth=(cfg["user"], cfg["password"])
        )

    def write(self, nodes, rels):
        with self.driver.session() as s:
            by_label = defaultdict(list)
            for n in nodes:
                by_label[n["label"]].append(n)

            for lbl, items in by_label.items():
                s.run(
                    f"UNWIND $items AS n MERGE (x:{lbl} {{id:n.id}})",
                    items=items
                )

            by_type = defaultdict(list)
            for r in rels:
                by_type[r["type"]].append(r)

            for t, items in by_type.items():
                f, to = items[0]["from_label"], items[0]["to_label"]
                s.run(
                    f"""
                    UNWIND $items AS r 
                    MATCH (a:{f} {{id:r.from_id}}) 
                    MATCH (b:{to} {{id:r.to_id}}) 
                    MERGE (a)-[rel:{t}]->(b) 
                    SET rel += r.props 
                    """,
                    items=items
                )
