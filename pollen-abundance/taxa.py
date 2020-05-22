"""
taxa.py
~~~~~~~

Map land land cover types to species.
"""
from dataclasses import dataclass
import re
from typing import List


@dataclass
class SpeciesGroup:
    """Relate regex identifying a species to its family/ group."""
    regex: str
    desc: str
    note: str = None


POLLEN_LCT_MAPS = {
    'shrubland': [
        SpeciesGroup(r'.*Poaceae|.*Gramineae|.*Cerealia.',
                     'Grasses'),
        SpeciesGroup(r'.*Juniperus',
                     'Juniper'),
        SpeciesGroup(r'.*Cupressaceae',
                     'Cypress family'),
        SpeciesGroup(r'.*Isoetes',
                     'Quillwort',
                     'Prolific in Sanabria Marsh'),
        SpeciesGroup(r'.*Chenopodiaceae',
                     'Goosefoot family',
                     'Prolific in e.g. San Rafael'),
        SpeciesGroup(r'.*Artemisia',
                     'Mugwort genus',
                     'Prolific in e.g. San Rafael'),
        SpeciesGroup(r'.*Cichorioideae',
                     'Flowering plants in lettuce/ dendelion family'),
        SpeciesGroup(r'.*Asteroideae',
                     'Family of shrubby plants'),
        SpeciesGroup(r'.*Cyperaceae',
                     'Sedge family (superficially resemble grasses)',
                     'See e.g. Atxuri'),
        SpeciesGroup(r'.*Calluna vulgaris|.*Erica(ceae|-type|\s)',
                     'Heather family'),
        SpeciesGroup(r'.*Umbelliferae',
                     'Celery, carrot, parsley family'),
        SpeciesGroup(r'.*Apium',
                     'Celery and marthwort genus'),
        SpeciesGroup(r'.*Buxus',
                     'Box plant (shrubby tree)'),
        SpeciesGroup(r'.*Ranunculus',
                     'Genus of flowering plants including buttercup'),
        SpeciesGroup(r'.*Rumex',
                     'Doc/ sorrel genus'),
        SpeciesGroup(r'.*Pteridium|.*Polypodium|.*Filicales',
                     'Bracken/ ferns',
                     'Associated with pine forest?'),
        SpeciesGroup(r'.*Ephedra',
                     'Genus of gymnosperm shrubs'),
        SpeciesGroup(r'.*Sparganium|.*Typha angustifolia',
                     'Flowering plants found in wet regions'),
        SpeciesGroup(r'.*Plantago',
                     'Plantain/ fleawort genus'),
        SpeciesGroup(r'.*Olea',
                     'Olive genus'),
    ],
    'pine_forest': [
        SpeciesGroup(r'\s?Pinus\s?',
                     'Pine genus')
    ],
    'deciduous_forest': [
        SpeciesGroup(r'.*Castanea',
                     'Chestnut genus'),
        SpeciesGroup(r'.*Betula',
                     'Birch genus'),
        SpeciesGroup(r'.*Fagaceae',
                     'Beech family'),
        SpeciesGroup(r'.*Fagus',
                     'Beech genus'),
        SpeciesGroup(r'.*Alnus',
                     'Alder genus'),
        SpeciesGroup(r'.*Corylus',
                     'Hazel genus'),
        SpeciesGroup(r'.*Salix',
                     'Willow genus'),
        SpeciesGroup(r'.*Carpinus',
                     'Hornbeam genus'),
    ],
    'oak_forest': [
        SpeciesGroup(r'\s?Quercus\s?',
                     'Oak genus'),
    ], 
}


def compose_regexs(regexs: List[str]) -> str:
    """Join list of regex patterns.
    
    Resulting pattern will match any one of the input patterns supplied in the
    list.
    """
    return  '|'.join(regexs)


def test_compose_regexs():
    test_patterns = [r'^foo.*', r'.*bar.*']
    test_str1 = 'foo blah blah'  # match
    test_str2 = 'blah bar foo'  # match
    test_str3 = 'blah foo blah'  # no match
    
    regex = compose_regexs(test_patterns)
    assert re.search(regex, test_str1)
    assert re.search(regex, test_str2)
    assert re.search(regex, test_str3) is None


if __name__ == '__main__':
    test_compose_regexs()
