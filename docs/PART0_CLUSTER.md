
# Part 0 — Building the MPI Cluster

## 1. Objective

The objective of Part 0 is to build a distributed-memory
computing cluster using three Ubuntu virtual machines
connected through Tailscale.

The cluster allows MPI programs to execute across
different physical computers, communicating through
a private encrypted network.

Before implementing the parallel 2D heat diffusion solver,
we measure communication performance using MPI
ping-pong experiments.

These measurements provide empirical estimates of:

- Communication startup latency.
- Transfer time per byte.
- Effective communication bandwidth.
- Differences between local and distributed MPI.
- Effects of network connectivity and Tailscale routing.

### Team members

- Jose Azzi
- Dia Hajjar
- Theresa Kozah

## 2. Cluster Architecture

The cluster consists of three physical laptops,
each hosting one Ubuntu virtual machine.

```text
              MPI CLUSTER OVER TAILSCALE

                  Encrypted Tailnet
                       |
         +-------------+-------------+
         |             |             |
     Jose's Mac    Dia's laptop  Theresa's laptop
         |             |             |
      Ubuntu VM     Ubuntu VM      Ubuntu VM
      heat-jose     heat-dia       heat-theresa
         |             |             |
   100.125.52.39 100.115.31.27 100.100.103.111
         |             |             |
         +-------------+-------------+
                       |
             Open MPI over TCP
                       |
               Tailscale Network
```

The three machines communicate through their
Tailscale IPv4 addresses.

Tailscale creates a private encrypted network,
allowing communication even when the laptops
are located behind different routers or NAT devices.

Open MPI uses:

- SSH to launch processes on remote machines.
- TCP for MPI communication.
- The tailscale0 interface for distributed communication.

Each Ubuntu VM acts as one compute node.

## 3. Hardware and Software Configuration

### Virtual machine specifications

| Specification | Jose | Dia | Theresa |
|---|---|---|---|
| Ubuntu hostname | heat-jose | heat-dia | heat-theresa |
| Operating system | Ubuntu 24.04.5 LTS | Ubuntu 24.04.5 LTS | Ubuntu 24.04.5 LTS |
| Architecture | ARM64 | x86-64 | x86-64 |
| Virtual CPUs | 2 | 2 | 2 |
| VM memory | 3.8 GiB | 1.9 GiB | 3.8 GiB |
| Open MPI | 4.1.6 | 4.1.6 | 4.1.6 |
| Tailscale IP | 100.125.52.39 | 100.115.31.27 | 100.100.103.111 |

### Host processor information

**Jose**

- Computer: Apple MacBook Pro.
- Model identifier: MacBookPro17,1.
- Processor: Apple M1.
- CPU cores: 8.
- Performance cores: 4.
- Efficiency cores: 4.
- Physical RAM: 8 GB.
- Virtualization software: Multipass.
- Virtual machine architecture: ARM64.
- VM allocated CPUs: 2.
- VM reported memory: approximately 3.8 GiB.

**Dia**

- Processor: 12th Gen Intel Core i5-1235U.
- VM architecture: x86-64.
- VM allocated CPUs: 2.
- VM reported memory: approximately 1.9 GiB.

**Theresa**

- Processor: 12th Gen Intel Core i7-1255U.
- VM architecture: x86-64.
- VM allocated CPUs: 2.
- VM reported memory: approximately 3.8 GiB.

### Architecture compatibility

All three virtual machines run Ubuntu 24.04.5 LTS
and Open MPI 4.1.6.

Jose's machine uses ARM64, while Dia's and Theresa's
machines use x86-64.

For distributed execution, the same source code
is compiled separately on each architecture.

The Makefile uses the following build options:

```bash
-O2 -std=c++17 -ffp-contract=off
```

The `-ffp-contract=off` option helps limit
architecture-dependent floating-point differences
caused by fused multiply-add operations.

The executable paths are kept consistent across
the three Ubuntu virtual machines.

### Resource requirement

The assignment specifies at least two virtual CPUs
and 4 GB RAM for each VM.

All three VMs provide two virtual CPUs.

The recorded memory configuration is shown in
the hardware table above. Dia's VM was measured
at approximately 1.9 GiB, below the specified
4 GB requirement.

## 4. Tailscale Network Configuration

### 4.1 Private network

Tailscale was installed inside each Ubuntu VM.

The three nodes use the following addresses:

