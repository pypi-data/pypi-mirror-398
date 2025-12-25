"""

This module contain some render function for the basics experiment

"""

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from matplotlib.patches import FancyBboxPatch


def plot_bipartite_graph_svg(
    x_names,
    b_names,
    edges,
    x_sol_indices,
    output_file="fancy_bipartite_graph.svg",
    iterations=5,
    important_exclusive=False,
):
    """
    Plots a bipartite graph with custom node ordering and auto-sized node boxes.

    Improvements:
      1. Custom node ordering:
         - Uses a simple iterative barycenter approach that reorders nodes so that each is placed
           closer to the average position of its connected nodes.
         - x_nodes appear at x=0 and b_nodes at x=1, with y-positions assigned by the ordering.
      2. Auto sizing for node boxes:
         - Node widths are determined by the maximum label length (scaled by a factor); you can adjust
           the scaling factor to suit your design needs.

    Parameters:
      x_names (list of str): Names for x nodes.
      b_names (list of str): Names for b nodes.
      edges (list of tuple): Each tuple (x_name, b_name) represents an edge.
      x_sol_indices (list of int): Indices (with respect to x_names) for important x nodes.
      output_file (str): Filename for the output SVG.
      iterations (int): Number of iterations to update barycenter orders.
    """

    # Determine the important x nodes.
    important_x = {x_names[i] for i in x_sol_indices}

    if important_exclusive:
        # If important_exclusive is True, only keep important x nodes.
        x_names = [x for x in x_names if x in important_x]

    # Build the graph.
    G = nx.Graph()
    for x in x_names:
        G.add_node(x, bipartite=0)
    for b in b_names:
        G.add_node(b, bipartite=1)
    for x, b in edges:
        if x in x_names and b in b_names:
            G.add_edge(x, b)
        # else:
        # raise ValueError(f"Edge {(x, b)} contains a node not provided in the node lists.")

    # Build connection dictionaries for the barycenter calculation.
    # For each x node, list the connected b nodes; similarly for b nodes.
    x_connections = {x: [] for x in x_names}
    b_connections = {b: [] for b in b_names}
    for x, b in edges:
        if x in x_names and b in b_names:
            x_connections[x].append(b)
            b_connections[b].append(x)

    # Initialize orders with the given lists.
    x_order = list(x_names)
    b_order = list(b_names)

    # Iterate to compute barycenters and update orders.
    for _ in range(iterations):
        # Update x ordering based on positions of connected b nodes.
        def barycenter_x(x):
            if x_connections[x]:
                # Average index of connected b nodes
                return sum(b_order.index(b) for b in x_connections[x]) / len(
                    x_connections[x]
                )
            return 0

        x_order.sort(key=barycenter_x)

        # Update b ordering based on positions of connected x nodes.
        def barycenter_b(b):
            if b_connections[b]:
                return sum(x_order.index(x) for x in b_connections[b]) / len(
                    b_connections[b]
                )
            return 0

        b_order.sort(key=barycenter_b)

    # Now assign positions: x nodes at x=0 and b nodes at x=1.
    pos = {}
    n_x = len(x_order)
    n_b = len(b_order)

    scale = max(n_x, 20)

    for i, node in enumerate(x_order):
        # y positions equally spaced (inverted so that 0 is at the bottom and 1 at the top).
        pos[node] = (0 * scale, (1 - (i / (n_x - 1) if n_x > 1 else 0.5)) * scale)
    for i, node in enumerate(b_order):
        pos[node] = (1 * scale, (1 - (i / (n_b - 1) if n_b > 1 else 0.5)) * scale)

    # Separate edges into those from important x nodes and the rest.
    important_edges = []
    other_edges = []
    for u, v in G.edges():
        # Determine the x-node in the edge.
        if u in x_names and v in b_names:
            xnode = u
        elif v in x_names and u in b_names:
            xnode = v
        else:
            continue
        if xnode in important_x:
            important_edges.append((u, v))
        else:
            other_edges.append((u, v))

    # Create figure and axis.
    fig, ax = plt.subplots(figsize=(scale / 2, scale / 2))
    ax.set_facecolor("#f0f2f5")

    # Draw edges.
    nx.draw_networkx_edges(
        G, pos, edgelist=important_edges, edge_color="#FF8A80", width=2, ax=ax
    )
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=other_edges,
        edge_color="#B0BEC5",
        style="dashed",
        width=1,
        ax=ax,
    )

    # --- Custom drawing of nodes ---
    # Auto-size: compute maximum label lengths for scaling node widths.
    max_label_len_x = max(len(label) for label in x_names) if x_names else 0
    max_label_len_b = max(len(label) for label in b_names) if b_names else 0

    # Set base sizes and scale factors (tweak these as needed).
    base_width = 20
    width_x = base_width + max_label_len_x * 0.02
    width_b = base_width + max_label_len_b * 0.02
    height_node = 0.6  # You can also relate this to font size if required.

    # Define colors.
    color_important_x = "#A8E6CF"  # Pastel green.
    color_unsolved_x = "#FFD3B6"  # Pastel peach.
    color_b = "#BBDEFB"  # Pastel blue.

    # node_offset = 10  # For subtle label alignment.

    # Draw x nodes (plain rectangles).
    for node in x_names:
        cx, cy = pos[node]
        # For x nodes, apply a slight left offset.
        cx_offset = cx - width_x / 2
        lower_left = (cx_offset - width_x / 2, cy - height_node / 2)
        facecolor = color_important_x if node in important_x else color_unsolved_x
        patch = FancyBboxPatch(
            lower_left,
            width_x,
            height_node,
            boxstyle="round,pad=0.2",
            linewidth=0.2,
            edgecolor="black",
            facecolor=facecolor,
            mutation_scale=0.5,
        )
        ax.add_patch(patch)
        ax.text(
            cx_offset, cy, node, ha="center", va="center", fontsize=10, color="black"
        )

    # Draw b nodes (rounded rectangles).
    for node in b_names:
        cx, cy = pos[node]
        # For b nodes, apply a slight right offset.
        cx_offset = cx + width_b / 2
        lower_left = (cx_offset - width_b / 2, cy - height_node / 2)
        patch = FancyBboxPatch(
            lower_left,
            width_b,
            height_node,
            boxstyle="round,pad=0.2",
            linewidth=2,
            edgecolor="black",
            facecolor=color_b,
            mutation_scale=1.5,
        )
        ax.add_patch(patch)
        ax.text(
            cx_offset, cy, node, ha="center", va="center", fontsize=10, color="black"
        )

    # Title and final touches.
    # plt.title("Fancy Bipartite Graph: Ordered Nodes and Auto-sized Boxes", fontsize=16, weight="bold", pad=20)
    ax.set_axis_off()
    ax.margins(0.05)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

    # Save the SVG output.
    plt.savefig(output_file, format="svg", bbox_inches="tight")
    plt.close()
    print(f"Graph saved as {output_file}")


