from maestrowf.datastructures.core import ParameterGenerator

MP = [5, 6]
OBJECTIVE = ["elements", "elements push", "weapon"]

def get_custom_generator(env, **kwargs):
    rows = []
    for mp in MP:
        for obj in OBJECTIVE:
            rows.append((mp, obj))

    cols = list(zip(*rows))
    params = ParameterGenerator()
    params.add_parameter("MP", list(cols[0]), label="MP.%%")
    params.add_parameter("OBJECTIVE", list(cols[1]), label="OBJ.%%")
    return params
