from operator import abs, add

from anytree import PreOrderIter, find


def compute_max_bbox_for_child(sim, parent_node_name):
    sim.volume_manager.update_volume_tree_if_needed()
    volMax = [0.0, 0.0, 0.0]
    for volumeNode in PreOrderIter(
        find(
            sim.volume_manager.volume_tree_root,
            lambda node: node.name == parent_node_name,
        )
    ):
        if volumeNode.name == parent_node_name:
            continue
        else:
            # Get bounding box limits
            bbLimits = volumeNode.bounding_limits

            # Apply translation to bounding box limits
            bbLimits = [
                list(map(add, point, volumeNode.translation)) for point in bbLimits
            ]

            # Apply rotation matrix to bounding box limits
            bbLimits = [point @ volumeNode.rotation for point in bbLimits]

            # Get farthest point from origin
            for point in bbLimits:
                volMax = list(map(max, volMax, list(map(abs, point))))

    # Multiply by 2 to get the full size
    volMax = list(map(lambda x: x * 2, volMax))

    return volMax
