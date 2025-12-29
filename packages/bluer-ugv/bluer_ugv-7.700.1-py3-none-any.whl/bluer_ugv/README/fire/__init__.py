from bluer_sbc.parts.db import db_of_parts
from bluer_sbc.parts.consts import parts_url_prefix

from bluer_ugv.README.fire.items import items
from bluer_ugv.designs.fire.parts import dict_of_parts

docs = [
    {
        "path": "../docs/fire",
        "items": items,
    },
    {
        "path": "../docs/fire/parts.md",
        "items": db_of_parts.as_images(
            dict_of_parts,
            reference=parts_url_prefix,
        ),
        "macros": {
            "parts:::": db_of_parts.as_list(
                dict_of_parts,
                reference=parts_url_prefix,
                log=False,
            ),
        },
    },
]
