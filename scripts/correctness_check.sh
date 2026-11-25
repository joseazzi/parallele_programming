#!/bin/bash
# Correctness evidence (deliverable 3): run serial, strips and blocks for
# several N and P and compare the output field files.
#
# Part A - one VM (one architecture): outputs must be bit-for-bit
#          identical to serial (checked with cmp). Uses --oversubscribe
#          for P > 2 because each VM has 2 vCPUs (fine for correctness,
#          not for timing).
# Part B - the mixed ARM64 / x86-64 cluster (Jose, Dia, Theresa): same
#          check across the three VMs, plus the largest difference.
#
# Usage (from ~/heat-mpi on heat-jose, after `make`):
#   bash scripts/correctness_check.sh            # Part A only
#   CLUSTER=1 bash scripts/correctness_check.sh  # Part A and Part B
# Output is printed and saved to results/correctness/correctness_output.txt

cd "$(dirname "$0")/.." || exit 1
OUTDIR=results/correctness
TMP=$(mktemp -d)
mkdir -p "$OUTDIR"
LOG=$OUTDIR/correctness_output.txt
: > "$LOG"
pass=0; fail=0

say() { echo "$*" | tee -a "$LOG"; }

maxdiff() {  # largest absolute difference between two raw double files
  python3 - "$1" "$2" <<'PY'
import sys, numpy as np
a = np.fromfile(sys.argv[1]); b = np.fromfile(sys.argv[2])
print("size-mismatch" if a.size != b.size else f"{np.max(np.abs(a - b)):.3e}")
PY
}

compare() {  # compare <label> <reference> <candidate>
  if [ ! -s "$3" ]; then
    say "FAIL  $1  (no output file)"; fail=$((fail + 1)); return
  fi
  if cmp -s "$2" "$3"; then
    say "PASS  $1  bit-for-bit identical"; pass=$((pass + 1))
  else
    say "FAIL  $1  max|diff| = $(maxdiff "$2" "$3")"; fail=$((fail + 1))
  fi
}

MPI_COMMON="--mca btl tcp,self,vader"
say "Correctness check  $(date)"
say "host: $(hostname)  commit: $(git rev-parse --short HEAD)"
say ""
say "== Part A: one VM ($(uname -m)), strips and blocks vs serial =="

for c in 1 2 V; do
  for N in 8 41 100; do
    steps=50; [ "$N" -eq 8 ] && steps=1
    ref=$TMP/serial_c${c}_N${N}.bin
    ./heat_serial --case "$c" --N "$N" --r 0.2 --steps "$steps" \
      --out "$ref" > /dev/null
    for P in 1 2 3 4; do
      for m in strips blocks; do
        out=$TMP/${m}_c${c}_N${N}_P${P}.bin
        mpirun --oversubscribe -np "$P" $MPI_COMMON "./heat_$m" \
          --case "$c" --N "$N" --r 0.2 --steps "$steps" --decomp "$m" \
          --out "$out" > /dev/null 2>&1
        compare "case=$c N=$N steps=$steps P=$P $m" "$ref" "$out"
      done
    done
  done
done

if [ "${CLUSTER:-0}" = 1 ]; then
  say ""
  say "== Part B: mixed cluster (ARM64 Jose + x86-64 Dia, Theresa) =="
  HOSTS="100.125.52.39:2,100.115.31.27:2,100.100.103.111:2"
  NET="--mca oob_tcp_if_include tailscale0 --mca btl_tcp_if_include tailscale0 --mca btl tcp,self"
  for N in 41 100; do
    ref=$TMP/serial_c2_N${N}.bin
    for P in 2 3; do
      for m in strips blocks; do
        out=$TMP/cluster_${m}_N${N}_P${P}.bin
        timeout -k 5 120 mpirun --host "$HOSTS" --map-by node -np "$P" $NET \
          "./heat_$m" --case 2 --N "$N" --r 0.2 --steps 50 --decomp "$m" \
          --out "$out" > /dev/null 2>&1 < /dev/null
        compare "cluster case=2 N=$N P=$P (map-by node) $m" "$ref" "$out"
      done
    done
  done
fi

say ""
say "SUMMARY: $pass passed, $fail failed"
rm -rf "$TMP"
[ "$fail" -eq 0 ]
