# Presentation Speaker Notes & Defense Guide
**Project:** Socket-Level Lightweight Detection of TCP Flooding Attacks in Edge Networks  
**Presentation File:** [`tcp_flood_detection_presentation.pptx`](file:///Users/raja/Documents/syn-edge-flooding/tcp_flood_detection_presentation.pptx)  
**Target Audience:** Professor / Academic Committee (Systems, Networking, Security)

---

## Slide-by-Slide Speaking Script & Defense Points

### Slide 1: Title Slide
- **What to Say:** 
  > "Good morning, Professor. Today I am presenting our empirical research on lightweight detection of TCP flooding attacks on resource-constrained Linux edge servers. Rather than running heavy packet inspection, we designed and evaluated a socket-level telemetry approach that monitors kernel state tables directly."
- **Key Emphasis:** Emphasize that this is an empirical lab with real cloud measurements across 65 runs on AWS EC2, not a pure simulation.

---

### Slide 2: The Problem: Edge Dilemma
- **What to Say:** 
  > "Edge servers (like 5G gateways, IoT aggregators, micro-proxies) face two bad choices today:
  > 1. Packet-level IDSes like Suricata or Snort consume 5% to 15% CPU and 140 MB of RAM because they copy packets to user space for deep inspection.
  > 2. Simple firewall thresholds drop traffic whenever volume surges. But during a legitimate flash crowd—like breaking news or a product release—it blocks paying users!
  > Our question was: Can we detect floods in under 2 seconds with less than 0.2% CPU while cleanly separating a flash crowd ('the wedding') from a flood ('the prank')?"

---

### Slide 3: Network Programming Under the Hood (Linux TCP Queues)
- **What to Say:** 
  > "To understand where attack signatures live, let's look at the Linux kernel TCP connection queues:
  > 1. When a SYN arrives, the kernel allocates a lightweight request socket in the Half-Open Queue (`TCP_SYN_RECV`).
  > 2. Once the 3-way handshake completes, the connection moves to the Accept Backlog in `TCP_ESTABLISHED` state.
  > 3. The user-space web server (Nginx) calls `accept()` to consume it.
  > Instead of capturing packets, our sampler reads `/proc/net/tcp`, `/proc/net/snmp`, and `/proc/net/netstat` at 1 Hz. It executes in just 0.64 milliseconds per sample without packet-copying overhead."
- **Expected Professor Question:** *"Doesn't reading `/proc/net/tcp` lock kernel socket tables?"*
- **Your Answer:** *"In modern Linux kernels (3.x through 6.8), `/proc/net/tcp` uses RCU (Read-Copy Update) and lockless socket iteration. Our measured sampling latency on an active 23k req/s server was only 0.64 ms, confirming negligible lock contention."*

---

### Slide 4: Testbed & Experimental Matrix
- **What to Say:** 
  > "We provisioned a 3-node isolated VPC on AWS EC2: a Victim server running Nginx with a backlog of 128, an Attacker node with `hping3` and connection hold tools, and a Client node running `wrk` and `ab`.
  > To ensure safety and reproducibility, all attacks were bound by an automated attack guard enforcing private VPC targets, a 60-second cap, and a 10,000 pps rate limit.
  > We ran 65 runs across 13 scenarios in randomized blocks, with a 100% completion rate and zero aborts."

---

### Slide 5: The Secret Metric: Handshake Completion Ratio (HCR)
- **What to Say:** 
  > "This is our primary feature innovation: the Handshake Completion Ratio (HCR).
  > We calculate completed handshakes (`PassiveOpens`) divided by total connection attempts (`PassiveOpens` + `ListenDrops` + half-open `syn_recv`).
  > Look at Figure F3 on the right: in baseline traffic and all three flash crowd intensities (Small, Medium, Large), HCR stays pinned at 1.0. But the moment a SYN flood starts, HCR collapses to near zero! This is the mathematical key that prevents false alarms."

---

### Slide 6: Detector Evolution (B1 $\to$ D1 $\to$ D2)
- **What to Say:** 
  > "We benchmarked three detectors:
  > 1. B1 is a static volume baseline (`syn_recv >= 16`).
  > 2. D1 is our adaptive dual-signal detector. It uses an EWMA to track baseline volume and HCR, alerting only when volume is elevated AND HCR is collapsed. Crucially, it freezes baseline updates during alarms so the attack cannot poison the baseline.
  > 3. D2 extends D1 with two branches: a Connection Flood branch that monitors established socket surges with high single-source concentration, and a Mitigation branch that monitors SYN cookie counters."

---

### Slide 7: Observation 1 — Flash Crowd vs. SYN Flood (Figure F2)
- **What to Say:** 
  > "Here is our side-by-side empirical contrast.
  > On the left (Flash Crowd, S1M), 30,000 requests hit the server. Notice that `syn_recv` barely rises above 4, and completion ratio remains at 1.0! D1 produces zero false alarms.
  > On the right (SYN Flood, S2M), `syn_recv` hits the 128-slot backlog within 2.3 seconds, and completion ratio plunges to zero. D1 alarms immediately."

---

### Slide 8: Observation 2 — The Connection Flood Blindspot (Figure F8)
- **What to Say:** 
  > "Now for our most critical systems discovery: Connection Hold Floods.
  > In a connection hold attack (S3), the attacker *does* complete the 3-way handshake! Because the handshake finishes, HCR is 1.0 and `syn_recv` is 0.
  > Both B1 and D1 were 100% blind to connection floods!
  > D2 solves this: it monitors `established` socket growth combined with `top_src_share`. In normal traffic, connections come from diverse IPs. In S3, a single IP holds 100% of established sockets. D2 catches 100% of connection floods in 1.2 seconds."

---

### Slide 9: Observation 3 — SYN Cookie Mitigation Dynamics (Figure F6)
- **What to Say:** 
  > "When Linux SYN cookies are turned on (`S5`), the kernel stops allocating half-open socket state in memory. Attack sockets never appear in `syn_recv`!
  > As shown in Figure F6, SYN cookies protect client probe availability (restoring success from 40% to 99.8%). But naive monitors think the server is idle!
  > D2's mitigation branch monitors `SyncookiesSent` in `/proc/net/netstat`, which spikes to 10,700 cookies/s during attack, raising an alert within 1.15 seconds."

---

### Slide 10: Benchmark Results (Test Set Performance)
- **What to Say:** 
  > "Following strict academic protocol, we tuned hyperparameters on Repetitions 1 to 3 (39 runs), and evaluated performance strictly on held-out Repetitions 4 and 5 (26 runs).
  > As shown in Table T2:
  > - D2 achieved 100.0% Detection Rate across all attack categories with a median delay of just 1.19 seconds and an AUC-ROC of 0.9331.
  > - B1 and D1 achieved only 66.7% recall because they missed connection-hold attacks."

---

### Slide 11: Edge Resource Overhead (Figure F7)
- **What to Say:** 
  > "Finally, resource overhead:
  > Compared to Suricata (4.80% CPU and 142 MB RAM), our D2 socket detector consumes only 0.18% CPU and 15.6 MB RAM.
  > That is a 96.2% reduction in CPU utilization and an 89% reduction in RAM, proving this can run continuously on production edge hardware."

---

### Slide 12: Threats to Validity
- **What to Say:** 
  > "We actively document our experimental limitations:
  > 1. Single-source attacker due to AWS VPC anti-spoofing (real-world DDoS requires entropy-based features).
  > 2. Flash crowd traffic came from a single client instance, though HCR is invariant to IP distribution.
  > 3. Synthetic workloads (`ab`, `wrk`) test transport L4 mechanics but lack human think-time.
  > 4. Evaluated on Linux 6.8 (Ubuntu 24.04), though `/proc/net/` interfaces have been stable since Linux 2.6."

---

### Slide 13: Conclusion
- **What to Say:** 
  > "In conclusion:
  > 1. Socket telemetry is fully sufficient for high-accuracy flood detection without packet inspection.
  > 2. Handshake Completion Ratio completely solves the flash crowd false alarm problem.
  > 3. Connection floods and SYN cookies require multi-queue state tracking.
  > 4. D2 provides 100% recall with 96% lower CPU overhead.
  > Thank you! I would be delighted to answer any questions."

