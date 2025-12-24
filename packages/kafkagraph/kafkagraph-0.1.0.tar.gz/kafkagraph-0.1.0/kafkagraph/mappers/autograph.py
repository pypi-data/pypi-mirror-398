def map_autograph(event):
    nodes, rels = [], []

    for k, v in event.items():
        if k.endswith("Id") or k.endswith("Number"):
            nodes.append({
                "label": k.replace("Id", "").replace("Number", "").capitalize(),
                "id": v
            })

    for i in range(len(nodes) - 1):
        rels.append({
            "type": "RELATED_TO",
            "from_label": nodes[i]["label"],
            "from_id": nodes[i]["id"],
            "to_label": nodes[i+1]["label"],
            "to_id": nodes[i+1]["id"],
            "props": {}
        })

    return nodes, rels
