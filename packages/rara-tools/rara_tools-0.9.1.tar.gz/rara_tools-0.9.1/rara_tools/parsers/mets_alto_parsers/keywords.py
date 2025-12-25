import re
from bs4 import Tag, Comment

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