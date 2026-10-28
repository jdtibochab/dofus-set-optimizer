from maestrowf.datastructures.core import ParameterGenerator

ELEMENTS = ["cha"]
MP = [5, 6]
MELEE = ["true"]
EXO = ["ap:1 mp:1 vit:200 range:1", "none"] # With and without exos
INCLUSIONS = ["7754 32118 6980", "7754 32118"] # With and without vulbis

# These two are zipped together in the generator loop
HEALS = [200]
OBJECTIVE = ["elements weapon-heals"]

def get_custom_generator(env, **kwargs):
    rows = []
    for mp in MP:
            for melee in MELEE:
                for elements in ELEMENTS:
                    for exo in EXO:
                        for inclusions in INCLUSIONS:
                            for heals, obj in zip(HEALS, OBJECTIVE): # Zip these two
                                rows.append((mp, obj, melee, heals, elements, exo, inclusions))

    cols = list(zip(*rows))
    params = ParameterGenerator()
    params.add_parameter("MP", list(cols[0]), label="MP.%%")
    params.add_parameter("OBJECTIVE", list(cols[1]), label="OBJ.%%")
    params.add_parameter("MELEE", list(cols[2]), label="MELEE.%%")
    params.add_parameter("HEALS", list(cols[3]), label="HEALS.%%")
    params.add_parameter("ELEMENTS", list(cols[4]), label="ELEMENTS.%%")
    params.add_parameter("EXO", list(cols[5]), label="EXO.%%")
    params.add_parameter("INCLUSIONS", list(cols[6]), label="INCLUSIONS.%%")
    return params
