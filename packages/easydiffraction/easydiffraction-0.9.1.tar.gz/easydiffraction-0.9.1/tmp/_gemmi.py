#from easydiffraction.utils.logging import Logger
#Logger.configure(
#    level=Logger.Level.INFO,
#    mode=Logger.Mode.VERBOSE,
#    reaction=Logger.Reaction.WARN,
#)

import time
import gemmi
import numpy as np
import scipp as sc

doc = gemmi.cif.read_file("data/hrpt.cif")
block = doc.sole_block()

t0 = time.perf_counter()
col1 = block.find_loop('_pd_meas.2theta_scan')
t1 = time.perf_counter()
print("find_loop:", t1 - t0, "s")

t0 = time.perf_counter()
col2 = block.find_values('_pd_meas.2theta_scan')
t1 = time.perf_counter()
print("find_values:", t1 - t0, "s")

t0 = time.perf_counter()
l = list(col2)
t1 = time.perf_counter()
print("list(col2):", t1 - t0, "s")

t0 = time.perf_counter()
loop = col2.get_loop()
t1 = time.perf_counter()
print("col2.get_loop():", t1 - t0, "s")


t0 = time.perf_counter()
loop = col2.get_loop()  # or block.find_loop(...)
vals = loop.values      # flat list of strings
t1 = time.perf_counter()
print("vars:", t1 - t0, "s")

t0 = time.perf_counter()
nrow = loop.length()
ncol = loop.width()
t1 = time.perf_counter()
print("size:", t1 - t0, "s")



# Convert all to float and reshape
t0 = time.perf_counter()
arr = np.fromiter((float(v) for v in vals),
                  dtype=np.float64,
                  count=nrow*ncol).reshape(nrow, ncol)
t1 = time.perf_counter()
print("np.fromiter:", t1 - t0, "s")

t0 = time.perf_counter()
np_arr = np.array(loop.values, dtype=np.float64).reshape(loop.length(), loop.width())
t1 = time.perf_counter()
print("np.array.reshape:", t1 - t0, "s")

print('np_arr:', np_arr)

t0 = time.perf_counter()
arr = np.array(loop.values, dtype=np.float64).reshape(loop.length(), loop.width()).T
t1 = time.perf_counter()
print("np.array.reshape.T:", t1 - t0, "s")

print('arr:', arr)

t0 = time.perf_counter()
data = {tag: arr[i] for i, tag in enumerate(loop.tags)}
t1 = time.perf_counter()
print("make data:", t1 - t0, "s")

#print('data:', data)
print('data._pd_meas.2theta_scan:', data['_pd_meas.2theta_scan'])
print('data._pd_meas.intensity_total:', data['_pd_meas.intensity_total'])
print('data._pd_meas.intensity_total_su:', data['_pd_meas.intensity_total_su'])

print(arr.size, arr[0].size)

ncol = arr.shape[0]
nrow = arr.shape[1]

t0 = time.perf_counter()
collection = []
for i in range(nrow):
    item = {}
    for j in range(ncol):
        item[loop.tags[j]] = arr[j, i]
    collection.append(item)
t1 = time.perf_counter()
print("- make collection:", t1 - t0, "s")
print('  collection[1]:', collection[1])

from easydiffraction.experiments.categories.data.bragg_pd import PdCwlData, PdCwlDataPoint


t0 = time.perf_counter()
collection = []
for i in range(nrow):
    item = PdCwlDataPoint()
    collection.append(item)
t1 = time.perf_counter()
print("- init multiple PdCwlDataPoint:", t1 - t0, "s")
print('  collection[1]:', collection[1])




# Insert test code here

# Test smart collection approach
from easydiffraction.experiments.categories.data.smart_pd import SmartPdCwlData

# Test 1: Smart collection with pre-allocated arrays
t0 = time.perf_counter()
smart_collection = SmartPdCwlData()
smart_collection.add_from_arrays(
    two_theta=arr[0],
    intensity_meas=arr[1], 
    intensity_meas_su=arr[2]
)
t1 = time.perf_counter()
print("- make smart collection (bulk):", t1 - t0, "s")
print('  collection[1]:', smart_collection[1])
print('  collection[2].intensity_meas:', smart_collection[2].intensity_meas.value)
print('  collection[3].intensity_meas:', smart_collection.intensity_meas.values[3])

