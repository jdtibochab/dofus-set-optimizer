#!/bin/bash

cd /Users/jdtibochab/other/dofus-set-optimizer/workflows/..

flags=(
  "/Users/jdtibochab/other/dofus-set-optimizer/workflows/../scripts/main.py"
  "--objective" elements
  "--elements" int
  "--level" "200"
  "--level-offset" "10"
  "--ap" "12"
  "--mp" "6"
  "--vit" "3800"
  "--res-neutral" "10"
  "--res-fire" "13"
  "--res-air" "13"
  "--res-water" "13"
  "--res-earth" "13"
  "--crit" "0"
  "--range" "6"
  "--path" "/Users/jdtibochab/other/dofus-set-optimizer/workflows/report-steamer_20261008-213301/run_optimization/HEALS.200.MELEE.true.MP.6.OBJ.elements"
  "--islands" "16"
  "--max-workers" "8"
  "--language" "es"
  "--lock" "0"
  "--dodge" "0"
  "--initiative" "0"
  "--push" "0"
  "--heals" "200"
)

if [ "true" = "true" ]; then
  flags+=("--normalize-by-apcost")
fi
if [ "32121 13344" != "none" ]; then
  flags+=("--exclusions" 32121 13344)
fi
if [ "7754 6980 25222 32118" != "none" ]; then
  flags+=("--inclusions" 7754 6980 25222 32118)
fi
if [ "true" = "true" ]; then
  flags+=("--scrolled")
fi
if [ "ap:1 mp:1 vit:200 range:1" != "none" ]; then
  flags+=("--exo" ap:1 mp:1 vit:200 range:1)
fi
if [ "none" != "none" ]; then
  flags+=("--distributed-points" none)
fi
if [ "none" != "none" ]; then
  flags+=("--weapon-range" none)
fi
if [ "true" = "true" ]; then
  flags+=("--melee")
fi
if [ "true" = "true" ]; then
  flags+=("--ranged")
fi
if [ "none" != "none" ]; then
  flags+=("--reference" none)
fi

echo "Running with flags: ${flags[@]}"

python "${flags[@]}"
