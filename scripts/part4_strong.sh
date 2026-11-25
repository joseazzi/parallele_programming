#!/bin/bash

N="$1"
LOG="results/part4/strong_${N}_20steps_twovm_raw.txt"
touch "$LOG"

for placement in slot node; do
  for P in 1 2 3 4; do
    if [ "$placement" = "slot" ]; then
      if [ "$P" -le 2 ]; then
        hosts="localhost:2"
      elif [ "$P" -le 4 ]; then
        hosts="localhost:2,100.115.31.27:2"
      else
        hosts="localhost:2,100.115.31.27:2"
      fi
    else
      if [ "$P" -eq 1 ]; then
        hosts="localhost:2"
      elif [ "$P" -eq 2 ]; then
        hosts="localhost:2,100.115.31.27:2"
      else
        hosts="localhost:2,100.115.31.27:2"
      fi
    fi
    for mode in strips blocks; do
      for run in 1 2 3; do
        echo "N=$N placement=$placement P=$P mode=$mode run=$run" | tee -a "$LOG"

        timeout -k 5s 20s mpirun \
          --host "$hosts" \
          --map-by "$placement" \
          -np "$P" \
          --mca oob_tcp_if_include tailscale0 \
          --mca btl_tcp_if_include tailscale0 \
          --mca btl tcp,vader,self \
          "./heat_$mode" \
          --case 2 --N "$N" --r 0.2 --steps 20 \
          --decomp "$mode" \
          --out "/tmp/part4_${mode}.bin" \
          2>&1 | tee -a "$LOG"

        status=${PIPESTATUS[0]}
        if [ "$status" -ne 0 ]; then
          echo "FAILED: exit=$status" | tee -a "$LOG"
          exit "$status"
        fi
      done
    done
  done
done