def plot_bipartite_graph_svg_dep(
    x_names, b_names, edges, x_sol_indices, output_file="fancy_bipartite_graph.svg"
):
    """
    Plots a modern, fancy bipartite graph with custom node shapes and updated colors,
    then saves the plot as an SVG file.

    Parameters:
      x_names (list of str): Names for the x variables.
      b_names (list of str): Names for the b groups.
      edges (list of tuple): Each tuple (x_name, b_name) represents an edge from an x-node to a b-node.
      x_sol_indices (list of int): List of indices (with respect to x_names) corresponding to important (solved) x nodes.
      output_file (str): Filename for the output SVG.

    Customizations:
      - x-nodes are drawn as plain rectangles.
      - b-nodes are drawn as rounded rectangles.
      - Edges originating from an important x-node are drawn in a modern red (thicker),
        others in a dashed soft gray-blue.
      - A modern pastel color scheme is used with generous margins.
    """

    # Build the bipartite graph.
    G = nx.Graph()
    for x in x_names:
        G.add_node(x, bipartite=0)
    for b in b_names:
        G.add_node(b, bipartite=1)
    for edge in edges:
        if edge[0] in x_names and edge[1] in b_names:
            G.add_edge(edge[0], edge[1])
        else:
            raise ValueError(
                f"Edge {edge} contains a node not provided in the node lists."
            )

    # Compute a bipartite layout.
    pos = nx.bipartite_layout(G, x_names, scale=1.5)

    # Determine the set of important (solved) x nodes.
    important_x = {x_names[i] for i in x_sol_indices}

    # Separate edges: those that "originate" from an important x-node and the others.
    important_edges = []
    other_edges = []
    for u, v in G.edges():
        if u in x_names and v in b_names:
            xnode = u
        elif v in x_names and u in b_names:
            xnode = v
        else:
            continue
        if xnode in important_x:
            important_edges.append((u, v))
        else:
            other_edges.append((u, v))

    # Create the figure and axis.
    fig, ax = plt.subplots(figsize=(30, 30))
    ax.set_facecolor("#f0f2f5")  # Light modern background.

    # Draw edges first.
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=important_edges,
        edge_color="#FF8A80",  # Modern red for important edges.
        width=2,
        ax=ax,
    )
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=other_edges,
        edge_color="#B0BEC5",  # Soft gray-blue.
        style="dashed",
        width=1,
        ax=ax,
    )

    # --- Custom drawing of nodes via patches ---
    # Define sizes for node patches (adjust if labels are very long).
    width_x, height_x = 0.2, 0.0003  # For x nodes (plain rectangles).
    width_b, height_b = 0.1, 0.0003  # For b nodes (rounded rectangles).

    # Colors using a modern pastel palette.
    color_important_x = "#A8E6CF"  # Pastel green.
    color_unsolved_x = "#FFD3B6"  # Pastel peach.
    color_b = "#BBDEFB"  # Pastel blue.

    node_offset = 0.1  # Offset for node labels.

    # Draw x nodes as plain rectangles.
    for node in x_names:
        cx, cy = pos[node]
        cx -= node_offset  # Offset for x nodes.
        lower_left = (cx - width_x / 2, cy - height_x / 2)
        facecolor = color_important_x if node in important_x else color_unsolved_x
        patch = FancyBboxPatch(
            lower_left,
            width_x,
            height_x,
            boxstyle="round,pad=0.02",
            linewidth=2,
            edgecolor="black",
            facecolor=facecolor,
            mutation_scale=1.5,
        )
        ax.add_patch(patch)
        ax.text(cx, cy, node, ha="center", va="center", fontsize=10, color="black")

    # Draw b nodes as rounded rectangles.
    for node in b_names:
        cx, cy = pos[node]
        cx += node_offset  # Offset for x nodes.
        lower_left = (cx - width_b / 2, cy - height_b / 2)
        patch = FancyBboxPatch(
            lower_left,
            width_b,
            height_b,
            boxstyle="square,pad=0.02",
            linewidth=2,
            edgecolor="black",
            facecolor=color_b,
            mutation_scale=1.5,
        )
        ax.add_patch(patch)
        ax.text(cx, cy, node, ha="center", va="center", fontsize=10, color="black")

    # Final touches.
    plt.title(
        "Fancy Bipartite Graph: x Variables and b Groups",
        fontsize=16,
        weight="bold",
        pad=20,
    )
    ax.set_axis_off()
    # Increase margins so that nodes are not cut off.
    ax.margins(0.05)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

    # Save the output as an SVG file.
    plt.savefig(output_file, format="svg", bbox_inches="tight")
    plt.close()
    print(f"Graph saved as {output_file}")


