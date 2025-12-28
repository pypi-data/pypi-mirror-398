import pandas as pd

df = pd.DataFrame({
    ("Name", "left"): ["Alice", "Bob", "Charlie"],
    ("Age", "center"): [25, 3000, 35],
    ("Score", "right"): [6585.5, 90.202, -558.8],
})
df

# Filtering
df = df[['Name', 'Score']]
df

# +
# Table Model
# -

#import sys, os
#sys.path.insert(0, "src")
#os.chdir("/Users/andrewsazonov/Development/github.com/EasyScience/diffraction-lib")
import easydiffraction as ed

from easydiffraction.display.tables import TableRenderer


tabler = TableRenderer()

tabler.render(df)



tabler.show_config()
tabler.show_supported_engines()

tabler.show_current_engine()

tabler.engine = 'pandas'

tabler.render(df)

tabler.show_supported_engines()




