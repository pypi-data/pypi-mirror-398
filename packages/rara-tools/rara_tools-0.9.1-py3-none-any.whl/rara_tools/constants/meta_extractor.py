from dataclasses import dataclass

COMPONENT_KEY = "meta_extractor"


class Tasks:
    SINGLE = "extract_meta_from_text"
    PIPELINE = "run_meta_extractor_with_core_logic"


class Queue:
    MAIN = "meta_extractor"


class StatusKeys:
    EXTRACT_METADATA = "extract_metadata"

class Error:
    UNKNOWN = "Failed to extract meta information from digitizer output!"


@dataclass(frozen=True)
class TitleType:
    AUTHOR_WITHOUT_TITLE: str = "pealkirjata autor"
    NORMALIZED_TITLE: str = "normitud eelispealkiri"
    TITLE: str = "väljaandes esitatud kujul põhipealkiri"
    PARALLEL_TITLE: str = "rööppealkiri"
    ADDITIONAL_TITLE: str = "alampealkiri"
    METS_TITLE: str = "väljaandes esitatud kujul põhipealkiri"
    ANON: str = "anonüümne väljaanne"

@dataclass(frozen=True)
class IssueType:
    NEWSPAPER: str = "Ajaleht"
    JOURNAL: str = "Ajakiri"
    PERIODICAL: str = "Jätkväljaanne"
    BOOK: str = "Raamat"

@dataclass(frozen=True)
class AuthorField:
    AUTHOR: str = "author"
    UNKNOWN: str = "Teadmata"

ISSUE_STYLE_MAP = {
    "newspaper": IssueType.NEWSPAPER,
    "ajalehed": IssueType.NEWSPAPER,
    "journal": IssueType.JOURNAL,
    "ajakirjad": IssueType.JOURNAL,
    "periodical": IssueType.PERIODICAL,
    "jätkväljanded": IssueType.PERIODICAL,
    "books": IssueType.BOOK,
    "raamatud": IssueType.BOOK
}

TITLE_TYPES_MAP = {
    TitleType.AUTHOR_WITHOUT_TITLE: 130,
    TitleType.NORMALIZED_TITLE: 240,
    TitleType.TITLE: 245,
    TitleType.PARALLEL_TITLE: 246,
    TitleType.ADDITIONAL_TITLE: 245,
    TitleType.METS_TITLE: 245,
    TitleType.ANON: 130
}

AUTHOR_ROLES_MAP = {
  "egr": "Graveerija",
  "ccp": "Idee autor",
  "win": "Sissejuhatuse autor",
  "ltg": "Litograaf",
  "org": "Käsikirja autor",
  "mfr": "Väljaandja",
  "cmp": "Helilooja",
  "trl": "Tõlkija",
  "pbl": "Kirjastaja",
  "ivr": "Intervjueerija",
  "ill": "Illustreerija",
  "abr": "Konspekteerija",
  "dto": "Dedikatsiooni autor",
  "cns": "Tsensor",
  "wfw": "Eessõna (järelsõna) auto",
  "art": "Kunstnik",
  "rpt": "Reporter",
  "ive": "Intervjueeritav",
  "sgn": "Sissekirjutuse autor",
  "pdr": "Projektijuht",
  "own": "Omanik",
  "lbt": "Libretist",
  "dte": "Dedikatsiooni saaja",
  "aut": "Autor",
  "cur": "Kuraator",
  "ths": "Juhendaja",
  "pfr": "Korrektor",
  "lyr": "Sõnade autor",
  "prf": "Esitaja",
  "wat": "Teksti autor",
  "aus": "Stsenarist",
  "cmm": "Kommenteerija",
  "bsl": "Raamatukaupmees",
  "ctg": "Kartograaf",
  "red": "Redaktor",
  "scr": "Ümberkirjutaja",
  "sad": "Konsultant",
  "dpc": "Portreteeritav",
  "opn": "Oponent",
  "pht": "Fotograaf",
  "rsp": "Respondent",
  "edt": "Toimetaja",
  "dsr": "Levitaja",
  "bkp": "Tootja",
  "translator": "Tõlkija"
}

PUBLISHER_KEY = "Väljaandja"