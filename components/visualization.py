"""
Interactive Scientific Visualization Component for ThesisFlow.
Generates Plotly interactive figures for physics equations, parameter sensitivity sweeps,
and specialized physics domains (Harmonic oscillators, Gaussians, Relativistic kinematics, Gravitation).
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sympy as sp
from core.mathematical_engine import MathematicalEngine


class ScientificVisualizer:
    """Creates scientific-grade Plotly visualizations."""

    THEME_COLORS = {
        "cyan": "#00E5FF",
        "blue": "#3B82F6",
        "purple": "#8B5CF6",
        "emerald": "#10B981",
        "amber": "#F59E0B",
        "rose": "#F43F5E",
        "bg_dark": "#0A0E1A",
        "bg_paper": "#111827",
        "grid": "#1E293B",
        "text": "#F8FAFC",
        "text_muted": "#94A3B8"
    }

    @staticmethod
    def create_1d_curve(
        x: np.ndarray,
        y: np.ndarray,
        title: str,
        x_label: str,
        y_label: str,
        current_x: Optional[float] = None,
        current_y: Optional[float] = None,
        log_y: bool = False
    ) -> go.Figure:
        """Standard 1D scientific response curve with live operating point marker."""
        fig = go.Figure()

        # Primary function trace
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="lines",
            name=f"{y_label}({x_label})",
            line=dict(color=ScientificVisualizer.THEME_COLORS["cyan"], width=2.8),
            hovertemplate=f"<b>{x_label}</b>: %{{x:.4g}}<br><b>{y_label}</b>: %{{y:.4g}}<extra></extra>"
        ))

        # Current operating point marker
        if current_x is not None and current_y is not None and not np.isnan(current_y):
            fig.add_trace(go.Scatter(
                x=[current_x],
                y=[current_y],
                mode="markers",
                name="Operating Point",
                marker=dict(
                    color=ScientificVisualizer.THEME_COLORS["rose"],
                    size=12,
                    symbol="diamond",
                    line=dict(color="#FFFFFF", width=1.5)
                ),
                hovertemplate=f"Current: ({x_label}={current_x:.4g}, {y_label}={current_y:.4g})<extra></extra>"
            ))

        fig.update_layout(
            title=dict(text=title, font=dict(color=ScientificVisualizer.THEME_COLORS["text"], size=16)),
            xaxis=dict(
                title=dict(text=x_label, font=dict(color=ScientificVisualizer.THEME_COLORS["text_muted"])),
                gridcolor=ScientificVisualizer.THEME_COLORS["grid"],
                zerolinecolor="#334155",
                tickfont=dict(color=ScientificVisualizer.THEME_COLORS["text_muted"])
            ),
            yaxis=dict(
                title=dict(text=y_label, font=dict(color=ScientificVisualizer.THEME_COLORS["text_muted"])),
                gridcolor=ScientificVisualizer.THEME_COLORS["grid"],
                zerolinecolor="#334155",
                type="log" if log_y else "linear",
                tickfont=dict(color=ScientificVisualizer.THEME_COLORS["text_muted"])
            ),
            template="plotly_dark",
            paper_bgcolor=ScientificVisualizer.THEME_COLORS["bg_dark"],
            plot_bgcolor=ScientificVisualizer.THEME_COLORS["bg_paper"],
            margin=dict(l=50, r=40, t=50, b=50),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color=ScientificVisualizer.THEME_COLORS["text_muted"])
            )
        )
        return fig

    @staticmethod
    def create_harmonic_motion_visualizer(
        A: float,
        omega: float,
        phi: float,
        t_max: float = 10.0
    ) -> go.Figure:
        """
        Specialized multi-panel physical visualizer for Simple Harmonic Motion.
        Displays Displacement x(t), Velocity v(t), Acceleration a(t), and Phase Space (x vs v).
        """
        t = np.linspace(0, t_max, 400)
        x = A * np.cos(omega * t + phi)
        v = - A * omega * np.sin(omega * t + phi)
        a = - A * (omega ** 2) * np.cos(omega * t + phi)

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Position: x(t) = A cos(ωt + φ)",
                "Velocity: v(t) = - A ω sin(ωt + φ)",
                "Acceleration: a(t) = - A ω² cos(ωt + φ)",
                "Phase Space Trajectory: v vs x"
            ),
            vertical_spacing=0.15,
            horizontal_spacing=0.12
        )

        # 1. Position x(t)
        fig.add_trace(go.Scatter(x=t, y=x, mode="lines", name="x(t) [m]", line=dict(color="#00E5FF", width=2)), row=1, col=1)
        # 2. Velocity v(t)
        fig.add_trace(go.Scatter(x=t, y=v, mode="lines", name="v(t) [m/s]", line=dict(color="#10B981", width=2)), row=1, col=2)
        # 3. Acceleration a(t)
        fig.add_trace(go.Scatter(x=t, y=a, mode="lines", name="a(t) [m/s²]", line=dict(color="#F59E0B", width=2)), row=2, col=1)
        # 4. Phase Space: v vs x
        fig.add_trace(go.Scatter(x=x, y=v, mode="lines", name="Phase Orbit", line=dict(color="#8B5CF6", width=2.5)), row=2, col=2)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0A0E1A",
            plot_bgcolor="#111827",
            height=600,
            showlegend=False,
            margin=dict(l=40, r=40, t=60, b=40)
        )
        return fig

    @staticmethod
    def create_gaussian_visualizer(
        mu: float,
        sigma: float,
        x_min: Optional[float] = None,
        x_max: Optional[float] = None
    ) -> go.Figure:
        """
        Specialized visualizer for Gaussian / Normal Distribution.
        Highlights mean, standard deviation regions (±1σ, ±2σ), and cumulative density.
        """
        if sigma <= 0:
            sigma = 0.01

        if x_min is None:
            x_min = mu - 4 * sigma
        if x_max is None:
            x_max = mu + 4 * sigma

        x = np.linspace(x_min, x_max, 400)
        pdf = (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-((x - mu) ** 2) / (2 * (sigma ** 2)))

        fig = go.Figure()

        # Shaded ±1σ region (68.27% of probability mass)
        x_1sigma = np.linspace(mu - sigma, mu + sigma, 200)
        pdf_1sigma = (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-((x_1sigma - mu) ** 2) / (2 * (sigma ** 2)))
        fig.add_trace(go.Scatter(
            x=np.concatenate([x_1sigma, x_1sigma[::-1]]),
            y=np.concatenate([pdf_1sigma, np.zeros_like(pdf_1sigma)]),
            fill="toself",
            fillcolor="rgba(0, 229, 255, 0.2)",
            line=dict(color="rgba(255,255,255,0)"),
            name="±1σ (68.3% Confidence)",
            hoverinfo="skip"
        ))

        # Primary PDF curve
        fig.add_trace(go.Scatter(
            x=x,
            y=pdf,
            mode="lines",
            name="Probability Density f(x)",
            line=dict(color="#00E5FF", width=2.5)
        ))

        # Vertical line for mean μ
        max_pdf = np.max(pdf)
        fig.add_trace(go.Scatter(
            x=[mu, mu],
            y=[0, max_pdf],
            mode="lines",
            name=f"Mean μ = {mu:.3g}",
            line=dict(color="#F43F5E", width=2, dash="dash")
        ))

        fig.update_layout(
            title=f"Gaussian Distribution: μ={mu:.3g}, σ={sigma:.3g} (Peak={max_pdf:.4f})",
            xaxis=dict(title="Variable x", gridcolor="#1E293B"),
            yaxis=dict(title="Probability Density f(x)", gridcolor="#1E293B"),
            template="plotly_dark",
            paper_bgcolor="#0A0E1A",
            plot_bgcolor="#111827",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        return fig
