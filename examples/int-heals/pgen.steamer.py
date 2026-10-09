from maestrowf.datastructures.core import ParameterGenerator

MP = [6]
OBJECTIVE = ["elements"]
MELEE = ["true"]
HEALS = [200]

def get_custom_generator(env, **kwargs):
    rows = []
    for mp in MP:
            for melee in MELEE:
                for heals, obj in zip(HEALS, OBJECTIVE): # Zip these two
                    rows.append((mp, obj, melee, heals))

    cols = list(zip(*rows))
    params = ParameterGenerator()
    params.add_parameter("MP", list(cols[0]), label="MP.%%")
    params.add_parameter("OBJECTIVE", list(cols[1]), label="OBJ.%%")
    params.add_parameter("MELEE", list(cols[2]), label="MELEE.%%")
    params.add_parameter("HEALS", list(cols[3]), label="HEALS.%%")
    return params
