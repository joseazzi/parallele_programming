
# Part 0 — Building the MPI Cluster

## 1. Objective

The objective of Part 0 is to build a distributed-memory
cluster using three Ubuntu virtual machines connected
through Tailscale.

The cluster is used to run MPI applications across
different computers and measure network communication
performance before running the parallel 2D heat
diffusion solver.

Team members:
- Jose Azzi
- Dia Hajjar
- Theresa Kozah

## 2. Cluster Architecture

The cluster consists of three Ubuntu VMs:

Jose's computer
    |
    +-- heat-jose (Ubuntu VM)
         Tailscale: 100.125.52.39

Dia's computer
    |
    +-- heat-dia (Ubuntu VM)
         Tailscale: 100.115.31.27

Theresa's computer
    |
    +-- heat-theresa (Ubuntu VM)
         Tailscale: 100.100.103.111

All three VMs communicate through a private
Tailscale network.

Tailscale provides encrypted connectivity between
the machines, including when they are behind
different routers or NAT configurations.

Open MPI uses SSH to launch remote processes and
TCP over the tailscale0 interface for communication.

## 3. Hardware and Software Configuration

| Specification | Jose | Dia | Theresa |
|---|---|---|---|
| Hostname | heat-jose | heat-dia | heat-theresa |
| Ubuntu | 24.04.5 LTS | 24.04.5 LTS | 24.04.5 LTS |
| Architecture | ARM64 | x86-64 | x86-64 |
| Virtual CPUs | 2 | 2 | 2 |
| VM RAM | 3.8 GiB | 1.9 GiB | 3.8 GiB |
| Open MPI | 4.1.6 | 4.1.6 | 4.1.6 |
| Tailscale IP | 100.125.52.39 | 100.115.31.27 | 100.100.103.111 |

Known processor information:
- Dia: 12th Gen Intel Core i5-1235U
- Theresa: 12th Gen Intel Core i7-1255U
- Jose: Apple M1 processor, 8 CPU cores
  (4 performance and 4 efficiency).
  MacBook Pro (MacBookPro17,1), 8 GB host RAM.
  Ubuntu ARM64 VM running through Multipass
  with 2 virtual CPUs and approximately
  3.8 GiB of RAM.
Jose's Ubuntu VM was created using Multipass.
The hypervisor used by the other machines should
be confirmed before final submission.

### Important observations

All three machines use the same Ubuntu release
and Open MPI version.

Jose uses an ARM64 VM, while Dia and Theresa
use x86-64 VMs. This mixed architecture must be
considered when compiling the programs and
comparing floating-point results.

Dia's VM has approximately 1.9 GiB of RAM,
below the assignment requirement of at least
4 GB per VM. This configuration needs to be
corrected or explicitly reported.

## 4. Tailscale Network Configuration

Each Ubuntu VM is connected to Tailscale.

The following commands were used to inspect
the network:

    tailscale status
    tailscale ip -4
    tailscale netcheck
    tailscale ping <peer-ip>

The Tailscale network uses private 100.x.y.z
addresses to identify each machine.

Tailscale may establish either:
- Direct peer-to-peer communication.
- Relayed communication through DERP servers.

During the experiments, some connections
initially used the Paris DERP relay before
switching to direct peer-to-peer communication.

Direct connectivity was observed for:
- Jose and Dia
- Jose and Theresa
- Dia and Theresa

Connection state can change during a run.
Therefore, a direct Tailscale ping confirms
direct connectivity only at the time checked.

The original Jose-Dia full-range benchmark
does not have a fully documented direct/DERP
state for the entire measurement.

## 5. SSH Configuration

OpenSSH is used to allow MPI to start processes
on remote Ubuntu machines.

Passwordless SSH authentication was configured
using SSH keys.

An example connectivity test is:

    ssh ubuntu@100.115.31.27 hostname

From Theresa's VM, this command successfully
returned:

    heat-dia

SSH is required for distributed execution
with Open MPI.

Before running MPI, remote hosts must be
reachable without interactive password prompts.

## 6. Open MPI Configuration

Open MPI version 4.1.6 is installed on
all three Ubuntu virtual machines.

MPI programs are compiled using:

    mpic++ -O2 source.cpp -o executable

For mixed-architecture floating-point
reproducibility, the assignment recommends:

    -ffp-contract=off

Each machine must compile a compatible executable
locally at the same filesystem path.

For cross-machine benchmarks, MPI was configured
to use the Tailscale interface.

Example command:

    mpirun \
      --mca btl_tcp_if_include tailscale0 \
      --mca oob_tcp_if_include tailscale0 \
      --mca btl tcp,self \
      --host 100.125.52.39,100.100.103.111 \
      -np 2 \
      ~/heat-mpi/pingpong

The --host option selects the machines.

The -np 2 option launches two MPI processes,
one on each selected machine.

The MCA options select TCP communication
through the Tailscale interface.

The btl tcp,self setting explicitly selects
TCP and local self communication for MPI data.

