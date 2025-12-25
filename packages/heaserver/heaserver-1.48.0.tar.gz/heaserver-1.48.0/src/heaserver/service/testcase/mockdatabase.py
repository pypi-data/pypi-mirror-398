from ..db.database import Database
from aiohttp.web import Request
from heaobject.root import DesktopObject


class MockDatabase(Database):
    async def is_creator(self, request: Request, for_type_or_type_name: str | type[DesktopObject]) -> bool:
        """
        Returns whether the current user may create new desktop objects of the given type. Always returns True.

        :param request: the HTTP request (required).
        :param for_type_or_type_name: the desktop object type or type name.
        :return: True or False.
        :raises ValueError: if an error occurred checking the registry service.
        """
        return True
