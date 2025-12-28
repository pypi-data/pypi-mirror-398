# PieDrilldown

[![PyPI version](https://badge.fury.io/py/piedrilldown.svg)](https://badge.fury.io/py/piedrilldown)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python package for creating professional **"Bar of Pie"** and **"Pie of Pie"** charts with drill-down visualizations using Matplotlib.

## Features

- 📊 **Bar of Pie**: Expand a pie segment into a stacked bar chart
- 🥧 **Pie of Pie**: Expand a pie segment into a secondary pie chart
- 🔗 **Automatic connection lines** between main chart and drill-down
- 🎨 **Customizable colors** for both charts
- 📐 **Smart positioning**: Drill-down segment automatically faces the detail chart
- 📏 **Flexible percentages**: Show raw values or normalize to 100%

## Installation

```bash
pip install piedrilldown
```

## Quick Start

### Bar of Pie Chart

```python
from piedrilldown import PieDrilldown

chart = PieDrilldown(
    main_labels=['Oil', 'Gas', 'Coal', 'Renewables', 'Nuclear'],
    main_values=[39, 23, 19, 17, 2],
    drilldown_labels=['Bioenergy', 'Hydro', 'Solar', 'Wind'],
    drilldown_values=[12, 3, 1, 1],
    drilldown_index=3  # Drill down on 'Renewables'
)

chart.plot(drilldown_type='bar', title='Energy Consumption 2019')
chart.save('energy_chart.png')
chart.show()
```

### Pie of Pie Chart

```python
from piedrilldown import PieDrilldown

chart = PieDrilldown(
    main_labels=['Category A', 'Category B', 'Category C', 'Others'],
    main_values=[45, 25, 20, 10],
    drilldown_labels=['Sub 1', 'Sub 2', 'Sub 3'],
    drilldown_values=[5, 3, 2],
    drilldown_index=3
)

chart.plot(drilldown_type='pie', title='Sales Distribution')
chart.show()
```

### Using Convenience Functions

```python
from piedrilldown import bar_of_pie, pie_of_pie

# Quick bar-of-pie
chart = bar_of_pie(
    main_labels=['A', 'B', 'C'],
    main_values=[50, 30, 20],
    drilldown_labels=['X', 'Y', 'Z'],
    drilldown_values=[10, 15, 5],
    drilldown_index=2,
    title='My Chart'
)
chart.show()
```

## Customization Options

### Custom Colors

```python
chart = PieDrilldown(
    main_labels=['Oil', 'Gas', 'Renewables'],
    main_values=[50, 30, 20],
    drilldown_labels=['Solar', 'Wind', 'Hydro'],
    drilldown_values=[8, 7, 5],
    drilldown_index=2,
    main_colors=['#333333', '#666666', '#4CAF50'],
    drilldown_colors=['#FFC107', '#03A9F4', '#2196F3']
)
```

### Plot Options

```python
chart.plot(
    drilldown_type='bar',           # 'bar' or 'pie'
    figsize=(14, 8),                # Figure size
    title='My Chart',               # Chart title
    explode_drilldown=True,         # Explode the drilldown segment
    explode_amount=0.1,             # How much to explode
    show_percentages=True,          # Show percentage labels
    show_connections=True,          # Draw connection lines
    connection_color='gray',        # Connection line color
    connection_width=2,             # Connection line width
    width_ratios=(2, 1),            # Ratio of main pie to drilldown
    normalize_drilldown=False       # False: raw values, True: normalize to 100%
)
```

### Percentage Display

```python
# Raw values (default): 12%, 3%, 1%, 1%
chart.plot(normalize_drilldown=False)

# Normalized to 100%: 70.6%, 17.6%, 5.9%, 5.9%
chart.plot(normalize_drilldown=True)
```

## API Reference

### PieDrilldown Class

```python
PieDrilldown(
    main_labels,           # List of labels for main pie
    main_values,           # List of values for main pie
    drilldown_labels,      # List of labels for drilldown
    drilldown_values,      # List of values for drilldown
    drilldown_index=0,     # Index of segment to drill down
    main_colors=None,      # Optional custom colors for main pie
    drilldown_colors=None  # Optional custom colors for drilldown
)
```

### Methods

| Method | Description |
|--------|-------------|
| `plot(**options)` | Create the chart with specified options |
| `save(filename, dpi=150)` | Save the chart to a file |
| `show()` | Display the chart |
| `get_figure()` | Get the matplotlib Figure object |
| `get_axes()` | Get the matplotlib Axes objects |

### Convenience Functions

- `bar_of_pie(...)` - Quick bar-of-pie chart creation
- `pie_of_pie(...)` - Quick pie-of-pie chart creation

## Requirements

- Python 3.7+
- matplotlib >= 3.0.0
- numpy >= 1.15.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0 (2024-12-24)
- Initial release
- Bar of Pie and Pie of Pie chart types
- Automatic segment positioning
- Connection lines between charts
- Customizable colors and styles
- `normalize_drilldown` option for percentage display
