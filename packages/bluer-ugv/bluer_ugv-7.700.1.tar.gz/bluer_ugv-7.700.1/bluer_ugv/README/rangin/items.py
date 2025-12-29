from bluer_objects.README.items import ImageItems

from bluer_ugv.README.rangin.consts import rangin_assets2
from bluer_ugv.README.ugvs.db import dict_of_ugvs

items = ImageItems(
    {
        **{
            f"{rangin_assets2}/concepts/11.png": "",
            f"{rangin_assets2}/concepts/12.png": "",
        },
        **{url: "" for url in dict_of_ugvs["rangin"]["items"]},
    }
)
