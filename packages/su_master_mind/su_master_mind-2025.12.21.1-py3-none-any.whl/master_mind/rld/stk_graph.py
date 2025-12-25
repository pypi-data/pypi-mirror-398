import logging
import threading

import gymnasium as gym
import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html, Patch
from pystk2_gymnasium.utils import rotate
import pystk2


class LivePlotServer:
    def __init__(self, host="127.0.0.1", port=8050, refresh_interval=1):
        self.host = host
        self.port = port
        self._lock = threading.Lock()
        self._fig = go.Figure()
        self._trace_count = 0
        self._trace_updates = {}  # pending updates
        logging.getLogger("werkzeug").setLevel(logging.WARNING)  # or ERROR, CRITICAL

        # Allow subclass to setup the initial figure
        if hasattr(self, "setup_figure") and callable(self.setup_figure):
            self.setup_figure(self._fig)

        # Initialize Dash
        self.app = Dash(__name__)
        self.app.layout = html.Div(
            [
                dcc.Graph(
                    id="live-plot",
                    figure=self._fig,
                    style={"width": "100%", "height": "90vh"},
                ),
                dcc.Interval(
                    id="interval", interval=int(refresh_interval * 1000), n_intervals=0
                ),
            ]
        )

        # Callback: triggered every interval
        @self.app.callback(
            Output("live-plot", "figure"), Input("interval", "n_intervals")
        )
        def _refresh(n_intervals):
            with self._lock:
                if not self._trace_updates:
                    return Patch()  # nothing to update

                patch = Patch()
                for idx, data in self._trace_updates.items():
                    patch.data[idx].x = data.get("x", [])
                    patch.data[idx].y = data.get("y", [])
                    patch.data[idx].z = data.get("z", [])
                self._trace_updates.clear()
                return patch

    # ------------------------
    # Server control
    # ------------------------
    def start(self, block=False):
        from werkzeug.serving import make_server

        self._server = make_server(self.host, self.port, self.app.server)
        if block:
            self._server.serve_forever()
        else:

            def run():
                self._server.serve_forever()

            self._thread = threading.Thread(target=run, daemon=True)
            self._thread.start()
        return f"http://{self.host}:{self.port}/"

    def close(self):
        if hasattr(self, "_server"):
            self._server.shutdown()
            if hasattr(self, "_thread"):
                self._thread.join()

    # ------------------------
    # Trace management
    # ------------------------
    def add_trace(self, trace):
        """Add a new trace to the figure."""
        with self._lock:
            self._fig.add_trace(trace)
            idx = self._trace_count
            self._trace_count += 1
            return idx

    def set_trace(self, trace_index, x=None, y=None, z=None):
        """Set or replace the full data of a trace (applied on next refresh)."""
        with self._lock:
            self._trace_updates[trace_index] = {
                "x": None if x is None else x,
                "y": None if y is None else y,
                "z": None if z is None else z,
            }


def quaternion_inverse(q):
    """
    Compute the inverse of a quaternion.
    q = [w, x, y, z]
    """
    w, x, y, z = q
    norm_sq = w**2 + x**2 + y**2 + z**2
    return np.array([w, -x, -y, -z]) / norm_sq


