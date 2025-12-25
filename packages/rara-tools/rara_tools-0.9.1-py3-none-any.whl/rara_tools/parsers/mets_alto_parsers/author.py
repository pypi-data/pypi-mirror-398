from bs4 import Tag
from typing import List
import rara_tools.constants.meta_extractor as constants

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