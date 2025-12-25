import os
import json

from rara_tools.constants import YYMMDD_FORMAT
from rara_tools.normalizers import BibRecordNormalizer, AuthoritiesRecordNormalizer
from tests.test_utils import (
    get_linker_res_example,
    get_formatted_sierra_response,
    check_record_tags_sorted,
    check_no_dupe_tag_values,
    check_record_tags_have_values,
)
from rara_tools.normalizers.viaf import VIAFRecord

from rara_tools.constants.linker import EntityType

from datetime import datetime

from pymarc import Record, JSONReader


TEST_LEVEL = os.getenv("TEST_LEVEL", "unit")

EMPTY_SIERRA_RECORDS = [
    {"sierraID": "1", "leader": "00000nz  a2200000n  4500", "fields": []},
]

REQUIRED_FIELDS = ["667", "925"]  # always included after normalization
MOCK_LINKER_ONE_FOUND = get_linker_res_example("oneFound.json")
MOCK_LINKER_MULTIPLE_FOUND = get_linker_res_example("multipleFound.json")
MOCK_LINKER_NOT_FOUND = get_linker_res_example("notFound.json")

def get_100_field(author: str = "Autor", title: str = "Pealkiri") -> dict:
        return {
            "100": {
                "ind1": "1",
                "ind2": " ",
                "subfields": [{"a": author, "t": title}],
            }
        }


def test_normalizers_OK():
    """Test field editing logic & internals"""

    linking_results = [MOCK_LINKER_ONE_FOUND, MOCK_LINKER_MULTIPLE_FOUND]

    test_sierra_data = get_formatted_sierra_response("authorities.json")

    normalizer = AuthoritiesRecordNormalizer(
        linking_results=linking_results,
        sierra_data=test_sierra_data,
    )

    assert len(normalizer.records_extra_data) == len(normalizer.data)

    normalizer = BibRecordNormalizer(
        linking_results=linking_results,
        sierra_data=test_sierra_data,
    )
    assert len(normalizer.records_extra_data) == len(normalizer.data)

    data = [
        {
            "sierraID": "1",
            "leader": "00000nz  a2200000n  4500",
            "fields": [
                {"667": {"ind1": " ", "ind2": " ", "subfields": [{"a": "Val"}]}},
            ],
        },
    ]

    # default behavior - added if not in record &
    normalizer = AuthoritiesRecordNormalizer(
        sierra_data=data,
        ALLOW_EDIT_FIELDS=[],
        REPEATABLE_FIELDS=[],
    )
    for r in normalizer:
        assert r.get_fields("667")[0].get_subfields("a")[0] == "Val"

    # not edited if exists
    normalizer = AuthoritiesRecordNormalizer(
        sierra_data=data, ALLOW_EDIT_FIELDS=[], REPEATABLE_FIELDS=[]
    )
    for r in normalizer:
        assert r.get_fields("667")[0].get_subfields("a")[0] == "Val"

    # allow repeatable, new field will be added
    normalizer = AuthoritiesRecordNormalizer(
        sierra_data=data, ALLOW_EDIT_FIELDS=[], REPEATABLE_FIELDS=["667"]
    )
    for r in normalizer:
        fields_667 = r.get_fields("667")
        assert len(fields_667) == 2
        assert fields_667[0].get_subfields("a")[0] == "Val"
        assert fields_667[1].get_subfields("a")[0] == "Muudetud AI poolt"

    # allow editing, field will be edited
    normalizer = AuthoritiesRecordNormalizer(
        sierra_data=data, ALLOW_EDIT_FIELDS=["667"], REPEATABLE_FIELDS=[]
    )
    for r in normalizer:
        fields_667 = r.get_fields("667")
        assert len(fields_667) == 1
        assert fields_667[0].get_subfields("a")[0] == "Muudetud AI poolt"


def _validate_existing_record_notes(record: Record):
    """Validate notes in existing record - 667 & 925 fields"""

    fields_667 = record.get_fields("667")
    assert any("Muudetud AI poolt" in f.get_subfields("a") for f in fields_667)

    fields_925 = record.get_fields("925")
    assert len(fields_925) == 1
    assert len(fields_925[0].get_subfields("p")) == 1
    assert len(fields_925[0].get_subfields("t")) == 0


def _validate_new_record_notes(record: Record):
    """Validate notes in new record - 667 & 925 fields"""

    fields_667 = record.get_fields("667")

    assert any("Loodud AI poolt" in f.get_subfields("a") for f in fields_667)

    fields_925 = record.get_fields("925")
    assert len(fields_925) == 1
    assert len(fields_925[0].get_subfields("p")) == 0
    assert len(fields_925[0].get_subfields("t")) == 1


