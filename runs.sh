
# Sacri
python -m main \
    --keys omni crit melee \
    --exo AP MP crit \
    --objective weapon \
    --normalize-by-apcost \
    --include-items 7115 18043 \
    --reference 8993 13641 13642 14161 14162 14169 14092 14093 18718 13673 739 694 7754 737 7043 18043

python -m main \
    --keys omni crit melee \
    --exo AP MP crit \
    --objective weapon \
    --include-items 7115 18043
python -m main \
    --keys omni crit melee \
    --exo AP MP crit \
    --objective elements \
    --include-items 7115 18043
python -m main \
    --keys omni melee \
    --exo AP MP crit \
    --objective weapon \
    --include-items 7115 18043
python -m main \
    --keys omni melee \
    --exo AP MP crit \
    --objective elements \
    --include-items 7115 18043
python -m main \
    --keys str int agi crit melee \
    --exo AP MP crit \
    --normalize-by-apcost \
    --objective weapon \
    --include-items 7115 18043

# Hupper
python -m main \
    --keys omni crit \
    --exo AP MP crit \
    --normalize-by-apcost \
    --objective weapon \
    --include-items 18043
python -m main \
    --keys omni crit \
    --exo AP MP crit \
    --objective elements \
    --include-items 18043
python -m main \
    --keys omni \
    --exo AP MP crit \
    --objective elements \
    --include-items 18043

# Cra
python -m main \
    --keys omni crit ranged \
    --exo AP MP AL crit \
    --normalize-by-apcost \
    --objective weapon \
    --include-items 7115 18043 \
    --reference 17578 17579 17580 19984 19983 19985 19986 15190 18700 13673 739 13825 18043 7754 7043 694 7115