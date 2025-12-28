"""
Core module for PieDrilldown package.
Contains the main PieDrilldown class for creating drill-down pie charts.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import ConnectionPatch
from typing import List, Optional, Tuple, Union


class PieDrilldown:
    """
    A class to create pie charts with drill-down visualizations.
    
    The drill-down can be either a stacked bar chart or a smaller pie chart,
    showing the breakdown of one segment from the main pie chart.
    
    Parameters
    ----------
    main_labels : list
        Labels for the main pie chart segments.
    main_values : list
        Values for the main pie chart segments.
    drilldown_labels : list
        Labels for the drill-down chart segments.
    drilldown_values : list
        Values for the drill-down chart segments.
    drilldown_index : int, optional
        Index of the main pie segment to drill down (default: 0).
    main_colors : list, optional
        Colors for the main pie chart segments.
    drilldown_colors : list, optional
        Colors for the drill-down chart segments.
    
    Examples
    --------
    >>> from piedrilldown import PieDrilldown
    >>> 
    >>> # Create a bar of pie chart
    >>> chart = PieDrilldown(
    ...     main_labels=['Oil', 'Gas', 'Coal', 'Renewables', 'Nuclear'],
    ...     main_values=[39, 23, 19, 17, 2],
    ...     drilldown_labels=['Bioenergy', 'Hydro', 'Solar', 'Wind'],
    ...     drilldown_values=[12, 3, 1, 1],
    ...     drilldown_index=3  # Drill down on 'Renewables'
    ... )
    >>> chart.plot(drilldown_type='bar')
    >>> chart.show()
    """
    
    # Default color palettes
    DEFAULT_MAIN_COLORS = [
        '#4a4a4a', '#a67c52', '#c4a35a', '#5b9e4d', '#f0e68c',
        '#6495ed', '#ff6b6b', '#48d1cc', '#dda0dd', '#98d8c8'
    ]
    
    DEFAULT_DRILLDOWN_COLORS = [
        '#2e7d32', '#42a5f5', '#fdd835', '#90caf9', '#e0e0e0',
        '#ff8a65', '#a5d6a7', '#ce93d8', '#80deea', '#ffcc80'
    ]
    
    def __init__(
        self,
        main_labels: List[str],
        main_values: List[float],
        drilldown_labels: List[str],
        drilldown_values: List[float],
        drilldown_index: int = 0,
        main_colors: Optional[List[str]] = None,
        drilldown_colors: Optional[List[str]] = None
    ):
        self.main_labels = main_labels
        self.main_values = main_values
        self.drilldown_labels = drilldown_labels
        self.drilldown_values = drilldown_values
        self.drilldown_index = drilldown_index
        
        # Set colors
        self.main_colors = main_colors or self.DEFAULT_MAIN_COLORS[:len(main_labels)]
        self.drilldown_colors = drilldown_colors or self.DEFAULT_DRILLDOWN_COLORS[:len(drilldown_labels)]
        
        # Figure and axes
        self.fig = None
        self.ax_main = None
        self.ax_drilldown = None
        
        # Store wedges for connection lines
        self._wedges = None
        
    def _calculate_startangle(self) -> float:
        """Calculate the start angle to position the drilldown segment facing right."""
        # Calculate cumulative percentages up to the drilldown segment
        total = sum(self.main_values)
        cumulative = sum(self.main_values[:self.drilldown_index])
        segment_half = self.main_values[self.drilldown_index] / 2
        
        # Position the center of the drilldown segment at 0° (right side)
        center_position = (cumulative + segment_half) / total * 360
        startangle = 360 - center_position
        
        return startangle
    
    def _get_connection_points(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Get the connection points from the drilldown wedge."""
        wedge = self._wedges[self.drilldown_index]
        theta1 = wedge.theta1
        theta2 = wedge.theta2
        
        theta1_rad = np.deg2rad(theta1)
        theta2_rad = np.deg2rad(theta2)
        
        pie_radius = 1.0
        x1 = pie_radius * np.cos(theta1_rad)
        y1 = pie_radius * np.sin(theta1_rad)
        x2 = pie_radius * np.cos(theta2_rad)
        y2 = pie_radius * np.sin(theta2_rad)
        
        # Sort points so top connects to top, bottom to bottom
        if y1 > y2:
            return (x1, y1), (x2, y2)
        else:
            return (x2, y2), (x1, y1)
    
    def _draw_main_pie(
        self,
        explode_drilldown: bool = True,
        explode_amount: float = 0.05,
        show_percentages: bool = True,
        title: Optional[str] = None
    ) -> None:
        """Draw the main pie chart."""
        explode = [0] * len(self.main_values)
        if explode_drilldown:
            explode[self.drilldown_index] = explode_amount
        
        startangle = self._calculate_startangle()
        
        autopct = '%1.0f%%' if show_percentages else ''
        
        self._wedges, texts, autotexts = self.ax_main.pie(
            self.main_values,
            labels=self.main_labels,
            autopct=autopct,
            startangle=startangle,
            colors=self.main_colors,
            explode=explode,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
            pctdistance=0.6,
            labeldistance=1.15
        )
        
        # Style texts
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
            autotext.set_color('white')
        
        if title:
            self.ax_main.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    def _draw_drilldown_bar(
        self,
        bar_width: float = 0.5,
        show_labels: bool = True,
        normalize_drilldown: bool = False
    ) -> Tuple[float, float]:
        """Draw the drilldown as a stacked bar chart.
        
        Parameters
        ----------
        normalize_drilldown : bool
            If True, percentages are normalized to add up to 100%.
            If False, raw values are displayed (e.g., 12%, 3%, 1%, 1%).
        """
        bar_bottom = 0
        bar_x = 0
        
        # Calculate total for normalization
        total = sum(self.drilldown_values)
        
        for value, color, label in zip(self.drilldown_values, self.drilldown_colors, self.drilldown_labels):
            self.ax_drilldown.bar(
                bar_x, value, bar_width,
                bottom=bar_bottom,
                color=color,
                edgecolor='white',
                linewidth=1
            )
            
            if show_labels and value > 0:
                text_y = bar_bottom + value / 2
                # Calculate display percentage
                if normalize_drilldown:
                    display_pct = (value / total * 100) if total > 0 else 0
                    pct_str = f'{display_pct:.1f}%'
                else:
                    pct_str = f'{value}%'
                
                self.ax_drilldown.text(
                    bar_x + bar_width/2 + 0.1, text_y,
                    f'{label}\n{pct_str}',
                    va='center', ha='left',
                    fontsize=9, fontweight='bold'
                )
            
            bar_bottom += value
        
        self.ax_drilldown.set_xlim(-0.5, 1.5)
        self.ax_drilldown.set_ylim(0, sum(self.drilldown_values) * 1.1)
        self.ax_drilldown.axis('off')
        
        return bar_width, sum(self.drilldown_values)
    
    def _draw_drilldown_pie(
        self,
        show_percentages: bool = True,
        show_legend: bool = True,
        normalize_drilldown: bool = True
    ) -> None:
        """Draw the drilldown as a smaller pie chart.
        
        Parameters
        ----------
        normalize_drilldown : bool
            If True, percentages are normalized to add up to 100% (pie chart default).
            If False, raw values are displayed as percentages.
        """
        if show_percentages:
            if normalize_drilldown:
                # Standard pie chart behavior - percentages add to 100%
                autopct = '%1.1f%%'
            else:
                # Custom autopct to show raw values
                total = sum(self.drilldown_values)
                def make_autopct(values):
                    def autopct_func(pct):
                        # Convert back from percentage to original value
                        val = pct * total / 100
                        return f'{val:.1f}%'
                    return autopct_func
                autopct = make_autopct(self.drilldown_values)
        else:
            autopct = ''
        
        wedges, texts, autotexts = self.ax_drilldown.pie(
            self.drilldown_values,
            labels=self.drilldown_labels if not show_legend else None,
            autopct=autopct,
            colors=self.drilldown_colors,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
            pctdistance=0.75
        )
        
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_fontweight('bold')
        
        if show_legend:
            self.ax_drilldown.legend(
                wedges, self.drilldown_labels,
                title="Detail",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1),
                fontsize=9
            )
    
    def _draw_connections(
        self,
        drilldown_type: str,
        bar_width: float = 0.5,
        bar_height: float = 17,
        line_color: str = 'gray',
        line_width: float = 1.5
    ) -> None:
        """Draw connection lines between main pie and drilldown chart."""
        top_point, bottom_point = self._get_connection_points()
        
        if drilldown_type == 'bar':
            # Connect to bar chart
            con1 = ConnectionPatch(
                xyA=top_point, coordsA=self.ax_main.transData,
                xyB=(-bar_width/2, bar_height), coordsB=self.ax_drilldown.transData,
                color=line_color, linewidth=line_width, linestyle='-'
            )
            con2 = ConnectionPatch(
                xyA=bottom_point, coordsA=self.ax_main.transData,
                xyB=(-bar_width/2, 0), coordsB=self.ax_drilldown.transData,
                color=line_color, linewidth=line_width, linestyle='-'
            )
        else:
            # Connect to pie chart
            con1 = ConnectionPatch(
                xyA=top_point, coordsA=self.ax_main.transData,
                xyB=(-1, 0.5), coordsB=self.ax_drilldown.transData,
                color=line_color, linewidth=line_width, linestyle='-'
            )
            con2 = ConnectionPatch(
                xyA=bottom_point, coordsA=self.ax_main.transData,
                xyB=(-1, -0.5), coordsB=self.ax_drilldown.transData,
                color=line_color, linewidth=line_width, linestyle='-'
            )
        
        self.fig.add_artist(con1)
        self.fig.add_artist(con2)
    
    def plot(
        self,
        drilldown_type: str = 'bar',
        figsize: Tuple[int, int] = (12, 7),
        title: Optional[str] = None,
        explode_drilldown: bool = True,
        explode_amount: float = 0.05,
        show_percentages: bool = True,
        show_connections: bool = True,
        connection_color: str = 'gray',
        connection_width: float = 1.5,
        width_ratios: Tuple[float, float] = (2, 1),
        normalize_drilldown: bool = False
    ) -> 'PieDrilldown':
        """
        Create the drill-down pie chart.
        
        Parameters
        ----------
        drilldown_type : str, optional
            Type of drill-down chart: 'bar' or 'pie' (default: 'bar').
        figsize : tuple, optional
            Figure size as (width, height) (default: (12, 7)).
        title : str, optional
            Title for the main pie chart.
        explode_drilldown : bool, optional
            Whether to explode the drilldown segment (default: True).
        explode_amount : float, optional
            Amount to explode the segment (default: 0.05).
        show_percentages : bool, optional
            Whether to show percentage labels (default: True).
        show_connections : bool, optional
            Whether to draw connection lines (default: True).
        connection_color : str, optional
            Color of connection lines (default: 'gray').
        connection_width : float, optional
            Width of connection lines (default: 1.5).
        width_ratios : tuple, optional
            Ratio of widths for main pie vs drilldown (default: (2, 1)).
        normalize_drilldown : bool, optional
            If True, drilldown percentages add up to 100%.
            If False, raw values are displayed (default: False).
        
        Returns
        -------
        PieDrilldown
            Returns self for method chaining.
        """
        if drilldown_type not in ['bar', 'pie']:
            raise ValueError("drilldown_type must be 'bar' or 'pie'")
        
        # Create figure
        self.fig, (self.ax_main, self.ax_drilldown) = plt.subplots(
            1, 2, figsize=figsize,
            gridspec_kw={'width_ratios': list(width_ratios)}
        )
        self.fig.patch.set_facecolor('white')
        
        # Draw main pie
        self._draw_main_pie(
            explode_drilldown=explode_drilldown,
            explode_amount=explode_amount,
            show_percentages=show_percentages,
            title=title
        )
        
        # Draw drilldown chart
        bar_height = sum(self.drilldown_values)
        bar_width = 0.5
        
        if drilldown_type == 'bar':
            bar_width, bar_height = self._draw_drilldown_bar(
                normalize_drilldown=normalize_drilldown
            )
        else:
            self._draw_drilldown_pie(
                show_percentages=show_percentages,
                normalize_drilldown=normalize_drilldown
            )
        
        # Draw connection lines
        if show_connections:
            self._draw_connections(
                drilldown_type=drilldown_type,
                bar_width=bar_width,
                bar_height=bar_height,
                line_color=connection_color,
                line_width=connection_width
            )
        
        plt.tight_layout()
        
        return self
    
    def save(
        self,
        filename: str,
        dpi: int = 150,
        bbox_inches: str = 'tight',
        **kwargs
    ) -> 'PieDrilldown':
        """
        Save the chart to a file.
        
        Parameters
        ----------
        filename : str
            Output filename (e.g., 'chart.png', 'chart.pdf').
        dpi : int, optional
            Resolution in dots per inch (default: 150).
        bbox_inches : str, optional
            Bounding box setting (default: 'tight').
        **kwargs
            Additional arguments passed to plt.savefig().
        
        Returns
        -------
        PieDrilldown
            Returns self for method chaining.
        """
        if self.fig is None:
            raise RuntimeError("No figure to save. Call plot() first.")
        
        self.fig.savefig(
            filename,
            dpi=dpi,
            bbox_inches=bbox_inches,
            facecolor='white',
            **kwargs
        )
        
        return self
    
    def show(self) -> None:
        """Display the chart."""
        if self.fig is None:
            raise RuntimeError("No figure to show. Call plot() first.")
        plt.show()
    
    def get_figure(self) -> plt.Figure:
        """
        Get the matplotlib Figure object.
        
        Returns
        -------
        matplotlib.figure.Figure
            The figure object.
        """
        return self.fig
    
    def get_axes(self) -> Tuple[plt.Axes, plt.Axes]:
        """
        Get the matplotlib Axes objects.
        
        Returns
        -------
        tuple
            Tuple of (main_axes, drilldown_axes).
        """
        return self.ax_main, self.ax_drilldown