def validate_bibrecord_normalized(record: Record, has_viaf_data=False):
    """Validate specific fields in normalized bibrecord"""

    field_008 = record.get_fields("008")[0].data
    assert len(field_008) == 40
    # pos 00-05 is current date in YYMMDD format
    timestamp = field_008[0:6]
    # check timestamp in correct format
    try:
        datetime.strptime(timestamp, YYMMDD_FORMAT)
    except ValueError:
        raise AssertionError(
            f"008 field timestamp {timestamp} is not in format {YYMMDD_FORMAT}"
        )

    expected_suffix_008 = "|||aznnnaabn          || |||" + 6 * " "
    suffix = field_008[6:]
    assert suffix == expected_suffix_008

    _validate_existing_record_notes(record)


def validate_authorities_record_normalized(record: Record, has_viaf_data=False):
    """Validate specific fields in normalized authority record"""

    field_008 = record.get_fields("008")[0].data
    assert len(field_008) == 40
    # pos 00-05 is current date in YYMMDD format
    timestamp = field_008[0:6]
    # check timestamp in correct format
    try:
        datetime.strptime(timestamp, YYMMDD_FORMAT)
    except ValueError:
        raise AssertionError(
            f"008 field timestamp {timestamp} is not in format {YYMMDD_FORMAT}"
        )

    expected_suffix_008 = "|n|adnnnaabn          || |a|" + 6 * " "
    suffix = field_008[6:]
    assert suffix == expected_suffix_008

    _validate_existing_record_notes(record)

    # check that a, b & c subfields have values (can have default or unique)
    field_040_subfields = record.get_fields("040")[0]
    assert len(field_040_subfields.get_subfields("a")) > 0
    assert len(field_040_subfields.get_subfields("b")) > 0
    assert len(field_040_subfields.get_subfields("c")) > 0

    # check that 008 field has a value of length 40
    field_008 = record.get_fields("008")[0].data
    assert len(field_008) == 40

    if has_viaf_data:
        field_043 = record.get_fields("043")[0].get_subfields("c")[
            0
        ]  # check that 043 has subfield c with value "ee"
        assert field_043 == "ee"

        field_024 = record.get_fields("024")
        for f in field_024:
            assert len(f.get_subfields("0")) > 0  # VIAF url

        field_046 = record.get_fields("046")[0]
        assert len(field_046.get_subfields("f")) > 0  # birth date
        assert len(field_046.get_subfields("g")) > 0  # death date


def test_missing_fields_created_bibrecord_normalization():
    linking_results = [MOCK_LINKER_ONE_FOUND]

    normalizer_entities_only = BibRecordNormalizer(
        linking_results=linking_results,
    )

    normalizer_sierra_data_only = BibRecordNormalizer(
        sierra_data=EMPTY_SIERRA_RECORDS,
    )

    for record in normalizer_entities_only:
        check_record_tags_have_values(
            record,
            [
                "008",  # Sierra related, always with bibs
                "100",  # VIAf enriched
            ]
            + REQUIRED_FIELDS,
        )
        validate_bibrecord_normalized(record, has_viaf_data=True)

    for record in normalizer_sierra_data_only:
        check_record_tags_have_values(
            record,
            [
                "008"  # Sierra related, always with bibs
            ]
            + REQUIRED_FIELDS,
        )
        validate_bibrecord_normalized(record)


def test_missing_fields_created_authorities_normalization():
    linking_results = [MOCK_LINKER_ONE_FOUND]

    normalizer_entities_only = AuthoritiesRecordNormalizer(
        linking_results=linking_results,  # find one match
    )

    normalizer_sierra_data_only = AuthoritiesRecordNormalizer(
        sierra_data=EMPTY_SIERRA_RECORDS,
    )

    for r in normalizer_entities_only:
        check_record_tags_have_values(
            r,
            [
                "008",
                "040",  # SIERRA related
                "024",
                "043",
                "046",  # VIAF enriched
            ]
            + REQUIRED_FIELDS,
        )

        validate_authorities_record_normalized(r, True)

    for r in normalizer_sierra_data_only:
        check_record_tags_have_values(r, ["040"] + REQUIRED_FIELDS)
        validate_authorities_record_normalized(r)


