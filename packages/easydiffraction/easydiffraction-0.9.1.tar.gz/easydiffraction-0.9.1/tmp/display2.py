import pandas as pd

df = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30000, 35],
    "Score": [85.5, 90.2, 88.8],
})

df

# Filtering
df = df[['Name', 'Age']]

alignments = ["left", "center", "right"]

styles = [
    {"selector": "th", "props": [("border", "1px solid green"), ("text-align", "center")]},
    {"selector": "td", "props": [("border", "1px solid red")]},
]

styled = df.style.set_table_styles(styles)

for col, align in zip(df.columns, alignments):
    styled = styled.set_properties(subset=[col], **{"text-align": align})

styled


