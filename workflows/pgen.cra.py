from maestrowf.datastructures.core import ParameterGenerator

MP = [5]
OBJECTIVE = ["elements", "weapon"]
ELEMENTS = ["agi int", "str cha", "agi str", "str int", "agi int str cha"]

def get_custom_generator(env, **kwargs):
    rows = []
    for mp in MP:
        for obj in OBJECTIVE:
            for elem in ELEMENTS:
                rows.append((mp, obj, elem))

    cols = list(zip(*rows))
    params = ParameterGenerator()
    params.add_parameter("MP", list(cols[0]), label="MP.%%")
    params.add_parameter("OBJECTIVE", list(cols[1]), label="OBJ.%%")
    params.add_parameter("ELEMENTS", list(cols[2]), label="ELE.%%")
    return params
