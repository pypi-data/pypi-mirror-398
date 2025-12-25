from typing import List


class Tool(object):
    def __init__(
        self,
        name: bool = None,
        function: str = None,
        description: str = None,
        version: str = None,
    ):  # noqa: E501
        self._name = name
        self._function = function
        self._description = description
        self._version = version


class SubTask(object):
    def __init__(
        self,
        id: str = None,
        deleted: bool = None,
        created_time: int = None,
        created_by: str = None,
        updated_time: int = None,
        updated_by: str = None,
        name: str = None,
        tools: List[Tool] = None,
        type: str = None,
        status: str = None,
        result: str = None,
        error: str = None,
    ):  # noqa: E501
        self._id = id
        self._deleted = deleted
        self._created_time = created_time
        self._created_by = created_by
        self._updated_time = updated_time
        self._updated_by = updated_by
        self._name = name
        self._tools = tools
        self._type = type
        self._status = status
        self._result = result
        self._error = error
