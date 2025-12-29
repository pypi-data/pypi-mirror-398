from typing import List


class Reference:
    def __init__(
        self,
        title: str,
        url: str,
        list_of_ugvs: List[str] = [],
        is_in_farsi: bool = False,
    ):
        self.title = title
        self.url = url
        self.list_of_ugvs = list_of_ugvs
        self.is_in_farsi = is_in_farsi


class List_of_References:
    def __init__(self):
        self.db: List[Reference] = []

    def add(
        self,
        **kw_args,
    ):
        ugv = Reference(**kw_args)
        self.db.append(ugv)
