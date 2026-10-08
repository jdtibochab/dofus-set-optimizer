from maestrowf.datastructures.core import ParameterGenerator

MP = [5, 6]
OBJECTIVE = ["elements push", "elements"]
MELEE = ["true"]
PUSH = [0, 400]

def get_custom_generator(env, **kwargs):
    rows = []
    for mp in MP:
        for obj in OBJECTIVE:
            for melee in MELEE:
                for push in PUSH:
                    rows.append((mp, obj, melee, push))

    cols = list(zip(*rows))
    params = ParameterGenerator()
    params.add_parameter("MP", list(cols[0]), label="MP.%%")
    params.add_parameter("OBJECTIVE", list(cols[1]), label="OBJ.%%")
    params.add_parameter("MELEE", list(cols[2]), label="MELEE.%%")
    params.add_parameter("PUSH", list(cols[3]), label="PUSH.%%")
    return params
