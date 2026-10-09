#!/bin/bash

cd /Users/jdtibochab/other/dofus-set-optimizer/workflows/..

flags=(
  "/Users/jdtibochab/other/dofus-set-optimizer/workflows/../main.py"
  "--objective" "steal"
  "--elements" agi
  "--level" "200"
  "--level-offset" "10"
  "--ap" "12"
  "--mp" "5"
  "--vit" "4000"
  "--res-neutral" "20"
  "--res-fire" "20"
  "--res-air" "20"
  "--res-water" "20"
  "--res-earth" "20"
  "--crit" "0"
  "--range" "0"
  "--path" "/Users/jdtibochab/other/dofus-set-optimizer/workflows/report-sacri-tank_20261007-112403/run_training"
  "--islands" "16"
  "--max-workers" "8"
  "--lock" "150"
  "--dodge" "60"
  "--initiative" "3200"
)

if [ "true" = "true" ]; then
  flags+=("--normalize-by-apcost")
fi
if [ "32121 20354" != "none" ]; then
  flags+=("--exclusions" 32121 20354)
fi
if [ "7754 7115 18043 24034 20366" != "none" ]; then
  flags+=("--inclusions" 7754 7115 18043 24034 20366)
fi
if [ "true" = "true" ]; then
  flags+=("--scrolled")
fi
if [ "ap:1 mp:1 vit:200" != "none" ]; then
  flags+=("--exo" ap:1 mp:1 vit:200)
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
if [ "false" = "true" ]; then
  flags+=("--ranged")
fi
if [ "17581 13124 17582 15692 19979 20366 694 7115 7754 18043 25220 24034 19980 13765 12714 33166" != "none" ]; then
  flags+=("--reference" 17581 13124 17582 15692 19979 20366 694 7115 7754 18043 25220 24034 19980 13765 12714 33166)
fi

echo "Running with flags: ${flags[@]}"

python "${flags[@]}"
