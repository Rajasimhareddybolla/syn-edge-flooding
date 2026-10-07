want to run this 

Here's a first draft. The brackets are results you'll fill in after your experiments.

**Draft abstract**

TCP flooding attacks, such as SYN floods and connection floods, exhaust a server's connection resources and deny service to legitimate users. Edge networks are especially vulnerable because their devices have limited CPU and memory, which rules out heavy packet-inspection or machine-learning detectors. Lightweight volume-based rules are cheap, but they often misclassify legitimate flash crowds as attacks.

This work proposes a socket-level detector that monitors the operating system's connection-state table instead of inspecting packets. It tracks a small set of features, namely half-open connection count, handshake completion ratio, and established-connection growth, and raises an alarm only when abnormal volume coincides with poor completion, using an adaptive moving-average baseline.

We evaluate the detector in an AWS-based testbed under normal traffic, flash crowds, SYN floods of varying intensity, and floods hidden within flash crowds. Results show a detection rate of [X%], a false-alarm rate of [Y%] on flash crowds, and a detection time of [Z seconds], with [N%] lower CPU overhead than a packet-level IDS.

**Why it's built this way**
- Paragraph 1: problem and gap
- Paragraph 2: your idea
- Paragraph 3: how you'll prove it