## 7. MPI Connectivity Tests

The MPI hello-world program was used during
the cluster setup.

Its purpose is to verify:
- Successful MPI initialization.
- Correct process ranks and process count.
- Remote process execution.
- Communication across the cluster.

Distributed MPI execution was successfully
verified across all three Ubuntu VMs.

The hostname test returned:
- heat-jose
- heat-dia
- heat-theresa

The MPI Hello World test confirmed:
- Rank 0 of 3 on heat-jose
- Rank 1 of 3 on heat-dia
- Rank 2 of 3 on heat-theresa

Verification evidence is stored in:
- results/cluster/three_node_hostname.txt
- results/cluster/three_node_hello.txt

Both tests completed successfully using
Open MPI over the Tailscale network.
## 8. Ping-Pong Benchmark Methodology

The MPI ping-pong benchmark measures
communication performance between two ranks.

The procedure is:

1. Rank 0 sends a message to Rank 1.
2. Rank 1 receives the message.
3. Rank 1 sends the message back.
4. Rank 0 measures the round-trip time.
5. The round-trip time is averaged over
   multiple repetitions.

The experiment uses message sizes ranging
from 8 bytes to 16 MiB, increasing by
powers of two.

The benchmark uses warm-up exchanges
before timed measurements.

The one-way communication time is estimated by:

    t_one_way = t_round_trip / 2

This is an estimated average one-way time,
not an independently measured one-way latency.

Measurements were collected for:
- Jose local
- Dia local
- Theresa local
- Jose - Dia
- Jose - Theresa
- Dia - Theresa

All six configurations have benchmark data
covering the required 8-byte to 16-MiB range.

The raw benchmark measurements are stored
as CSV files in the project repository.

## 9. Communication Performance Model

The assignment uses the model:

    t_msg(m) = ts + m * tw

Where:
- m is message size in bytes.
- ts is the startup communication latency.
- tw is the incremental time per byte.

Bandwidth is estimated as:

    bandwidth = 1 / tw

For bandwidth in Mbps:

    bandwidth_Mbps = 8 / (tw * 1,000,000)

The initial analysis performed an ordinary
linear regression across all message sizes.

Some local benchmarks produced negative fitted
intercepts. These are mathematical fitting
artifacts and are not physically valid
negative communication latencies.

A refined empirical analysis was therefore
also performed:

- Startup latency was estimated using the
  median measured one-way time for messages
  up to 1024 bytes.
- Transfer cost per byte was fitted using
  messages of at least 1 MiB, holding
  the startup estimate fixed.

This method preserves positive empirical
startup estimates while fitting the
large-message bandwidth.

The refined estimates should not be described
as unconstrained full-range regression
intercepts. Both methods are retained for
comparison and transparent reporting.

## 10. Refined Communication Results

| Connection | Startup latency | Bandwidth |
|---|---:|---:|
| Jose local | 0.190 microseconds | 36658.571 Mbps |
| Dia local | 0.406 microseconds | 37991.234 Mbps |
| Theresa local | 0.404 microseconds | 41875.967 Mbps |
| Jose - Dia | 32.217 ms | 6.890 Mbps |
| Jose - Theresa | 33.019 ms | 6.375 Mbps |
| Dia - Theresa | 39.775 ms | 5.066 Mbps |

These results show that communication
between processes on the same VM is much
faster than communication between VMs
over Tailscale.

The fitted bandwidth values are empirical
application-level estimates. They are not
raw physical network link speeds.

## 11. Results and Analysis Files

Raw measurements:
- pingpong_jose_local.csv
- pingpong_dia_local.csv
- pingpong_theresa_local.csv
- pingpong_jose_dia.csv
- pingpong_jose_theresa_16mb.csv
- pingpong_dia_theresa_16mb.csv

Additional historical and direct-connection
benchmark CSVs are also preserved.

Analysis scripts:
- scripts/analyze_pingpong.py
- scripts/fit_pingpong_model.py

Communication model results:
- results/pingpong/communication_model.csv
- results/pingpong/communication_model.png
- results/pingpong/communication_model_refined.csv
- results/pingpong/communication_model_refined.png
- results/pingpong/communication_model_local.png
- results/pingpong/communication_model_cross_machine.png

Initial comparison graphs:
- plots/pingpong_latency.png
- plots/pingpong_bandwidth.png

## 12. Conclusion

A three-machine MPI cluster was successfully
established using Ubuntu, SSH, Open MPI
and Tailscale.

All three local and all three cross-machine
ping-pong benchmark configurations were
measured from 8 bytes to 16 MiB.

Communication analysis demonstrated a large
performance difference between local and
cross-machine MPI communication.

The network measurements provide a basis
for the communication model and later
performance studies of the parallel
2D heat diffusion solver.

Remaining documentation checks include
the host hardware details, Dia's VM RAM
requirement, reproducible three-node
MPI output, and the final connection-state
records.
