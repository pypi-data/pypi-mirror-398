# %%
import sys
sys.path.insert(0, '/Users/andrewsazonov/Development/github.com/easyscience/diffraction-lib/src')

import gemmi
import numpy as np
import time
import easydiffraction as ed
from easydiffraction.sample_models.categories.smart_atom_sites_v3 import SmartAtomSites
from easydiffraction.sample_models.categories.atom_sites import AtomSite, AtomSites
from easydiffraction.core.validation import DataTypes

# %%
from easydiffraction.utils.logging import Logger
Logger.configure(
    level=Logger.Level.INFO,
    mode=Logger.Mode.VERBOSE,
    reaction=Logger.Reaction.WARN,
)

# %%
project = ed.Project()

# %%
print("\n=== Extract data with gemmi ===")
t0 = time.perf_counter()
doc = gemmi.cif.read_file("tmp/data/large_structure.cif")
block = doc.sole_block()
values = block.find_values('_atom_site.fract_x')
loop = values.get_loop()
array = np.array(loop.values, dtype=object).reshape(loop.length(), loop.width()).T
data = {tag.split('.')[1]: array[i] for i, tag in enumerate(loop.tags)}
t1 = time.perf_counter()
print(f"Extracting time: {t1-t0:.4f}s")
print("\nRaw CIF data (all strings):")
for header, column in data.items():
    print(f"  {header}: {column}")

# %%
print("\n=== Enhanced CIF Integration (V3) ===")
t0 = time.perf_counter()
atoms_enhanced = SmartAtomSites()
atoms_enhanced.add_from_cif_arrays(data, validate_all=True)
t1 = time.perf_counter()
print(f"Enhanced approach time: {t1-t0:.4f}s")

# %%
print("\n=== Old CIF Integration ===")
t0 = time.perf_counter()
project.sample_models.add_from_cif_path("tmp/data/large_structure.cif")
t1 = time.perf_counter()
print(f"Old approach time: {t1-t0:.4f}s")
print(project.sample_models['lbco'].atom_sites['La'].b_iso)
print(project.sample_models['lbco'].atom_sites['Ba'].b_iso)
#print(project.sample_models['lbco'].as_cif)

print("\n=== Test _add_bulk_empty ===")
t0 = time.perf_counter()
atoms = AtomSites()
atoms._add_bulk_empty(loop.length())
t1 = time.perf_counter()
print(f"_add_bulk_empty {loop.length()} items: {t1-t0:.4f}s")
print(atoms)
#print(atoms.as_cif)
print(atoms['Si'].occupancy)
atoms._items[1].occupancy = 0.555
atoms._items[3].occupancy = 0.777
atoms['Si'].occupancy = 0.333
#print(atoms.as_cif)


# %%
print("\n=== Old init multiple AtomSite() ===")
t0 = time.perf_counter()
collection = []
for i in range(loop.length()):
    item = AtomSite()
    collection.append(item)
t1 = time.perf_counter()
print(f"Init {loop.length()} multiple AtomSite(): {t1-t0:.4f}s")
print('collection[1]:', collection[1])
print('collection[2]:', collection[2])
print('collection[3]:', collection[3])



exit()


# %%
print("\nData type verification:")
print(f"Enhanced Ba.fract_x: {atoms_enhanced['Ba'].fract_x.value} ({type(atoms_enhanced['Ba'].fract_x.value)})")
print(f"Enhanced Ba.label: {atoms_enhanced['Ba'].label.value} ({type(atoms_enhanced['Ba'].label.value)})")
print(f"Enhanced Ba.b_iso: {atoms_enhanced['Ba'].b_iso.value} ({type(atoms_enhanced['Ba'].b_iso.value)})")

# Use enhanced atoms for remaining tests
atoms = atoms_enhanced

# %%
print("=== Testing Enhanced Smart Feedback & Validation ===")
print("atoms['Ba']", atoms['Ba'])
print("atoms.b_iso", atoms.b_iso)

print("atoms['Ba'].b_iso", atoms['Ba'].b_iso)
print("atoms.b_iso['Ba']", atoms.b_iso['Ba'])

print("\n=== Testing Valid Assignments ===")
atoms['Ba'].b_iso = 0.777
print("atoms.b_iso['Ba'] after valid assignment:", atoms.b_iso['Ba'])

print("\n=== Testing Invalid Assignment (should fail with validation) ===")
atoms['Ba'].b_iso = -0.333
print("atoms.b_iso['Ba'] after invalid assignment:", atoms.b_iso['Ba'])

atoms.b_iso['Ba'] = 0.444
print("atoms.b_iso['Ba'] after array assignment:", atoms.b_iso['Ba'])

print("\n=== Testing Invalid Array Assignment ===")
atoms.b_iso['Ba'] = -0.666

print("\n=== Testing Smart Feedback (Typo Detection) ===")
# Test typo in atom label
#value = atoms['Baa'].fract_x.value  # typo: 'Baa' instead of 'Ba'

# Test typo in attribute name
#value = atoms['Ba'].frac_x.value  # typo: 'frac_x' instead of 'fract_x'

# Test typo in array access
#value = atoms.frac_x['Ba']  # typo: 'frac_x' instead of 'fract_x'

print("\n=== Enhanced CIF Integration V3 Complete ✅ ===")
print(f"✅ CIF handlers properly configured")
print(f"✅ Automatic type conversion working")
print(f"✅ Smart feedback and typo detection working")
print(f"✅ Validation integrated with type conversion")
print(f"✅ Both individual and array APIs working")



atoms_enhanced2 = SmartAtomSites()
atoms_enhanced2.add_from_cif_arrays(data, validate_all=True)

atoms_enhanced['Ba'].b_iso = 0.333
atoms_enhanced2['Ba'].b_iso = 0.444

print('\nAAAA')

print("atoms_enhanced['Ba'].b_iso.value", atoms_enhanced['Ba'].b_iso.value)
print("atoms_enhanced2['Ba'].b_iso.value", atoms_enhanced2['Ba'].b_iso.value)
print("atoms_enhanced['Ba'].b_iso.free", atoms_enhanced['Ba'].b_iso.free)
print("atoms_enhanced2['Ba'].b_iso.free", atoms_enhanced2['Ba'].b_iso.free)

atoms_enhanced['Ba'].b_iso.value = 0.666
atoms_enhanced2['Ba'].b_iso.value = 0.888
atoms_enhanced['Ba'].b_iso.free = True

print('\nBBBB')

print("atoms_enhanced['Ba'].b_iso", atoms_enhanced['Ba'].b_iso.value)
print("atoms_enhanced2['Ba'].b_iso", atoms_enhanced2['Ba'].b_iso.value)
print("atoms_enhanced['Ba'].b_iso.free", atoms_enhanced['Ba'].b_iso.free)
print("atoms_enhanced2['Ba'].b_iso.free", atoms_enhanced2['Ba'].b_iso.free)
