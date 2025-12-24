def map_sequence(event, cfg):
    nodes = []
    rels = []
    base = cfg.get("base")
    if not base:
        return nodes, rels
    base_id = event.get(base.get("id"))
    if base_id is None:
        return nodes, rels
    base_node = {"label": base["label"], "id": base_id}
    nodes.append(base_node)
    for seq in cfg.get("sequences", []):
        arr = event.get(seq.get("field")) or []
        for item in arr:
            item_id = item.get(seq.get("id_field", "id"))
            if item_id is None:
                continue
            child = {"label": seq["label"], "id": item_id}
            nodes.append(child)
            rels.append({
                "type": seq.get("type", "HAS"),
                "from_label": base_node["label"],
                "from_id": base_node["id"],
                "to_label": child["label"],
                "to_id": child["id"],
                "props": {p: item.get(p) for p in seq.get("properties", [])}
            })
    return nodes, rels
