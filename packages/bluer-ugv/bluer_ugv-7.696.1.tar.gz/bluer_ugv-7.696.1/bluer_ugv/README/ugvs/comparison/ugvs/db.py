from bluer_ugv.README.ugvs.comparison.features.control import UGV_Control
from bluer_ugv.README.ugvs.comparison.features.cost import UGV_Cost
from bluer_ugv.README.ugvs.comparison.features.size import UGV_Size
from bluer_ugv.README.ugvs.comparison.ugvs.classes import List_of_UGVs

list_of_ugvs = List_of_UGVs()

list_of_ugvs.add(
    nickname="arzhang",
    name="محصول ما",
    features={
        "concealment": True,
        "control": UGV_Control.AI,
        "cost": UGV_Cost.LOW,
        "payload": 40,
        "range": 10,
        "ps": True,
        "sanction_proof": True,
        "size": UGV_Size.SMALL,
        "speed": 4,
        "swarm": True,
        "uv_delivery": True,
    },
)

list_of_ugvs.add(
    nickname="nazir",
    image="nazir.jpg",
    name="ربات موشک‌انداز نذیر",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.MEDIUM,
        "payload": 700,
        "range": 4,
        "sanction_proof": True,
        "size": UGV_Size.MEDIUM,
    },
)

list_of_ugvs.add(
    nickname="heydar",
    name="ربات حیدر",
    image="heydar.jpg",
    features={
        "concealment": True,
        "control": UGV_Control.AI,
        "cost": UGV_Cost.LOW,
        "payload": 40,
        "range": 10,
        "sanction_proof": True,
        "size": UGV_Size.SMALL,
        "speed": 60,
        "swarm": True,
    },
    deficiencies=[
        "انتقال قدرت: زنجیر",
    ],
    comments=[
        "بیشترین تشابه",
    ],
)


list_of_ugvs.add(
    nickname="karakal",
    name="ربات جنگجوی هوشمند کاراکال",
    image="karakal.jpg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.MEDIUM,
        "sanction_proof": True,
        "size": UGV_Size.MEDIUM,
        "speed": 30,
        "range": 0.5,
    },
)

list_of_ugvs.add(
    nickname="qasem",
    name="ربات قاسم",
    image="qasem.jpg",
    features={
        "concealment": True,
        "cost": UGV_Cost.MEDIUM,
        "sanction_proof": True,
        "size": UGV_Size.MEDIUM,
        "uv_delivery": True,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="arya",
    name="ربات آریا",
    image="arya.jpg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.MEDIUM,
        "sanction_proof": True,
        "size": UGV_Size.MEDIUM,
        "speed": 50,
        "uv_delivery": True,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="sepah",
    name="ربات جنگ میدانی سپاه",
    features={
        "sanction_proof": True,
    },
    deficiencies=[],
)


list_of_ugvs.add(
    nickname="raad1",
    name="متلاشی‌کننده بمب و تله انفجاری رعد ۱",
    image="raad1.jpg",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.MEDIUM,
        "sanction_proof": True,
        "size": UGV_Size.SMALL,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="uran_6",
    name="Uran-6",
    image="Uran-6.jpeg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "range": 1,
        "size": UGV_Size.LARGE,
        "speed": 5,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="uran_9",
    name="Uran-9",
    image="Uran-9.jpg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "range": 1,
        "size": UGV_Size.LARGE,
        "speed": 133,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="uran_14",
    name="Uran-14",
    image="Uran-14.jpg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "payload": 2700,
        "range": 1.5,
        "size": UGV_Size.LARGE,
        "speed": 10,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="themis_9",
    name="THeMIS-9",
    image="THeMIS-9.jpeg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "payload": 1630,
        "range": 1.5,
        "size": UGV_Size.LARGE,
        "speed": 20,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="type_x",
    name="Type-X",
    image="Type-X.jpg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "payload": 4100,
        "size": UGV_Size.LARGE,
        "speed": 80,
    },
    deficiencies=[],
)


