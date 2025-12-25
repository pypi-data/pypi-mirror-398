from bs4 import BeautifulSoup, Tag, Comment
from typing import List
import rara_tools.constants.meta_extractor as constants
import re


class TitleInfo:
    """ For extracting information from title tags (tag level = "titleInfo")
    """
    def __init__(self, tag: Tag):
        self.tag: Tag = tag

        self.__title: str = ""
        self.__language: str = ""
        self.__part_number: str = ""
        self.__id: str = ""

        self.__non_sort: str = ""
        self.__title_main: str = ""

    @property
    def title_main(self) -> str:
        if not self.__title_main:
            try:
                self.__title_main = self.tag.title.string
            except:
                pass
        return self.__title_main

    @property
    def non_sort(self) -> str:
        if not self.__non_sort:
            try:
                self.__non_sort = self.tag.nonSort.string
            except:
                pass
        return self.__non_sort

    @property
    def title(self) -> str:
        if not self.__title:
            # Add non-sort words (articles etc) to the title,
            # if they are present
            if self.non_sort:
                self.__title = f"{self.non_sort} {self.title_main}"
            else:
                self.__title = self.title_main
        return self.__title

    @property
    def part_number(self):
        if not self.__part_number:
            try:
                self.__part_number = self.tag.partNumber.string
            except Exception as e:
                pass
        return self.__part_number

    @property
    def language(self) -> str:
        if not self.__language:
            try:
                self.__language = self.tag.attrs.get("xml:lang")
            except:
                pass
        return self.__language

    @property
    def id(self) -> str:
        if not self.__id:
            try:
                self.__id = self.tag.attrs.get("ID")
            except:
                pass
        return self.__id

    def to_dict(self) -> dict:

        output = {
            "title": self.title,
            # "non_sort": self.non_sort,
            "language": self.language,
            "id": self.id,
            "part_number": self.part_number
        }
        return output


class AuthorInfo:
    """ For extracting information from author tags (tag level = "name")
    """
    def __init__(self, tag: Tag, author_roles_map: dict = constants.AUTHOR_ROLES_MAP):
        self.tag: Tag = tag

        self.author_roles_map: dict = author_roles_map

        self.__name_part_tags: List[Tag] = []

        self.__first_name: str = ""
        self.__last_name: str = ""
        self.__role: str = ""
        self.__id: str = ""
        self.__type: str = ""

    @property
    def name_part_tags(self) -> List[Tag]:
        if not self.__name_part_tags:
            self.__name_part_tags = [
                tag for tag in self.tag.find_all("namePart")
            ]
        return self.__name_part_tags

    @property
    def first_name(self) -> str:
        if not self.__first_name:
            try:
                self.__first_name = [
                    tag.string for tag in self.name_part_tags
                    if tag.attrs.get("type") == "given"
                ][0]
            except:
                pass
        return self.__first_name

    @property
    def last_name(self) -> str:
        if not self.__last_name:
            try:
                self.__last_name = [
                    tag.string for tag in self.name_part_tags
                    if tag.attrs.get("type") == "family"
                ][0]
            except:
                pass
        return self.__last_name

    @property
    def id(self) -> str:
        if not self.__id:
            try:
                self.__id = self.tag.attrs.get("ID")
            except:
                pass
        return self.__id

    @property
    def type(self) -> str:
        if not self.__type:
            try:
                self.__type = self.tag.attrs.get("type")
            except:
                pass
        return self.__type

    @property
    def role(self) -> str:
        if not self.__role:
            try:
                role = self.tag.role.roleTerm.string
                self.__role = self._map_role(role)
            except:
                pass
        return self.__role

    def _map_role(self, role: str) -> str:
        """ Maps the role extracted from mets.xml
        with a supported role in taxonomy.
        """
        role = self.author_roles_map.get(role, constants.AuthorField.UNKNOWN)
        return role

    def to_dict(self) -> dict:
        output = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "id": self.id,
            "type": self.type,
            "role": self.role
        }
        return output


