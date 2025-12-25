from rara_tools.parsers.tools.validators import filter_names 
import pytest

are_equal = lambda x, y: not bool(set(x).difference(set(y)))

names_to_validate = [
    "ליסט, פראנץ",
    "Liszt, Franz",
    "Lißt, Franz",
    "ליסט, פרנץ",
    "Liszt, Ferencz",
    "Лист, Франц",
    "Listz",
    "Lißzt, Franz",
    "Lists, Francis",
    "List, Ferenc",
    "List, Frants리스",
    "List, Ferents",
    "李斯特，弗朗西斯庫斯",
    "ᓕᔅᑦ, ᕗᕌᓐᓯᔅᑲᔅ",
    "리스트, 프란치스코"
]

valid_names_1 = [
    "Liszt, Franz",
    "Lißt, Franz",
    "Liszt, Ferencz",
    "Лист, Франц",
    "Listz",
    "Lißzt, Franz",
    "Lists, Francis",
    "List, Ferenc",
    "List, Frants리스",
    "List, Ferents"
]

valid_names_2 = [
    "Liszt, Franz",
    "Lißt, Franz",
    "Liszt, Ferencz",
    "Listz",
    "Lißzt, Franz",
    "Lists, Francis",
    "List, Ferenc",
    "List, Frants리스",
    "List, Ferents"
]

def test_filtering_latin_cyrillic():
    filtered_names = filter_names(names_to_validate, allow_cyrillic=True)
    assert are_equal(filtered_names, valid_names_1)

def test_filtering_latin():
    filtered_names = filter_names(names_to_validate, allow_cyrillic=False)
    assert are_equal(filtered_names, valid_names_2)
