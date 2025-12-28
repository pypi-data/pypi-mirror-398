import pandas as pd

FLOAT_PRECISION = 4

df = pd.DataFrame({
    ("Name", "left"): ["Alice", "Bob", "Charlie"],
    ("Age", "center"): [25, 3000, 35],
    ("Score", "right"): [6585.5, 90.202, -558.8],
})
df

# Filtering
df = df[['Name', 'Age', 'Score']]

# +
# Table Model
# -

# Force starting index from 1
df.index += 1


# +
def rich_to_hex(color):
    from rich.color import Color
    c = Color.parse(color)
    rgb = c.get_truecolor()
    hex_value = "#{:02x}{:02x}{:02x}".format(*rgb)
    return hex_value

# Styling
rich_dim_color_dark = "grey35"
rich_dim_color_light = "grey85"
pd_dim_color_dark = rich_to_hex(rich_dim_color_dark)
pd_dim_color_light = rich_to_hex(rich_dim_color_light)

# +
from jupyter_dark_detect import is_dark
from IPython import get_ipython

def is_dark_theme() -> bool:
    """Return 'dark' or 'light'. 
    If not running inside Jupyter, return default."""
    default = True
    
    in_jupyter = get_ipython() is not None and \
                 get_ipython().__class__.__name__ == "ZMQInteractiveShell"
    
    if not in_jupyter:
        return default

    return True if is_dark() else False


rich_dim_color = rich_dim_color_dark if is_dark_theme() else rich_dim_color_light
pd_dim_color = pd_dim_color_dark if is_dark_theme() else pd_dim_color_light
print("is_dark", is_dark_theme())
print("rich_dim_color", rich_dim_color)
print("pd_dim_color", pd_dim_color)


# +
# Model View: Rich
from rich.table import Table
from rich.console import Console
from rich.box import Box
# box.SQUARE
# ┌─┬┐ top
# │ ││ head
# ├─┼┤ head_row
# │ ││ mid
# ├─┼┤ foot_row
# ├─┼┤ foot_row
# │ ││ foot
# └─┴┘ bottom
custom_box = Box(
    """\
┌──┐
│  │
├──┤
│  │
├──┤
├──┤
│  │
└──┘
""",
    ascii=False,
)


console = Console()
table = Table(
    title=None,
    box=custom_box,
    show_header=True,
    header_style='bold',
    border_style=rich_dim_color,
)

# Add index column header first
#table.add_column("#", justify="right")
table.add_column(style=rich_dim_color)

# Add other column headers with alignment from 2nd level
for col, align in zip(df.columns.get_level_values(0), df.columns.get_level_values(1)):
    table.add_column(str(col), justify=align)

# Define precision
float_fmt = (f"{{:.{FLOAT_PRECISION}f}}").format

# Add rows (prepend the index value as first column)
for idx, row in df.iterrows():
    formatted_row = [
        float_fmt(val) if isinstance(val, float) else str(val)
        for val in row
    ]
    #table.add_row(str(idx), *map(str, row))
    table.add_row(str(idx), *formatted_row)
    
console.print(table)
# -

# Extract column alignments
alignments = df.columns.get_level_values(1)
alignments

# Remove alignments from df (Keep only the first index level)
df.columns = df.columns.get_level_values(0)
df

# +
styled = (
    df.style
      .set_table_styles(
          [
              # Outer border on the entire table
              {"selector": " ", "props": [
                  ("border", f"1px solid {pd_dim_color}"),
                  ("border-collapse", "collapse")
              ]},

              # Horizontal border under header row
              {"selector": "thead", "props": [
                  ("border-bottom", f"1px solid {pd_dim_color}")
              ]},

              # Remove all cell borders
              {"selector": "th, td", "props": [
                  ("border", "none")
              ]},

              # Style for index column
              {"selector": "th.row0, th.row1, th.row2, th.row_heading", "props": [
                  ("color", pd_dim_color),
                  ("font-weight", "normal")
              ]},
          ]
      )
      .format(precision=FLOAT_PRECISION)
)

styled
# -
# column alignment
for col, align in zip(df.columns, alignments):
    styled = styled.set_properties(subset=[col], **{"text-align": align})
styled






