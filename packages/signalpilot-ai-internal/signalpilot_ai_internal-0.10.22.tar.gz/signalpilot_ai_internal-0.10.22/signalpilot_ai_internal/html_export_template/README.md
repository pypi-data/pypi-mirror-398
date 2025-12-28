# HTML Export Template with Code Toggle

This is a custom Jupyter NBConvert HTML template that adds a toggle to hide/show each code cell.

## Usage

The handler uses this template automatically. You can modify the notebook cells to control their visibility:

- By default, all code cells are hidden with a "Show Code" button
- To show a code cell by default, tag the cell with 'code_shown' in its metadata

## Template Files

- `index.html.j2` - The main template that extends lab/index.html.j2
- `conf.json` - Configuration for the template
- `README.md` - This file

## Features

- Clean presentation with toggleable code cells
- Uses JQuery for smooth transitions
- Removes input/output prompts for cleaner appearance
- Responsive and modern styling
