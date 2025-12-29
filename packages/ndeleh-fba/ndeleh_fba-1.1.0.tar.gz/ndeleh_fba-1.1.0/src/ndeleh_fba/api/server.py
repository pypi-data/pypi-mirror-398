from ndeleh_fba.api.auth import get_api_key
from fastapi import FastAPI, Depends
from ndeleh_fba import Graph
from ndeleh_fba.schemas import (
    FishboneRequest,
    FishboneResponse,
    FishboneV2Request
)
# 🔐 NEW: API key auth
from .auth import get_api_key

# Old v1 fishbone
from ndeleh_fba.fishbone import build_fishbone
from .fishbone_v2_api import router as fishbone_v2_router
from .torque_reasoning_api import router as torque_reasoning_router
from .torque_api import router as torque_router
from ndeleh_fba.api.industrial_endpoints import router as industrial_router

# -------------------------------
# CREATE THE APP **BEFORE** include_router()
# -------------------------------

app = FastAPI(
    title="Ndeleh Fish Bone Algorithm API",
    description="Web API for running the N-FBA associative intelligence algorithm.",
    version="1.0.0"
)

# -------------------------------
# NOW include routers (AFTER app is created)
# -------------------------------

# Protect these routers
app.include_router(industrial_router, dependencies=[Depends(get_api_key)])
app.include_router(torque_reasoning_router, dependencies=[Depends(get_api_key)])
app.include_router(torque_router, dependencies=[Depends(get_api_key)])

# OPTIONAL: Leave FBA builder open for testing
app.include_router(fishbone_v2_router)


# Existing v1 FBA route
@app.post("/api/fishbone/v2/build", response_model=FishboneResponse)
def build_v2(
    req: FishboneV2Request,
    api_key: str = Depends(get_api_key),
):
    g = Graph()
    # AUTO mode
    if not req.edges or len(req.edges) == 0:
        from ndeleh_fba.auto_edges import auto_build_edges_from_torque
        auto_edges = auto_build_edges_from_torque(req)
        edges = auto_edges
    else:
        # MANUAL mode
        edges = [e.dict() for e in req.edges]

    # Build graph
    for e in edges:
        g.add_edge(e["src"], e["dst"], e["weight"])

    # --- Step B: run N-FBA v2 ---
    result = build_fishbone_v2(g, seed=list(g.nodes.keys())[0])

    return FishboneResponse(
        spine_nodes=result.spine_nodes,
        microspines=result.microspines,
        morphology=result.morphology.name
    )

