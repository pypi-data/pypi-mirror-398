import argparse
from ndeleh_fba import Graph
from ndeleh_fba.fishbone import build_fishbone


def fba_cli():
    parser = argparse.ArgumentParser(
        description="Run the Ndeleh Fish Bone Algorithm (N-FBA)."
    )
    
    parser.add_argument(
        "--seed",
        required=True,
        help="Starting node for N-FBA"
    )

    parser.add_argument(
        "--file",
        required=False,
        help="Graph file (.txt) with edges: nodeA nodeB weight"
    )

    args = parser.parse_args()

    g = Graph()

    if args.file:
        # Load graph from file
        with open(args.file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 3:
                    src, dst, w = parts
                    g.add_edge(src, dst, weight=float(w))
        print(f"Loaded graph from {args.file}")
    else:
        # Default sample graph
        g.add_edge("A", "B", weight=0.9)
        g.add_edge("B", "C", weight=0.8)
        g.add_edge("A", "D", weight=0.5)
        g.add_edge("D", "E", weight=0.6)
        g.add_edge("C", "F", weight=0.4)

    # Run algorithm
    result = build_fishbone(g, seed=args.seed)

    print("\n=== N-FBA SPINE ===")
    print(result.spine_nodes)

    print("\n=== N-FBA RIBS ===")
    for spine_node, rib_dict in result.ribs.items():
        print(f"\nSpine Node: {spine_node}")
        for rib_node, rib in rib_dict.items():
            print(f"  Rib → {rib_node} (score={rib.score:.3f})")
            for micro_id, micro_rib in rib.children.items():
                print(f"    Micro-rib → {micro_id} (score={micro_rib.score:.3f})")

    print("\n=== MORPHOLOGY ===")
    print(result.morphology)