# Test 2: Smart collection with individual item creation (should be slower but still faster than original)
t0 = time.perf_counter()
smart_collection2 = SmartPdCwlData()
for i in range(nrow):
    point = smart_collection2.add_point()
    point.two_theta.value = arr[0, i]
    point.intensity_meas.value = arr[1, i]
    point.intensity_meas_su.value = arr[2, i]
t1 = time.perf_counter()
print("- make smart collection (individual):", t1 - t0, "s")
print('  collection[1]:', smart_collection2[1])

# Test 3: Array-style bulk assignment
t0 = time.perf_counter()
smart_collection3 = SmartPdCwlData(nrow)
smart_collection3.two_theta.values[:] = arr[0]
smart_collection3.intensity_meas.values[:] = arr[1]
smart_collection3.intensity_meas_su.values[:] = arr[2]
t1 = time.perf_counter()
print("- make smart collection (array assignment):", t1 - t0, "s")
print('  collection[1]:', smart_collection3[1])


# Test Smart Atom Sites with LBCO CIF data
print("\n=== Smart Atom Sites Test ===")

import gemmi
from easydiffraction.sample_models.categories.smart_atom_sites import SmartAtomSites
from easydiffraction.sample_models.categories.atom_sites import AtomSites, AtomSite
from easydiffraction.core.validation import DataTypes

# Add enhanced CIF methods to existing SmartAtomSites for testing
def add_from_cif_arrays_method(self, cif_data, validate_all=True):
    """Enhanced method to add atoms from CIF data with automatic type conversion."""
    if not cif_data:
        return
        
    # Build CIF name → internal attribute mapping
    descriptor_map = {}
    for attr_name in dir(type(self)):
        if not attr_name.startswith('_'):
            attr = getattr(type(self), attr_name, None)
            if hasattr(attr, 'cif_handler') and hasattr(attr, 'value_spec'):
                for cif_full_name in attr.cif_handler.names:
                    cif_field = cif_full_name.replace('_atom_site.', '')
                    descriptor_map[cif_field] = {
                        'attr_name': attr_name,
                        'descriptor': attr
                    }
    
    converted_data = {}
    
    for cif_name, string_values in cif_data.items():
        internal_attr = descriptor_map.get(cif_name)
        if internal_attr:
            attr_name = internal_attr['attr_name']
            descriptor = internal_attr['descriptor']
            
            # Convert types based on descriptor.value_spec.type_
            converted_values = []
            for value_str in string_values:
                try:
                    if descriptor.value_spec.type_ == DataTypes.NUMERIC:
                        if value_str in ['.', '?']:
                            converted_value = descriptor.value_spec.default
                        else:
                            clean_val = value_str.split('(')[0] if '(' in value_str else value_str
                            converted_value = float(clean_val)
                    elif descriptor.value_spec.type_ == DataTypes.STRING:
                        converted_value = value_str.strip("'\"")
                    else:
                        converted_value = value_str
                        
                    # Apply validation if available
                    if validate_all and descriptor.value_spec.content_validator:
                        try:
                            converted_value = descriptor.value_spec.content_validator.validate(converted_value)
                        except Exception:
                            converted_value = descriptor.value_spec.default
                    
                    converted_values.append(converted_value)
                except ValueError:
                    converted_values.append(descriptor.value_spec.default)
            
            converted_data[attr_name] = converted_values
            print(f"✓ CIF '{cif_name}' → '{attr_name}' ({descriptor.value_spec.type_}) | First: {converted_values[0]} ({type(converted_values[0])})")
        else:
            print(f"⚠️  No CIF handler for: '{cif_name}' - skipping")
    
    # Use existing add_from_arrays with converted data
    self.add_from_arrays(**converted_data)
    print(f"✅ Successfully imported {len(converted_data)} attributes for {len(list(converted_data.values())[0])} atoms")

# Monkey patch the method for testing
SmartAtomSites.add_from_cif_arrays = add_from_cif_arrays_method