def test_normalized_fields_sorted():
    unsorted_bibdata = [
        {
            "sierraID": "1",
            "leader": "00000nz  a2200000n  4500",
            "fields": [
                {
                    "035": {
                        "ind1": " ",
                        "ind2": " ",
                        "subfields": [{"a": "(ErESTER)<1>"}],
                    }
                },
                {"008": "220805|||aznnnaabn          || |||      nz n  "},
                {"046": {"ind1": " ", "ind2": " ", "subfields": [{"k": "1912"}]}},
            ],
        }
    ]

    normalizers = (BibRecordNormalizer, AuthoritiesRecordNormalizer)

    for normalizer in normalizers:
        normalizer = normalizer(linking_results=[], sierra_data=unsorted_bibdata)

        for r in normalizer:
            check_no_dupe_tag_values(r)
            check_record_tags_sorted(r)


def test_authority_normrecord_found_in_es_and_normalized():
    """KATA elastic normkirjete seast leitakse 1 vaste & normaliseerija täiendab leitud normkirjet VIAF infoga.
    - valideeri normaliseerimise mapping, mis autori tabelis. Täiendatud väljad ja VIAFist info"""
    # Presume, author name identified and sent to linker
    linker_res = get_linker_res_example("oneFound.json")  # single result
    linking_results = [linker_res]

    # 1 result found
    normalizer = AuthoritiesRecordNormalizer(linking_results=linking_results)

    data = normalizer.data

    assert len(data) == 1
    record = next(iter(JSONReader(json.dumps(normalizer.data, ensure_ascii=False))))
    check_record_tags_have_values(record, ["040"] + REQUIRED_FIELDS)
    validate_authorities_record_normalized(record, has_viaf_data=True)


def _run_normalizer(linked_data):
    normalizer = AuthoritiesRecordNormalizer(linking_results=linked_data)
    return normalizer.data


def test_normalizer_handles_bad_inputs():
    linker_res = get_linker_res_example("oneFound.json")

    # pop the leader field to simulate record without leader
    linker_res["linked_info"][0]["json"].pop("leader", None)
    _run_normalizer([linker_res])

    # make fields empty to simulate a record with no fields
    linker_res["linked_info"][0]["json"]["fields"] = []
    _run_normalizer([linker_res])

    # pop the fields to simulate a record with no fields
    linker_res["linked_info"][0]["json"].pop("fields", None)
    _run_normalizer([linker_res])

    inputs = ["", None, [], {}, 123]

    _run_normalizer(inputs)


def test_matching_sierra_record_viaf_id_found():
    """normkirjelt leitakse VIAF ID, vajadusel normi asukoht, kus see ID sisaldub."""
    pass


def test_matching_sierra_record_viaf_id_not_found():
    """kirjelt VIAF IDd ei leitud, soorita otsing VIAFi pihta, et leida _vastutav isik_?. Loo uus vastavalt otsingu tulemusele."""
    pass


def test_authorities_normalizer_checks():
    """
    - kontrolli kas tuvastatud nimi on SIERRAst leitud vaste 1XX, 4XX väljadel. Kui pole, siis lisa 4XX väljale.
    - kontrolli, kas VIAF andmete nimekujud on normkandes olemas. Kui pole, lisa need 4XX väljale.
    - Kontrolli, kas VIAF kandes on sünni ja surma daatumid ja kas need klapivad normkandes olevaga. Kui pole, siis liiguta normkandest kogu 1XX väli 4XX väljale. Seejärel loo uute daatumitega 1XX väli.
    - Kontrolli, et väljal 046 olevad daatumid klapiksid just 1xx väljale lisatuga. Kui andmeid muudeti, siis märgi, et baasis on normkanne muutunud
    """
    pass


def test_add_birth_and_death_dates():
    """Test adding birth & death dates to 046 field from VIAF record. Expected Date format YYMMDD"""

    # Case one: viaf record has both birth & death date
    normalizer = AuthoritiesRecordNormalizer()
    record = Record()

    viaf_record = normalizer._get_viaf_record(
        record,
        False,
        # entity="Paul Keres"
        viaf_id=7432247,
    )
    for value in [viaf_record, viaf_record.birth_date, viaf_record.death_date]:
        assert value is not None

    normalizer._add_birth_and_death_dates(record, viaf_record)

    field_046 = str(record.get_fields("046")[0])
    assert field_046 == "=046  \\\\$f19160107$g19750605"

    # Case two: viaf record has birth date, but no death date (author still alive)
    viaf_record = normalizer._get_viaf_record(
        record,
        False,
        #   entity="Andrus Kivirähk"
        viaf_id=38111668,
    )

    assert viaf_record is not None
    assert viaf_record.birth_date is not None
    assert viaf_record.death_date == 0

    record = Record()
    normalizer._add_birth_and_death_dates(record, viaf_record)

    field_046 = str(record.get_fields("046")[0])
    # empty indicators represented with \
    assert field_046 == "=046  \\\\$f19700817"

    # Case 3 - viaf record has no birth or death date
    viaf_record = normalizer._get_viaf_record(
        False,
        record,
        viaf_id=1165154688467248380004,
        # entity="Eesti Interlingvistika Selts"
    )
    record = Record()
    normalizer._add_birth_and_death_dates(record, viaf_record)
    # should not add 046 field
    fields_046 = record.get_fields("046")
    assert len(fields_046) == 0


