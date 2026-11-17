#!/bin/bash
# Fetch the bench matches: the IDSSE open dataset (DFL, Bundesliga 2022/23; Bassek et al. 2025,
# Scientific Data, CC-BY 4.0), PySport mirror on Hugging Face. About 2.5 GB.
#
#   bench_data/download.sh ~/dfl_idsse
#
# The target folder must be OUTSIDE the repository; nothing downloaded here is ever committed.
set -eu
target=${1:?usage: bench_data/download.sh <folder outside the repository>}
mkdir -p "$target" && cd "$target"
base=https://huggingface.co/datasets/pysport/idsse-data/resolve/main
for entry in J03WMX:000001 J03WN1:000001 J03WOH:000002 J03WOY:000002 J03WPY:000002 \
             J03WQQ:000002 J03WR9:000002; do
  id=${entry%%:*}; com=${entry##*:}
  (
    curl -fsSL --retry 5 -o "$id.meta.xml" \
      "$base/DFL_02_01_matchinformation_DFL-COM-${com}_DFL-MAT-$id.xml"
    curl -fsSL --retry 5 -o "$id.tracking.xml" \
      "$base/DFL_04_03_positions_raw_observed_DFL-COM-${com}_DFL-MAT-$id.xml"
    echo "$id done"
  ) &
done
wait