list_of_ugvs.add(
    nickname="centaur",
    name="Centaur",
    image="Centaur.jpg",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.HIGH,
        "payload": 14.5,
        "range": 0.8,
        "size": UGV_Size.MEDIUM,
        "speed": 4,
    },
    deficiencies=[],
)


list_of_ugvs.add(
    nickname="xm1219",
    name="XM1219",
    image="XM1219.jpeg",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.HIGH,
        "size": UGV_Size.LARGE,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="talon",
    name="Foster-Miller TALON",
    image="talon.jpg",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.HIGH,
        "range": 1.2,
        "size": UGV_Size.MEDIUM,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="gladiator",
    name="Gladiator TUGV",
    image="Gladiator.jpg",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.HIGH,
        "size": UGV_Size.LARGE,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="ukap",
    name="UKAP",
    image="UKAP.jpg",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.HIGH,
        "size": UGV_Size.LARGE,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="ripsaw",
    name="Ripsaw",
    image="Ripsaw.jpg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "payload": 910,
        "size": UGV_Size.LARGE,
        "speed": 105,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="teodor",
    name="tEODor",
    image="tEODor.png",
    features={
        "concealment": True,
        "control": UGV_Control.RC,
        "cost": UGV_Cost.HIGH,
        "payload": 100,
        "size": UGV_Size.MEDIUM,
        "uv_delivery": True,
    },
    deficiencies=[],
)


list_of_ugvs.add(
    nickname="black_knight",
    name="Black Knight",
    image="black_knight.jpeg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "size": UGV_Size.LARGE,
        "speed": 77,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="guardium",
    name="Guardium",
    image="Guardium.jpg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "size": UGV_Size.LARGE,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="milica",
    name="Milos & Milica",
    image="Milos.jpg",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.MEDIUM,
        "payload": 100,
        "range": 3,
        "size": UGV_Size.LARGE,
        "speed": 12.5,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="taifun_m",
    name="Taifun-M",
    image="Taifun-M.jpg",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.HIGH,
        "size": UGV_Size.LARGE,
        "uv_delivery": True,
    },
    deficiencies=[],
)


list_of_ugvs.add(
    nickname="jackal",
    name="Jackal",
    image="Jackal.jpeg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "payload": 20,
        "size": UGV_Size.MEDIUM,
        "speed": 7.2,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="avantguard",
    name="AvantGuard UGCV",
    image="avantguard.jpg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "size": UGV_Size.MEDIUM,
        "speed": 20,
    },
    deficiencies=[],
)


list_of_ugvs.add(
    nickname="sr-lambda",
    name="SIM-RACAR-Lambda",
    image="SIM-RACAR-Lambda.jpg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "payload": 45,
        "range": 1,
        "size": UGV_Size.LARGE,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="sharp_claw_1",
    name="Sharp Claw 1",
    image="Sharp-Claw-1.jpg",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.HIGH,
        "range": 6,
        "size": UGV_Size.LARGE,
        "speed": 9,
        "uv_delivery": False,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="sharp_claw_2",
    name="Sharp Claw 2",
    image="Sharp-Claw-2.jpg",
    features={
        "control": UGV_Control.RC,
        "cost": UGV_Cost.HIGH,
        "payload": 120,
        "range": 50,
        "size": UGV_Size.LARGE,
        "speed": 30,
        "uv_delivery": True,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="robattle",
    name="Robattle",
    image="Robattle.jpeg",
    features={
        "control": UGV_Control.AI,
        "cost": UGV_Cost.HIGH,
        "payload": 3000,
        "size": UGV_Size.LARGE,
    },
    deficiencies=[],
)

list_of_ugvs.add(
    nickname="template",
    name="template",
    features={
        "control": ...,
        "cost": ...,
        "payload": ...,
        "range": ...,
        "size": ...,
        "speed": ...,
        "swarm": ...,
        "uv_delivery": ...,
    },
    deficiencies=[],
)