def test_add_nationality():
    """Test adding nationality from VIAF record to 043 field"""

    # Case 1: nationality is not estonian - do not add 043 field

    normalizer = AuthoritiesRecordNormalizer()
    record = Record()

    viaf_record = normalizer._get_viaf_record(
        record,
        False,
        viaf_id=52700,
        #   entity="Paulo Coelho"
    )

    assert viaf_record is not None
    assert viaf_record.nationality == "br"

    normalizer._add_nationality(record, viaf_record)
    fields_043 = record.get_fields("043")
    assert len(fields_043) == 0

    # Case 2, nationality missing

    normalizer = AuthoritiesRecordNormalizer()
    record = Record()

    viaf_record = normalizer._get_viaf_record(
        record, False, viaf_identifier="123zsxcasd"
    )

    assert viaf_record is None
    normalizer._add_nationality(record, viaf_record)
    fields_043 = record.get_fields("043")
    assert len(fields_043) == 0

    # Case 3 - Nationality is Estonian - add 043 field
    viaf_record = normalizer._get_viaf_record(
        record,
        False,
        viaf_id=249285257,
        #   entity="Jaan Tõnisson"
    )

    assert viaf_record is not None
    assert viaf_record.nationality == "ee"

    normalizer._add_nationality(record, viaf_record)
    fields_043 = record.get_fields("043")
    assert len(fields_043) == 1
    assert str(fields_043[0]) == "=043  \\\\$cee"

    # Case 4 - 043 field already exists - should not get edited (not in ALLOW_EDIT_FIELDS)
    linking_results = [
        {
            "original_entity": "Eduard Vilde",
            "entity_type": EntityType.PER,
            "linked_info": [
                {
                    "json": {
                        "leader": "00736nz  a2200217n  4500",
                        "fields": [
                            {
                                "043": {
                                    "ind1": " ",
                                    "ind2": " ",
                                    "subfields": [{"c": "gb"}],
                                }
                            }
                        ],
                    }
                }
            ],
        }
    ]
    normalizer = AuthoritiesRecordNormalizer(
        linking_results=linking_results,
    )
    record = normalizer.first
    # mock run add nationality with foreign VIAF record
    viaf_record = normalizer._get_viaf_record(
        record,
        False,
        viaf_id=249285257,
        #   entity="Jaan Tõnisson"
    )
    normalizer._add_nationality(record, viaf_record)
    fields_043 = record.get_fields("043")
    assert len(fields_043) == 1
    assert str(fields_043[0]) == "=043  \\\\$cgb"


def test_create_new_normrecord():
    # Case 1 - one entity found - update existing norm record
    linker_res = get_linker_res_example("oneFound.json")
    linking_results = [linker_res]

    normalizer = AuthoritiesRecordNormalizer(linking_results=linking_results)
    data = normalizer.data

    assert len(data) == 1  # should update existing record

    # Case 2 - entities not found - create new norm record
    linking_results = [MOCK_LINKER_NOT_FOUND]
    normalizer = AuthoritiesRecordNormalizer(linking_results=linking_results)
    data = normalizer.data
    assert len(data) == 1

    record = normalizer.first
    leader = str(record.leader)
    assert leader == "01682nz  a2200349n  4500"
    assert len(leader) == 24
    _validate_new_record_notes(record)

    # Case 3 - multiple entities found - record creation will be skipped
    linker_res = get_linker_res_example("multipleFound.json")
    linking_results = [linker_res]
    normalizer = AuthoritiesRecordNormalizer(linking_results=linking_results)
    data = normalizer.data
    assert len(data) == 0

    # Case 3 with bibnormalizer - update with better example
    linking_results = [MOCK_LINKER_NOT_FOUND]
    
    classified_fields = [
        [get_100_field()]
    ]

    normalizer = BibRecordNormalizer(linking_results=linking_results, classified_fields=classified_fields)
    data = normalizer.data
    assert len(data) == 1
    record = normalizer.first

    _validate_new_record_notes(record)
    # validate leader
    leader = str(record.leader)
    assert leader == "00399nz  a2200145n  4500"
    assert len(leader) == 24

    # Mock not found title
    linking_results = [
        {
            "original_entity": "Eesti Ekspress",
            "entity_type": EntityType.TITLE,
            "linked_info": [],
        }
    ]
    normalizer = BibRecordNormalizer(linking_results=linking_results)
    data = normalizer.data
    assert len(data) == 1
    record = normalizer.first

    # Test 100|d gets date
    linking_results = [
        {
            "original_entity": "Libe, Katariina",
            "entity_type": EntityType.PER,
            "linked_info": [],
        }
    ]

    normalizer = AuthoritiesRecordNormalizer(linking_results=linking_results)
    data = normalizer.data
    record = normalizer.first
    # Check that 100|d has date added from VIAF
    field_100 = record.get_fields("100")[0]
    assert field_100.get_subfields("d")[0] == "1986-"
    field_046 = record.get_fields("046")[0]
    assert field_046.get_subfields("f")[0] == "19861126"


