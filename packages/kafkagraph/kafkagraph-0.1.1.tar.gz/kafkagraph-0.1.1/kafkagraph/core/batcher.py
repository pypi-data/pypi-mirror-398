class Batch:
    def __init__(self, size):
        self.size = size
        self.nodes = []
        self.rels = []

    def add(self, nodes, rels):
        if nodes:
            self.nodes.extend(nodes)
        if rels:
            self.rels.extend(rels)

    def count(self):
        return len(self.nodes) + len(self.rels)

    def ready(self):
        return self.count() >= self.size

    def clear(self):
        self.nodes.clear()
        self.rels.clear()
