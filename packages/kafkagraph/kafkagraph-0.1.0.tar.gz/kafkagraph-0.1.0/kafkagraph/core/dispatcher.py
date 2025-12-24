from kafkagraph.mappers.simple import map_simple
from kafkagraph.mappers.autograph import map_autograph
from kafkagraph.mappers.sequence import map_sequence
from kafkagraph.license.features import Feature

def dispatch(event, cfg, license_mgr):
    mode = cfg.get("mode", "simple")

    if mode == "simple":
        return map_simple(event, cfg)

    if mode == "autograph":
        if not license_mgr.has_feature(Feature.AUTOGRAPH):
            raise RuntimeError("AutoGraph not licensed")
        return map_autograph(event)

    if mode == "sequence":
        if not license_mgr.has_feature(Feature.SEQUENCE_ARRAY):
            raise RuntimeError("Sequence mapping not licensed")
        return map_sequence(event, cfg)

    raise RuntimeError("Unsupported mode")