class STKLivePlotServer(LivePlotServer):
    def __init__(self, env: gym.Env, **kwargs):
        self.env = env
        self.top_tracks = 5

        self.track_traces_indices: list[int] = []
        self.item_indices: dict[str, int] = {}
        self.kart_trace_index = 0
        self.other_karts_index = 0
        super().__init__(**kwargs)

    def update_plot(self, obs):
        kart_ix = self.env.kart_indices[0]
        kart = self.env.world.karts[kart_ix]
        rotation = quaternion_inverse(kart.rotation)

        def global_coordinates(x):
            """Returns a vector in the global view

            X right, Y up, Z forwards
            """
            return rotate(x, rotation) + kart.location

        starts = np.vstack(
            [global_coordinates(p) for p in obs["paths_start"][: self.top_tracks]]
        )
        ends = np.vstack(
            [global_coordinates(p) for p in obs["paths_end"][: self.top_tracks]]
        )
        for ix, start, end in zip(self.track_traces_indices, starts, ends):
            self.set_trace(
                ix,
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                z=[start[2], end[2]],
            )

        # Add kart marker (yellow)
        kart_pos = global_coordinates(obs["front"])
        self.set_trace(
            self.kart_trace_index,
            x=[kart_pos[0]],
            y=[kart_pos[1]],
            z=[kart_pos[2]],
        )

        # Add other karts
        other_karts_pos = np.vstack(
            [
                global_coordinates(other_kart_pos)
                for other_kart_pos in obs["karts_position"]
            ]
        )
        self.set_trace(
            self.other_karts_index,
            x=other_karts_pos[:, 0],
            y=other_karts_pos[:, 1],
            z=other_karts_pos[:, 2],
        )

        # Set items
        items_position = np.vstack(
            [global_coordinates(p) for p in obs["items_position"]]
        )
        items_type = np.array(obs["items_type"])
        for v in pystk2.Item.Type.__members__.values():
            trace_ix = self.item_indices[v.name]
            pos = items_position[items_type == v.value]
            self.set_trace(trace_ix, x=pos[:, 0], y=pos[:, 1], z=pos[:, 2])

    def setup_figure(self, fig) -> go.Figure:
        """
        Visualize a 3D track with point indices labeled.

        Parameters:
        -----------
        track_points : numpy.ndarray
            Array of shape (N, 3) representing 3D points
        label_every_n : int
            Label every nth point (default: 5)
        show_all_points : bool
            Whether to show all points as markers (default: True)
        show_line : bool
            Whether to show connecting line (default: True)
        title : str
            Plot title
        """

        # numpy array with shape (N, 3)
        track: pystk2.Track = self.env.track
        track_points = track.path_nodes[:, 0]

        # Add the track line
        for ix in range(len(track.path_nodes)):
            self.add_trace(
                go.Scatter3d(
                    x=track.path_nodes[ix, :, 0],
                    y=track.path_nodes[ix, :, 1],
                    z=track.path_nodes[ix, :, 2],
                    mode="lines",
                    line=dict(color="lightblue", width=4),
                    showlegend=False,
                )
            )

        self.add_trace(
            go.Scatter3d(
                x=track_points[:, 0],
                y=track_points[:, 1],
                z=track_points[:, 2],
                mode="markers",
                marker=dict(size=3, color="red", opacity=0.6),
                name="All Points",
                hovertemplate="Point %{pointNumber}<br>"
                + "X: %{x:.3f}<br>"
                + "Y: %{y:.3f}<br>"
                + "Z: %{z:.3f}<extra></extra>",
            )
        )

        # Add start marker (green)
        self.add_trace(
            go.Scatter3d(
                x=[track_points[0, 0]],
                y=[track_points[0, 1]],
                z=[track_points[0, 2]],
                mode="markers+text",
                marker=dict(size=10, color="green", symbol="diamond"),
                text=["START"],
                textposition="top center",
                textfont=dict(size=14, color="green"),
                name="Start Point",
                hovertemplate="Start Point<br>"
                + "X: %{x:.3f}<br>"
                + "Y: %{y:.3f}<br>"
                + "Z: %{z:.3f}<extra></extra>",
            )
        )

        # Paths next to the kart
        for _ in range(self.top_tracks):
            self.track_traces_indices.append(
                self.add_trace(
                    go.Scatter3d(
                        x=[],
                        y=[],
                        z=[],
                        mode="lines",
                        line=dict(color="yellow", width=8),
                        showlegend=False,
                    )
                )
            )

        # The kart itself
        self.kart_trace_index = self.add_trace(
            go.Scatter3d(
                x=[],
                y=[],
                z=[],
                mode="markers+text",
                marker=dict(size=10, color="orange", symbol="diamond"),
                text=["Kart"],
                textposition="top center",
                textfont=dict(size=14, color="orange"),
                name="Kart",
            )
        )

        # The enemy karts
        self.other_karts_index = self.add_trace(
            go.Scatter3d(
                x=[],
                y=[],
                z=[],
                mode="markers",
                marker=dict(size=10, color="red", symbol="x"),
                text=["Other kart"],
                textposition="top center",
                textfont=dict(size=14, color="red"),
                name="Other",
            )
        )

        # Add items
        for v in pystk2.Item.Type.__members__.values():
            self.item_indices[v.name] = self.add_trace(
                go.Scatter3d(
                    x=[],
                    y=[],
                    z=[],
                    mode="text",
                    text=[v.name],
                    textfont=dict(size=12, color="black"),
                )
            )

        # Update layout for better visualization
        fig.update_layout(
            title=dict(text="STK Track", x=0.5, font=dict(size=16)),
            scene=dict(
                aspectmode="data",
                xaxis_title="X Coordinate",
                yaxis_title="Y Coordinate",
                zaxis_title="Z Coordinate",
                zaxis=dict(autorange="reversed"),
                # camera position (data domain => everything is between -1 and 1)
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=2.0),
                    center=dict(x=0, y=0, z=0),
                    up=dict(x=0, y=1, z=0),
                ),
            ),
            autosize=True,
            # width=1000,
            # height=700,
            showlegend=True,
        )
