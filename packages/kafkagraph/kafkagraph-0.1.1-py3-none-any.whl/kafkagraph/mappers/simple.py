def map_simple(event, cfg):
    nodes, rels = {}, []

    for k, n in cfg["nodes"].items():
        v = event.get(n["id"])
        if v is not None:
            nodes[k] = {"label": n["label"], "id": v}

    for r in cfg["relationships"]:
        f, t = nodes.get(r["from"]), nodes.get(r["to"])
        if f and t:
            rels.append({
                "type": r["type"],
                "from_label": f["label"],
                "from_id": f["id"],
                "to_label": t["label"],
                "to_id": t["id"],
                "props": {p: event.get(p) for p in r.get("properties", [])}
            })

    return list(nodes.values()), rels
