# source ~/Dropbox/Codes/MDIS/code/.venv/bin/activate

from leanrl import parse_label_linkbase, Roles
from leanrl import parse_reference_linkbase, parse_reference_linkbase_flat

from leanrl import parse_definition_linkbase

# Get documentation
path = "/tmp/us-gaap-2020-01-31/"
#path = "leanrl/tests/data/"

filename = "elts/us-gaap-doc-2020-01-31.xml"

docs = parse_label_linkbase(path + filename)

for i, (concept, doc) in enumerate(docs.items()):
    print(f"{i}: {concept}: {doc}")
    if i > 32:
        break


# Get display labels
labels = parse_label_linkbase(path + 'elts/us-gaap-lab-2020-01-31.xml', role=Roles.LABEL)


for i, (concept, label) in enumerate(labels.items()):
    print(f"{i}: {concept}: {label}")
    if i > 32:
        break


# Get references
#references = parse_label_linkbase(path + 'elts/us-gaap-ref-2020-01-31.xml', role=Roles.REFERENCE)
references = parse_label_linkbase( 'tests/data/us-gaap-ref-2020-01-31.xml', role=Roles.REFERENCE)
len(references)
#0 <- it is wrong



# Get structured Reference objects
refs = parse_reference_linkbase('tests/data/us-gaap-ref-2020-01-31.xml')
flat = parse_reference_linkbase_flat('tests/data/us-gaap-ref-2020-01-31.xml')

for concept, ref_list in refs.items():
    if "ResearchAndDevelopmentExpense" in concept:
        print(f'{concept}:')
        for ref in ref_list:
            print(f'  {ref.format_citation()}')  # "FASB ASC 210-10-S99-1"
            print(f'  Parts: {ref.parts}')        # {'Publisher': 'FASB', ...}
        print(f'  Flat: {flat[concept]}')
        print(flat[concept])
        break
# Or get flat dicts (for pandas/JSON)


# We need to write `parse_reference_linkbase` function to parse the reference linkbase.
for i, (concept, reference) in enumerate(references.items()):
    print(f"{i}: {concept}: {reference}")
    if i > 32:
        break
    

tree = parse_definition_linkbase(path + 'stm/us-gaap-stm-soi-def-2020-01-31.xml')
    