def test_680_field_on_existing_record_moved_to_667():
    """680 Should not be added for new, if exists on existing record, should be moved to 667"""
    linker_res = get_linker_res_example("oneFound.json")

    # add 680 field to existing record will have two 680 fields after adding
    linker_res["linked_info"][0]["json"]["fields"].append(
        {"680": {"ind1": " ", "ind2": " ", "subfields": [{"a": "Test 680 field"}]}}
    )
    initial_record = JSONReader(
        json.dumps([linker_res["linked_info"][0]["json"]], ensure_ascii=False)
    )
    record = next(iter(initial_record))
    fields_680 = record.get_fields("680")
    assert len(fields_680) == 2  # inital plus new
    fields_667 = record.get_fields("667")
    assert len(fields_667) == 0  # initial only

    linking_results = [linker_res]

    normalizer = AuthoritiesRecordNormalizer(linking_results=linking_results)
    record = normalizer.first

    fields_680 = record.get_fields("680")
    assert len(fields_680) == 0
    fields_667 = record.get_fields("667")
    assert len(fields_667) == 3  # original + moved from 680 + new note


def test_date_formatting():
    normalizer = AuthoritiesRecordNormalizer()

    dates = {
        "19700712": "19700712",
        "1970": "1970",
        "1970-07": "197007",
        "2001-12-31": "20011231",
        "1999-01": "199901",
    }

    for input_date, expected in dates.items():
        assert normalizer._format_date(input_date) == expected

    # invalid date formats - should return empty string
    invalid_dates = ["abcd", "199A0101"]
    for date in invalid_dates:
        assert normalizer._format_date(date) == ""


def test_new_bibrecord_title_included():
    """normrecord for bibs has to always have the 1XX|t field filled"""

    # Case 1 No linker response, & Viaf record found
    linking_results = [
        {
            "original_entity": "Lord of the Rings",
            "entity_type": EntityType.TITLE,
            "linked_info": [],
        }
    ]
    # classified_fields = [
    #     [get_100_field("Lord of the Rings")]
    # ]

    normalizer = BibRecordNormalizer(
        linking_results=linking_results,
        # classified_fields=classified_fields,
    )
    data = normalizer.data
    assert len(data) == 1  # should enrich existing record
    record = normalizer.first

    _validate_new_record_notes(record)
    fields_100 = record.get_fields("100")
    assert len(fields_100) == 1
    assert fields_100[0].get_subfields("t")[0] == "Lord of the rings"

    # Case 2 - Viaf record not found - should use classified author
    linking_results = [
        {
            # "original_entity": "Roolijoodiku katastroofiline jõulusõit",
            "entity_type": EntityType.TITLE,
            "linked_info": [],
        }
    ]
    classified_fields = [
        [get_100_field(title="Roolijoodiku katastroofiline jõulusõit")]
    ]
    
    normalizer = BibRecordNormalizer(
        linking_results=linking_results,
        classified_fields=classified_fields,
    )
    record = normalizer.first
    data = normalizer.data
    assert len(data) == 1  # should enrich existing record

    fields_100 = record.get_fields("100")
    assert len(fields_100) == 1
    assert (
        fields_100[0].get_subfields("t")[0] == "Roolijoodiku katastroofiline jõulusõit"
    )
    
    # withourt classified fields - should not create record
    normalizer = BibRecordNormalizer(
        linking_results=linking_results,
    )
    data = normalizer.data
    assert len(data) == 0  # should not create record