| Node | Tailscale IPv4 |
|---|---|
| Jose | 100.125.52.39 |
| Dia | 100.115.31.27 |
| Theresa | 100.100.103.111 |

The following commands were used to inspect
Tailscale configuration and connectivity:

```bash
tailscale status
tailscale ip -4
tailscale netcheck
tailscale ping <peer-ip>
```

Tailscale connectivity was verified between
the machines during cluster setup and benchmarking.

### 4.2 Direct and DERP communication

Tailscale supports two connection modes.

**Direct connection**

Traffic passes directly between the peers using
an established encrypted peer-to-peer connection.

**DERP connection**

Traffic passes through a Tailscale relay server
when direct peer-to-peer connectivity is unavailable.

DERP relaying can introduce additional latency
and affect communication performance.

During the experiments, both DERP and Direct
connectivity were observed.

In particular, Jose–Theresa initially used
the Paris DERP relay in some tests before
direct connectivity was established.

### 4.3 Recorded Tailscale ping measurements

The following measurements were recorded during
the cluster testing sessions.

| Direction | Observed ping latency | Connection status |
|---|---:|---|
| Jose to Dia | 63 ms | Direct |
| Jose to Theresa | 77 ms | Direct |
| Jose to Theresa | 58 ms | Direct |
| Theresa to Jose | 122 ms | Direct |
| Dia to Theresa | 57 ms | Direct |
| Theresa to Dia | 67 ms | Direct |
| Theresa to Dia | 71 ms | Direct |
| Theresa to Dia | 144 ms | Direct |
| Jose to Theresa | Approximately 260–320 ms | Paris DERP |

The measurements show that Direct connectivity
was successfully established for all three
cross-machine pairs:

- Jose–Dia.
- Jose–Theresa.
- Dia–Theresa.

The observed ping latency varied across
measurements and communication directions.

This variation can result from differences in
network conditions, peer routing, Wi-Fi conditions,
network congestion, and Tailscale connection state.

The recorded ping values describe the connection
status at the time of each observation.

They are separate from the MPI ping-pong
measurements presented in Section 8.

### 4.4 Network observations

The cluster was able to establish direct encrypted
peer-to-peer communication between all three pairs.

Earlier DERP observations demonstrate the effect
that Tailscale routing can have on the network.

For example, Jose–Theresa was observed through
the Paris DERP relay with approximately
260–320 ms ping latency.

Later direct measurements included 77 ms and 58 ms.

This demonstrates that network path selection can
have a substantial impact on observed latency.

The complete routing state of every individual MPI
message was not continuously recorded. The reported
statuses therefore represent the actual observations
made during testing.

## 5. Passwordless SSH Configuration

Open MPI uses SSH to launch processes on remote
Ubuntu virtual machines.

SSH key-based authentication was configured
between participating nodes.

The main steps involved:

1. Creating SSH keys.
2. Authorizing the public keys on remote machines.
3. Accepting remote host keys.
4. Testing passwordless login.
5. Verifying remote command execution.

Example SSH key generation:

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
```

Example remote connectivity test:

```bash
ssh ubuntu@100.115.31.27 hostname
```

During testing from Theresa's VM, this command
successfully returned:

```text
heat-dia
```

Successful passwordless SSH allows `mpirun`
to launch remote processes without requesting
interactive passwords.

The SSH and MPI configuration was successfully
used for the distributed cluster tests.

## 6. Open MPI Configuration

Open MPI 4.1.6 is installed on all three nodes.

MPI programs are compiled from C++ source files
using the Open MPI compiler wrapper.

Example:

```bash
mpic++ -O2 -std=c++17 -ffp-contract=off \
    hello_mpi.cpp -o hello_mpi
```

The project includes a Makefile for compiling
the main applications.

### 6.1 MPI over Tailscale

The following Open MPI configuration options
were used for distributed execution:

```bash
--mca btl_tcp_if_include tailscale0
--mca oob_tcp_if_include tailscale0
--mca btl tcp,self
```

These options direct relevant MPI TCP and
control traffic through the Tailscale interface.

### 6.2 Cluster hostfile

The repository includes `hosts.example`
with the following configuration:

```text
100.125.52.39 slots=2
100.115.31.27 slots=2
100.100.103.111 slots=2
```

Each machine is configured with two MPI slots,
corresponding to its two virtual CPUs.

The hostfile declares a total of six
available MPI process slots.

### 6.3 Distributed MPI launch

A successful three-machine MPI launch used
the following configuration:

```bash
mpirun \
  --mca btl_tcp_if_include tailscale0 \
  --mca oob_tcp_if_include tailscale0 \
  --mca btl tcp,self \
  --host 100.125.52.39,100.115.31.27,100.100.103.111 \
  -np 3 hostname