class KeywordInfo:
    """ For extracting information from keyword tags (tag level = "subject").
    """

    def __init__(self, tag: Tag):
        self.tag: Tag = tag

        self.__keyword: str = ""
        self.__ems_id: str = ""

        self.__comment: str = ""

    @property
    def comment(self) -> str | None:
        if not self.__comment:
            self.__comment = self.tag.find(string=lambda t: isinstance(t, Comment))
        return self.__comment

    @property
    def keyword(self) -> str:
        if not self.__keyword:
            self.__keyword = self.tag.topic.string
        return self.__keyword

    @property
    def ems_id(self) -> str:
        if not self.__ems_id:
            if self.comment:
                matches = re.search(r"EMS\S+(?=\s)", self.comment)
                if matches:
                    self.__ems_id = matches.group()
        return self.__ems_id

    def to_dict(self) -> dict:
        output = {
            "keyword": self.keyword,
            "ems_id": self.ems_id
        }
        return output


class SectionXMLMeta:
    """ Instance for parsing mets.xml sections.
    """

    def __init__(self, section_xml: str):
        self.soup = BeautifulSoup(section_xml, "lxml-xml")

        self.__title_tags: List[Tag] = []
        self.__author_tags: List[Tag] = []
        self.__subject_tags: List[Tag] = []

        self.__titles: List[dict] = []
        self.__authors: List[dict] = []
        self.__keywords: List[str] = []
        self.__keywords_tags: List[dict] = []
        self.__language: str = ""

    # ---------------------------------------------------------- #
    # Tags
    # ---------------------------------------------------------- #

    @property
    def title_tags(self) -> List[Tag]:
        if not self.__title_tags:
            self.__title_tags = [
                tag for tag in self.soup.find_all("titleInfo")
            ]
        return self.__title_tags

    @property
    def author_tags(self) -> List[Tag]:
        if not self.__author_tags:
            self.__author_tags = [
                tag for tag in self.soup.find_all("name")
            ]
        return self.__author_tags

    @property
    def subject_tags(self) -> List[Tag]:
        if not self.__subject_tags:
            self.__subject_tags = [
                tag for tag in self.soup.find_all("subject")
            ]
        return self.__subject_tags

    # ---------------------------------------------------------- #
    # Parsed information
    # ---------------------------------------------------------- #
    @property
    def titles(self) -> List[dict]:
        if not self.__titles:
            self.__titles = [
                TitleInfo(tag).to_dict() for tag in self.title_tags
            ]
        return self.__titles

    @property
    def authors(self) -> List[dict]:
        if not self.__authors:
            self.__authors = [
                AuthorInfo(tag).to_dict() for tag in self.author_tags
            ]
        return self.__authors

    @property
    def language(self) -> str:
        if not self.__language:
            try:
                self.__language = self.soup.language.languageTerm.string
            except:
                pass
        return self.__language

    @property
    def keywords_with_ems_id(self) -> List[dict]:
        if not self.__keywords_with_ems_id:
            self.__keywords_with_ems_id = [
                KeywordInfo(tag).to_dict() for tag in self.subject_tags
            ]
        return self.__keywords_with_ems_id

    @property
    def keywords(self) -> List[str]:
        if not self.__keywords:
            self.__keywords = [
                KeywordInfo(tag).keyword for tag in self.subject_tags
            ]
        return self.__keywords

    def to_dict(self) -> dict:
        output = {
            "titles": self.titles,
            "authors": self.authors,
            "language": self.language,
            "keywords": self.keywords
        }
        return output


