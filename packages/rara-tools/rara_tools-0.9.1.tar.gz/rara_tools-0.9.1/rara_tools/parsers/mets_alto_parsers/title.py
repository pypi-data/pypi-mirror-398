from typing import List

from bs4 import Tag



class TitleInfo:
    """ For extracting information from title tags (tag level = "titleInfo")
    """
    def __init__(self, tag: Tag | None = None):
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


    @title.setter
    def title(self, value: str):
        self.__title = value

    @language.setter
    def language(self, value: str):
        self.__language = value

    @part_number.setter
    def part_number(self, value: str):
        self.__part_number = value

    @id.setter
    def id(self, value: str):
        self.__id = value

    def to_dict(self) -> dict:
        output = {
            "title": self.title,
            "language": self.language,
            "id": self.id,
            "part_number": self.part_number
        }
        return output