def bar_of_pie(
    main_labels: List[str],
    main_values: List[float],
    drilldown_labels: List[str],
    drilldown_values: List[float],
    drilldown_index: int = 0,
    title: Optional[str] = None,
    **kwargs
) -> PieDrilldown:
    """
    Convenience function to create a bar-of-pie chart.
    
    Parameters
    ----------
    main_labels : list
        Labels for the main pie chart segments.
    main_values : list
        Values for the main pie chart segments.
    drilldown_labels : list
        Labels for the bar chart segments.
    drilldown_values : list
        Values for the bar chart segments.
    drilldown_index : int, optional
        Index of the main pie segment to drill down (default: 0).
    title : str, optional
        Title for the chart.
    **kwargs
        Additional arguments passed to PieDrilldown.plot().
    
    Returns
    -------
    PieDrilldown
        The chart object.
    
    Examples
    --------
    >>> from piedrilldown import bar_of_pie
    >>> chart = bar_of_pie(
    ...     main_labels=['A', 'B', 'C'],
    ...     main_values=[50, 30, 20],
    ...     drilldown_labels=['X', 'Y', 'Z'],
    ...     drilldown_values=[10, 15, 5],
    ...     drilldown_index=2,
    ...     title='My Chart'
    ... )
    >>> chart.show()
    """
    chart = PieDrilldown(
        main_labels=main_labels,
        main_values=main_values,
        drilldown_labels=drilldown_labels,
        drilldown_values=drilldown_values,
        drilldown_index=drilldown_index
    )
    chart.plot(drilldown_type='bar', title=title, **kwargs)
    return chart


