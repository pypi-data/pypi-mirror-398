import sys, os
sys.path.insert(0, "src")
os.chdir("/Users/andrewsazonov/Development/github.com/EasyScience/diffraction-lib")
import easydiffraction as ed

project = ed.Project()

print(project.tabler.engine)
project.tabler.engine = 'pandas'
project.tabler.engine = 'rich'
project.tabler.engine = 'rich2'
project.tabler.engine = 'pandas'

project.tabler.show_supported_engines()

project.tabler.engine = 'rich'
project.tabler.engine = 'pandas'
project.tabler.engine = 'rich2'
project.tabler.engine = 'rich'

project.tabler.show_supported_engines()



# +
import pyarrow as pa

# Creating two tables to join
left_table = pa.table({'key': [1, 2, 3], 'value_left': ['A', 'B', 'C']})
right_table = pa.table({'key': [1, 2, 3], 'value_right': ['X', 'Y', 'Z']})

# Performing an inner join on the 'key' column
joined_table = left_table.join(right_table, keys='key')
print(joined_table)
# -



# +
import polars as pl
import pandas as pd

df = pl.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [32, 28, 36],
    "City": ["London", "Paris", "New York"],
}).to_pandas()

alignments = ["left", "center", "right"]

styles = [
    {"selector": "th", "props": [("border", "1px solid black"), ("text-align", "center")]},
    {"selector": "td", "props": [("border", "1px solid black")]},
]

styled = df.style.set_table_styles(styles).apply(
    lambda row: ["background-color: #f9f9f9" if row.name % 2 else "" for _ in row], axis=1
)

for col, align in zip(df.columns, alignments):
    styled = styled.set_properties(subset=[col], **{"text-align": align})

styled  # ✅ works in Jupyter, plain Pandas Styler

# +
from itables import options

options.allow_html = True

# +
import polars as pl
import pandas as pd

df = pl.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [32, 28, 36],
    "City": ["London", "Paris", "New York"],
}).to_pandas()

alignments = ["left", "center", "right"]

styles = [
    {"selector": "th", "props": [("border", "1px solid black"), ("text-align", "center")]},
    {"selector": "td", "props": [("border", "1px solid black")]},
]

styled = df.style.set_table_styles(styles).apply(
    lambda row: ["background-color: #f9f9f9" if row.name % 2 else "" for _ in row], axis=1
)

for col, align in zip(df.columns, alignments):
    styled = styled.set_properties(subset=[col], **{"text-align": align})

styled  # ✅ works in Jupyter, plain Pandas Styler

# +
import pyarrow as pa
import pandas as pd

schema = pa.schema([
    pa.field("Name", pa.string(), metadata={"align": "left"}),
    pa.field("Age", pa.int32(), metadata={"align": "center"}),
    pa.field("City", pa.string(), metadata={"align": "right"}),
])

table = pa.Table.from_pydict(
    {"Name": ["Alice", "Bob", "Charlie"], "Age": [32, 28, 36], "City": ["London", "Paris", "New York"]},
    schema=schema
)

df = table.to_pandas()
alignments = [field.metadata.get(b"align", b"left").decode() for field in schema]

styled = df.style.apply(
    lambda row: ["background-color: #f2f2f2" if row.name % 2 else "" for _ in row], axis=1
)

for col, align in zip(df.columns, alignments):
    styled = styled.set_properties(subset=[col], **{"text-align": align})

styled  # ✅ works in Jupyter

# +
import pandas as pd
import ipydatagrid as gd
from IPython.display import display

df = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [32, 28, 36],
    "City": ["London", "Paris", "New York"],
})

grid = gd.DataGrid(
    df,
    style={
        "header": {"font_weight": "bold", "text_align": "center", "background_color": "#ddd"},
        "row_even": {"background_color": "#f9f9f9"},
        "row_odd": {"background_color": "#ffffff"},
        "cell": {"border": "1px solid black"},
        "column_Name": {"text_align": "left"},
        "column_Age": {"text_align": "center"},
        "column_City": {"text_align": "right"},
    },
    auto_fit_columns=True,
)

display(grid)   # ✅ force Jupyter to show the widget instead of repr

# +
import pandas as pd
from itables import init_notebook_mode, show

init_notebook_mode(all_interactive=True)  # global setup

df = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [32, 28, 36],
    "City": ["London", "Paris", "New York"],
})

alignments = ["left", "center", "right"]

styled = df.style.apply(
    lambda row: ["background-color: red" if row.name % 2 else "" for _ in row], axis=1
)

for col, align in zip(df.columns, alignments):
    styled = styled.set_properties(subset=[col], **{"text-align": align})

# ✅ must pass allow_html=True here
show(styled, allow_html=True)

# +
from ipydatagrid import DataGrid
from IPython.display import display
import pandas as pd

df = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "Score": [85.5, 90.2, 88.8],
})

