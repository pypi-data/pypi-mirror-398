from typing import Any

import matplotlib.pyplot as plt
import networkx as nx


class GraphRender:
    """We want this to render Verge Graph"""

    def __init__(self, g: Any, with_labels: bool = True):
        _ = plt.subplot(122)
        nx.draw_shell(g, nlist=[range(5, 10), range(5)], with_labels=True, font_weight="bold")
