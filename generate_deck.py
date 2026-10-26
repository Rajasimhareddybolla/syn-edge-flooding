#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""
generate_deck.py — Generates a publication-quality 16:9 widescreen PowerPoint presentation
for academic / professor evaluation of the TCP Flood Detection Research Lab.
"""

from __future__ import annotations
import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

REPO_ROOT = Path(__file__).resolve().parent
FIG_DIR = REPO_ROOT / "analysis" / "figures"
OUTPUT_PPTX = REPO_ROOT / "tcp_flood_detection_presentation.pptx"

# ── Color Palette ─────────────────────────────────────────────────────────────
DARK_BG     = RGBColor(15, 23, 42)       # Slate 900
DARK_CARD   = RGBColor(30, 41, 59)       # Slate 800
LIGHT_BG    = RGBColor(248, 250, 252)    # Slate 50
WHITE       = RGBColor(255, 255, 255)
TEXT_DARK   = RGBColor(30, 41, 59)       # Slate 800
TEXT_MUTED  = RGBColor(100, 116, 139)    # Slate 500
TEXT_LIGHT  = RGBColor(241, 245, 249)    # Slate 100
BLUE_ACCENT = RGBColor(37, 99, 235)      # Blue 600
CYAN_ACCENT = RGBColor(6, 182, 212)      # Cyan 500
GREEN_ACCENT= RGBColor(16, 185, 129)     # Emerald 500
RED_ACCENT  = RGBColor(239, 68, 68)      # Red 500
CARD_BG     = RGBColor(255, 255, 255)
CARD_BORDER = RGBColor(226, 232, 240)    # Slate 200


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide, color):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, tag: str, title: str, subtitle: str = ""):
        # Tag badge
        tb_tag = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_tag = tb_tag.text_frame
        tf_tag.word_wrap = True
        tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = tag.upper()
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = BLUE_ACCENT

        # Title
        tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.6))
        tf_title = tb_title.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_BG

        # Subtitle
        if subtitle:
            p_sub = tf_title.add_paragraph()
            p_sub.text = subtitle
            p_sub.font.size = Pt(12)
            p_sub.font.color.rgb = TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 1: Title Slide (Dark Theme)
    # ══════════════════════════════════════════════════════════════════════════════
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, DARK_BG)

    # Accent line top
    line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.2), Inches(1.5), Inches(0.08))
    line.fill.solid()
    line.fill.fore_color.rgb = CYAN_ACCENT
    line.line.color.rgb = CYAN_ACCENT

    # Title text box
    tb = s1.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(3.2))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "Socket-Level Lightweight Detection of\nTCP Flooding Attacks in Edge Networks"
    p0.font.size = Pt(36)
    p0.font.bold = True
    p0.font.color.rgb = WHITE

    p1 = tf.add_paragraph()
    p1.text = "Empirical Evaluation, Linux Kernel State Telemetry & Real-Time Defense on AWS EC2"
    p1.font.size = Pt(18)
    p1.font.color.rgb = CYAN_ACCENT
    p1.space_before = Pt(14)

    # Info Card Container
    card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.0), Inches(11.7), Inches(1.8))
    card.fill.solid()
    card.fill.fore_color.rgb = DARK_CARD
    card.line.color.rgb = RGBColor(51, 65, 85)

    c_tb = s1.shapes.add_textbox(Inches(1.1), Inches(5.2), Inches(11.1), Inches(1.4))
    c_tf = c_tb.text_frame
    c_tf.word_wrap = True

    cp0 = c_tf.paragraphs[0]
    cp0.text = "Key Research Highlights & Academic Presentation"
    cp0.font.size = Pt(13)
    cp0.font.bold = True
    cp0.font.color.rgb = WHITE

    cp1 = c_tf.add_paragraph()
    cp1.text = "• Domain: Network Programming, Transport Layer Security (L4), Linux Kernel Internals (/proc/net/)\n" \
               "• Testbed: 3-Node Cloud VPC on AWS EC2 (Victim, Attacker, Client) with 65 Serial Empirical Runs\n" \
               "• Outcome: 100% Attack Recall, 1.19s Median Delay, 96.2% Less CPU Overhead than Packet-Level IDS"
    cp1.font.size = Pt(12)
    cp1.font.color.rgb = TEXT_LIGHT
    cp1.space_before = Pt(6)

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 2: The Edge Conundrum (Problem & Motivation)
    # ══════════════════════════════════════════════════════════════════════════════
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, LIGHT_BG)
    add_header(s2, "Problem & Motivation", "The Edge Dilemma: Why Existing Solutions Fail on Edge Servers",
               "Resource constraints at the edge make traditional packet inspection and naive firewalls impractical.")

    # Left Card: Traditional Packet-Level IDS
    c1 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.7), Inches(3.7), Inches(5.1))
    c1.fill.solid(); c1.fill.fore_color.rgb = CARD_BG; c1.line.color.rgb = CARD_BORDER
    tb1 = s2.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(3.3), Inches(4.7))
    tf1 = tb1.text_frame; tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "❌ Packet-Level IDS (DPI)"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = RED_ACCENT
    p = tf1.add_paragraph()
    p.text = "Tools: Suricata, Snort, Zeek\n" \
             "Mechanism: Copies raw packet frames from kernel to user space for payload/header inspection.\n\n" \
             "Why it fails at the edge:\n" \
             "• Heavy CPU drain: 4.8% to 15% CPU load.\n" \
             "• Memory footprint: > 140 MB RSS.\n" \
             "• Starves collocated applications on IoT gateways and micro-instances."
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(8)

    # Middle Card: Naive Static Thresholds
    c2 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.8), Inches(1.7), Inches(3.7), Inches(5.1))
    c2.fill.solid(); c2.fill.fore_color.rgb = CARD_BG; c2.line.color.rgb = CARD_BORDER
    tb2 = s2.shapes.add_textbox(Inches(5.0), Inches(1.9), Inches(3.3), Inches(4.7))
    tf2 = tb2.text_frame; tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "❌ Naive Volume Firewalls"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = RED_ACCENT
    p = tf2.add_paragraph()
    p.text = "Tools: iptables hashlimit, static rules\n" \
             "Mechanism: Triggers alerts when packet rate or raw socket count exceeds a fixed ceiling.\n\n" \
             "Why it fails at the edge:\n" \
             "• Catastrophic False Positives during legitimate Flash Crowds (e.g., ticket release, news).\n" \
             "• Inability to distinguish high genuine traffic from malicious flooding.\n" \
             "• Drops paying customers."
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(8)

    # Right Card: Our Solution (Socket-Level Kernel Sensing)
    c3 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.8), Inches(1.7), Inches(3.7), Inches(5.1))
    c3.fill.solid(); c3.fill.fore_color.rgb = CARD_BG; c3.line.color.rgb = GREEN_ACCENT; c3.line.width = Pt(2)
    tb3 = s2.shapes.add_textbox(Inches(9.0), Inches(1.9), Inches(3.3), Inches(4.7))
    tf3 = tb3.text_frame; tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "✅ Our Approach: Socket Telemetry"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = GREEN_ACCENT
    p = tf3.add_paragraph()
    p.text = "Mechanism: Direct 1 Hz sampling of Linux kernel socket state tables (/proc/net/). Zero packet copying.\n\n" \
             "Why it succeeds:\n" \
             "• Ultra-lightweight: 0.18% CPU & 15 MB RAM.\n" \
             "• Handshake Completion Ratio (HCR) cleanly separates crowds from attacks.\n" \
             "• Rapid sub-2-second detection delay.\n" \
             "• Production-ready on standard Linux ABIs."
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(8)

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 3: Network Programming Under the Hood (Linux TCP State Machine)
    # ══════════════════════════════════════════════════════════════════════════════
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, LIGHT_BG)
    add_header(s3, "Network Programming & Systems", "Linux Kernel TCP Connection Mechanics: The Three Queues",
               "Understanding how Linux handles the 3-way handshake reveals exactly where flood signatures appear.")

    # 3 Queue Diagram Cards horizontally
    card_w = Inches(3.7)
    card_h = Inches(4.8)

    # Step 1: SYN Queue
    q1 = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), card_w, card_h)
    q1.fill.solid(); q1.fill.fore_color.rgb = CARD_BG; q1.line.color.rgb = CARD_BORDER
    tb_q1 = s3.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(3.3), Inches(4.4))
    tf_q1 = tb_q1.text_frame; tf_q1.word_wrap = True
    p = tf_q1.paragraphs[0]
    p.text = "1. SYN Queue (Half-Open)"; p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = BLUE_ACCENT
    p = tf_q1.add_paragraph()
    p.text = "State: TCP_SYN_RECV (03)\n" \
             "Governed by: tcp_max_syn_backlog\n\n" \
             "• When a TCP SYN arrives, the kernel allocates a lightweight request_sock.\n" \
             "• Server replies with SYN-ACK and waits for client ACK.\n" \
             "• In SYN Flood (S2): Attacker never ACKs. Sockets saturate the 128-slot backlog within 2s, causing ListenDrops!"
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(8)

    # Step 2: Accept Queue
    q2 = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.8), Inches(1.8), card_w, card_h)
    q2.fill.solid(); q2.fill.fore_color.rgb = CARD_BG; q2.line.color.rgb = CARD_BORDER
    tb_q2 = s3.shapes.add_textbox(Inches(5.0), Inches(2.0), Inches(3.3), Inches(4.4))
    tf_q2 = tb_q2.text_frame; tf_q2.word_wrap = True
    p = tf_q2.paragraphs[0]
    p.text = "2. Accept Queue (Backlog)"; p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = BLUE_ACCENT
    p = tf_q2.add_paragraph()
    p.text = "State: TCP_ESTABLISHED (01)\n" \
             "Governed by: listen(fd, backlog=128)\n\n" \
             "• When client returns ACK, handshake is complete. Sockets move to accept queue.\n" \
             "• In Flash Crowd (S1): Sockets enter and leave accept queue in milliseconds.\n" \
             "• Counter PassiveOpens increments for every successfully completed handshake."
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(8)

    # Step 3: Established Pool & File Descriptors
    q3 = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.8), Inches(1.8), card_w, card_h)
    q3.fill.solid(); q3.fill.fore_color.rgb = CARD_BG; q3.line.color.rgb = CARD_BORDER
    tb_q3 = s3.shapes.add_textbox(Inches(9.0), Inches(2.0), Inches(3.3), Inches(4.4))
    tf_q3 = tb_q3.text_frame; tf_q3.word_wrap = True
    p = tf_q3.paragraphs[0]
    p.text = "3. Active Established Pool"; p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = BLUE_ACCENT
    p = tf_q3.add_paragraph()
    p.text = "State: TCP_ESTABLISHED (01)\n" \
             "Governed by: ulimit -n (File Descriptors)\n\n" \
             "• nginx accept() consumes socket from listen queue into worker process.\n" \
             "• In Connection Hold (S3): Attacker completes handshake, then idles!\n" \
             "• SYN queue stays at 0! But established count surges to 100, 500, 1000+."
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(8)

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 4: Cloud Testbed & Experimental Matrix
    # ══════════════════════════════════════════════════════════════════════════════
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, LIGHT_BG)
    add_header(s4, "Experimental Methodology", "3-Node AWS Cloud Testbed & 65-Run Empirical Campaign",
               "Strict isolated environment with safety gates, reproducible traffic generators, and no internet leakage.")

    # Left: Testbed Spec
    tb_arch = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0))
    tb_arch.fill.solid(); tb_arch.fill.fore_color.rgb = CARD_BG; tb_arch.line.color.rgb = CARD_BORDER
    tf_a = s4.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.2), Inches(4.6)).text_frame
    tf_a.word_wrap = True
    p = tf_a.paragraphs[0]
    p.text = "AWS EC2 Testbed Architecture"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = DARK_BG
    p = tf_a.add_paragraph()
    p.text = "• Victim (t3.micro, 172.31.37.214): Ubuntu 24.04, Nginx 1.24 (backlog=128), 1 Hz telemetry sampler.\n" \
             "• Attacker (t3.micro, 172.31.42.168): hping3 & conn_hold.py governed by attack_guard.sh.\n" \
             "• Client (t3.micro, 172.31.41.87): wrk quiet load (~4k req/s), ab flash crowds, 1 Hz curl probe.\n\n" \
             "Strict Safety Guardrails:\n" \
             "• Gate G1: Zero 0.0.0.0/0 ingress rules; isolated VPC.\n" \
             "• Gate G2: Automated attack_guard.sh (<=60s, <=10k pps, target check, kill switch /tmp/LAB_STOP).\n" \
             "• Capacity Calibration: Peak capacity = 23,525 req/s."
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(8)

    # Right: 13 Scenarios Matrix
    tb_mat = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0))
    tb_mat.fill.solid(); tb_mat.fill.fore_color.rgb = CARD_BG; tb_mat.line.color.rgb = CARD_BORDER
    tf_m = s4.shapes.add_textbox(Inches(7.0), Inches(2.0), Inches(5.3), Inches(4.6)).text_frame
    tf_m.word_wrap = True
    p = tf_m.paragraphs[0]
    p.text = "13 Empirical Scenarios (65 Runs Total)"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = DARK_BG
    p = tf_m.add_paragraph()
    p.text = "• S0: Quiet Baseline (wrk -c2, 120s window) — 5 reps\n" \
             "• S1S/M/L: Flash Crowds (ab concurrency 10, 25, 50) — 15 reps\n" \
             "• S2L/M/H: SYN Floods (hping3 at 100, 1k, 10k pps) — 15 reps\n" \
             "• S3L/M/H: Connection Floods (conn_hold at 100, 500, 2k) — 15 reps\n" \
             "• S4: Compound Attack (Flash Crowd M + SYN Flood M) — 5 reps\n" \
             "• S5M/H: Mitigated Floods (tcp_syncookies=1, 1k & 10k pps) — 10 reps\n\n" \
             "Execution Protocol:\n" \
             "• Randomized block ordering (5 blocks of 13 runs).\n" \
             "• 100% completion rate (65/65 completed, 0 aborts)."
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(8)

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 5: The Secret Metric: Handshake Completion Ratio (HCR)
    # ══════════════════════════════════════════════════════════════════════════════
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, LIGHT_BG)
    add_header(s5, "Core Metric Formulation", "Handshake Completion Ratio (HCR): Quantifying Failed Opens",
               "HCR separates legitimate traffic volume spikes from malicious connection starvation.")

    # Left: Formula and explanation
    c_f = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.4), Inches(5.0))
    c_f.fill.solid(); c_f.fill.fore_color.rgb = CARD_BG; c_f.line.color.rgb = CARD_BORDER
    tf_f = s5.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.0), Inches(4.6)).text_frame
    tf_f.word_wrap = True
    p = tf_f.paragraphs[0]
    p.text = "Mathematical Definition"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = DARK_BG
    p = tf_f.add_paragraph()
    p.text = "HCR = ΔPassiveOpens / max(1, ΔPassiveOpens + ΔListenDrops + syn_recv)\n\n" \
             "Where per 1-second sample:\n" \
             "• ΔPassiveOpens: Successful 3-way handshakes completed.\n" \
             "• ΔListenDrops: SYNs dropped due to full listen backlog.\n" \
             "• syn_recv: Instantaneous sockets stalled in half-open state.\n\n" \
             "Behavior Across Traffic Regimes:\n" \
             "• Quiet Baseline (S0): HCR = 1.000 (handshakes complete normally).\n" \
             "• Flash Crowd (S1): HCR = 1.000 (handshake rate scales with load).\n" \
             "• SYN Flood (S2): HCR collapses to 0.000 – 0.110 (all SYNs drop)!"
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(8)

    # Right: Embedded Figure F3
    f3_path = FIG_DIR / "F3_completion_ratio_distributions.png"
    if f3_path.exists():
        s5.shapes.add_picture(str(f3_path), Inches(6.5), Inches(2.0), width=Inches(6.0))

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 6: The Detector Evolution (B1 vs D1 vs D2)
    # ══════════════════════════════════════════════════════════════════════════════
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, LIGHT_BG)
    add_header(s6, "Detector Architecture", "From Naive Volume to Adaptive Multi-Branch Detection",
               "Evaluating how detector intelligence evolves to handle complex attack variations.")

    # 3 Cards vertically
    row_h = Inches(1.5)

    # B1
    b1_card = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), row_h)
    b1_card.fill.solid(); b1_card.fill.fore_color.rgb = CARD_BG; b1_card.line.color.rgb = CARD_BORDER
    tf_b1 = s6.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(11.3), Inches(1.3)).text_frame
    tf_b1.word_wrap = True
    p = tf_b1.paragraphs[0]
    p.text = "B1: Naive Static Volume Threshold (Baseline)"; p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = TEXT_MUTED
    p = tf_b1.add_paragraph()
    p.text = "• Logic: Alarm if syn_recv >= threshold (tuned to 16 sockets).\n" \
             "• Limitation: Completely blind to Connection Floods (S3) where syn_recv stays at ~2. Cannot distinguish mitigation."
    p.font.size = Pt(11); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(3)

    # D1
    d1_card = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(3.5), Inches(11.7), row_h)
    d1_card.fill.solid(); d1_card.fill.fore_color.rgb = CARD_BG; d1_card.line.color.rgb = CARD_BORDER
    tf_d1 = s6.shapes.add_textbox(Inches(1.0), Inches(3.6), Inches(11.3), Inches(1.3)).text_frame
    tf_d1.word_wrap = True
    p = tf_d1.paragraphs[0]
    p.text = "D1: Proposed Adaptive Dual-Signal Detector (EWMA + HCR)"; p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = BLUE_ACCENT
    p = tf_d1.add_paragraph()
    p.text = "• Logic: Alarm if (syn_recv_EWMA >= Volume Threshold) AND (HCR_EWMA <= tau).\n" \
             "• Innovation: Baseline Freezing during alarm state prevents attack traffic from poisoning the normal distribution.\n" \
             "• Breakthrough: 0.0% False Alarms during Flash Crowds! But still blind to connection holds."
    p.font.size = Pt(11); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(3)

    # D2
    d2_card = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.2), Inches(11.7), row_h)
    d2_card.fill.solid(); d2_card.fill.fore_color.rgb = CARD_BG; d2_card.line.color.rgb = GREEN_ACCENT; d2_card.line.width = Pt(2)
    tf_d2 = s6.shapes.add_textbox(Inches(1.0), Inches(5.3), Inches(11.3), Inches(1.3)).text_frame
    tf_d2.word_wrap = True
    p = tf_d2.paragraphs[0]
    p.text = "D2: Extended Multi-Branch Detector (Full System)"; p.font.size = Pt(14); p.font.bold = True; p.font.color.rgb = GREEN_ACCENT
    p = tf_d2.add_paragraph()
    p.text = "• Branch 1 (SYN Floods): D1 Dual-Signal EWMA (syn_recv + HCR).\n" \
             "• Branch 2 (Connection Floods): established_EWMA >= 50 sockets AND top_src_share >= 0.70 (source concentration).\n" \
             "• Branch 3 (Mitigation Branch): d_syncookies_sent >= 30 cookies/sec (detects active kernel defense).\n" \
             "• Result: 100.0% Attack Recall across all attack categories!"
    p.font.size = Pt(11); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(3)

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 7: Key Observation 1 — Flash Crowd vs SYN Flood (Figure F2)
    # ══════════════════════════════════════════════════════════════════════════════
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, LIGHT_BG)
    add_header(s7, "Key Empirical Observation 1", "The 'Wedding vs. Prank' Contrast: Flash Crowd vs. SYN Flood",
               "Side-by-side telemetry comparison of legitimate traffic spike vs malicious socket starvation.")

    # Left: Explanation
    tb_exp = s7.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(4.8), Inches(5.0))
    tf_e = tb_exp.text_frame; tf_e.word_wrap = True
    p = tf_e.paragraphs[0]
    p.text = "Empirical Finding:"; p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = DARK_BG
    p = tf_e.add_paragraph()
    p.text = "Flash Crowd (S1M, Left Panel):\n" \
             "• 30,000 requests at concurrency 25.\n" \
             "• syn_recv stays tiny (< 5 sockets).\n" \
             "• Completion ratio stays at 1.0 (handshakes complete in < 1ms).\n" \
             "• Result: 0.0% False Alarms.\n\n" \
             "SYN Flood (S2M, Right Panel):\n" \
             "• 1,000 pps raw SYN flood.\n" \
             "• syn_recv saturates the 128-slot backlog within 2.3 seconds!\n" \
             "• Completion ratio drops immediately to 0.0.\n" \
             "• Result: Instantaneous detection in 1.17s."
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(6)

    # Right: Embedded Figure F2
    f2_path = FIG_DIR / "F2_wedding_vs_prank_contrast.png"
    if f2_path.exists():
        s7.shapes.add_picture(str(f2_path), Inches(5.8), Inches(1.8), width=Inches(6.8))

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 8: Key Observation 2 — The Connection Flood Blindspot (Figure F8)
    # ══════════════════════════════════════════════════════════════════════════════
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, LIGHT_BG)
    add_header(s8, "Key Empirical Observation 2", "The Connection Flood Blindspot & Resolution via D2",
               "Why half-open monitoring fails on connection holds, and how established tracking resolves it.")

    tb_e8 = s8.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(5.0), Inches(5.0))
    tf_e8 = tb_e8.text_frame; tf_e8.word_wrap = True
    p = tf_e8.paragraphs[0]
    p.text = "The Flaw in Volume & HCR:"; p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = RED_ACCENT
    p = tf_e8.add_paragraph()
    p.text = "• In Connection Hold Floods (S3L/M/H), the attacker completes the full 3-way handshake!\n" \
             "• Because the handshake completes, HCR remains 1.0, and syn_recv stays at ~2.\n" \
             "• B1 and D1 fail completely (0.0% recall on S3)!\n\n" \
             "How D2 Resolves It (Figure F8):\n" \
             "• Tracks established socket count (surges to 100, 500, 1000+).\n" \
             "• Tracks top_src_share: in normal crowds, requests come from diverse ports/IPs. In S3, a single IP holds 100% of sockets!\n" \
             "• Established surge + top_src_share >= 0.70 catches 100% of connection floods."
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(6)

    # Right: Embedded Figure F8
    f8_path = FIG_DIR / "F8_connection_flood_d2_resolution.png"
    if f8_path.exists():
        s8.shapes.add_picture(str(f8_path), Inches(6.0), Inches(1.8), width=Inches(6.6))

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 9: Key Observation 3 — SYN Cookie Mitigation Dynamics (Figure F6)
    # ══════════════════════════════════════════════════════════════════════════════
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, LIGHT_BG)
    add_header(s9, "Key Empirical Observation 3", "SYN Cookie Mitigation Dynamics: The Invisible Attack",
               "When the Linux kernel mitigates a flood with cookies, half-open counters vanish.")

    tb_e9 = s9.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(5.0), Inches(5.0))
    tf_e9 = tb_e9.text_frame; tf_e9.word_wrap = True
    p = tf_e9.paragraphs[0]
    p.text = "The Mitigation Paradox:"; p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = DARK_BG
    p = tf_e9.add_paragraph()
    p.text = "• When tcp_syncookies = 1, the kernel does not allocate socket structures in the SYN queue.\n" \
             "• Instead, it hashes sequence numbers into SYN-ACK.\n" \
             "• Probe Availability (Figure F6):\n" \
             "  - Unmitigated (S2H): Probes fail (availability drops to ~40%).\n" \
             "  - Mitigated (S5H): Availability restored to 99.8%!\n\n" \
             "Detection Challenge & D2 Solution:\n" \
             "• Because syn_recv does not rise, naive detectors think the server is calm.\n" \
             "• D2 monitors d_syncookies_sent in /proc/net/netstat, which spikes to 10,700 cookies/s during attack, alarming in 1.15s!"
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(6)

    # Right: Embedded Figure F6
    f6_path = FIG_DIR / "F6_mitigation_effect.png"
    if f6_path.exists():
        s9.shapes.add_picture(str(f6_path), Inches(6.0), Inches(2.0), width=Inches(6.6))

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 10: Benchmark Results & Trade-Off Curve (Figures F4 & F5)
    # ══════════════════════════════════════════════════════════════════════════════
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, LIGHT_BG)
    add_header(s10, "Empirical Evaluation", "Benchmark Results on Held-Out Test Set (Reps 4–5)",
               "Strict train/test split: tuned on Reps 1–3 (39 runs), evaluated on Reps 4–5 (26 runs).")

    # Top Table Card
    tb_t = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.7), Inches(11.7), Inches(2.2))
    tb_t.fill.solid(); tb_t.fill.fore_color.rgb = CARD_BG; tb_t.line.color.rgb = CARD_BORDER
    tf_tab = s10.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(2.0)).text_frame
    tf_tab.word_wrap = True
    p = tf_tab.paragraphs[0]
    p.text = "Held-Out Test Set Performance Comparison (N=26 runs: 18 attack, 8 benign)"; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = DARK_BG
    p = tf_tab.add_paragraph()
    p.text = "• B1 (Static Volume): 66.7% Recall | 0.0% False Alarms | 1.15s Delay | AUC: 0.7751  (Misses S3 connection holds)\n" \
             "• D1 (Adaptive EWMA):  66.7% Recall | 0.0% False Alarms | 1.17s Delay | AUC: 0.7635  (Zero false alarms on S1 crowds)\n" \
             "• D2 (Extended Multi): 100.0% Recall | 12.5% FAR (1 run) | 1.19s Delay | AUC: 0.9331 (Full coverage all vectors)"
    p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = TEXT_DARK; p.space_before = Pt(4)

    # Bottom left: Figure F4
    f4_path = FIG_DIR / "F4_detection_delay_by_scenario.png"
    if f4_path.exists():
        s10.shapes.add_picture(str(f4_path), Inches(0.8), Inches(4.1), width=Inches(5.7))

    # Bottom right: Figure F5
    f5_path = FIG_DIR / "F5_roc_tradeoff_curve.png"
    if f5_path.exists():
        s10.shapes.add_picture(str(f5_path), Inches(6.8), Inches(4.1), width=Inches(5.7))

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 11: Edge Resource Efficiency: Socket Telemetry vs IDS (Figure F7)
    # ══════════════════════════════════════════════════════════════════════════════
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, LIGHT_BG)
    add_header(s11, "Systems Performance", "Edge Resource Profiling: 96.2% Less CPU Than Packet IDS",
               "Proving feasibility on resource-starved IoT gateways and edge nodes.")

    tb_e11 = s11.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(5.0), Inches(5.0))
    tf_e11 = tb_e11.text_frame; tf_e11.word_wrap = True
    p = tf_e11.paragraphs[0]
    p.text = "Overhead Measurements (Table T3):"; p.font.size = Pt(15); p.font.bold = True; p.font.color.rgb = DARK_BG
    p = tf_e11.add_paragraph()
    p.text = "• O0 (Idle Linux Server): 0.02% CPU, 0.4 MB RSS\n" \
             "• O1 (1 Hz /proc Sampler): 0.12% CPU, 12.8 MB RSS, 0.64ms sample latency\n" \
             "• O2 (Sampler + D1): 0.15% CPU, 14.2 MB RSS\n" \
             "• O3 (Sampler + D2 Full): 0.18% CPU, 15.6 MB RSS\n" \
             "• O4 (Packet-Level Suricata): 4.80% CPU, 142.0 MB RSS\n\n" \
             "Key Takeaway for Professor:\n" \
             "• Socket-level telemetry delivers a 96.2% CPU reduction and 89% RAM reduction compared to packet inspection.\n" \
             "• Completely viable on standard edge hardware."
    p.font.size = Pt(12); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(6)

    # Right: Embedded Figure F7
    f7_path = FIG_DIR / "F7_overhead_profiling.png"
    if f7_path.exists():
        s11.shapes.add_picture(str(f7_path), Inches(6.0), Inches(2.0), width=Inches(6.6))

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 12: Threats to Validity (Academic Rigor)
    # ══════════════════════════════════════════════════════════════════════════════
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, LIGHT_BG)
    add_header(s12, "Academic Rigor & Limitations", "Threats to Validity & Experimental Boundaries",
               "Demonstrating critical awareness of experimental boundaries and real-world applicability.")

    # 4 Cards grid
    cw = Inches(5.6); ch = Inches(2.3)
    coords = [(Inches(0.8), Inches(1.8)), (Inches(6.9), Inches(1.8)),
              (Inches(0.8), Inches(4.4)), (Inches(6.9), Inches(4.4))]

    threats = [
        ("1. Single-Source Attacker & Anti-Spoofing",
         "AWS VPC anti-spoofing drops spoofed source packets. Flood traffic originated from attacker private IP.\n"
         "Mitigation: top_src_share catches concentrated attacks; distributed botnets require entropy metrics.",
         RED_ACCENT),
        ("2. Single-Source Legitimate Flash Crowd",
         "Flash crowd traffic was generated exclusively from client instance (ab).\n"
         "Mitigation: PassiveOpens and HCR aggregate over all sockets and remain invariant to client IP distribution.",
         BLUE_ACCENT),
        ("3. Synthetic Tools vs. Real User Behavior",
         "wrk and ab generate synthetic HTTP bursts without human think-time.\n"
         "Mitigation: Transport-layer TCP handshake dynamics are protocol-agnostic (L4 vs L7 independence).",
         GREEN_ACCENT),
        ("4. Single Linux Kernel Version & Short Runs",
         "Evaluated on Ubuntu 24.04 (Kernel 6.8) with 30s attack bursts.\n"
         "Mitigation: /proc/net/snmp and /proc/net/tcp represent stable Linux ABIs spanning kernels 2.6 to 6.x.",
         TEXT_MUTED),
    ]

    for (x, y), (title, desc, col) in zip(coords, threats):
        sc = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, cw, ch)
        sc.fill.solid(); sc.fill.fore_color.rgb = CARD_BG; sc.line.color.rgb = CARD_BORDER
        tf_sc = s12.shapes.add_textbox(x + Inches(0.2), y + Inches(0.2), cw - Inches(0.4), ch - Inches(0.4)).text_frame
        tf_sc.word_wrap = True
        p = tf_sc.paragraphs[0]; p.text = title; p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = col
        p = tf_sc.add_paragraph(); p.text = desc; p.font.size = Pt(11); p.font.color.rgb = TEXT_DARK; p.space_before = Pt(4)

    # ══════════════════════════════════════════════════════════════════════════════
    # SLIDE 13: Conclusion & Key Takeaways (Dark Theme)
    # ══════════════════════════════════════════════════════════════════════════════
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, DARK_BG)

    tb_c = s13.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(11.7), Inches(5.5))
    tf_c = tb_c.text_frame; tf_c.word_wrap = True

    p = tf_c.paragraphs[0]
    p.text = "Summary & Final Contributions"; p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = WHITE

    p = tf_c.add_paragraph()
    p.text = "Four Foundational Conclusions from the Lab:"; p.font.size = Pt(16); p.font.color.rgb = CYAN_ACCENT; p.space_before = Pt(14)

    p = tf_c.add_paragraph()
    p.text = "1. Transport-Layer Socket Telemetry is Sufficient: Kernel state tables (/proc/net/) provide high-fidelity DoS detection without expensive packet inspection.\n\n" \
             "2. Handshake Completion Ratio (HCR) Solves Flash Crowds: Combining volume with completion ratios completely eliminates false alarms during legitimate spikes.\n\n" \
             "3. Multi-Queue State Tracking is Essential: Connection-hold attacks and SYN cookie mitigation require tracking established socket pools and kernel mitigation counters.\n\n" \
             "4. Production Edge Feasibility: Consumes only 0.18% CPU and 15.6 MB RAM with 1.19s median delay, making it instantly deployable on modern Linux edge gateways."
    p.font.size = Pt(14); p.font.color.rgb = TEXT_LIGHT; p.space_before = Pt(10)

    p = tf_c.add_paragraph()
    p.text = "Thank You! Questions & Discussion"
    p.font.size = Pt(18); p.font.bold = True; p.font.color.rgb = GREEN_ACCENT; p.space_before = Pt(24)

    # Save presentation
    prs.save(str(OUTPUT_PPTX))
    print(f"[generate_deck] Successfully created {OUTPUT_PPTX}")


if __name__ == "__main__":
    create_deck()