def _validate_new_record_008_field(record: Record):
    """Validate 008 field in new record"""
    field_008 = record.get_fields("008")[0].data
    assert len(field_008) == 40
    # pos 00-05 is current date in YYMMDD format
    timestamp = field_008[0:6]
    try:
        datetime.strptime(timestamp, YYMMDD_FORMAT)
    except ValueError:
        raise AssertionError(
            f"008 field timestamp {timestamp} is not in format {YYMMDD_FORMAT}"
        )


def test_008_field_formatting():
    """00-04 position will be changed for new record, not edited on existing record"""

    # Case 1 - new record created, should have current date in 008 field

    linking_results = [
        {
            "original_entity": "Eesti Ekspress",
            "entity_type": EntityType.TITLE,
            "linked_info": [],
        }
    ]

    normalizer = BibRecordNormalizer(
        linking_results=linking_results,
    )
    new_record = normalizer.first
    _validate_new_record_008_field(new_record)

    # Case 2 - existing record updated, 008 field should not be changed
    linker_res = get_linker_res_example("oneFound.json")
    linking_results = [linker_res]
    original_record = JSONReader(
        json.dumps([linker_res["linked_info"][0]["json"]], ensure_ascii=False)
    )
    record = next(iter(original_record))
    original_008 = record.get_fields("008")[0].data

    # for authorities
    normalizer = AuthoritiesRecordNormalizer(linking_results=linking_results)
    authorities_record = normalizer.first
    field_008 = authorities_record.get_fields("008")[0].data
    assert len(field_008) == 40

    assert field_008 == original_008

    # for bibs
    normalizer = BibRecordNormalizer(linking_results=linking_results)
    expected_008 = "990107|||aznnnaabn          || |||" + 6 * " "
    bibrecord = normalizer.first
    field_008 = bibrecord.get_fields("008")[0].data
    assert len(field_008) == 40
    assert field_008 == expected_008


def test_classified_fields_added_to_linked_record():
    """Test that classified fields Can be passed to normalizer & added to linked record"""

    classified_fields = (
        [
            {
                "046": {"ind1": " ", "ind2": " ", "subfields": [{"k": "2021"}]},
                "670": {
                    "ind1": " ",
                    "ind2": "0",
                    "subfields": [{"a": "Päikesekiri, 2021"}],
                },
                "100": {
                    "ind1": "2",
                    "ind2": " ",
                    "subfields": [{"a": "Eesti Kirjandusmuuseum"}],
                },
            }
        ],
    )
    # Case 1 - no 670 exists, should be added to linked record
    for normalizer in (AuthoritiesRecordNormalizer, BibRecordNormalizer):
        linking_results = [MOCK_LINKER_NOT_FOUND]
        normalizer = normalizer(
            linking_results=linking_results, classified_fields=classified_fields
        )

        record = normalizer.first
        fields_670 = record.get_fields("670")
        assert len(fields_670) == 1
        assert fields_670[0].get_subfields("a")[0] == "Päikesekiri, 2021"

    # Case 2 - existing record with 670 should not update (same behavior for both normalizers)
    linker_res = get_linker_res_example("oneFound.json")
    linking_results = [linker_res]

    for normalizer in (AuthoritiesRecordNormalizer,
                       BibRecordNormalizer):
        normalizer = normalizer(
            linking_results=linking_results, classified_fields=classified_fields
        )
        record = normalizer.first
        fields_670 = record.get_fields("670")
        assert len(fields_670) == 1
        assert fields_670[0].get_subfields("a")[0] == "Eesti kirjarahva leksikon, 1995."

    def get_046_field(year: str) -> dict:
        return {"046": {"ind1": " ", "ind2": " ", "subfields": [{"k": year}]}}
    
    # Case 3 - 046 $k - publication date Passed for bib
    classified_fields = [
        [get_046_field("2021"), get_100_field("Title 2021")],
        [get_046_field("1999"), get_100_field("Title 1999")],
        [get_046_field("2022"), get_100_field("Title 2022")],
    ]

    mock_046_exists = MOCK_LINKER_ONE_FOUND.copy()
    mock_046_exists["linked_info"][0]["json"]["fields"].append(get_046_field("2000"))

    # for new record should get included
    linking_results = [
        MOCK_LINKER_NOT_FOUND,  # new record
        MOCK_LINKER_ONE_FOUND,  # new record
        MOCK_LINKER_NOT_FOUND,
    ]  # editing existing record

    normalizer = BibRecordNormalizer(
        linking_results=linking_results, classified_fields=classified_fields
    )

    # for i, record in enumerate(normalizer):
    # first two should have 046 from classified data
    record1 = normalizer.get_record(0)
    fields_046 = record1.get_fields("046")
    assert len(fields_046) == 1
    assert fields_046[0].get_subfields("k")[0] == "2021"

    record2 = normalizer.get_record(1)
    fields_046 = record2.get_fields("046")
    assert len(fields_046) == 1
    # should be unchanged, aka 2000
    assert fields_046[0].get_subfields("k")[0] == "2000"

    record3 = normalizer.get_record(2)
    fields_046 = record3.get_fields("046")
    assert len(fields_046) == 1
    assert fields_046[0].get_subfields("k")[0] == "2022"


