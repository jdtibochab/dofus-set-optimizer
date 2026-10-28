from maestrowf.datastructures.core import ParameterGenerator

MP = [5, 6]
EXO = ["ap:1 mp:1 vit:200 range:1", "none"] # With and without exos
INCLUSIONS = ["7754 32235 6980", "7754 32235"] # With and without vulbis

def get_custom_generator(env, **kwargs):
    rows = []
    for mp in MP:
        for exo in EXO:
            for inclusions in INCLUSIONS:
                rows.append((mp, exo, inclusions))

    cols = list(zip(*rows))
    params = ParameterGenerator()
    params.add_parameter("MP", list(cols[0]), label="MP.%%")
    params.add_parameter("EXO", list(cols[1]), label="EXO.%%")
    params.add_parameter("INCLUSIONS", list(cols[2]), label="INCLUSIONS.%%")
    return params