# Load LBCO CIF data
cif_path = "data/lbco.cif"
try:
    doc = gemmi.cif.read(cif_path)
    block = doc.sole_block()
    
    # Find atom site data
    atom_loop = None
    for item in block:
        if hasattr(item, 'loop') and item.loop:
            tags = item.loop.tags
            if any('atom_site' in tag for tag in tags):
                atom_loop = item.loop
                break
                
    if atom_loop:
        nrows = len(atom_loop.values) // len(atom_loop.tags)
        print(f"Found {nrows} atom sites in CIF")
        
        # Extract data arrays using your optimal approach
        atom_data = {}
        for i, tag in enumerate(atom_loop.tags):
            values = [atom_loop.values[j * len(atom_loop.tags) + i] for j in range(nrows)]
            
            # Clean up tag name
            clean_tag = tag.replace('_atom_site.', '')
            atom_data[clean_tag] = values
            
        print(f"Available CIF data: {list(atom_data.keys())}")
        print(f"Raw data types (all strings): {[(k, type(v[0])) for k, v in atom_data.items()]}")
        
        # Test 1: Enhanced Smart collection with automatic type conversion
        print(f"\n=== Enhanced CIF Integration Test ===")
        t0_smart = time.perf_counter()
        smart_atoms = SmartAtomSites()
        smart_atoms.add_from_cif_arrays(atom_data, validate_all=True)
        t1_smart = time.perf_counter()
        smart_time = t1_smart - t0_smart
        print(f"- Enhanced smart atoms creation: {smart_time:.6f}s")
        print(f"  smart_atoms['La']: {smart_atoms['La']}")
        
        # Test that types are now correct
        print(f"\n=== Type Verification ===")
        la_atom = smart_atoms['La']
        print(f"La fract_x: {la_atom.fract_x.value} (type: {type(la_atom.fract_x.value)})")
        print(f"La type_symbol: {la_atom.type_symbol.value} (type: {type(la_atom.type_symbol.value)})")
        print(f"La occupancy: {la_atom.occupancy.value} (type: {type(la_atom.occupancy.value)})")
        
        # Convert numeric data manually for comparison (old way)
        print(f"\n=== Comparison with Manual Conversion ===")
        manual_atom_data = atom_data.copy()
        for key in ['fract_x', 'fract_y', 'fract_z', 'occupancy', 'B_iso_or_equiv']:
            if key in manual_atom_data:
                manual_atom_data[key] = [float(v) for v in manual_atom_data[key]]
        
        # Map CIF names to our internal names (old way)
        if 'B_iso_or_equiv' in manual_atom_data:
            manual_atom_data['b_iso'] = manual_atom_data.pop('B_iso_or_equiv')
        if 'ADP_type' in manual_atom_data:
            manual_atom_data['adp_type'] = manual_atom_data.pop('ADP_type')
        if 'Wyckoff_letter' in manual_atom_data:
            manual_atom_data['wyckoff_letter'] = manual_atom_data.pop('Wyckoff_letter')
            
        # Test 1: Smart collection bulk creation (old manual way)
        t0_manual = time.perf_counter()
        manual_atoms = SmartAtomSites()
        manual_atoms.add_from_arrays(**manual_atom_data)
        t1_manual = time.perf_counter()
        manual_time = t1_manual - t0_manual
        print(f"- Manual conversion atoms creation: {manual_time:.6f}s")
        print(f"  manual_atoms['La']: {manual_atoms['La']}")
        
        # Test 2: Original collection for comparison
        t0_original = time.perf_counter()
        original_atoms = AtomSites()
        for i, label in enumerate(manual_atom_data['label']):
            atom = AtomSite(
                label=label,
                type_symbol=manual_atom_data['type_symbol'][i],
                fract_x=manual_atom_data['fract_x'][i],
                fract_y=manual_atom_data['fract_y'][i],
                fract_z=manual_atom_data['fract_z'][i],
                occupancy=manual_atom_data['occupancy'][i],
                b_iso=manual_atom_data['b_iso'][i],
                adp_type=manual_atom_data['adp_type'][i],
                wyckoff_letter=manual_atom_data['wyckoff_letter'][i]
            )
            original_atoms.add(atom)
        t1_original = time.perf_counter()
        original_time = t1_original - t0_original
        print(f"- original atoms creation: {original_time:.6f}s")
        print(f"  original_atoms['La']: {original_atoms['La']}")
        
        # Performance comparison
        speedup_vs_original = original_time / smart_time if smart_time > 0 else float('inf')
        speedup_vs_manual = manual_time / smart_time if smart_time > 0 else float('inf')
        print(f"\n=== Performance Summary ===")
        print(f"Enhanced smart atoms: {smart_time*1000:.3f}ms")
        print(f"Manual conversion: {manual_time*1000:.3f}ms") 
        print(f"Original atoms: {original_time*1000:.3f}ms")
        print(f"Speedup vs original: {speedup_vs_original:.1f}x")
        print(f"Speedup vs manual: {speedup_vs_manual:.1f}x")
        
        # Test 3: API Compatibility with enhanced atoms
        print(f"\n=== API Tests (Enhanced CIF Integration) ===")
        print(f"Current API - smart_atoms['La'].fract_x.value = {smart_atoms['La'].fract_x.value}")
        
        # Test modification with current API
        smart_atoms['La'].fract_x.value = 0.1234
        print(f"After modification - smart_atoms['La'].fract_x.value = {smart_atoms['La'].fract_x.value}")
        
        # Test 4: New Array API
        print(f"New API - smart_atoms.fract_x['La'] = {smart_atoms.fract_x['La']}")
        
        # Test modification with new API
        smart_atoms.fract_x['La'] = 0.5678
        print(f"After array modification - smart_atoms.fract_x['La'] = {smart_atoms.fract_x['La']}")
        print(f"Verify with individual API - smart_atoms['La'].fract_x.value = {smart_atoms['La'].fract_x.value}")
        
        # Test validation with converted types
        print(f"\n=== Validation Testing (Enhanced CIF) ===")
        
        # Test 1: Negative B-factor (should fail)
        try:
            smart_atoms['Ba'].b_iso = -10.0
            print(f"❌ ERROR: Negative B-factor should have failed")
        except Exception as e:
            print(f"✅ Validation correctly caught negative B-factor: {type(e).__name__}")
        
        # Test 2: Valid assignment should work with proper types
        try:
            smart_atoms['Ba'].b_iso = 1.5  # Valid B-factor
            print(f"✅ Valid B-factor assignment: {smart_atoms['Ba'].b_iso.value} (type: {type(smart_atoms['Ba'].b_iso.value)})")
            
            smart_atoms.occupancy['Ba'] = 0.8  # Valid occupancy
            print(f"✅ Valid occupancy assignment: {smart_atoms.occupancy['Ba']} (type: {type(smart_atoms.occupancy['Ba'])})")
        except Exception as e:
            print(f"❌ Valid assignment failed: {e}")
        
    else:
        print("No atom site loop found in CIF")
        
