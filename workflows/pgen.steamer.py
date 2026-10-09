from maestrowf.datastructures.core import ParameterGenerator

MP = [6]
OBJECTIVE = ["heals"]
MELEE = ["true"]

def get_custom_generator(env, **kwargs):
    rows = []
    for mp in MP:
        for obj in OBJECTIVE:
            for melee in MELEE:
                rows.append((mp, obj, melee)) 

    cols = list(zip(*rows))
    params = ParameterGenerator()
    params.add_parameter("MP", list(cols[0]), label="MP.%%")
    params.add_parameter("OBJECTIVE", list(cols[1]), label="OBJ.%%")
    params.add_parameter("MELEE", list(cols[2]), label="MELEE.%%")
    return params