grid = DataGrid(df)
display(grid)  # <-- Should render interactive table if widgets are enabled

# +
import pandas as pd

# Example dataframe
df = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "Score": [85.5, 90.2, 88.8],
    "_align": ["left", "center", "right"]  # alignment metadata
})

# Exclude _align when displaying
display(df.drop(columns="_align"))

# Define a styler
styled = (
    df.style
    .set_properties(**{
        "border": "1px solid grey",
        "border-collapse": "collapse",
    })
    .set_table_styles(
        [
            {"selector": "th", "props": [("text-align", "center"), ("background-color", "#f2f2f2")]},
            {"selector": "td", "props": [("padding", "4px 8px")]},
        ],
        overwrite=False,
    )
    .apply(lambda s: ["background-color: #f9f9f9" if i % 2 == 0 else "" for i in range(len(s))], axis=0)
)

# Apply column-specific alignment
for col, a in align.items():
    styled = styled.set_properties(subset=[col], **{"text-align": a})

display(styled)


# +
import pandas as pd

# Build DataFrame with MultiIndex columns
df = pd.DataFrame({
    ("Name", "left"): ["Alice", "Bob", "Charlie"],
    ("Age", "center"): [25, 3000, 35],
    ("Score", "right"): [85.5, 90.2, 88.8],
})

filtered_df = df[['Name', 'Age']]
print(filtered_df)
# -


























# +
import pandas as pd

# Build DataFrame with MultiIndex columns
df = pd.DataFrame({
    ("Name", "left"): ["Alice", "Bob", "Charlie"],
    ("Age", "center"): [25, 30, 35],
    ("Score", "right"): [85.5, 90.2, 88.8],
})

filtered = 


df.columns = pd.MultiIndex.from_tuples(df.columns, names=["#", "align"])

# Extract alignments
alignments = dict(zip(df.columns.get_level_values("#"),
                      df.columns.get_level_values("align")))

# Drop alignment level for display
df_display = df.copy()
#df_display.columns = df_display.columns.get_level_values("#")

# Styler with alignment + number formatting
def apply_alignment(styler, aligns):
    for col, align in aligns.items():
        styler = styler.set_properties(
            subset=[col],
            **{ "text-align": align }
        )
    return styler

styled = apply_alignment(df_display.style, alignments).format(
    precision=2,  # max 2 decimals
    na_rep="",    # empty for NaN
)


html = styled.to_html(
            escape=False,
            index=False,
            #formatters=formatters,
            #border=0,
            #header=not skip_headers,
        )

display(HTML(html))

# +
import pandas as pd

# Create DataFrame with MultiIndex columns (name, alignment)
df = pd.DataFrame(
    {
        ("#", "left"):   [1, 2, 3],
        ("Name", "left"): ["Alice", "Bob", "Charlie"],
        ("Age", "center"): [25, 30, 35],
        ("Score", "right"): [85.5, 90.2, 88.8],
    }
)

# Extract alignments in a simple way
alignments = {col: align for col, align in df.columns}

# Drop MultiIndex for display (keep only column names)
df.columns = [col for col, _ in df.columns]

# Apply alignment via Styler
styler = df.style.set_properties(**{
    "text-align": "center"  # default
})
for col, align in alignments.items():
    styler = styler.set_properties(subset=[col], **{"text-align": align})

# Hide the pandas default index
styler = styler.hide(axis="index")

# Optional: set precision for numeric formatting
styler = styler.format(precision=1)

styler

# +
import pandas as pd

df = pd.DataFrame({
    "_align": ["center", "left", "left"],  # alignment metadata
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30000, 35],
    "Score": [85.5, 90.2, 88.8],
})

# Exclude _align when displaying
#display(df.drop(columns="_align"))

# Use _align column when building Styler
align = dict(zip(df.columns[:-1], df["_align"]))
print(align.values())
#styled = df.drop(columns="_align").style.set_properties(
#    **{f"text-align": v for v in align.values()}
#)

# Apply alignment via Styler
styled = df.style.set_properties(**{
    "text-align": "center"  # default
})
for col, align in alignments.items():
    styled = styler.set_properties(subset=[col], **{"text-align": align})

html = styled.to_html(
            escape=False,
            index=False,
            #formatters=formatters,
            #border=0,
            #header=not skip_headers,
        )
display(HTML(html))


print(df.index)
# -



# +
df = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "Score": [85.5, 90.2, 88.8],
})

df.attrs["align"] = {"Name": "left", "Age": "center", "Score": "right"}

# Retrieve later
align = df.attrs.get("align", {})
styled = df.style.set_properties(
    **{col: f"text-align: {a}" for col, a in align.items()}
)
html = styled.to_html(
            escape=False,
            index=False,
            #formatters=formatters,
            #border=0,
            #header=not skip_headers,
        )
display(HTML(html))
# -