except Exception as e:
    print(f"Error reading CIF: {e}")
    # Create synthetic test data
    print("\n=== Synthetic Atom Sites Test ===")
    
    # Create test data
    test_labels = ['La', 'Ba', 'Co', 'O1', 'O2']
    test_symbols = ['La', 'Ba', 'Co', 'O', 'O']
    test_x = [0.0, 0.0, 0.5, 0.0, 0.5]
    test_y = [0.0, 0.0, 0.5, 0.5, 0.0]
    test_z = [0.0, 0.0, 0.5, 0.5, 0.5]
    test_occ = [0.5, 0.5, 1.0, 1.0, 1.0]
    test_biso = [0.5, 0.5, 0.5, 0.5, 0.5]
    
    t0 = time.perf_counter()
    smart_atoms = SmartAtomSites()
    smart_atoms.add_from_arrays(
        label=test_labels,
        type_symbol=test_symbols,
        fract_x=test_x,
        fract_y=test_y,
        fract_z=test_z,
        occupancy=test_occ,
        b_iso=test_biso,
        adp_type=['Biso'] * len(test_labels),
        wyckoff_letter=['a', 'a', 'b', 'c', 'c']
    )
    t1 = time.perf_counter()
    print(f"- synthetic smart atoms: {t1 - t0:.6f}s")
    print(f"  smart_atoms['La']: {smart_atoms['La']}")
    
    # Test both APIs
    print(f"Current API: smart_atoms['La'].fract_x.value = {smart_atoms['La'].fract_x.value}")
    print(f"New API: smart_atoms.fract_x['La'] = {smart_atoms.fract_x['La']}")


exit()


t0 = time.perf_counter()
collection = []
for i in range(nrow):
    item = object.__new__(PdCwlDataPoint)
    collection.append(item)
t1 = time.perf_counter()
print("- object.__new__ multiple PdCwlDataPoint:", t1 - t0, "s")
print('  collection[1]:', collection[1])



t0 = time.perf_counter()
collection = []
for i in range(nrow):
    item = PdCwlDataPoint()
    #item._two_theta = arr[0, i]
    #item._intensity_meas = arr[1, i]
    #collection.append(item)
t1 = time.perf_counter()
print("make PdCwlDataPoint collection:", t1 - t0, "s")

exit()

t0 = time.perf_counter()
collection = []
for i in range(nrow):
    item = PdCwlDataPoint()
    item.two_theta.value = arr[0, i]
    item.intensity_meas.value = arr[1, i]
    item.intensity_bkg.value = arr[2, i]
    collection.append(item)