class SectionMeta:
    """ Instance for parsing and handling section dicts (`texts`) in `digitizer_output`.
    """

    def __init__(self, section: dict):
        self.section: dict = section
        self.section_xml_meta: SectionXMLMeta = SectionXMLMeta(self.section_xml)

    @property
    def section_xml(self) -> str:
        _section_xml = self.section.get("section_meta")

        # Make sure section_xml is not None as XML parser
        # will break otherwise
        if not _section_xml:
            _section_xml = ""
        return _section_xml

    @property
    def article_id(self) -> str:
        return self.section.get("article_id", "")

    @property
    def unique_id(self) -> str:
        return self.section.get("unique_id", "")

    @property
    def sequence_number(self) -> str:
        return self.section.get("sequence_nr", "")

    @property
    def keywords(self) -> List[str]:
        return self.section_xml_meta.keywords

    @property
    def authors(self) -> List[dict]:
        return self.section_xml_meta.authors

    @property
    def titles(self) -> List[dict]:
        return self.section_xml_meta.titles

    @property
    def language(self) -> str:
        return self.section_xml_meta.language

    def to_dict(self) -> dict:
        output = {
            "titles": self.titles,
            "authors": self.authors,
            "language": self.language,
            "keywords": self.keywords,
            "article_id": self.article_id,
            "unique_id": self.unique_id,
            "sequence_nr": self.sequence_number
        }
        return output


class DocumentIdentifier:
    def __init__(self, identifier: Tag):
        self.identifier: Tag = identifier

        self.value = identifier.string
        self.type = identifier.attrs.get("type", "unknown")

    def to_dict(self) -> dict:
        output = {
            "value": self.value,
            "type": self.type
        }
        return output


class DocumentMetaXML:
    """ Instance for parsing document level meta from XML.
    """

    def __init__(self, document_xml: str, issue_style_map: dict = constants.ISSUE_STYLE_MAP):
        self.document_xml: str = document_xml
        self.soup = BeautifulSoup(document_xml, "lxml-xml")

        self.issue_style_map: dict = issue_style_map

        # Needed subitems from METS ALTO meta fields
        # (don't want separate metadata for pictures, chapters/articles)
        self.relevant_subitems: List[str] = ["PRINT", "ELEC", "ISSUE"]

        # Dates
        self.__publication_date: str = ""
        self.__copyright_date: str = ""

        # Identifiers
        self.__issn: str = ""
        self.__isbn: str = ""
        self.__ester_id: str = ""
        self.__id: str = ""
        self.__local_id: str = ""

        self.__resource_type: str = ""
        self.__genres: List[str] = []
        self.__frequency: str = ""

        self.__identifiers: List[DocumentIdentifier] = []

        ### title ?
        # self.__part_number: str = ""
        self.__title: dict = {}
        self.__issue_style: str = ""

    @property
    def publication_date(self) -> str:
        if not self.__publication_date:
            try:
                self.__publication_date = self.soup.dateIssued.string
            except:
                pass
        return self.__publication_date

    @property
    def copyright_date(self) -> str:
        if not self.__copyright_date:
            try:
                self.__copyright_date = self.soup.copyrightDate.string
            except:
                pass
        return self.__copyright_date

    @property
    def identifiers(self) -> List[DocumentIdentifier]:
        if not self.__identifiers:
            identifiers = self.soup.find_all("identifier")
            for identifier in identifiers:
                new_identifier = DocumentIdentifier(identifier)
                self.__identifiers.append(new_identifier)

        return self.__identifiers

    @property
    def issn(self) -> str:
        # TODO: List???
        if not self.__issn:
            raw_issn = self._get_identifier_value("issn")
            self.__issn = self._normalize_issn(raw_issn)
        return self.__issn

    @property
    def isbn(self) -> str:
        # TODO: List???
        if not self.__isbn:
            self.__isbn = self._get_identifier_value("isbn")
        return self.__isbn

    @property
    def ester_id(self) -> str:
        if not self.__ester_id:
            self.__ester_id = self._get_identifier_value("CatalogueIdentifier")
        return self.__ester_id

    @property
    def id(self) -> str:
        if not self.__id:
            self.__id = ""
        pass

    @property
    def local_id(self) -> str:
        if not self.__local_id:
            self.__local_id = self._get_identifier_value("local")
        return self.__local_id

    @property
    def resource_type(self) -> str:
        if not self.__resource_type:
            try:
                self.__resource_type = self.soup.typeOfResource.string
            except:
                pass
        return self.__resource_type

    @property
    def genres(self) -> str:
        """ Contains stuff like "newspaper", "periodical" - not actual genres (?)
        """
        if not self.__genres:
            try:
                genres = self.soup.find_all("genre")
                self.__genres = [
                    genre.string for genre in genres
                    if genre.string != "\n"
                ]
            except:
                pass
        return self.__genres

    @property
    def frequency(self) -> str:
        """ Used for issue type detection, contains information like
        "Local newspaper"
        """
        if not self.__frequency:
            try:
                self.__frequency = self.soup.frequency.string
            except:
                pass
        return self.__frequency

    @property
    def issue_style(self) -> str:
        if not self.__issue_style:
            original = None

            if self.genres:
                original = self.genres[0]
            elif self.frequency:
                original = self.frequency

            if original:
                options = self.issue_style_map.keys()
                pattern = r"|".join(options)
                match = re.search(pattern, original, re.IGNORECASE)
                if match:
                    key = match.group()
                    self.__issue_style = self.issue_style_map.get(key, "")
        return self.__issue_style

    @property
    def title(self) -> dict:
        if not self.__title:
            self.__title = TitleInfo(self.soup.titleInfo).to_dict()
        return self.__title

    def _get_identifier_value(self, identifier_type: str) -> str:
        # TODO: Or output a list???
        value = ""
        for identifier in self.identifiers:
            if identifier.type == identifier_type:
                value = identifier.value
                break
        return value

    def _normalize_issn(self, issn: str) -> str:
        issn = issn.replace("-", "")
        return issn

    def to_dict(self) -> dict:
        output = {
            "publication_date": self.publication_date,
            "copyright_date": self.copyright_date,
            "issn": self.issn,
            "isbn": self.isbn,
            "ester_id": self.ester_id,
            "id": self.id,
            "local_id": self.local_id,
            "resource_type": self.resource_type,
            "issue_type": self.issue_style,
            "title": self.title
        }
        return output