def pie_of_pie(
    main_labels: List[str],
    main_values: List[float],
    drilldown_labels: List[str],
    drilldown_values: List[float],
    drilldown_index: int = 0,
    title: Optional[str] = None,
    **kwargs
) -> PieDrilldown:
    """
    Convenience function to create a pie-of-pie chart.
    
    Parameters
    ----------
    main_labels : list
        Labels for the main pie chart segments.
    main_values : list
        Values for the main pie chart segments.
    drilldown_labels : list
        Labels for the secondary pie chart segments.
    drilldown_values : list
        Values for the secondary pie chart segments.
    drilldown_index : int, optional
        Index of the main pie segment to drill down (default: 0).
    title : str, optional
        Title for the chart.
    **kwargs
        Additional arguments passed to PieDrilldown.plot().
    
    Returns
    -------
    PieDrilldown
        The chart object.
    
    Examples
    --------
    >>> from piedrilldown import pie_of_pie
    >>> chart = pie_of_pie(
    ...     main_labels=['A', 'B', 'C'],
    ...     main_values=[50, 30, 20],
    ...     drilldown_labels=['X', 'Y', 'Z'],
    ...     drilldown_values=[10, 15, 5],
    ...     drilldown_index=2,
    ...     title='My Chart'
    ... )
    >>> chart.show()
    """
    chart = PieDrilldown(
        main_labels=main_labels,
        main_values=main_values,
        drilldown_labels=drilldown_labels,
        drilldown_values=drilldown_values,
        drilldown_index=drilldown_index
    )
    chart.plot(drilldown_type='pie', title=title, **kwargs)
    return chart
