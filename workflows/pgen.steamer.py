from maestrowf.datastructures.core import ParameterGenerator

ELEMENTS = ["cha", "int"]
MP = [6]
MELEE = ["true"]

# These two are zipped together in the generator loop
HEALS = [200, 200]
OBJECTIVE = ["elements", "elements weapon-heals"]

def get_custom_generator(env, **kwargs):
    rows = []
    for mp in MP:
            for melee in MELEE:
                for elements in ELEMENTS:
                    for heals, obj in zip(HEALS, OBJECTIVE): # Zip these two
                        rows.append((mp, obj, melee, heals, elements))

    cols = list(zip(*rows))
    params = ParameterGenerator()
    params.add_parameter("MP", list(cols[0]), label="MP.%%")
    params.add_parameter("OBJECTIVE", list(cols[1]), label="OBJ.%%")
    params.add_parameter("MELEE", list(cols[2]), label="MELEE.%%")
    params.add_parameter("HEALS", list(cols[3]), label="HEALS.%%")
    params.add_parameter("ELEMENTS", list(cols[4]), label="ELEMENTS.%%")
    return params
