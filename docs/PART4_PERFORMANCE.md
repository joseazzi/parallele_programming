# Part 4 — Performance Study (Strong Scaling)

## 1. Objective

Measure how the MPI strips and blocks solvers scale when the
problem size is fixed and the number of processes P grows, and
explain the result with the communication model from Part 0.

Metrics (median of 3 runs where available):

- T(P): total wall time (`t_total`, max over ranks)
- Speedup: S(P) = T(1) / T(P)
- Efficiency: E(P) = S(P) / P
- Communication fraction: t_comm / t_total

## 2. Setup

- Case 2, r = 0.2, explicit 5-point scheme
- Main study: N = 512, 20 steps, P = 1..5
- Extra data: N = 512 with 100 and 500 steps (P = 1..5),
  N = 2048 with 20 steps (P = 1..4)
- Hosts: heat-jose (2 slots), heat-dia-1 (2 slots),
  heat-theresa (2 slots), connected through Tailscale
- Placement:
  - `slot`: fill Jose first (P = 1, 2 on one VM; P >= 3 crosses VMs)
  - `node`: round-robin (P >= 2 already crosses VMs)

The number of steps was reduced from 500 to 20 so that runs
crossing machines finish within the 20–60 s timeout. Step count
does not change the per-step cost, only the total time.

Launch script: `scripts/part4_strong.sh`  
Analysis script: `python3 scripts/part4_analyze.py`

## 3. Serial baseline (500 steps, median of 3)

Raw: `results/part4/{jose,dia,theresa}_serial_raw.txt`

| N | Jose (s) | Dia (s) | Theresa (s) |
|---:|---:|---:|---:|
| 512 | 0.082 | 0.112 | 0.139 |
| 1024 | 0.341 | 0.815 | 0.747 |
| 2048 | 1.432 | 3.719 | 5.136 |
| 4096 | 6.652 | 14.209 | 16.818 |
| 8192 | 26.510 | 61.000 | 54.248 |

Run time grows about 4x each time N doubles, as expected
for O(N²) work per step. Jose (ARM64) is about 2x faster
than the other two VMs, so the cluster is heterogeneous. In
any multi-VM run the slowest rank sets the pace.

## 4. Strong scaling results (N = 512, 20 steps, `slot` placement)

Full table: `results/part4/strong_scaling.csv`

| P | Machines | Strips T (s) | Strips S | Blocks T (s) | Blocks S | Comm fraction |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Jose | 0.00374 | 1.00 | 0.00402 | 1.00 | ~0 % |
| 2 | Jose | 0.00209 | 1.79 | 0.00201 | 2.00 | 10–12 % |
| 3 | Jose + Dia | 1.966 | 0.0019 | 1.974 | 0.0020 | 99.9 % |
| 4 | Jose + Dia | 2.051 | 0.0018 | 1.925 | 0.0021 | 99.9 % |
| 5 | Jose + Dia + Theresa | 4.724 | 0.0008 | 4.817* | 0.0008 | 99.96 % |
| 6 | all three | failed | – | failed | – | – |

\* single run (runs 2–3 timed out).

With `node` placement, P = 2 already spans two VMs and takes
1.80 s instead of 0.002 s, which confirms that the slowdown
comes from the network and not from the number of ranks.

N = 2048 (20 steps) behaves the same way: S(2) = 1.77
(strips) and 1.72 (blocks) on one VM, but S(3) and S(4) are
about 0.025 once ranks cross VMs.

Plots:

- `plots/part4_time.png`
- `plots/part4_speedup.png`
- `plots/part4_efficiency.png`

## 5. Interpretation with the communication model

The Part 0 model is t_msg(m) = ts + m·tw, with ts ≈ 32–40 ms
between VMs (Tailscale DERP relays) and ts ≈ 0.0002–0.0004 ms
inside one VM.

For N = 512, one halo row is 512·8 = 4 KiB, so
m·tw ≈ 5 ms. Each step a rank exchanges with its
neighbours, so the predicted cost per step across VMs is
about 2·(ts + m·tw) ≈ 75–90 ms.

Measured cost (P = 2 to 4 across Jose and Dia):
1.8–2.0 s / 20 steps ≈ **90–100 ms per step**. This matches
the model. Computation is only about 0.0002 s per step.

With Theresa included (P = 5), a step costs about 235 ms.
The extra relayed links (Jose–Theresa, Dia–Theresa) add their
own latency, and the strip chain must wait for the slowest one.

Inside one VM, communication is about 10 % of the time and
speedup is close to ideal (1.8–2.0).

### Why strips and blocks are about equal

Both decompositions are limited by latency (ts), not by
bandwidth (m·tw). Blocks send fewer bytes, but at P ≤ 5 they
send a similar number of messages, so the time per step is
the same. Blocks would only win for much larger N, when the
m·tw term dominates. Part 3 estimated N ≈ 4400 for P = 8.

### When would it pay off across VMs?

Distributing only helps when the computation saved per step
is larger than the communication added:

  T_serial_step · (1 − 1/P) > ~0.1 s

Jose's serial cost per step is about 26.5 s / 500 ≈ 53 ms at
N = 8192. Even at that size, the computation saved is smaller
than the 90–235 ms of latency per step. On this Tailscale
network, **no tested size benefits from more than one VM**.
A LAN with sub-millisecond latency would change this
conclusion.

## 6. Problems encountered and decisions

- **500-step runs across VMs** took about 50 s each
  (`strong_512_raw.txt`) and 85 s at P = 5. We reduced to
  100 and then 20 steps.
- **P = 5 / P = 6**: several runs ended with exit 124/137
  (timeout) or with `connect() ... failed` / `Connection closed
  by 100.100.103.111`. The Tailscale links to Theresa are
  relayed (DERP) and drop intermittently.
- **P = 6 (final attempt, 25 Nov)**: N = 512, 5 steps,
  60 s timeout. Strips failed with
  `ssh: connect to host 100.100.103.111 port 22: Connection timed out`,
  and blocks hung (`results/part4/p6_test_raw.log`).
  We recorded P = 6 as not measurable on this network
  instead of debugging further. Its expected time would be
  similar to or worse than P = 5.
- Dia's executables were built from an older commit
  (35c4b7e). Parts 2/3 verified that the solver logic is
  unchanged.

## 7. Conclusion

- On one VM (P = 2) both solvers scale well:
  S ≈ 1.8–2.0, E ≈ 0.9–1.0.
- Across VMs, the latency of the Tailscale relays
  (~35 ms per message) dominates. Over 99 % of the time is
  communication, and the parallel runs are about 500x slower
  than serial.
- The measured cost per step (90–100 ms between two VMs)
  agrees with the ts + m·tw model from Part 0.
- Strips and blocks perform the same, because the cost is
  dominated by latency.
- Strong scaling over this cluster is limited by the network,
  not by the algorithm.