def test_classified_author_included_to_new_bibrecord():
    # Case 1 - new record created, should have 100|a from classified data
    expected_author = "Primary Author"
    expected_date = "2002-"
    expected_title = "Title"
    expected_role = "autor"
    classified_fields = [
        [
            {
                "100": {
                    "ind1": "2",
                    "ind2": " ",
                    "subfields": [
                        {"a": expected_author},
                        {"d": expected_date},
                        {"e": expected_role},
                        {"t": expected_title},
                    ],
                }
            },
        ],
        [
            {
                "670": {
                    "ind1": " ",
                    "ind2": " ",
                    "subfields": [{"a": "Another Task, 2022"}],
                }
            },
            {"046": {"ind1": " ", "ind2": " ", "subfields": [{"k": "2022"}]}},
            {
                "100": {
                    "ind1": "2",
                    "ind2": " ",
                    "subfields": [
                        {"a": expected_author},
                        {"d": expected_date},
                        {"e": expected_role},
                        {"t": expected_title},
                    ],
                }
            },
        ],
        [],
    ]

    linking_results = [
        MOCK_LINKER_NOT_FOUND,  # create new
        MOCK_LINKER_ONE_FOUND,  # update existing
        MOCK_LINKER_NOT_FOUND,  # create new
    ]

    normalizer = BibRecordNormalizer(
        linking_results=linking_results, classified_fields=classified_fields
    )

    data = normalizer.data
    assert len(data) == 2  # two records created/updated, third one skipped

    # Should include 100 from classified data
    first_record = normalizer.get_record(0)
    field_100 = first_record.get_fields("100")[0]
    assert field_100.get_subfields("a")[0] == expected_author
    assert field_100.get_subfields("d")[0] == expected_date
    assert field_100.get_subfields("t")[0] == expected_title
    assert field_100.get_subfields("e")[0] == expected_role

    # Case 2 - existing record updated, original record, should not be changed
    second_record = normalizer.get_record(1)
    field_100 = second_record.get_fields("100")[0]
    # =100  1\$aVilde, Eduard,$d1865-1933.
    assert field_100.get_subfields("a")[0] == "Vilde, Eduard,"
    assert field_100.get_subfields("d")[0] == "1865-1933."


def test_classified_data_with_multiple_records():
    """Test classified data with multiple records - should match by sierraID"""

    classified_fields = [
        [
            {
                "670": {
                    "ind1": " ",
                    "ind2": "0",
                    "subfields": [{"a": "Päikesekiri, 2021"}],
                },
                "111": {
                    "ind1": "2",
                    "ind2": " ",
                    "subfields": [{"a": "Eesti Kirjandusmuuseum"}],
                },
            }
        ],
        [],
        [
            {
                "670": {
                    "ind1": " ",
                    "ind2": "0",
                    "subfields": [{"a": "Teine kirjeldus, 2022"}],
                },
                "111": {
                    "ind1": "2",
                    "ind2": " ",
                    "subfields": [{"a": "ERM"}],
                },
            }
        ],
    ]

    # Case 1 - no 670 exists, should be added to linked record
    for normalizer in (AuthoritiesRecordNormalizer, BibRecordNormalizer):
        linking_results = [
            MOCK_LINKER_NOT_FOUND,
            MOCK_LINKER_ONE_FOUND,
            MOCK_LINKER_NOT_FOUND,
        ]
        normalizer = normalizer(
            linking_results=linking_results, classified_fields=classified_fields
        )

        # Check first record - should have 670 & 111 from classified data
        record = normalizer.first
        assert len(record.get_fields("670")) == 1
        fields_670 = record.get_fields("670")[0]
        fields_111 = record.get_fields("111")[0]
        assert fields_670.get_subfields("a")[0] == "Päikesekiri, 2021"
        assert fields_111.get_subfields("a")[0] == "Eesti Kirjandusmuuseum"

        # Check second record - should not have 670 from classified data
        record = normalizer.get_record(1)
        assert len(record.get_fields("670")) == 1
        fields_670 = record.get_fields("670")[0]
        assert fields_670.get_subfields("a")[0] == "Eesti kirjarahva leksikon, 1995."

        # Check third record - should have 670 from classified data
        record = normalizer.get_record(2)
        assert len(record.get_fields("670")) == 1
        fields_670 = record.get_fields("670")[0]
        assert fields_670.get_subfields("a")[0] == "Teine kirjeldus, 2022"