def animate_single_pendulum(
    length: float, angle_array: np.ndarray, time_array: np.ndarray
):
    """
    Animates a single pendulum based on its length, angle data, and time steps.

    Parameters:
        length (float): Length of the pendulum.
        angle_array (ndarray): Array of angular positions over time.
        time_array (ndarray): Array of time steps corresponding to angles.
    """
    x_coords = length * np.sin(angle_array[:, 0])
    y_coords = -length * np.cos(angle_array[:, 0])

    fig = plt.figure(figsize=(5, 4))
    ax = fig.add_subplot(
        autoscale_on=False, xlim=(-length, length), ylim=(-length, length)
    )
    ax.set_aspect("equal")
    ax.grid()

    (trace_line,) = ax.plot([], [], ".-", lw=1, ms=2)
    (pendulum_line,) = ax.plot([], [], "o-", lw=2)
    time_template = "time = %.1fs"
    time_text = ax.text(0.05, 0.9, "", transform=ax.transAxes)

    def update_frame(i):
        current_x = [0, x_coords[i]]
        current_y = [0, y_coords[i]]

        trace_x = x_coords[:i]
        trace_y = y_coords[:i]

        pendulum_line.set_data(current_x, current_y)
        trace_line.set_data(trace_x, trace_y)
        time_text.set_text(time_template % time_array[i])
        return pendulum_line, trace_line, time_text

    animation.FuncAnimation(fig, update_frame, len(angle_array), interval=40, blit=True)
    plt.show()


def animate_double_pendulum(
    length1: float,
    length2: float,
    angle_array: np.ndarray,
    time_array: np.ndarray,
    fig=None,
):
    """
    Animates a double pendulum based on its segment lengths, angles, and time steps.

    Parameters:
        length1 (float): Length of the first segment.
        length2 (float): Length of the second segment.
        angle_array (ndarray): Array of angular positions of both segments over time.
        time_array (ndarray): Array of time steps corresponding to angles.
    """
    total_length = length1 + length2

    x1 = length1 * np.sin(angle_array[:, 0])
    y1 = -length1 * np.cos(angle_array[:, 0])

    x2 = length2 * np.sin(angle_array[:, 2]) + x1
    y2 = -length2 * np.cos(angle_array[:, 2]) + y1
    if fig is None:
        fig = plt.figure(figsize=(5, 4))

    ax = fig.add_subplot(
        autoscale_on=False,
        xlim=(-total_length, total_length),
        ylim=(-total_length, total_length),
    )
    ax.set_aspect("equal")
    ax.grid()

    (trace_line,) = ax.plot([], [], ".-", lw=1, ms=2)
    (pendulum_line,) = ax.plot([], [], "o-", lw=2)
    time_template = "time = %.1fs"
    time_text = ax.text(0.05, 0.9, "", transform=ax.transAxes)

    def update_frame(i):
        current_x = [0, x1[i], x2[i]]
        current_y = [0, y1[i], y2[i]]

        trace_x = x2[:i]
        trace_y = y2[:i]

        pendulum_line.set_data(current_x, current_y)
        trace_line.set_data(trace_x, trace_y)
        time_text.set_text(time_template % time_array[i])
        return pendulum_line, trace_line, time_text

    animation.FuncAnimation(fig, update_frame, len(angle_array), interval=40, blit=True)
    plt.show()