```

This launches three processes across the
three Ubuntu virtual machines.

The executable is independently compiled
on the machines where required.

## 7. MPI Connectivity Verification

### 7.1 Three-node hostname test

The MPI hostname test was successfully executed
across all three virtual machines.

Recorded output:

```text
heat-jose
heat-dia
heat-theresa
```

This demonstrates that MPI could launch
a process on every participating machine.

The verification output is stored in:

```text
results/cluster/three_node_hostname.txt
```

### 7.2 MPI Hello World test

A C++ MPI Hello World application was compiled
and executed across the complete cluster.

The program reports:

- MPI process rank.
- Total number of MPI processes.
- Hostname of the executing machine.

The recorded output was:

```text
Hello from rank 0 of 3 on heat-jose
Hello from rank 1 of 3 on heat-dia
Hello from rank 2 of 3 on heat-theresa
```

The verification output is stored in:

```text
results/cluster/three_node_hello.txt
```

These results confirm:

- MPI successfully initialized across three nodes.
- All three nodes participated in the same execution.
- The process ranks were assigned correctly.
- MPI reported a communicator size of three.
- Remote execution worked through the Tailscale network.

### 7.3 Verification summary

The successful three-node hostname and MPI
Hello World tests validate the core distributed
cluster configuration.

The evidence files are committed to the
project's GitHub repository.

## 8. MPI Ping-Pong Benchmarks

### 8.1 Objective

MPI ping-pong experiments measure communication
time between two MPI ranks.

The procedure consists of:

1. Rank 0 sends a message to Rank 1.
2. Rank 1 receives the message.
3. Rank 1 immediately sends the message back.
4. Rank 0 receives the returning message.
5. The elapsed time is measured as round-trip time.
6. The measurement is repeated and averaged.

Warm-up communications are performed before
timed measurements.

### 8.2 Message sizes

The benchmark uses messages ranging from
8 bytes to 16 MiB, increasing by powers of two.

The message sizes are:

```text
8
16
32
64
128
256
512
1024
2048
4096
8192
16384
32768
65536
131072
262144
524288
1048576
2097152
4194304
8388608
16777216
```

There are 22 message sizes in total.

### 8.3 Communication configurations

Six configurations were measured.

**Local benchmarks**

1. Jose local.
2. Dia local.
3. Theresa local.

Both MPI ranks execute on the same VM.

**Cross-machine benchmarks**

4. Jose–Dia.
5. Jose–Theresa.
6. Dia–Theresa.

The two MPI ranks execute on separate VMs
and communicate through Tailscale.

### 8.4 Timing calculations

The benchmark measures average round-trip time:

```text
RTT = total measured round-trip time / repetitions
```

The estimated one-way communication time is:

```text
t_one_way = RTT / 2
```

This assumes approximately symmetric forward
and return communication.

The raw CSV files contain:

```text
bytes,rtt_seconds,one_way_seconds
```

### 8.5 Raw benchmark datasets

The six complete benchmark datasets are:

| Benchmark | CSV file | Maximum message |
|---|---|---|
| Jose local | pingpong_jose_local.csv | 16 MiB |
| Dia local | pingpong_dia_local.csv | 16 MiB |
| Theresa local | pingpong_theresa_local.csv | 16 MiB |
| Jose–Dia | pingpong_jose_dia.csv | 16 MiB |
| Jose–Theresa | pingpong_jose_theresa_16mb.csv | 16 MiB |
| Dia–Theresa | pingpong_dia_theresa_16mb.csv | 16 MiB |

Each full-range dataset contains measurements
for the expected 22 message sizes.

Historical intermediate CSV files were also
retained to preserve the progression of testing.

The original recorded measurement files have
not been altered by the plotting improvements.

### 8.6 Results interpretation

Local MPI communication is substantially faster
than communication between separate machines.

For local MPI, the two ranks operate within
the same VM, avoiding the distributed network.

For cross-machine MPI, messages traverse the
virtualized networking environment and Tailscale.

Communication performance is consequently
affected by network latency, bandwidth,
routing, and the relative performance of
the participating machines.

## 9. Communication Performance Model

### 9.1 Model definition

The project uses the communication model:

```text
t_msg(m) = ts + m * tw
```

Where:

- `m` is the message size in bytes.
- `ts` is the communication startup time in seconds.
- `tw` is the incremental transfer time per byte.
- `t_msg(m)` is the estimated one-way communication time.

The corresponding bandwidth is:

```text
Bandwidth (bytes/s) = 1 / tw
```

To express bandwidth in Mbps:

```text
Bandwidth (Mbps) = 8 / (tw * 1,000,000)
```

### 9.2 Initial linear regression

An ordinary linear fit was initially performed
using all message sizes.

The fit models:

```text
t_msg(m) = intercept + slope * m
```

For some local measurements, the resulting
intercepts were negative.

Negative communication startup latency is
not physically meaningful.

These values are artifacts of fitting a
single linear model across communication
regimes with different performance behavior.

The original model results were preserved
for transparent analysis.

### 9.3 Refined empirical model

A refined fitting procedure was implemented
to estimate the model parameters more
appropriately.

**Startup latency estimation**

Startup latency is estimated using the median
one-way time for messages of up to 1024 bytes.

```text
ts = median(t_one_way for m <= 1024 bytes)
```

**Bandwidth estimation**

The incremental transfer time is fitted
using messages of at least 1 MiB.

The startup estimate is held fixed.

For the large-message observations,
the transfer-time parameter is:

```text
tw = sum(m * (t_one_way - ts)) / sum(m^2)
```

Bandwidth is then calculated from `tw`.

### 9.4 Model validation

The fitted parameters are used to calculate
the predicted communication time:

```text
t_predicted(m) = ts + m * tw
```

Measured and predicted values are compared
on communication-model graphs.

The coefficient of determination, R-squared,
is calculated for the large-message fitting region.

The refined model is an empirical approximation,
rather than a guarantee that communication follows
a single linear relationship at every message size.

## 10. Communication Results

### 10.1 Refined model results

| Connection | Startup latency | Bandwidth | Large-message R² |
|---|---:|---:|---:|
| Jose local | 0.190 µs | 36658.571 Mbps | 0.9163 |
| Dia local | 0.406 µs | 37991.234 Mbps | 0.9700 |
| Theresa local | 0.404 µs | 41875.967 Mbps | 0.9843 |
| Jose–Dia | 32.217 ms | 6.890 Mbps | 0.9956 |
| Jose–Theresa | 33.019 ms | 6.375 Mbps | 0.9974 |
| Dia–Theresa | 39.775 ms | 5.066 Mbps | 0.9963 |

These are measured-model estimates derived from
the corresponding MPI ping-pong CSV files.

### 10.2 Communication status comparison

| Connection | Tailscale status | Recorded ping evidence |
|---|---|---|
| Jose local | Local MPI | Same VM |
| Dia local | Local MPI | Same VM |
| Theresa local | Local MPI | Same VM |
| Jose–Dia | Direct observed | 63 ms |
| Jose–Theresa | Direct observed; DERP also observed earlier | 58 ms, 77 ms Direct; approximately 260–320 ms DERP |
| Dia–Theresa | Direct observed | 57 ms, 67 ms, 71 ms, 144 ms Direct observations |

The three local benchmarks do not use a
cross-machine Tailscale network connection.

For the cross-machine benchmarks, Direct
connectivity was observed for every pair.

The connection status is based on the recorded
Tailscale tests. It describes observed routing
rather than continuous per-message monitoring.

### 10.3 Local communication

The local benchmarks produced approximate
startup estimates between:

```text
0.190 microseconds and 0.406 microseconds
```

Their fitted effective bandwidths ranged from
approximately:

```text
36.66 Gbps to 41.88 Gbps
```

These are application-level MPI communication
estimates, not physical network interface speeds.

### 10.4 Cross-machine communication

The cross-machine benchmarks produced startup
estimates ranging from approximately:

```text
32.217 ms to 39.775 ms
```

The fitted effective bandwidths ranged from:

```text
5.066 Mbps to 6.890 Mbps
```

Among the three cross-machine measurements:

- Jose–Dia had the highest fitted bandwidth.
- Jose–Theresa had the second-highest fitted bandwidth.
- Dia–Theresa had the lowest fitted bandwidth.

This difference can be influenced by network
conditions, routing, available throughput,
host performance, and other system effects.

### 10.5 Local versus distributed communication

Communication between ranks on the same VM
has far lower startup overhead than communication
between ranks on separate VMs.

The distributed benchmarks demonstrate why
communication overhead is an important factor
in the performance of parallel applications.

For relatively small computations, sending
data across the network can cost more than
performing the computation locally.

These measured parameters will be used in
the later performance models for the parallel
2D heat diffusion solver.

### 10.6 Statistical model quality

The R-squared values for the large-message
fits are:

```text
Jose local:       0.9163
Dia local:        0.9700
Theresa local:    0.9843
Jose–Dia:         0.9956
Jose–Theresa:     0.9974
Dia–Theresa:      0.9963
```

The high R-squared values for the cross-machine
datasets show that the refined model explains
much of the variation among the measured
large-message transfer times.

This does not imply that the same model is
equally accurate in the small-message region.

## 11. Results, Scripts and GitHub Repository

### 11.1 Project repository

The project source code and results are stored in:

https://github.com/joseazzi/parallele_programming

The repository includes:

- C++ source code.
- Build configuration.
- MPI cluster configuration.
- Benchmark CSV files.
- Python analysis scripts.
- Generated communication graphs.
- MPI verification evidence.
- Project documentation.

### 11.2 Benchmark data

The six full-range benchmark CSV files are:

```text
pingpong_jose_local.csv
pingpong_dia_local.csv
pingpong_theresa_local.csv
pingpong_jose_dia.csv
pingpong_jose_theresa_16mb.csv
pingpong_dia_theresa_16mb.csv
```

### 11.3 Analysis scripts

```text
scripts/analyze_pingpong.py
scripts/fit_pingpong_model.py
```

The scripts perform numerical analysis
and generate reproducible results.

### 11.4 Communication analysis results

```text
plots/pingpong_analysis.csv
plots/pingpong_latency.png
plots/pingpong_bandwidth.png
```

### 11.5 Communication-model results

```text
results/pingpong/communication_model.csv
results/pingpong/communication_model.png
results/pingpong/communication_model_refined.csv
results/pingpong/communication_model_refined.png
results/pingpong/communication_model_local.png
results/pingpong/communication_model_cross_machine.png
```

The separate local and cross-machine graphs
improve readability by avoiding large differences
in vertical scales on a single plot.

They show measured communication times
and the corresponding model predictions.

### 11.6 Cluster verification files

```text
results/cluster/three_node_hostname.txt
results/cluster/three_node_hello.txt
```

These files preserve the successful
three-machine MPI tests.

### 11.7 Build configuration

The project Makefile compiles the main
C++ programs using the documented compiler
flags.

Example:

```bash
make
```

The repository also includes `.gitignore`,
which excludes locally compiled executables
and temporary build files.

### 11.8 GitHub collaboration

Git and GitHub were used to preserve:

- Source-code changes.
- Benchmark datasets.
- Numerical analysis.
- Cluster documentation.
- Generated results.
- MPI testing evidence.

Contributors can independently compile
the source code for their own VM architecture.

## 12. Conclusion

Part 0 established a functioning three-machine
distributed-memory MPI cluster using:

- Ubuntu 24.04.5 LTS.
- Open MPI 4.1.6.
- SSH key-based authentication.
- Tailscale encrypted networking.
- Three separate physical computers.

Distributed execution was demonstrated through
successful three-node MPI hostname and Hello
World tests.

All six required MPI ping-pong configurations
were measured over the full message-size range
from 8 bytes to 16 MiB.

The measurements were analyzed using the
communication model:

```text
t_msg(m) = ts + m * tw
```

The analysis produced empirical estimates of
communication startup latency, transfer time
per byte, and effective bandwidth.

The local benchmarks produced much lower
communication startup times and much higher
effective bandwidth than the cross-machine runs.

Direct Tailscale connectivity was recorded for
all three machine pairs.

DERP connectivity was also observed during
the testing sessions, demonstrating that
routing conditions can influence performance.

The recorded connection evidence and benchmark
results have been retained in the project
documentation and repository.

The communication results provide the baseline
needed to investigate communication overhead,
domain decomposition, halo exchange and
strong/weak scaling in the later project parts.

The cluster implementation, numerical datasets,
analysis scripts and verification evidence are
available in the shared GitHub repository.