t1 = time.perf_counter()
print("make PdCwlDataPoint.value collection:", t1 - t0, "s")

t0 = time.perf_counter()
collection = []
for i in range(nrow):
    item = PdCwlDataPoint()
    item.two_theta._value = arr[0, i]
    item.intensity_meas._value = arr[1, i]
    collection.append(item)
t1 = time.perf_counter()
print("make PdCwlDataPoint._value collection:", t1 - t0, "s")


t0 = time.perf_counter()
for i in range(nrow):
    item = PdCwlDataPoint()
t1 = time.perf_counter()
print("init multiple PdCwlDataPoint:", t1 - t0, "s")


t0 = time.perf_counter()
for i in range(nrow):
    item = object.__new__(PdCwlDataPoint)
t1 = time.perf_counter()
print("object.__new__ multiple PdCwlDataPoint:", t1 - t0, "s")

from easydiffraction.core.parameters import NumericDescriptor, GenericDescriptorBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.io.cif.handler import CifHandler

t0 = time.perf_counter()
for i in range(nrow):
    for _ in range(4):
        p = NumericDescriptor(
                name='p', description='...',
                value_spec=AttributeSpec(
                    type_=DataTypes.NUMERIC,
                    default=0.0,
                    content_validator=RangeValidator(ge=0),
                ),
                cif_handler=CifHandler(names=['_pd_proc.d_spacing']),
            )
t1 = time.perf_counter()
print("init multiple NumericDescriptor:", t1 - t0, "s")



t0 = time.perf_counter()
collection = []
for i in range(nrow):
    item = PdCwlDataPoint()
    item.two_theta.value = arr[0, i]
    item.intensity_meas.value = arr[1, i]
    item.intensity_bkg.value = arr[2, i]
    collection.append(item)
t1 = time.perf_counter()
print("make PdCwlDataPoint.value collection:", t1 - t0, "s")


t0 = time.perf_counter()
collection = []
for i in range(nrow):
    item = PdCwlDataPoint()
    for param in item.parameters:
        param.value = arr[0, i]
    collection.append(item)
t1 = time.perf_counter()
print("make PdCwlDataPoint.value collection 2:", t1 - t0, "s")


t0 = time.perf_counter()
collection = []
for i in range(nrow):
    item = PdCwlDataPoint()
    for param in item.parameters:
        for name in param._cif_handler.names:
            if name in data.keys():
                param.value = data[name][i]
                break
    collection.append(item)
t1 = time.perf_counter()
print("make PdCwlDataPoint.value collection 3:", t1 - t0, "s")
print(collection[0])
print(collection[1])
print(collection[2])



t0 = time.perf_counter()
collection = PdCwlData()
for i in range(nrow):
    item = PdCwlDataPoint()
    for param in item.parameters:
        for name in param._cif_handler.names:
            if name in data.keys():
                param.value = data[name][i]
                break
    collection.add(item)
t1 = time.perf_counter()
print("make PdCwlDataPoint.value collection X:", t1 - t0, "s")
print(collection)


t0 = time.perf_counter()
collection = PdCwlData()
for i in range(nrow):
    item = PdCwlDataPoint()
    for param in item.parameters:
        for name in param._cif_handler.names:
            if name in data.keys():
                param.value = data[name][i]
                break
    collection._items.append(item)
t1 = time.perf_counter()
print("make PdCwlDataPoint.value collection Y:", t1 - t0, "s")
print(collection)



t0 = time.perf_counter()
collection = PdCwlData()
for i in range(nrow):
    item = PdCwlDataPoint()
    for param in item.parameters:
        for name in param._cif_handler.names:
            if name in data.keys():
                param.value = data[name][i]
                break
    collection._items.append(item)


t1 = time.perf_counter()
print("make PdCwlDataPoint.value collection Y:", t1 - t0, "s")
print(collection)


exit()

t0 = time.perf_counter()
for i in range(nrow):
    for _ in range(4):
        p = GenericDescriptorBase(
                name='p', description='...',
                value_spec=AttributeSpec(
                    type_=DataTypes.NUMERIC,
                    default=0.0,
                    content_validator=RangeValidator(ge=0),
                ),
            )
t1 = time.perf_counter()
print("init multiple GenericDescriptorBase:", t1 - t0, "s")


exit()


t0 = time.perf_counter()
sc_arr = sc.array(dims=loop.tags, values=np_arr)
t1 = time.perf_counter()
print("sc.array:", t1 - t0, "s")

print('sc_arr:', sc_arr)





print(arr[:, 0])

pass