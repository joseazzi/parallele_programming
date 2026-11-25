#!/bin/bash
# Part 4 final measurement campaign (run on heat-jose from ~/heat-mpi).
#   - strong scaling: N = 512, 2048 (8192 skipped); strips and blocks; P = 1..6;
#     placements --map-by slot and --map-by node
#   - P = 6 (2 ranks on Theresa's 2-vCPU VM) is skipped: it repeatedly
#     knocked that VM off the tailnet. Earlier P = 6 runs are kept.
#   - weak scaling: about 1024x1024 nodes per process, N = 1024*sqrt(P)
# 3 repetitions per configuration, 20 steps, r = 0.2, Case 2.
# Each run has a timeout; a failed run is logged as "FAILED: exit=..."
# and the campaign continues. The script is resumable: runs that already
# have a result in the logs are skipped. If a VM stops answering, the
# script writes results/part4/final/PAUSED and exits; just run it again.
#
# Usage: bash scripts/part4_final.sh
cd ~/heat-mpi || exit 1

HOSTS="100.125.52.39:2,100.115.31.27:2,100.100.103.111:2"   # Jose, Dia, Theresa
STEPS=20
OUT=results/part4/final
mkdir -p "$OUT"
rm -f "$OUT/PAUSED"

# NO_THERESA=1: only run configurations that do not place a rank on
# Theresa's VM (slot: P <= 4, node: P <= 2); the rest is done later.
REMOTE="100.115.31.27 100.100.103.111"
[ "${NO_THERESA:-0}" = 1 ] && REMOTE="100.115.31.27"

check_hosts() {
  for h in $REMOTE; do
    if ! timeout 15 ssh -o BatchMode=yes -o ConnectTimeout=10 "$h" true; then
      echo "$h unreachable at $(date)" > "$OUT/PAUSED"
      exit 2
    fi
  done
}

run() {  # run <log> <N> <placement> <P> <mode> <rep> <timeout>
  local log=$1 N=$2 pl=$3 P=$4 m=$5 rep=$6 to=$7
  local head="N=$N placement=$pl P=$P mode=$m run=$rep"
  touch "$log"
  # skip runs that already have a result
  grep -x -A1 "$head" "$log" | grep -q t_total && return
  if [ "${NO_THERESA:-0}" = 1 ]; then
    [ "$pl" = slot ] && [ "$P" -ge 5 ] && return
    [ "$pl" = node ] && [ "$P" -ge 3 ] && return
  fi
  check_hosts
  echo "$head" >> "$log"
  # output goes to a file, not a pipe: after a timeout, a leftover ssh
  # to a remote daemon would otherwise keep the pipe open forever
  timeout -k 5 "$to" mpirun --host "$HOSTS" --map-by "$pl" -np "$P" \
    --mca oob_tcp_if_include tailscale0 --mca btl_tcp_if_include tailscale0 \
    --mca btl tcp,self \
    "./heat_$m" --case 2 --N "$N" --r 0.2 --steps "$STEPS" --decomp "$m" \
    > /tmp/part4_run.out 2>&1 < /dev/null
  local s=$?
  grep -v setpgid /tmp/part4_run.out >> "$log"
  if [ "$s" -ne 0 ]; then
    echo "FAILED: exit=$s" >> "$log"
    pkill -f "[s]sh -x 100\." ; sleep 2      # clean up orphaned daemons
  fi
}

strong() {  # strong <N> <timeout>
  local N=$1 to=$2
  for pl in slot node; do
    local log=$OUT/strong_N${N}_${pl}_raw.txt
    for P in 1 2 3 4 5; do
      # P=1 is identical for both placements (one rank on Jose)
      [ "$pl" = node ] && [ "$P" -eq 1 ] && continue
      for m in strips blocks; do for rep in 1 2 3; do
        run "$log" "$N" "$pl" "$P" "$m" "$rep" "$to"
      done; done
    done
  done
}

weak() {
  local log=$OUT/weak_raw.txt
  for P in 1 2 3 4 5; do
    N=$(python3 -c "import math; print(round(1024*math.sqrt($P)))")
    for m in strips blocks; do for rep in 1 2 3; do
      run "$log" "$N" slot "$P" "$m" "$rep" 120
    done; done
  done
}

strong 512 60
strong 2048 60
weak
# N=8192 skipped to save time (see docs/PART4_PERFORMANCE.md)
echo "ALL DONE $(date)" > "$OUT/DONE"
