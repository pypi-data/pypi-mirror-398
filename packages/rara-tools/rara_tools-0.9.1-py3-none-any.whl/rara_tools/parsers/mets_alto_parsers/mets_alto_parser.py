from bs4 import BeautifulSoup, Tag, Comment
from typing import List
from rara_tools.parsers.mets_alto_parsers.author import AuthorInfo
from rara_tools.parsers.mets_alto_parsers.title import TitleInfo
from rara_tools.parsers.mets_alto_parsers.keywords import KeywordInfo

import rara_tools.constants.meta_extractor as constants
import re


class SectionXMLMeta:
    """ Instance for parsing mets.xml sections.
    """

    def __init__(self, section_xml: str):
        self.soup = BeautifulSoup(section_xml, "lxml-xml")

        self.__title_tags: List[Tag] = []
        self.__author_tags: List[Tag] = []
        self.__subject_tags: List[Tag] = []

        self.__titles: List[TitleInfo] = []
        self.__merged_titles: List[TitleInfo] = []
        self.__authors: List[AuthorInfo] = []
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
    def titles(self) -> List[TitleInfo]:
        if not self.__titles:
            self.__titles = [
                TitleInfo(tag) for tag in self.title_tags
            ]
        return self.__titles

    @property
    def merged_titles(self) -> List[TitleInfo]:
        if not self.__merged_titles:
            # Merge section titles into one.
            merged_title = SectionXMLMeta.merge_titles(self.titles)

            # Force output into list.
            self.__merged_titles = [merged_title]
        return self.__merged_titles

    @property
    def authors(self) -> List[AuthorInfo]:
        if not self.__authors:
            self.__authors = [
                AuthorInfo(tag) for tag in self.author_tags
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

    @staticmethod
    def merge_titles(titles: List[TitleInfo]) -> TitleInfo:
        """ Merge a list of titles into one. Necessary for sections where
        a single article title is split between multiple tags.

        Parameters
        -----------
        titles: List[TitleInfo]
            List of TitleInfo objects.

        Returns
        -----------
        TitleInfo:
            Merged TitleInfo object.
        """
        merged_title_object = TitleInfo()

        if titles:
            title_list = [title.title for title in titles if title.title]
            new_title = " ".join(title_list)

            # Take first part number, language and ID
            part_number = titles[0].part_number
            language = titles[0].language
            id = titles[0].id

            # Set values for merged TitleInfo object
            merged_title_object.title = new_title
            merged_title_object.language = language
            merged_title_object.id = id
            merged_title_object.part_number = part_number
        return merged_title_object

    def to_dict(self) -> dict:
        output = {
            "titles": [title.to_dict() for title in self.titles],
            "merged_titles": [title.to_dict() for title in self.merged_titles],
            "authors": [author.to_dict() for author in self.authors],
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
    def section_id(self) -> str:
        return self.section.get("section_id", "")

    @property
    def keywords(self) -> List[str]:
        return self.section_xml_meta.keywords

    @property
    def authors(self) -> List[AuthorInfo]:
        return self.section_xml_meta.authors

    @property
    def titles(self) -> List[TitleInfo]:
        return self.section_xml_meta.titles

    @property
    def merged_titles(self) -> List[TitleInfo]:
        return self.section_xml_meta.merged_titles

    @property
    def language(self) -> str:
        return self.section_xml_meta.language

    def to_dict(self) -> dict:
        output = {
            "titles": [title.to_dict() for title in self.titles],
            "merged_titles": [title.to_dict() for title in self.merged_titles],
            "authors": [author.to_dict() for author in self.authors],
            "language": self.language,
            "keywords": self.keywords,
            "article_id": self.article_id,
            "unique_id": self.unique_id,
            "sequence_nr": self.sequence_number,
            "section_id": self.section_id
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
        self.__title: TitleInfo = {}
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
    def genres(self) -> List[str]:
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
    def title(self) -> TitleInfo:
        if not self.__title:
            self.__title = TitleInfo(self.soup.titleInfo)
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
            "title": self.title.to_dict()
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
            titles: List[TitleInfo] = []

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
            doc_meta["title"] = DocumentMeta.select_title(titles)
            self.__document_meta = doc_meta
        return self.__document_meta

    @staticmethod
    def select_title(titles: List[TitleInfo]) -> dict:
        """ Select a title batch with
        a) most likely to be the title of the whole document and
        b) containing as much information as possible.
        """
        selected_title = {}
        if titles:
            earliest = {}
            with_part_number = {}
            for title in titles:
                if title.title and not earliest:
                    earliest = title.to_dict()
                if title.part_number and title.title:
                    with_part_number = title.to_dict()
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
            "sections": [
                section.to_dict()
                for section in self.sections_meta
            ]
        }
        output.update(self.document_meta)
        return output
