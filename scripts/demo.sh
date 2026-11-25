#!/bin/bash
# Live demo: Case 1 and Case 2 across the three VMs, with a heat map.
#
# Usage (on heat-jose, from ~/heat-mpi, after `make`):
#   bash scripts/demo.sh                 # defaults: N=48, P=3, strips
#   bash scripts/demo.sh 64 5 blocks     # change N, P, decomposition
#   CASES="2" bash scripts/demo.sh       # only one case
#
# For each case it:
#   1. shows which VM every rank runs on (MPI hostname),
#   2. runs the solver across the VMs (--map-by node: P >= 3 uses all 3),
#   3. runs the serial solver and checks the output is bit-for-bit equal,
#   4. prints a heat map in the terminal and saves a PNG in results/demo/.
#
# Each step across VMs costs ~0.1 s (network latency), so T is chosen to
# keep each case under about a minute: steps = T / (r h^2).
cd "$(dirname "$0")/.." || exit 1

N=${1:-48}
P=${2:-3}
DECOMP=${3:-strips}
R=0.25
T=${T:-0.05}
CASES=${CASES:-"1 2"}
HOSTS="100.125.52.39:2,100.115.31.27:2,100.100.103.111:2"
NET="--mca oob_tcp_if_include tailscale0 --mca btl_tcp_if_include tailscale0 --mca btl tcp,self"
OUT=results/demo
mkdir -p "$OUT"

STEPS=$(python3 -c "print(round($T / ($R / ($N * $N))))")
echo "=================================================================="
echo " Demo: N=$N  P=$P  decomp=$DECOMP  r=$R  T=$T  (~$STEPS steps)"
echo " Expected time: ~$(python3 -c "print(round($STEPS * 0.1))") s per case across VMs"
echo "=================================================================="

echo
echo "--- Where the $P ranks run (--map-by node) ---"
timeout 60 mpirun --host "$HOSTS" --map-by node -np "$P" $NET hostname \
  | sort | uniq -c

for c in $CASES; do
  echo
  echo "=================== Case $c ==================="
  par=$OUT/case${c}_N${N}_P${P}_${DECOMP}.bin
  ser=$OUT/case${c}_N${N}_serial.bin

  echo "--- parallel run across the VMs ---"
  timeout 600 mpirun --host "$HOSTS" --map-by node -np "$P" $NET \
    "./heat_$DECOMP" --case "$c" --N "$N" --r "$R" --T "$T" \
    --decomp "$DECOMP" --out "$par" 2>&1 | grep -v setpgid

  echo "--- serial reference ---"
  ./heat_serial --case "$c" --N "$N" --r "$R" --T "$T" --out "$ser"

  if cmp -s "$par" "$ser"; then
    echo ">>> parallel output is bit-for-bit IDENTICAL to serial"
  else
    echo ">>> WARNING: parallel output differs from serial"
  fi

  python3 scripts/demo_heatmap.py "$par" "$N" \
    "Case $c, N=$N, P=$P ($DECOMP), T=$T" "${par%.bin}.png"
done