class DocumentMeta:
    """ Parses METS/ALTO metadata from `digitizer_outputs`.
    """
    def __init__(self, digitizer_output: dict):
        self.digitizer_output: dict = digitizer_output

        self.__document_xmls: List[str] = []
        self.__sections: List[dict] = []
        self.__sections_meta: List[SectionMeta] = []
        self.__document_meta: dict = {}

    @property
    def document_xmls(self) -> List[str]:
        if not self.__document_xmls:
            self.__document_xmls = self.digitizer_output.get(
                "doc_meta", {}
            ).get("mets_alto_metadata", "")
        return self.__document_xmls

    @property
    def sections(self) -> List[str]:
        if not self.__sections:
            self.__sections = self.digitizer_output.get("texts", [])
        return self.__sections

    @property
    def sections_meta(self) -> List[SectionMeta]:
        if not self.__sections_meta:
            self.__sections_meta = [
                SectionMeta(section)
                for section in self.sections
            ]
        return self.__sections_meta

    @property
    def document_meta(self) -> dict:
        if not self.__document_meta:
            doc_meta = {}
            titles = []

            for document_xml in self.document_xmls:
                doc_meta_i = DocumentMetaXML(document_xml)
                titles.append(doc_meta_i.title)
                if not doc_meta:
                    doc_meta.update(doc_meta_i.to_dict())
                else:
                    # Add values only, if they haven`t already been added
                    for key, value in doc_meta_i.to_dict().items():
                        if not doc_meta[key]:
                            doc_meta[key] = value
            # Select title batch with most info
            doc_meta["title"] = self._select_title(titles)
            self.__document_meta = doc_meta
        return self.__document_meta

    def _select_title(self, titles: List[dict]) -> dict:
        """ Select a title batch with
        a) most likely to be the title of the whole document and
        b) containing as much information as possible.
        """
        selected_title = {}
        if titles:
            earliest = {}
            with_part_number = {}
            for title in titles:
                if title.get("title") and not earliest:
                    earliest = title
                if title.get("part_number") and title.get("title"):
                    with_part_number = title
                    break
            if with_part_number:
                # If a title with part number was detected,
                # use this one
                selected_title = with_part_number
            else:
                # otherwise, use the earliest title
                # with existing value
                selected_title = earliest
        return selected_title


    def to_dict(self) -> dict:
        output = {
            "sections": [section.to_dict() for section in self.sections_meta]
        }
        output.update(self.document_meta)
        return output
