
# Sacri
python -m main --keys omni crit melee --exo AP MP crit
python -m main --keys omni melee --exo AP MP crit
python -m main --keys omni melee --exo AP MP crit --objective elements

# Hyper
python -m main --keys omni crit --exo AP MP crit --normalize-by-apcost
python -m main --keys omni crit --exo AP MP crit --objective elements
python -m main --keys omni --exo AP MP crit --objective elements

# Cra
python -m main --keys omni crit ranged --exo AP MP AL crit --normalize-by-apcost