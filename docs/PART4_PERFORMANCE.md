# Part 4 — Performance Study

This chapter is written to be included as section (d) of the final
report. It covers the experiments of Section 8.2 of the project
statement, the performance model of Section 8.3, and the answers to
the Part 4 questions.

## 4.1 Setup and measurement rules

| Item | Value |
|---|---|
| Problem | Case 2 (hot top and bottom), r = 0.2 (stability limit 0.25) |
| Steps | 20 per run for the parallel study, 500 for the serial baseline |
| Repetitions | 3 per configuration; median reported, spread in the CSV files |
| Cluster | heat-jose (ARM64, Apple M1 host), heat-dia-1 (x86-64), heat-theresa (x86-64, Windows host); 2 vCPUs each, so at most 6 slots |
| Network | all three laptops on the **same Wi-Fi**, linked through Tailscale. During the final campaign (25 Nov 2026), Jose–Dia and Jose–Theresa were mostly **direct**, with Dia occasionally on the Paris DERP relay |
| Launch | `mpirun --host jose:2,dia:2,theresa:2 --map-by {slot,node} --mca btl tcp,self` over `tailscale0` |
| Scripts | `scripts/part4_final.sh` (runs), `scripts/part4_analyze.py` (analysis, model, plots) |
| Raw data | `results/part4/final/*_raw.txt`, `results/part4/*_serial_raw.txt` |

**Departures from the suggested settings, and why:**

- **20 steps instead of 500.** Across VMs, one step costs about 0.1 s,
  so 500 steps would take about 50 s per run and 2–3 hours for the
  whole campaign on an unstable network. Time *per step* does not
  depend on the number of steps, so all comparisons are made per step.
- **P ≤ 5 instead of 6.** P = 6 places two busy ranks on each 2-vCPU VM.
  It repeatedly made Theresa's VM drop off the tailnet
  (`ssh: connect … timed out`). Four P = 6 runs did succeed earlier
  (N = 512: strips 2.49 s and 7.20 s, blocks 2.84 s and 3.06 s per
  20 steps; `results/part4/strong_512_20steps_p5p6_raw.txt`). The
  systematic study stops at P = 5.
- **N = 8192 not run** in the strong-scaling study, to save time.
  The model gives its predictions (Section 4.5).

