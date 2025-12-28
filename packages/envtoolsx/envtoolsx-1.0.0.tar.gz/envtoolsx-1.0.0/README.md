# NetBenchKit

NetBenchKit is a transport-layer diagnostics toolkit designed for systems where TCP and UDP behavior directly impacts application performance.  
The library provides controlled benchmarking profiles, low-level socket probes, and reproducible metrics suitable for modern web infrastructure.

## Overview

NetBenchKit focuses on transport predictability under load.  
It evaluates handshake overhead, packet delivery precision, connection churn handling, and throughput consistency across a wide range of network conditions.

The toolkit is suitable for high-traffic services, API gateways, distributed pipelines, and testing environments that require deterministic network behavior analysis.

## Core Features

### Transport Analysis
- TCP handshake timing  
- UDP variance and packet drop behavior  
- Throughput and flow stability  
- Stall and retransmission indicators  
- Payload-level latency distributions

### Profiling Models
NetBenchKit provides configurable profiling modes for:
- Long-running persistent connections  
- High-frequency short-lived connections  
- Burst-pattern traffic  
- Mixed workloads reflecting typical web service pressure

### System Context
Optional OS-level insights include:
- NIC utilization
- Kernel buffer usage
- Socket queue saturation
- Latency fluctuation under resource contention

### Interoperability
The toolkit integrates cleanly with:
- Web servers
- API gateways
- Reverse and edge proxies
- Load-balancing layers
- Microservice performance pipelines

## Example

```python
from netbenchkit import TCPProfile, Benchmark

profile = TCPProfile(
    target="192.168.0.10:8080",
    connections=150,
    duration=10,
)

report = Benchmark(profile).run()
print(report.summary())
```