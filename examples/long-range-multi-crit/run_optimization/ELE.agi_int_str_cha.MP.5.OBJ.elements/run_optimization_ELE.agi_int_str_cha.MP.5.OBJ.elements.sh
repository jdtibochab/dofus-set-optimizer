#!/bin/bash

cd /Users/jdtibochab/other/dofus-set-optimizer/workflows/..

flags=(
  "/Users/jdtibochab/other/dofus-set-optimizer/workflows/../scripts/main.py"
  "--objective" elements
  "--elements" agi int str cha
  "--level" "200"
  "--level-offset" "10"
  "--ap" "12"
  "--mp" "5"
  "--vit" "3800"
  "--res-neutral" "10"
  "--res-fire" "13"
  "--res-air" "13"
  "--res-water" "13"
  "--res-earth" "13"
  "--crit" "87"
  "--range" "6"
  "--path" "/Users/jdtibochab/other/dofus-set-optimizer/workflows/report-cra_20261008-175406/run_optimization/ELE.agi_int_str_cha.MP.5.OBJ.elements"
  "--islands" "16"
  "--max-workers" "8"
  "--language" "es"
  "--lock" "0"
  "--dodge" "0"
  "--initiative" "0"
  "--push" "0"
)

if [ "true" = "true" ]; then
  flags+=("--normalize-by-apcost")
fi
if [ "32121 13344" != "none" ]; then
  flags+=("--exclusions" 32121 13344)
fi
if [ "7754 18043 739" != "none" ]; then
  flags+=("--inclusions" 7754 18043 739)
fi
if [ "true" = "true" ]; then
  flags+=("--scrolled")
fi
if [ "ap:1 mp:1 crit:2 vit:200 range:1" != "none" ]; then
  flags+=("--exo" ap:1 mp:1 crit:2 vit:200 range:1)
fi
if [ "none" != "none" ]; then
  flags+=("--distributed-points" none)
fi
if [ "6" != "none" ]; then
  flags+=("--weapon-range" 6)
fi
if [ "false" = "true" ]; then
  flags+=("--melee")
fi
if [ "true" = "true" ]; then
  flags+=("--ranged")
fi
if [ "17578 17579 17580 19984 19983 19985 19986 15190 18700 13673 739 13825 18043 7754 7043 694 7115" != "none" ]; then
  flags+=("--reference" 17578 17579 17580 19984 19983 19985 19986 15190 18700 13673 739 13825 18043 7754 7043 694 7115)
fi

echo "Running with flags: ${flags[@]}"

python "${flags[@]}"
