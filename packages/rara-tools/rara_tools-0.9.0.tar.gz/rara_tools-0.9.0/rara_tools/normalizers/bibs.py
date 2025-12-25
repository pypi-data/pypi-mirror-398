from pymarc import Field, Subfield, Record
from typing import List, Optional

from rara_tools.constants import EMPTY_INDICATORS
from rara_tools.normalizers.viaf import VIAFRecord
from rara_tools.normalizers import RecordNormalizer
from rara_tools.normalizers.exceptions import SkipRecordException


import logging


logger = logging.getLogger(__name__)


class BibRecordNormalizer(RecordNormalizer):
    """Normalize bib records."""

    def __init__(
        self,
        linking_results: List[dict] = [],
        sierra_data: List[dict] = [],
        classified_fields: List[List[dict]] = [],
        ALLOW_EDIT_FIELDS: List[str] = ["008", "925"],
        REPEATABLE_FIELDS: List[str] = ["667"],
    ):
        super().__init__(linking_results, sierra_data, classified_fields)
        self.DEFAULT_LEADER = "00399nz  a2200145n  4500"  # must be 24 digits
        self.ALLOW_EDIT_FIELDS = ALLOW_EDIT_FIELDS
        self.REPEATABLE_FIELDS = REPEATABLE_FIELDS

        self.records_extra_data = []
        self.sierra_data = sierra_data
        self.records = self._setup_records(
            linking_results, sierra_data, classified_fields
        )

    def _normalize_sierra(
        self, record: Record, is_editing_existing_record: bool
    ) -> Record:
        suffix_008 = "|||aznnnaabn          || |||      "

        if is_editing_existing_record:
            # Try to reuse prefix from existing 008 field if present
            existing_008 = next(
                (f for f in record.fields if f.tag == "008" and hasattr(f, "data")),
                None,
            )
            if existing_008 and len(existing_008.data) >= 6:
                prefix = existing_008.data[:6]  # keep existing timestamp
            else:
                prefix = self.current_timestamp()  # fallback if no valid existing data
        else:
            prefix = self.current_timestamp()

        fields = [
            Field(tag="008", data=f"{prefix}{suffix_008}"),
        ]

        self._add_fields_to_record(record, fields)

    def _add_author(
        self, record: Record, viaf_record: Optional[VIAFRecord], original_entity: str
    ) -> Optional[Field]:
        if record.get("100") or record.get("110") or record.get("111"):
            return record

        type_map = {"Personal": "100", "Corporate": "110", "Collective": "111"}

        tag = type_map.get(getattr(viaf_record, "name_type", None), "100")

        # KRAT-785 if author cannot be found at all
        title = getattr(viaf_record, "name", None)
        if not title:
            logger.info(
                f"No author name found in classified data or VIAF for original entity: {original_entity}, skipping creating bib normrecord"
            )
            # Skip to the next iteration
            raise SkipRecordException("No author name found, skipping record")

        # Note that without title, the record will not be created further along in the pipeline
        fields = [
            Field(
                tag=tag, indicators=EMPTY_INDICATORS, subfields=[Subfield("t", title)]
            )
        ]

        if viaf_record:
            author_dates = self.get_formatted_dates(viaf_record)
            if author_dates:
                fields[0].add_subfield("d", author_dates)

        self._add_fields_to_record(record, fields)

        if viaf_record:
            self._include_name_variations(record, viaf_record, author_tag=tag)

    def _normalize_viaf(
        self, record: Record, viaf_record: VIAFRecord, original_entity: str
    ) -> None:
        if not viaf_record:
            # viaf record not found, include original entity as 100|t
            self._add_author(record, viaf_record=None, original_entity=original_entity)
            return record

        self._add_author(record, viaf_record, original_entity=original_entity)

    def _normalize_record(
        self,
        record: Record,
        sierraID: str,
        viaf_record: VIAFRecord,
        is_editing_existing_record: bool,
        original_entity: str,
    ) -> Record:
        self._normalize_sierra(record, is_editing_existing_record)
        self._normalize_viaf(record, viaf_record, original_entity=original_entity)

        return record