def test_viaf_name_variations():
    """Test adding alternative name forms from VIAF to 4XX fields. Should skip some variants"""

    normalizer = AuthoritiesRecordNormalizer()
    record = Record()

    viaf_record: VIAFRecord = normalizer._get_viaf_record(
        record,
        False,
        viaf_id=73918842,
        # entity="Jaan Kaplinski"
    )

    assert viaf_record is not None
    assert len(viaf_record.name_variations) > 0

    normalizer._add_author(record, viaf_record)

    fields_4xx = record.get_fields("400", "410", "411")

    unfiltered_name_variations = viaf_record.name_variations

    assert len(fields_4xx) > 0
    assert len(fields_4xx) < len(unfiltered_name_variations)


def test_name_variations_variate_with_author_type():
    """Test that name variations added depend on author type (PER, ORG)"""

    normalizer = AuthoritiesRecordNormalizer()

    # Case 1 - Person
    record = Record()
    viaf_record: VIAFRecord = normalizer._get_viaf_record(
        record,
        False,
        viaf_id=73918842,
        # entity="Jaan Kaplinski"
    )
    normalizer._add_author(record, viaf_record)

    def check_fields_exist(record: Record, tags: list):
        for tag in tags:
            fields = record.get_fields(tag)
            if len(fields) > 0:
                return True
        return False

    # record should only have 400 from 4xx fields
    assert check_fields_exist(record, ["400"])
    assert not check_fields_exist(record, ["410", "411"])

    # Case 2 - Organization
    record = Record()
    viaf_record: VIAFRecord = normalizer._get_viaf_record(
        record,
        False,
        viaf_id=154334700,
        # entity="Eesti Kirjandusmuuseum"
    )
    normalizer._add_author(record, viaf_record)
    # Record should only have 410 from 4xx fields
    assert check_fields_exist(record, ["410"])
    assert not check_fields_exist(record, ["400", "411"])


def test_existing_record_linked_to_viaf_record():
    """Test existing record linked to VIAF record - should enrich with VIAF data"""

    base_path = "tests/test_data/marc_records/json/"
    with (
        open(os.path.join(base_path, "imbi.json"), "r", encoding="utf-8") as f,
        open(os.path.join(base_path, "ernits.json"), "r", encoding="utf-8") as f2,
        open(os.path.join(base_path, "rowling.json"), "r", encoding="utf-8") as f3,
    ):
        imbi = json.load(f)
        ernits = json.load(f2)
        rowling = json.load(f3)

    linking_results = [imbi, ernits, rowling]

    normalizer = AuthoritiesRecordNormalizer(
        linking_results=linking_results,
    )

    def get_viaf_url(record: Record):
        field_024 = record.get_fields("024")
        if len(field_024) == 0:
            return None
        return field_024[0].get_subfields("0")[0]

    viaf_base_url = "http://viaf.org/viaf"
    assert get_viaf_url(normalizer.get_record(0)) == f"{viaf_base_url}/167120147/"
    assert get_viaf_url(normalizer.get_record(1)) == f"{viaf_base_url}/22458146/"
    assert get_viaf_url(normalizer.get_record(1)) == f"{viaf_base_url}/22458146/"
    assert get_viaf_url(normalizer.get_record(2)) == f"{viaf_base_url}/116796842/"


def test_existing_record_enriched_by_elastic_identifier():
    """Test that elastic identifier is correctly parsed from linker response and used to enrich existing record"""

    # Case 1: one linker response with identifier, should find match and enrich
    original_record_json = MOCK_LINKER_ONE_FOUND["linked_info"][0]["json"]
    original_record = next(
        iter(JSONReader(json.dumps([original_record_json], ensure_ascii=False)))
    )
    # check no 024 field with viaf url exists
    assert len(original_record.get_fields("024")) == 0

    linker_res = MOCK_LINKER_ONE_FOUND.copy()
    # add an identifier field to existing record

    normalizer = AuthoritiesRecordNormalizer(
        linking_results=[linker_res],
    )

    record: Record = normalizer.first
    assert len(record.get_fields("024")) == 1
    viaf_url = record.get_fields("024")[0].get_subfields("0")[0]
    expected_viaf_url = "http://viaf.org/viaf/105016/"
    assert viaf_url == expected_viaf_url
