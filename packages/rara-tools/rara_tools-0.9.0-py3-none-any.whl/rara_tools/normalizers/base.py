from datetime import datetime
from pymarc import Field, Subfield, JSONReader, Record
from typing import List, Optional, Iterator
from rara_tools.normalizers.reader import SafeJSONReader

from rara_tools.parsers.tools.validators import filter_names
from rara_tools.normalizers.exceptions import SkipRecordException


from rara_tools.normalizers.viaf import VIAFRecord, VIAFClient
from rara_tools.constants.normalizers import (
    DEFAULT_VIAF_FIELD,
    ALLOWED_VIAF_FIELDS,
    ALLOWED_VIAF_WIKILINK_LANGS,
    VIAF_SIMILARITY_THRESHOLD,
    VERIFY_VIAF_RECORD,
    MAX_VIAF_RECORDS_TO_VERIFY,
    EMPTY_INDICATORS,
    YYMMDD_FORMAT,
    YY_DD_FORMAT,
    YYYYMMDD_FORMAT,
)
from glom import glom
from dateutil import parser
from datetime import date

import logging
import json

logger = logging.getLogger(__name__)


class RecordNormalizer:
    """
    Base class for normalizing different record types corresponding classes have been created.
    By default existing record fields will not be changed, unless included in ALLOW_EDIT_FIELDS. If a field
    included in the normalization is not present, it will be added to the record. If under REPEATABLE_FIELDS.
    a new record field is added.

    Args:
        sierra_data: Optionally, can normalize records from SIERRA. Must be in specific format,
        e.g converted with SierraResponseConverter. examples at: tests/sierra/output
        classified_fields: Optionally can include marc fields, will follow the rules of the tag number.
        Useful to send classified data from core.
        entities: List of Full names (str). If included, will use NormLinker to match with normalized records on KATA elastic.
    """

    def __init__(
        self,
        linking_results: List[dict] = [],
        sierra_data: List[dict] = [],
        classified_fields: List[List[dict]] = [],
        ALLOW_EDIT_FIELDS: List[str] = ["925"],
        REPEATABLE_FIELDS: List[str] = ["667"],
    ):
        # Include, if will replace existing field
        self.ALLOW_EDIT_FIELDS = ALLOW_EDIT_FIELDS
        # include, if should be added alongside existing fields
        self.REPEATABLE_FIELDS = REPEATABLE_FIELDS
        # leader applied to new records
        self.DEFAULT_LEADER = "01682nz  a2200349n  4500"  # must be 24 digits

    def _setup_records(
        self,
        linking_results: List[dict],
        sierra_data: List[dict],
        classified_fields: List[List[dict]] = [],
    ) -> JSONReader:
        """Setup initial MARC records and data.

        If no linked entities or more than one linked entity found, we create a new record.
        If one linked entity found, we create an updated record from the linked entity data.
        """
        linked_records = []

        def handle_create_new_record(entity, idx, elastic_meta):
            logger.info(f"No linked entities found for {entity}, Creating new record.")
            linked_records.append({"leader": self.DEFAULT_LEADER, "fields": []})
            self.records_extra_data.append(
                {
                    "entity": entity,
                    "classified_fields": classified_fields[idx]
                    if idx < len(classified_fields)
                    else [],
                    "edited": False,
                    "elastic": elastic_meta,
                }
            )

        for idx, linked in enumerate(linking_results or []):
            if not isinstance(linked, dict):
                logger.debug(f"Skipping invalid linked result: {linked}")
                continue

            entity = linked.get("original_entity")
            linked_info = linked.get("linked_info", [])

            if not isinstance(linked_info, list) or not linked_info:
                # No linked entities found, create new record
                elastic_meta = {}  # Always empty in this case
                handle_create_new_record(entity, idx, elastic_meta)
                continue

            elif len(linked_info) > 1:
                # Multiple linked entities found, Skip
                logger.info(
                    f"Multiple ({len(linked_info)}) linked entities found for {entity}, skipping creating normrecord."
                )
                continue

            elif len(linked_info) == 1:
                # one record match found, we update existing record

                linked_item = linked_info[0]
                if not isinstance(linked_item, dict):
                    continue

                elastic_meta = linked_item.get("elastic", {})

                # handle case where we have linked an entity without a record
                if not linked_item.get("json", None):
                    handle_create_new_record(entity, idx, elastic_meta)
                    continue

                linked_records.append(linked_item.get("json", {}))

                self.records_extra_data.append(
                    {
                        "entity": entity,
                        "viaf": linked_item.get("viaf", {}),
                        "classified_fields": classified_fields[idx]
                        if idx < len(classified_fields)
                        else [],
                        "edited": True,
                        "elastic": elastic_meta,
                    }
                )
                continue

        self.records_extra_data.extend(
            {"sierraID": obj.get("sierraID"), "edited": True}
            for obj in (sierra_data or [])
            if isinstance(obj, dict)
        )

        all_records = linked_records + (sierra_data or [])

        return SafeJSONReader(json.dumps(all_records, ensure_ascii=False))

    @staticmethod
    def current_timestamp():
        """6 digit timestamp, format YYMMDD"""
        return datetime.now().strftime(YYMMDD_FORMAT)

    @staticmethod
    def current_yyyy_dd():
        """format of 2025-03"""
        return datetime.now().strftime(YY_DD_FORMAT)

    @staticmethod
    def _is_person_est_nationality(viaf_record: VIAFRecord) -> bool:
        return hasattr(viaf_record, "nationality") and viaf_record.nationality == "ee"

    def get_formatted_dates(self, viaf_record: VIAFRecord) -> str | None:
        """Get birth and death date in the form 1878-1940. If only birth date is present, return 1878-.
        If no dates, return empty string.
        """
        birth_date = self._extract_year(viaf_record.birth_date)
        death_date = (
            self._extract_year(viaf_record.death_date)
            if viaf_record.death_date != 0
            else ""
        )

        if birth_date and death_date:
            return f"{birth_date}-{death_date}"
        elif birth_date:
            return f"{birth_date}-"
        else:
            return None

    def _is_nxx(self, field: Field, n: str):
        """Check if fields tag is in nxx range."""
        return field.tag.startswith(n)

    def get_record_field_or_none(self, record: Record, tag: str) -> Optional[Field]:
        return record.get_fields(tag)[0] if record.get_fields(tag) else None

    def _field_in_record(self, field: Field, record: Record) -> bool:
        """Check if field exists in record."""
        existing_fields = record.get_fields(field.tag)
        return any(
            field.data == existing_field.data for existing_field in existing_fields
        )

    def _filter_equivalent_field_not_in_record(
        self, record: Record, fields: List[Field]
    ) -> bool:
        """filter out fields, that do not have an equivalent in the record."""
        return filter(lambda field: not self._field_in_record(field, record), fields)

    def _extract_year(self, value: str) -> str:
        if value is None:
            return ""

        if isinstance(value, (datetime, date)):
            return str(value.year)

        try:
            dt = parser.parse(str(value), fuzzy=True)
            parsed_year = str(dt.year)
            logger.info(f"Extracted year '{parsed_year}' from value '{value}'")
            return parsed_year
        except Exception as e:
            logger.info(f"Failed to extract year string '{value}': {e}")
            return ""

    def _format_date(self, value: str) -> str:
        if not value:
            return ""

        if isinstance(value, (datetime, date)):
            return value.strftime(YYYYMMDD_FORMAT)

        val = str(value).strip()

        try:
            dt = parser.parse(val, fuzzy=False, default=datetime(1, 1, 1))
        except Exception:
            return ""

        if len(val) == 4 and val.isdigit():
            return dt.strftime("%Y")  # YYYY
        if len(val) in (6, 7):  # YYYYMM or YYYY-MM
            return dt.strftime("%Y%m")  # YYYYMM
        return dt.strftime(YYYYMMDD_FORMAT)  # YYYYMMDD

    def get_subfield(
        self, record: Record, tag: str, subfield: str, default: str
    ) -> str:
        """get record existing subfield value or assign a fallback value."""

        field = self.get_record_field_or_none(record, tag)

        if field is None:
            return default

        subfields = field.get_subfields(subfield)
        return subfields[0] if subfields else default

    def _handle_default_fields(self, record: Record, *fields: List[Field]) -> Record:
        """Default behavior - add field to record iff not present already"""
        record.add_field(
            *filter(
                lambda field: field.tag not in [f.tag for f in record.get_fields()],
                fields,
            )
        )

    def _handle_editable_fields(self, record: Record, *fields: List[Field]) -> Record:
        """replace existing field with a new field."""

        editable_fields = filter(
            lambda field: field.tag in self.ALLOW_EDIT_FIELDS, fields
        )

        tags = [f.tag for f in editable_fields]

        record.remove_fields(*tags)
        record.add_field(*editable_fields)

    def _handle_repeatable_fields(self, record: Record, *fields: List[Field]) -> Record:
        """add field to the record & don't replace existing field."""

        repeatable_fields = [
            field for field in fields if field.tag in self.REPEATABLE_FIELDS
        ]

        record.add_field(
            *repeatable_fields
            # *self._filter_equivalent_field_not_in_record(
            #     record, repeatable_fields)
        )

    def _add_fields_to_record(self, record: Record, fields: List[Field]) -> Record:
        cleaned_fields = []

        for field in fields:
            # Always assume control fields cleaned
            if field.tag < "010" and field.tag.isdigit():
                cleaned_fields.append(field)
                continue

            # filter out subfields that are empty or 0 (VIAF returns 0 for unknown dates)
            field.subfields = [
                sub
                for sub in field.subfields
                if sub.value and sub.value not in ["0", 0]
            ]

            # only keep the field if it still has subfields left
            if field.subfields:
                cleaned_fields.append(field)

        if not cleaned_fields:
            return record

        self._handle_repeatable_fields(record, *cleaned_fields)
        self._handle_editable_fields(record, *cleaned_fields)
        self._handle_default_fields(record, *cleaned_fields)

        return record

    def _add_author(self, record: Record, viaf_record: VIAFRecord) -> Optional[Field]:
        existing_author: Optional[Field] = (
            record.get("100") or record.get("110") or record.get("111")
        )

        if existing_author:
            # Attempt to add alternative name variations only
            # if viaf_record:
            #     author_tag = hasattr(existing_author, 'tag') and existing_author.tag or "100"
            #     self._include_name_variations(record, viaf_record, author_tag=author_tag)
            return record

        type_map = {"Personal": "100", "Corporate": "110", "Collective": "111"}
        author_type = viaf_record.name_type
        tag = type_map.get(author_type, "100")

        fields = [
            Field(
                tag=tag,
                indicators=EMPTY_INDICATORS,
                subfields=[
                    Subfield("a", viaf_record.name),
                ],
            )
        ]

        if viaf_record:
            author_dates = self.get_formatted_dates(viaf_record)
            if author_dates:
                fields[0].add_subfield("d", author_dates)

        self._add_fields_to_record(record, fields)

        if viaf_record:
            self._include_name_variations(record, viaf_record, author_tag=tag)

    def _include_name_variations(
        self,
        record: Record,
        viaf_record: VIAFRecord,
        author_tag: str,
        filter_variations=True,
    ) -> None:
        """Include name variations from VIAF record as 400|t fields"""

        if not viaf_record or not viaf_record.name_variations:
            return

        existing_name_variations = record.get_fields("400")
        existing_variations = [
            sf.value
            for field in existing_name_variations
            for sf in field.get_subfields("a")
        ]

        if filter_variations:
            allowed_variations = filter_names(viaf_record.name_variations)
            logger.debug(
                f"filtered out {len(viaf_record.name_variations) - len(allowed_variations)} name variations for '{viaf_record.name}'"
            )

        else:
            allowed_variations = viaf_record.name_variations

        fields = []

        tag = "4" + author_tag[1:] if author_tag in ["100", "110", "111"] else "400"

        for variation in allowed_variations:
            if variation not in existing_variations:
                fields.append(
                    Field(
                        tag=tag,
                        indicators=EMPTY_INDICATORS,
                        subfields=[Subfield("a", variation)],
                    )
                )

        self._add_fields_to_record(record, fields)

    def _move680_fields_to_667(self, record: Record) -> None:
        """Move existing 680 fields to 667, if any."""
        fields_680 = record.get_fields("680")
        if not fields_680:
            return

        fields_667 = [
            Field(tag="667", indicators=EMPTY_INDICATORS, subfields=field.subfields)
            for field in fields_680
        ]

        record.remove_fields("680")
        self._add_fields_to_record(record, fields_667)

    def _include_classified_fields(
        self, record: Record, classified_fields: list[dict]
    ) -> None:
        """Include classified fields from core, if any.
        e.g. classified_fields=[{'670': {'ind1': ' ', 'ind2': '0', 'subfields': [{'a': 'Päikesekiri, 2021'}]}}]

        For each record, we need a list of dicts, to handle repeatable fields.
        """
        if not classified_fields:
            return

        fields = [
            Field(
                tag=str(tag),
                indicators=v.get(
                    "indicators", [v.get("ind1", " "), v.get("ind2", " ")]
                ),
                subfields=[
                    Subfield(code, value)
                    for sub in v.get("subfields", [])
                    for code, value in sub.items()
                ],
            )
            for field_dict in classified_fields
            for tag, v in field_dict.items()
        ]

        self._add_fields_to_record(record, fields)

    def _normalize_common(
        self,
        record: Record,
        is_editing_existing_record: bool,
        classified_fields: List[dict],
    ) -> None:
        """Common logic for all normalizations.
        - Includes note about record being created/edited.
        - include date note with a different subfield, depending on if record is new or edited.
        - move existing 680 fields to 667
        """
        self._include_classified_fields(record, classified_fields)

        # before adding new notes
        self._move680_fields_to_667(record)

        note = "Muudetud AI poolt" if is_editing_existing_record else "Loodud AI poolt"
        date_note = f"KRATT {self.current_yyyy_dd()}"

        field_667 = Field(
            tag="667", indicators=EMPTY_INDICATORS, subfields=[Subfield("a", note)]
        )

        fields = [field_667]

        if is_editing_existing_record:
            field_925 = Field(
                tag="925",
                indicators=EMPTY_INDICATORS,
                subfields=[
                    Subfield("p", self.get_subfield(record, "925", "p", date_note))
                ],
            )
            fields.append(field_925)

        else:
            field_925 = Field(
                tag="925",
                indicators=EMPTY_INDICATORS,
                subfields=[
                    Subfield("t", self.get_subfield(record, "925", "t", date_note))
                ],
            )
            fields.append(field_925)

        self._add_fields_to_record(record, fields)

        return record

    def _get_viaf_search_term(
        self, record: Record, entity: Optional[str]
    ) -> Optional[str]:
        """prioritize entity name, if not available, use author name."""
        if entity:
            return entity

        author_field = record.get("100") or record.get("110") or record.get("111")
        if author_field:
            return (
                author_field.get_subfields("a")[0]
                if author_field.get_subfields("a")
                else None
            )

        logger.warning(
            "No entity or author name found for VIAF search. Skipping VIAF enrichment."
        )

    def _get_viaf_record(
        self,
        record: Record,
        is_editing_existing_record: bool,
        viaf_id: Optional[int] = None,
        entity: Optional[str] = None,
        viaf_identifier: Optional[str] = None,
        viaf_field: str = DEFAULT_VIAF_FIELD,
        threshold: float = VIAF_SIMILARITY_THRESHOLD,
        verify: bool = VERIFY_VIAF_RECORD,
        max_records: int = MAX_VIAF_RECORDS_TO_VERIFY,
    ) -> Optional[VIAFRecord]:
        """

        Get VIAF record either by ID if possible, otherwise by search term.
        We do not use the entity as the search term directly, due to inaccuracies.

        Instead, search by search term user only if viaf_identifier is available

        """

        viaf_record = None

        try:
            viaf_client = VIAFClient()

            if viaf_id:
                viaf_records = viaf_client.get_normalized_data_by_ids([viaf_id])
                if viaf_records:
                    viaf_record = viaf_records[0]
            else:
                # KRATT-787
                #  If editing, only allow to use viaf_identifier
                if is_editing_existing_record:
                    search_term = viaf_identifier if viaf_identifier else None
                else:
                    search_term = self._get_viaf_search_term(record, entity)
                    verify = True  # more accurate with author name search

                if search_term:
                    logger.info(
                        f"Searching for VIAF record with search term: {search_term}"
                    )

                    if not verify:
                        logger.warning(
                            f"Record verification is turned off. If multiple records are "
                            f"detected for search term '{search_term}', the first "
                            f"result is automatically returned. This might lead to "
                            f"some inaccuracies!"
                        )

                    viaf_record = viaf_client.get_normalized_data_by_search_term(
                        search_term=search_term,
                        field=viaf_field,
                        max_records=max_records,
                        verify=verify,
                        threshold=threshold,
                    )
                    if viaf_record:
                        logger.debug(
                            f"VIAF {search_term}, linked to ID: {viaf_record.viaf_id}"
                        )

        except Exception as e:
            logger.error(
                f"Error fetching VIAF record with ID={viaf_id} / entity='{entity}': {e}"
            )
        return viaf_record

    def _normalize_record(
        self,
        record: Record,
        sierraID: str,
        viaf_record: VIAFRecord,
        is_editing_existing_record: bool,
        original_entity: str,
    ) -> Record:
        return record

    def get_record(self, index: int) -> Record:
        """Get normalized record by index."""
        for idx, record in enumerate(self):
            if idx == index:
                return record
        raise IndexError("Record index out of range.")

    @property
    def data(self) -> List[dict]:
        """Shorthand to get all normalized records as dict, skipping failures."""
        result = []
        for record in self:
            try:
                result.append(record.as_dict())
            except Exception as e:
                logger.error(f"Failed to normalize record: {e}")
                continue
        return result

    @property
    def first(self) -> Record:
        return next(iter(self))

    def __iter__(self) -> Iterator:
        # viaf_id_path = "viaf.original.queryResult.viafID"
        viaf_id_path = "viaf.parsed.viaf_id"
        viaf_identifier_path = "elastic.identifier"
        sierra_id_path = "sierraID"

        for record, extra_data in zip(self.records, self.records_extra_data):
            sierra_id = glom(extra_data, sierra_id_path, default="")
            viaf_id = glom(extra_data, viaf_id_path, default=None)
            # KRAT-787 - In our elasticsearch docs, we store an "identifier"
            # field, that is infrequently filled, but can be used for exact VIAF record search.
            viaf_identifier = glom(extra_data, viaf_identifier_path, default=None)
            logger.info(
                f"Processing record with VIAF ID: {viaf_id}, VIAF Identifier: {viaf_identifier}"
            )

            classified_fields = extra_data.get("classified_fields", [])
            entity = extra_data.get("entity")
            is_editing_existing_record = extra_data.get("edited") is True

            viaf_record = self._get_viaf_record(
                record=record,
                is_editing_existing_record=is_editing_existing_record,
                viaf_id=viaf_id,
                entity=entity,
                viaf_identifier=viaf_identifier,
                verify=False,  # Not accurate with identifier search
            )
            if viaf_record:
                logger.debug(
                    f"linked VIAF record with ID {viaf_record.viaf_id} for entity '{entity}'"
                )

            record = self._normalize_common(
                record, is_editing_existing_record, classified_fields
            )
            
            try:
                normalized_record = self._normalize_record(
                    record,
                    sierra_id,
                    viaf_record,
                    is_editing_existing_record,
                    original_entity=entity,
                )
            except SkipRecordException as e:
                logger.info(f"Skipping record normalization: {e}")
                continue

            normalized_record.fields.sort(key=lambda field: field.tag)

            yield normalized_record