Out of 141 runs in the final campaign, 3 failed (2 at P = 6, 1 while
Theresa's VM was offline); the failed configurations were then rerun.

## 4.2 Single-node baseline (compute rate)

Serial solver, 500 steps, median of 3 (`results/part4/baseline.csv`).

| N | Jose: ms/step | Jose: ns/node | Dia: ms/step | Dia: ns/node | Theresa: ms/step | Theresa: ns/node |
|---:|---:|---:|---:|---:|---:|---:|
| 512 | 0.164 | 0.63 | 0.223 | 0.86 | 0.278 | 1.06 |
| 1024 | 0.682 | 0.65 | 1.630 | 1.56 | 1.494 | 1.43 |
| 2048 | 2.865 | 0.68 | 7.438 | 1.78 | 10.272 | 2.45 |
| 4096 | 13.30 | 0.79 | 28.42 | 1.69 | 33.64 | 2.01 |
| 8192 | 53.02 | 0.79 | 122.0 | 1.82 | 108.5 | 1.62 |

The cost per node rises once the grid no longer fits in cache
(N ≥ 1024). Jose's ARM64 VM is **2–3.5× faster** than the two x86-64
VMs. In any multi-VM run, the slowest rank therefore sets the pace.

## 4.3 Strong scaling

**Rank placement on our cluster:**

| P | `--map-by slot` | `--map-by node` |
|---|---|---|
| 2 | Jose ×2 (one VM) | Jose, Dia |
| 3 | Jose ×2, Dia | Jose, Dia, Theresa |
| 4 | Jose ×2, Dia ×2 | Jose ×2, Dia, Theresa |
| 5 | Jose ×2, Dia ×2, Theresa | Jose ×2, Dia ×2, Theresa |

**Measured time per step (ms), median of 3** (full table with spread,
model, S and E: `results/part4/strong_scaling.csv`):

| N | Mode | P=1 | P=2 slot | P=2 node | P=3 slot | P=3 node | P=4 slot | P=4 node | P=5 slot | P=5 node |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 512 | strips | 0.35 | **0.19** | 87.5 | 94.7 | 109.5 | 96.1 | 103.7 | 142.7 | 113.7 |
| 512 | blocks | 0.36 | **0.16** | 88.7 | 95.7 | 94.7 | 92.1 | 179.1 | 117.9 | 108.1 |
| 2048 | strips | 3.14 | **2.03** | 107.0 | 115.2 | 138.9 | 127.6 | 147.8 | 132.2 | 135.9 |
| 2048 | blocks | 3.30 | **1.75** | 107.3 | 116.8 | 139.1 | 103.1 | 196.1 | 122.4 | 161.3 |

**Speedup S(P) = T₁/T_P:**

- **Inside one VM** (P = 2, slot): S = 1.83 / 2.21 (N = 512, strips /
  blocks) and 1.55 / 1.88 (N = 2048). Efficiency is 0.77–1.1. A value
  above 1 is a cache effect: each half-grid fits better in cache.
- **As soon as ranks are on two or more VMs:** S = 0.002–0.004 at
  N = 512 and 0.017–0.032 at N = 2048. The parallel run is **30–500×
  slower** than serial.

Figures:

- `plots/part4_strong_N512.png`, `plots/part4_strong_N2048.png`:
  time per step, measured points with the model as lines on the same axes
- `plots/part4_speedup.png`, `plots/part4_efficiency.png`

**Communication share** (t_comm / t_total, max over ranks):

| Configuration | Share of time in halo exchange |
|---|---|
| P = 1 | < 0.1 % |
| P = 2 on one VM | 5–12 % |
| Ranks on ≥ 2 VMs, N = 512 | 99.8–99.96 % |
| Ranks on ≥ 2 VMs, N = 2048 | 98.1–99.6 % |

## 4.4 Weak scaling

About 1024 × 1024 nodes per process, N = 1024·√P, `--map-by slot`
(`results/part4/weak_scaling.csv`, `plots/part4_weak.png`).

| P | N | Strips ms/step | Blocks ms/step | Comm share |
|---:|---:|---:|---:|---:|
| 1 | 1024 | 1.15 | 1.10 | 0 % |
| 2 | 1448 | 1.14 | 1.08 | 6–7 % |
| 3 | 1774 | 110.3 | 144.0 | 96–97 % |
| 4 | 2048 | 111.4 | 99.3 | 99 % |
| 5 | 2290 | 136.7 | 154.1 | 98–99 % |

On one VM (P = 1 → 2), the time stays constant, which is ideal weak
scaling. When the job spreads to a second VM (P = 3), the time jumps
**about 100×** and then stays roughly flat. The cost is now the
per-step network latency, which does not grow with N. P = 5 is a bit
higher because Theresa's VM, the slowest compute node, joins with
its own link.

## 4.5 Performance model

The model starts from Task 8.2 of the background notes.

**Time per step:**

    T_step(N, P) = max over ranks ( c_vm(N) · n_x · n_y )  +  Σ_phases 2 · max over pairs ( t_s + m · t_w )

- **c_vm(N):** measured seconds per node per step on that VM
  (Section 4.2), interpolated in log N.
- **n_x · n_y:** interior nodes owned by the rank. For strips,
  n_y = (N−1)/P. For blocks, the grid is P_x × P_y from
  `MPI_Dims_create`.
- **Halo phases:** each direction with more than one process costs two
  `MPI_Sendrecv` phases (send up and send down). Strips have 2 phases;
  blocks with P_x, P_y > 1 have 4.
- **Phase cost:** each phase lasts as long as its slowest pair. A pair
  costs t_s + m·t_w, using that pair's own Part 0 values: the same-VM
  values if both ranks share a VM, or the measured Jose–Dia,
  Jose–Theresa or Dia–Theresa values otherwise
  (t_s ≈ 32–40 ms, 1/t_w ≈ 5–7 Mbit/s, i.e. 0.6–0.9 MB/s).
- **m:** message size in bytes, 8 × (row or column length + 2).

**Model vs measurement:**

- **Same VM:** the model predicts 0.08 ms/step at N = 512, P = 2;
  measured is 0.16–0.19 ms.
- **Across VMs:** measurements range from 10 % below to 55 % above the
  model, typically 10–30 % above. The worst case is N = 512, P = 5
  slot strips, whose 3 runs spread from 2.29 to 8.20 s.
- **Shape:** the model reproduces the measured pattern. Examples:
  - The 100× jump when the job leaves the first VM.
  - Blocks with `--map-by node` at P = 4 are the slowest configuration
    (179 ms at N = 512, 196 ms at N = 2048). With ranks on
    Jose, Dia, Theresa, Jose in a 2×2 grid, **all four** halo phases
    cross machines.

## 4.6 Answers to the Part 4 questions

**For which N does spreading across machines start to pay off, and
does the model predict the same crossover?**
On our cluster, it never pays off for the sizes we can run. The
measurements show no crossover up to N = 2048: across VMs,
S ≤ 0.03. The model puts the crossover for P = 5 at
**N ≈ 67 000** (`results/part4/model_predictions.csv`). At that size,
the halo latency (~0.1–0.2 s per step) is finally smaller than the
compute time saved. Such a grid needs about 72 GB for the two time
levels, far beyond our 2–4 GB VMs. The model predicts S₅ ≈ 0.17 for
N = 8192. Both model and measurement say: no crossover on this
cluster.

**Where do model and measurement disagree, and why?**

1. **Wi-Fi and relays.** All three laptops share one Wi-Fi network,
   yet Tailscale sometimes routes through DERP (Paris or London) when
   the access point blocks peer-to-peer traffic. Per-step times then
   rise by 20–40 % and the spread grows: for example, the N = 512
   P = 5 slot strips runs ranged from 2.29 to 8.20 s. The Part 0 t_s
   values were themselves measured partly over relays.
2. **A slower node holds everybody back.** Every step waits for the
   slowest rank and the slowest link. Theresa's VM is the slowest
   compute node, and its links have the highest t_s (Dia–Theresa:
   39.8 ms). P = 5 is therefore always the slowest slot configuration.
3. **Unstable node.** Theresa's 2-vCPU VM on a Windows host dropped
   off the tailnet four times during the campaign, both under load
   (P = 6) and with one rank. We attribute this to host sleep and
   Wi-Fi power saving, combined with tailscaled being starved when
   both vCPUs are busy.
4. **Short runs and caches.** With 20 steps, the P = 1 MPI run
   (0.35 ms/step at N = 512) is slower than the 500-step serial
   baseline (0.16 ms/step). First-touch page faults and a cold cache
   are not amortised. The same effect makes the measured one-VM points
   lie above the model.
5. **The model ignores synchronisation.** One slow phase delays all
   ranks, and OS noise on the hosts adds to it.

**What would change on a real cluster with t_s ≈ 1 µs?**
Using the same model with t_s = 1 µs and 10 GB/s between nodes:

- Communication drops from ~100 ms to ~10 µs per step, below 1 % of
  the run time.
- The crossover falls from N ≈ 67 000 to **N ≈ 80**.
- Predicted speedup with P = 5 is 2.8 at N = 512, 1.4 at N = 2048 and
  2.2 at N = 8192.

The remaining gap to S = 5 is **load imbalance**, not the network.
Ranks on Dia and Theresa compute 2–3× slower than ranks on Jose. A
weighted decomposition, giving each rank a share of rows proportional
to its speed, would be the next improvement. With identical nodes,
the model gives near-linear speedup for N ≥ 512.

**How would you advise someone who wants to run this simulation over
Tailscale?**

- **Don't distribute it** unless the grid does not fit on one
  machine. One multi-core VM is 30–500× faster than our 3-VM runs for
  every size we tested.
- **If you must distribute:**
  - Check `tailscale ping` for a **direct** connection; avoid DERP.
  - Prefer wired connections over Wi-Fi.
  - Keep machines awake, plugged in, with Wi-Fi power saving off.
  - Use `--map-by slot`, so neighbouring ranks share a VM and fewer
    halo messages cross the network.
  - Prefer **strips**: 2 messages per step instead of up to 4. With a
    latency-bound network, the number of messages matters more than
    their size.
  - Use the largest N that fits in memory.
  - Leave a core free on 2-vCPU VMs so Tailscale and SSH keep running.
  - Consider exchanging deeper halos every k steps, or overlapping
    communication with computation, to cut the number of latency
    payments.

## 4.7 Cross-check of the Part 3 prediction on the real cluster

Part 3 predicted, from the latency-dominated model, that strips and
blocks cost about the same at P = 4. On the cluster:

- **`--map-by slot`, P = 4:** strips 96 vs blocks 92 ms/step at
  N = 512, and 128 vs 103 ms/step at N = 2048. The two are close,
  with blocks slightly ahead.
- **`--map-by node`, P = 4:** blocks are much worse (179 vs 104 and
  196 vs 148 ms/step), because all four block phases cross VMs.

P = 8 cannot be run on our 6-slot cluster.

## 4.8 Earlier measurements (relay period)

Before the final campaign, the same study was run while most links
went through DERP relays (`results/part4/strong_*_raw.txt`, analysed
by `scripts/part4_analyze_relay_era.py`, plots `plots/*_relay_era.png`).
Per-step times then were 90–235 ms. They are kept as evidence of how
much the connection type matters but are not used in the tables above.

## Appendix: files

| File | Content |
|---|---|
| `scripts/part4_final.sh` | measurement campaign (resumable, pauses if a VM disappears) |
| `scripts/part4_analyze.py` | medians, S, E, comm share, model, all plots |
| `results/part4/final/` | raw output of every run |
| `results/part4/baseline.csv` | serial compute rate per VM |
| `results/part4/strong_scaling.csv` | strong-scaling table with model column |
| `results/part4/weak_scaling.csv` | weak-scaling table with model column |
| `results/part4/model_predictions.csv` | crossover N and speedups, Tailscale vs t_s = 1 µs |
| `plots/part4_*.png` | figures |
