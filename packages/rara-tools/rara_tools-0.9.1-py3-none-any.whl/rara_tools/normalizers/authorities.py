from rara_tools.constants import EMPTY_INDICATORS
from rara_tools.normalizers.viaf import VIAFRecord

from rara_tools.normalizers import RecordNormalizer

from pymarc import Field, Subfield, Record
from typing import List


class AuthoritiesRecordNormalizer(RecordNormalizer):
    """Normalize authorities records"""

    def __init__(
        self,
        linking_results: List[dict] = [],
        sierra_data: List[dict] = [],
        classified_fields: List[List[dict]] = [],
        ALLOW_EDIT_FIELDS: List[str] = ["008", "925"],
        REPEATABLE_FIELDS: List[str] = ["024", "035", "400", "667"],
    ):
        super().__init__(linking_results, sierra_data, classified_fields)
        self.ALLOW_EDIT_FIELDS = ALLOW_EDIT_FIELDS
        self.REPEATABLE_FIELDS = REPEATABLE_FIELDS
        self.records_extra_data = []
        self.sierra_data = sierra_data
        self.records = self._setup_records(
            linking_results, sierra_data, classified_fields
        )

    def _normalize_sierra(
        self, record: Record, sierraID: str, is_editing_existing_record: bool
    ) -> Record:
        """008 updated only for new records, unless editing where prefix is preserved."""

        suffix_008 = "|n|adnnnaabn          || |a|      "

        if is_editing_existing_record:
            # Try to reuse prefix from existing 008 field if present
            existing_008 = next(
                (f for f in record.fields if f.tag == "008" and hasattr(f, "data")),
                None,
            )
            if existing_008 and len(existing_008.data) >= 6:
                prefix = existing_008.data[:6]
            else:
                prefix = self.current_timestamp()  # fallback if missing
        else:
            prefix = self.current_timestamp()

        fields = [Field(tag="008", data=f"{prefix}{suffix_008}")]

        field_040 = Field(
            tag="040",
            indicators=EMPTY_INDICATORS,
            subfields=[
                Subfield("a", self.get_subfield(record, "040", "a", "ErESTER")),
                Subfield("b", self.get_subfield(record, "040", "b", "est")),
                Subfield("c", self.get_subfield(record, "040", "c", "ErEster")),
            ],
        )
        fields.append(field_040)

        self._add_fields_to_record(record, fields)

        return record

    def _add_birth_and_death_dates(
        self, record: Record, viaf_record: VIAFRecord
    ) -> None:
        formatted_birth_date = self._format_date(viaf_record.birth_date)
        formatted_death_date = (
            self._format_date(viaf_record.death_date)
            if viaf_record.death_date != 0
            else ""
        )

        birth_date = self.get_subfield(record, "046", "f", formatted_birth_date)
        death_date = self.get_subfield(record, "046", "g", formatted_death_date)

        if not birth_date and not death_date:
            return

        subfields_046 = [
            Subfield("f", birth_date),
            Subfield("g", death_date),
        ]

        self._add_fields_to_record(
            record,
            [Field(tag="046", indicators=EMPTY_INDICATORS, subfields=subfields_046)],
        )

    def _add_viaf_url_or_isni(self, record: Record, viaf_record: VIAFRecord) -> None:
        viaf_url = viaf_record.viaf_url

        subfields = [Subfield("0", self.get_subfield(record, "024", "0", viaf_url))]

        if viaf_record.has_isni:
            subfields.append(Subfield("2", "isni"))

        field = Field(tag="024", indicators=EMPTY_INDICATORS, subfields=subfields)

        self._add_fields_to_record(record, [field])

    def _add_nationality(self, record: Record, viaf_record: VIAFRecord) -> None:
        """Non-repeatable field 043 - adds ee only if is estonian nationality and
        the records does not have the field already."""

        is_person_est = self._is_person_est_nationality(viaf_record)

        if is_person_est:
            fields = [
                Field(
                    tag="043",
                    indicators=EMPTY_INDICATORS,
                    subfields=[Subfield("c", "ee")],
                )
            ]

            self._add_fields_to_record(record, fields)

    def _normalize_viaf(self, record: Record, viaf_record: VIAFRecord) -> None:
        """
        Attempts to enrich the record with VIAF data.

        024 - repeatable field, add VIAF URL to subfield 0. If ISNI found, add to subfield 2
        043 - repeatable field. Add "ee" if found to be estonian nationality
        046 - non-repeatable field, add birth and death dates
        100, 110, 111 - non-repeatable field, attempts to add author type, if missing.

        """
        if not viaf_record:
            return

        self._add_nationality(record, viaf_record)
        self._add_viaf_url_or_isni(record, viaf_record)
        self._add_birth_and_death_dates(record, viaf_record)
        self._add_author(record, viaf_record)

    def _normalize_record(
        self,
        record: Record,
        sierraID: str,
        viaf_record: VIAFRecord,
        is_editing_existing_record: bool,
        original_entity: str,
    ) -> Record:
        self._normalize_sierra(record, sierraID, is_editing_existing_record)
        self._normalize_viaf(record, viaf_record)

        return record
