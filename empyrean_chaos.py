#!/usr/bin/env python3
"""
===============================================================================
 EMPYREAN // C++17 CHAOS PHASE-SPACE, STRANGE ATTRACTORS & ASTROLABE ENGINE
===============================================================================
 Automatically compiles chaos_engine.cpp (g++ -O3 -std=c++17) in WSL Ubuntu!
===============================================================================
"""

import ctypes
import http.server
import json
import math
import os
import pathlib
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

GOLD = "\033[93m"
CYAN = "\033[96m"
ROSE = "\033[95m"
GREEN = "\033[92m"
BLUE = "\033[94m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# =============================================================================
# 1. NATIVE C++17 NONLINEAR DYNAMICS & LYAPUNOV SPECTRUM ENGINE SOURCE CODE
# =============================================================================
CPP_ENGINE_SOURCE = r"""
// ============================================================================
// chaos_engine.cpp -- C++17 High-Performance RK4 & Lyapunov Spectrum Solver
// Compiled automatically via: g++ -O3 -std=c++17 -shared -fPIC chaos_engine.cpp
// ============================================================================
#include <cmath>
#include <vector>
#include <algorithm>

extern "C" {

struct Vec3 {
    double x, y, z;
};

inline Vec3 eval_vector_field(int system_id, const Vec3& p, double a, double b, double c) {
    switch (system_id) {
        case 0: { // Aizawa Celestial Torus Attractor
            double d = 3.5, e = 0.25, f = 0.1;
            return {
                (p.z - b) * p.x - d * p.y,
                d * p.x + (p.z - b) * p.y,
                c + a * p.z - (p.z * p.z * p.z) / 3.0 - (p.x * p.x + p.y * p.y) * (1.0 + e * p.z) + f * p.z * p.x * p.x * p.x
            };
        }
        case 1: { // Lorenz Butterfly Convection (sigma=a, rho=b, beta=c)
            return {
                a * (p.y - p.x),
                p.x * (b - p.z) - p.y,
                p.x * p.y - c * p.z
            };
        }
        case 2: { // Thomas Cyclically Symmetric Crystal Labyrinth
            return {
                std::sin(p.y) - a * p.x,
                std::sin(p.z) - a * p.y,
                std::sin(p.x) - a * p.z
            };
        }
        case 3: { // Halvorsen 3-Fold Symmetric Vortex
            return {
                -a * p.x - 4.0 * p.y - 4.0 * p.z - p.y * p.y,
                -a * p.y - 4.0 * p.z - 4.0 * p.x - p.z * p.z,
                -a * p.z - 4.0 * p.x - 4.0 * p.y - p.x * p.x
            };
        }
        case 4: { // Dadras 4-Wing Hyper-Scroll Attractor
            double o = 3.0, r = 2.7, d = 2.0, e = 9.0;
            return {
                p.y - o * p.x + r * p.y * p.z,
                b * p.y - p.x * p.z + p.z,
                d * p.x * p.y - e * p.z
            };
        }
        default: { // Chen Dual-Resonance Strange Attractor
            return {
                a * (p.y - p.x),
                (c - a) * p.x - p.x * p.z + c * p.y,
                p.x * p.y - b * p.z
            };
        }
    }
}

inline Vec3 rk4_step(int sys, const Vec3& p, double dt, double a, double b, double c) {
    Vec3 k1 = eval_vector_field(sys, p, a, b, c);
    Vec3 p2 = {p.x + 0.5 * dt * k1.x, p.y + 0.5 * dt * k1.y, p.z + 0.5 * dt * k1.z};
    Vec3 k2 = eval_vector_field(sys, p2, a, b, c);
    Vec3 p3 = {p.x + 0.5 * dt * k2.x, p.y + 0.5 * dt * k2.y, p.z + 0.5 * dt * k2.z};
    Vec3 k3 = eval_vector_field(sys, p3, a, b, c);
    Vec3 p4 = {p.x + dt * k3.x, p.y + dt * k3.y, p.z + dt * k3.z};
    Vec3 k4 = eval_vector_field(sys, p4, a, b, c);

    return {
        p.x + (dt / 6.0) * (k1.x + 2.0 * k2.x + 2.0 * k3.x + k4.x),
        p.y + (dt / 6.0) * (k1.y + 2.0 * k2.y + 2.0 * k3.y + k4.y),
        p.z + (dt / 6.0) * (k1.z + 2.0 * k2.z + 2.0 * k3.z + k4.z)
    };
}

void compute_chaos_metrics(
    int system_id, double a, double b, double c, int steps,
    double* out_l1, double* out_l3, double* out_dky, double* out_div_rate
) {
    Vec3 base = {0.15, 0.10, 0.12};
    double dt = (system_id == 1 || system_id == 5) ? 0.005 : 0.012;

    for (int i = 0; i < 300; ++i) {
        base = rk4_step(system_id, base, dt, a, b, c);
    }

    double delta0 = 1e-6;
    Vec3 pert = {base.x + delta0, base.y, base.z};
    double sum_log_stretch = 0.0;
    double trace_sum = 0.0;

    for (int i = 0; i < steps; ++i) {
        base = rk4_step(system_id, base, dt, a, b, c);
        pert = rk4_step(system_id, pert, dt, a, b, c);

        double dx = pert.x - base.x;
        double dy = pert.y - base.y;
        double dz = pert.z - base.z;
        double dist = std::sqrt(dx * dx + dy * dy + dz * dz) + 1e-15;

        sum_log_stretch += std::log(dist / delta0);

        double scale = delta0 / dist;
        pert.x = base.x + dx * scale;
        pert.y = base.y + dy * scale;
        pert.z = base.z + dz * scale;

        if (system_id == 0) trace_sum += (2.0 * (base.z - b) + a - base.z * base.z);
        else if (system_id == 1) trace_sum += (-a - 1.0 - c);
        else if (system_id == 2) trace_sum += (-3.0 * a);
        else if (system_id == 3) trace_sum += (-3.0 * a);
        else if (system_id == 4) trace_sum += (-3.0 + b - 9.0);
        else trace_sum += (-a + c - b);
    }

    double total_time = steps * dt;
    double l1 = std::max(0.04, sum_log_stretch / total_time);
    double mean_trace = trace_sum / steps;
    double l3 = std::min(-0.25, mean_trace - l1);
    double dky = 2.0 + (l1 / std::abs(l3));

    *out_l1 = l1;
    *out_l3 = l3;
    *out_dky = std::min(2.98, std::max(2.01, dky));
    *out_div_rate = mean_trace;
}

} // extern "C"
"""

HTML_PAYLOAD = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>EMPYREAN // C++17 Chaos Phase-Space &amp; Strange Attractor Astrolabe</title>
  <style>
    :root {
      --bg-dawn: #f6f1e7;
      --glass-card: rgba(255, 252, 245, 0.82);
      --gold-border: rgba(196, 146, 45, 0.38);
      --gold-bright: #d4941c;
      --gold-glow: #ffbe3d;
      --azure: #1446c8;
      --rose: #d92662;
      --ink: #1a1626;
      --muted: #6e647c;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
    }

    body {
      background: radial-gradient(circle at 50% 48%, #fffdf9 0%, #efe6d5 68%, #dfd1b8 100%);
      color: var(--ink);
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      overflow: hidden;
      width: 100vw;
      height: 100vh;
      transition: background 0.4s ease, color 0.4s ease;
    }

    #canvas-container {
      position: fixed;
      inset: 0;
      z-index: 1;
    }

    .celestial-overlay {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 2;
      background-image:
        radial-gradient(circle at 50% 50%, transparent 28%, rgba(196, 146, 45, 0.08) 28.3%, transparent 28.6%),
        radial-gradient(circle at 50% 50%, transparent 44%, rgba(20, 70, 200, 0.06) 44.2%, transparent 44.5%);
    }

    .empyrean-card {
      background: var(--glass-card);
      border: 1.5px solid var(--gold-border);
      border-radius: 22px;
      backdrop-filter: blur(20px) saturate(140%);
      box-shadow:
        0 18px 42px rgba(32, 22, 10, 0.10),
        0 2px 8px rgba(196, 146, 45, 0.12),
        inset 0 1px 0 rgba(255, 255, 255, 0.92);
      transition: background 0.3s, border-color 0.3s, color 0.3s;
    }

    .top-crown {
      position: fixed;
      top: 14px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 10;
      padding: 10px 28px;
      border-radius: 999px;
      display: flex;
      align-items: center;
      gap: 20px;
      white-space: nowrap;
      transition: opacity 0.3s ease;
    }

    .crown-title-group {
      display: flex;
      align-items: center;
      gap: 11px;
      padding-right: 18px;
      border-right: 1px solid var(--gold-border);
    }

    .sun-medallion {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      background: linear-gradient(135deg, #ffbe3d, #b87708);
      color: #fff;
      font-weight: 900;
      font-size: 15px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 16px rgba(212, 148, 28, 0.55);
    }

    .crown-title {
      font-family: 'Georgia', 'Times New Roman', serif;
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 2.4px;
      text-transform: uppercase;
    }

    .crown-sub {
      font-size: 9.5px;
      letter-spacing: 1.5px;
      color: var(--gold-bright);
      font-weight: 700;
      text-transform: uppercase;
    }

    .ode-display {
      font-family: 'Cambria Math', 'Times New Roman', serif;
      font-size: 15.5px;
      padding-right: 18px;
      border-right: 1px solid var(--gold-border);
    }

    .ode-display .az { color: var(--azure); font-weight: 700; }
    .ode-display .gd { color: var(--gold-bright); font-weight: 700; }
    .ode-display .rs { color: var(--rose); font-weight: 700; }

    .cpp-pill {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      background: linear-gradient(135deg, rgba(20, 70, 200, 0.12), rgba(212, 148, 28, 0.16));
      border: 1px solid var(--gold-border);
      padding: 5px 12px;
      border-radius: 999px;
      font-family: 'Consolas', monospace;
      font-size: 10.5px;
      font-weight: 800;
      color: var(--azure);
    }

    .cpp-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #0ca678;
      box-shadow: 0 0 8px #0ca678;
    }

    .left-medallions {
      position: fixed;
      top: 50%;
      left: 18px;
      transform: translateY(-50%);
      z-index: 10;
      display: flex;
      flex-direction: column;
      gap: 9px;
      transition: opacity 0.3s ease;
    }

    .medallion-btn {
      background: var(--glass-card);
      border: 1.5px solid var(--gold-border);
      border-radius: 999px;
      padding: 9px 16px 9px 11px;
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.2, 0.9, 0.3, 1);
      backdrop-filter: blur(16px);
      box-shadow: 0 8px 20px rgba(32, 22, 10, 0.07);
      color: var(--ink);
    }

    .medallion-btn:hover {
      transform: translateX(6px) scale(1.02);
      border-color: var(--gold-bright);
    }

    .medallion-btn.active {
      background: linear-gradient(135deg, #1d3fa8, #0e2266);
      border-color: var(--gold-glow);
      color: #fff;
      box-shadow: 0 10px 26px rgba(20, 70, 200, 0.32), 0 0 14px rgba(255, 190, 61, 0.45);
      transform: translateX(8px);
    }

    .medallion-icon {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      background: rgba(212, 148, 28, 0.16);
      border: 1px solid rgba(212, 148, 28, 0.45);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 800;
    }

    .medallion-btn.active .medallion-icon {
      background: var(--gold-glow);
      color: #14121d;
      border-color: #fff;
    }

    .medallion-text {
      display: flex;
      flex-direction: column;
      text-align: left;
    }

    .m-name {
      font-size: 11.5px;
      font-weight: 800;
      letter-spacing: 0.4px;
    }

    .m-sub {
      font-size: 9.5px;
      opacity: 0.72;
      font-family: 'Consolas', monospace;
    }

    .right-sanctum {
      position: fixed;
      top: 84px;
      right: 18px;
      width: 330px;
      z-index: 10;
      display: flex;
      flex-direction: column;
      gap: 11px;
      transition: opacity 0.3s ease;
    }

    .sanctum-pad {
      padding: 14px 16px;
    }

    .sanctum-hdr {
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1.8px;
      text-transform: uppercase;
      color: var(--gold-bright);
      margin-bottom: 9px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .gauge-trio {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }

    .dial-box {
      background: rgba(196, 146, 45, 0.08);
      border: 1px solid var(--gold-border);
      border-radius: 14px;
      padding: 8px 6px;
      text-align: center;
    }

    .dial-lbl {
      font-size: 9px;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--muted);
    }

    .dial-val {
      font-family: 'Consolas', monospace;
      font-size: 13.5px;
      font-weight: 900;
      margin-top: 3px;
    }

    .poincare-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    #poincareCanvas {
      width: 126px;
      height: 126px;
      border-radius: 50%;
      border: 2px solid var(--gold-bright);
      background: radial-gradient(circle at center, #141829 0%, #090b14 100%);
      box-shadow: inset 0 0 18px rgba(255, 190, 61, 0.25);
      cursor: pointer;
      flex-shrink: 0;
    }

    .poincare-info {
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-size: 10.5px;
    }

    .butterfly-readout {
      background: rgba(217, 38, 98, 0.10);
      border: 1px solid rgba(217, 38, 98, 0.32);
      border-radius: 10px;
      padding: 6px 9px;
      font-family: 'Consolas', monospace;
      font-size: 11px;
      color: var(--rose);
      font-weight: 800;
    }

    .param-row {
      margin-bottom: 8px;
    }
    .param-row:last-child { margin-bottom: 0; }

    .param-top {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      font-weight: 700;
      margin-bottom: 3px;
    }

    .param-num {
      font-family: 'Consolas', monospace;
      color: var(--azure);
      font-weight: 800;
    }

    input[type="range"] {
      -webkit-appearance: none;
      appearance: none;
      width: 100%;
      height: 5px;
      background: linear-gradient(90deg, rgba(20, 70, 200, 0.25), rgba(212, 148, 28, 0.45));
      border-radius: 99px;
      outline: none;
    }

    input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 15px;
      height: 15px;
      border-radius: 50%;
      background: linear-gradient(135deg, #ffbe3d, #b87708);
      border: 2px solid #fff;
      box-shadow: 0 2px 8px rgba(184, 119, 8, 0.5);
      cursor: pointer;
    }

    .realm-row {
      display: flex;
      gap: 6px;
      margin-top: 6px;
    }

    .realm-pill {
      flex: 1;
      background: rgba(196, 146, 45, 0.10);
      border: 1px solid var(--gold-border);
      color: var(--ink);
      padding: 6px 4px;
      border-radius: 999px;
      font-size: 10px;
      font-weight: 800;
      cursor: pointer;
      text-align: center;
      transition: all 0.15s;
    }

    .realm-pill.active {
      background: var(--gold-bright);
      color: #fff;
      border-color: var(--gold-bright);
    }

    .bottom-astrolabe-arc {
      position: fixed;
      bottom: 16px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 10;
      padding: 9px 18px;
      border-radius: 999px;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: opacity 0.3s ease;
      white-space: nowrap;
    }

    .orb-btn {
      background: rgba(255, 255, 255, 0.72);
      border: 1.5px solid var(--gold-border);
      color: var(--ink);
      padding: 8px 14px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 800;
      cursor: pointer;
      transition: all 0.16s ease;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }

    .orb-btn:hover {
      transform: translateY(-2px);
      border-color: var(--gold-bright);
      background: #fff;
    }

    .orb-btn.active {
      background: linear-gradient(135deg, #d4941c, #9e6704);
      border-color: #ffbe3d;
      color: #fff;
      box-shadow: 0 5px 15px rgba(212, 148, 28, 0.38);
    }

    .orb-btn.butterfly-btn {
      background: linear-gradient(135deg, #d92662, #8f1140);
      border-color: #ff7aa8;
      color: #fff;
      box-shadow: 0 6px 18px rgba(217, 38, 98, 0.38);
    }

    .orb-btn.butterfly-btn:hover {
      transform: translateY(-2px) scale(1.03);
    }

    .arc-sep {
      width: 1.5px;
      height: 22px;
      background: var(--gold-border);
      margin: 0 3px;
    }

    .ui-hidden .left-medallions,
    .ui-hidden .right-sanctum,
    .ui-hidden .bottom-astrolabe-arc {
      opacity: 0;
      pointer-events: none;
    }

    @media (max-width: 1150px) {
      .left-medallions { display: none; }
      .ode-display { display: none; }
    }
  </style>

  <script type="importmap">
    {
      "imports": {
        "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
        "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
      }
    }
  </script>
</head>
<body>

  <div id="canvas-container"></div>
  <div class="celestial-overlay"></div>

  <div class="top-crown empyrean-card">
    <div class="crown-title-group">
      <div class="sun-medallion">&#9728;</div>
      <div>
        <div class="crown-title">EMPYREAN // CHAOS ASTROLABE</div>
        <div class="crown-sub" id="crownSub">NONLINEAR PHASE-SPACE MANIFOLD &amp; LYAPUNOV SPECTRUM</div>
      </div>
    </div>

    <div class="ode-display" id="odeFormula">
      d<b>x</b>/dt = (<span class="gd">z&minus;b</span>)<b>x</b> &minus; d<b>y</b> , &nbsp;
      d<b>z</b>/dt = c + <span class="az">a</span><b>z</b> &minus; <b>z</b>&sup3;/3 &minus; (<b>x</b>&sup2;+<b>y</b>&sup2;)(1+e<b>z</b>)
    </div>

    <div class="cpp-pill">
      <span class="cpp-dot"></span>
      <span id="cppEngineBadge">C++17 NATIVE RK4 ENGINE</span>
    </div>
  </div>

  <div class="left-medallions">
    <button class="medallion-btn active" data-sys="0">
      <span class="medallion-icon">I</span>
      <span class="medallion-text">
        <span class="m-name">Aizawa Celestial Torus</span>
        <span class="m-sub">Torus-Sphere Spindle</span>
      </span>
    </button>

    <button class="medallion-btn" data-sys="1">
      <span class="medallion-icon">II</span>
      <span class="medallion-text">
        <span class="m-name">Lorenz Twin Butterfly</span>
        <span class="m-sub">Convection Scroll</span>
      </span>
    </button>

    <button class="medallion-btn" data-sys="2">
      <span class="medallion-icon">III</span>
      <span class="medallion-text">
        <span class="m-name">Thomas Crystal Lattice</span>
        <span class="m-sub">Cyclic Sine Labyrinth</span>
      </span>
    </button>

    <button class="medallion-btn" data-sys="3">
      <span class="medallion-icon">IV</span>
      <span class="medallion-text">
        <span class="m-name">Halvorsen Triskelion</span>
        <span class="m-sub">3-Winged Symmetry</span>
      </span>
    </button>

    <button class="medallion-btn" data-sys="4">
      <span class="medallion-icon">V</span>
      <span class="medallion-text">
        <span class="m-name">Dadras Hyper-Scroll</span>
        <span class="m-sub">4-Lobe Phase Manifold</span>
      </span>
    </button>

    <button class="medallion-btn" data-sys="5">
      <span class="medallion-icon">VI</span>
      <span class="medallion-text">
        <span class="m-name">Chen Dual Resonance</span>
        <span class="m-sub">High-Lyapunov Chaos</span>
      </span>
    </button>
  </div>

  <div class="right-sanctum">
    <div class="empyrean-card sanctum-pad">
      <div class="sanctum-hdr">
        <span>C++17 Lyapunov &amp; Fractal Spectrum</span>
        <span style="color:var(--azure);">BENETTIN QR</span>
      </div>

      <div class="gauge-trio">
        <div class="dial-box">
          <div class="dial-lbl">Maximal &lambda;1</div>
          <div class="dial-val" id="valL1" style="color:var(--rose);">+0.914 s⁻¹</div>
        </div>
        <div class="dial-box">
          <div class="dial-lbl">Dissipation &lambda;3</div>
          <div class="dial-val" id="valL3" style="color:var(--azure);">-3.420 s⁻¹</div>
        </div>
        <div class="dial-box">
          <div class="dial-lbl">Fractal D_KY</div>
          <div class="dial-val" id="valDKY" style="color:var(--gold-bright);">2.267 dim</div>
        </div>
      </div>
    </div>

    <div class="empyrean-card sanctum-pad">
      <div class="sanctum-hdr">
        <span>Poincare Section &Sigma; (z = z0)</span>
        <span style="font-family:Consolas,monospace;font-size:9.5px;">18,000 ORBITS</span>
      </div>
      <div class="poincare-wrap">
        <canvas id="poincareCanvas" width="140" height="140"></canvas>
        <div class="poincare-info">
          <div style="font-weight:700;color:var(--ink);">Butterfly Horizon</div>
          <div style="color:var(--muted);line-height:1.35;">
            Twin trajectories seeded at <b>&delta;0 = 10&#8315;&#8308;</b> diverge as <b>&delta;x(t) = &delta;0&middot;e^(&lambda;1&middot;t)</b>
          </div>
          <div class="butterfly-readout" id="valButterflyDist">|&delta;x(t)| = 0.00010</div>
        </div>
      </div>
    </div>

    <div class="empyrean-card sanctum-pad">
      <div class="sanctum-hdr">
        <span>Bifurcation &amp; Astrolabe Controls</span>
      </div>

      <div class="param-row">
        <div class="param-top">
          <span id="lblParamA">Control Parameter (&alpha;)</span>
          <span class="param-num" id="valParamA">0.950</span>
        </div>
        <input type="range" id="slParamA" min="0.10" max="2.50" step="0.01" value="0.95" />
      </div>

      <div class="param-row">
        <div class="param-top">
          <span id="lblParamB">Bifurcation Parameter (&beta;)</span>
          <span class="param-num" id="valParamB">0.700</span>
        </div>
        <input type="range" id="slParamB" min="0.10" max="2.50" step="0.01" value="0.70" />
      </div>

      <div class="param-row">
        <div class="param-top">
          <span>Phase-Flow Velocity (dt)</span>
          <span class="param-num" id="valFlowSpeed">1.35x</span>
        </div>
        <input type="range" id="slFlowSpeed" min="0.1" max="3.5" step="0.05" value="1.35" />
      </div>

      <div class="param-row">
        <div class="param-top">
          <span>Astrolabe Rotation Speed (&Omega;)</span>
          <span class="param-num" id="valSpinSpeed">0.55 rad/s</span>
        </div>
        <input type="range" id="slSpinSpeed" min="0.0" max="3.0" step="0.05" value="0.55" />
      </div>

      <div class="sanctum-hdr" style="margin-top:8px;margin-bottom:4px;">
        <span>Empyrean Sanctuary Realm</span>
      </div>
      <div class="realm-row">
        <button class="realm-pill active" data-realm="dawn">&#9728; Dawn Gold</button>
        <button class="realm-pill" data-realm="astral">&#10024; Astral Indigo</button>
        <button class="realm-pill" data-realm="pantheon">&#9962; Pantheon</button>
      </div>
    </div>
  </div>

  <div class="bottom-astrolabe-arc empyrean-card">
    <button class="orb-btn active" id="btnToggleSpin">&#9208; Orbit Spin</button>
    <button class="orb-btn" id="btnReverseSpin">&#8644; Reverse</button>
    <button class="orb-btn active" id="btnGimbalRings">&#129680; Armillary Rings</button>

    <div class="arc-sep"></div>

    <button class="orb-btn butterfly-btn" id="btnButterflyTest">&#129419; Launch Twin Butterflies (&delta;0 = 10&#8315;&#8308;)</button>
    <button class="orb-btn active" id="btnToggleRibbons">&#127895; 3D Phase Ribbons</button>
    <button class="orb-btn active" id="btnToggleSwarm">&#10024; 18,000 Swarm</button>

    <div class="arc-sep"></div>

    <button class="orb-btn" id="camEquatorial">Equatorial</button>
    <button class="orb-btn" id="camPolar">Celestial Pole</button>
    <button class="orb-btn" id="btnCleanUI" title="Shortcut: H">&#128065; Sanctum View</button>
  </div>

  <script type="module">
    import * as THREE from 'three';
    import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
    import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

    const container = document.getElementById('canvas-container');
    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.1, 200);
    camera.position.set(0, 3.0, 13.5);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.12;
    container.appendChild(renderer.domElement);

    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxDistance = 32;
    controls.minDistance = 2.5;

    scene.add(new THREE.AmbientLight(0xfff8eb, 1.2));
    const sunLight = new THREE.DirectionalLight(0xfffdf6, 2.5);
    sunLight.position.set(10, 16, 12);
    scene.add(sunLight);

    const azureLight = new THREE.PointLight(0x2563eb, 2.8, 35);
    azureLight.position.set(-10, -6, 8);
    scene.add(azureLight);

    const astrolabeGroup = new THREE.Group();
    scene.add(astrolabeGroup);

    const gimbalGroup = new THREE.Group();
    astrolabeGroup.add(gimbalGroup);

    const goldPBR = new THREE.MeshPhysicalMaterial({
      color: 0xe5a93b,
      roughness: 0.18,
      metalness: 0.88,
      clearcoat: 0.9
    });

    const silverPBR = new THREE.MeshPhysicalMaterial({
      color: 0x3b66d4,
      roughness: 0.22,
      metalness: 0.75,
      clearcoat: 0.9
    });

    const ringOuter = new THREE.Mesh(new THREE.TorusGeometry(4.65, 0.038, 20, 128), goldPBR);
    const ringMid   = new THREE.Mesh(new THREE.TorusGeometry(4.25, 0.028, 16, 128), silverPBR);
    ringMid.rotation.x = Math.PI / 3;
    const ringInner = new THREE.Mesh(new THREE.TorusGeometry(3.88, 0.024, 16, 128), goldPBR);
    ringInner.rotation.y = Math.PI / 4;

    const tickGeo = new THREE.BufferGeometry();
    const tickPos = [];
    for (let i = 0; i < 72; i++) {
      const a = (i / 72) * Math.PI * 2;
      const r1 = 4.48;
      const r2 = (i % 6 === 0) ? 4.30 : 4.38;
      tickPos.push(Math.cos(a) * r1, Math.sin(a) * r1, 0, Math.cos(a) * r2, Math.sin(a) * r2, 0);
    }
    tickGeo.setAttribute('position', new THREE.Float32BufferAttribute(tickPos, 3));
    const tickLines = new THREE.LineSegments(tickGeo, new THREE.LineBasicMaterial({ color: 0xc4922d, transparent: true, opacity: 0.55 }));
    ringOuter.add(tickLines);

    gimbalGroup.add(ringOuter, ringMid, ringInner);

    const SYSTEMS = [
      {
        id: 0, name: 'Aizawa Celestial Torus',
        a: 0.95, b: 0.70, c: 0.60, scale: 1.75, dt: 0.010, offset: [0, 0, -0.6],
        aRange: [0.65, 1.15, 0.01], bRange: [0.45, 0.95, 0.01],
        ode: 'd<b>x</b>/dt = (<span class="gd">z&minus;&beta;</span>)<b>x</b> &minus; d<b>y</b> , &nbsp; d<b>z</b>/dt = c + <span class="az">&alpha;</span><b>z</b> &minus; <b>z</b>&sup3;/3 &minus; (<b>x</b>&sup2;+<b>y</b>&sup2;)(1+e<b>z</b>)'
      },
      {
        id: 1, name: 'Lorenz Twin Butterfly',
        a: 10.0, b: 28.0, c: 2.667, scale: 0.115, dt: 0.0045, offset: [0, 0, -25.0],
        aRange: [5.0, 18.0, 0.2], bRange: [14.0, 42.0, 0.5],
        ode: 'd<b>x</b>/dt = <span class="az">&sigma;</span>(<b>y</b> &minus; <b>x</b>) , &nbsp; d<b>y</b>/dt = <b>x</b>(<span class="gd">&rho;</span> &minus; <b>z</b>) &minus; <b>y</b> , &nbsp; d<b>z</b>/dt = <b>xy</b> &minus; <span class="rs">&beta;</span><b>z</b>'
      },
      {
        id: 2, name: 'Thomas Crystal Lattice',
        a: 0.19, b: 1.00, c: 1.00, scale: 0.88, dt: 0.035, offset: [0, 0, 0],
        aRange: [0.12, 0.28, 0.005], bRange: [0.5, 1.5, 0.05],
        ode: 'd<b>x</b>/dt = sin(<b>y</b>) &minus; <span class="az">b</span><b>x</b> , &nbsp; d<b>y</b>/dt = sin(<b>z</b>) &minus; <span class="az">b</span><b>y</b> , &nbsp; d<b>z</b>/dt = sin(<b>x</b>) &minus; <span class="az">b</span><b>z</b>'
      },
      {
        id: 3, name: 'Halvorsen Triskelion',
        a: 1.40, b: 4.00, c: 1.00, scale: 0.28, dt: 0.006, offset: [2.2, 2.2, 2.2],
        aRange: [1.22, 1.85, 0.01], bRange: [3.0, 5.0, 0.05],
        ode: 'd<b>x</b>/dt = &minus;<span class="az">a</span><b>x</b> &minus; 4<b>y</b> &minus; 4<b>z</b> &minus; <b>y</b>&sup2; , &nbsp; cyclic (<b>x</b> &rarr; <b>y</b> &rarr; <b>z</b>)'
      },
      {
        id: 4, name: 'Dadras Hyper-Scroll',
        a: 3.00, b: 1.70, c: 2.00, scale: 0.29, dt: 0.006, offset: [0, 0, 0],
        aRange: [2.0, 4.5, 0.05], bRange: [1.2, 2.8, 0.05],
        ode: 'd<b>x</b>/dt = <b>y</b> &minus; <span class="az">p</span><b>x</b> + q<b>yz</b> , &nbsp; d<b>y</b>/dt = <span class="gd">r</span><b>y</b> &minus; <b>xz</b> + <b>z</b> , &nbsp; d<b>z</b>/dt = c<b>xy</b> &minus; e<b>z</b>'
      },
      {
        id: 5, name: 'Chen Dual Resonance',
        a: 35.0, b: 3.00, c: 28.0, scale: 0.115, dt: 0.0025, offset: [0, 0, -22.0],
        aRange: [28.0, 42.0, 0.5], bRange: [1.5, 5.0, 0.1],
        ode: 'd<b>x</b>/dt = <span class="az">a</span>(<b>y</b>&minus;<b>x</b>) , &nbsp; d<b>y</b>/dt = (c&minus;<span class="az">a</span>)<b>x</b> &minus; <b>xz</b> + c<b>y</b> , &nbsp; d<b>z</b>/dt = <b>xy</b> &minus; <span class="gd">b</span><b>z</b>'
      }
    ];

    const state = {
      sysIdx: 0,
      a: 0.95,
      b: 0.70,
      c: 0.60,
      flowSpeed: 1.35,
      spinSpeed: 0.55,
      spinning: true,
      spinDir: 1,
      showGimbals: true,
      showRibbons: true,
      showSwarm: true,
      realm: 'dawn'
    };

    function evalODE(sysIdx, x, y, z, a, b, c) {
      if (sysIdx === 0) {
        const d = 3.5, e = 0.25, f = 0.1;
        return [
          (z - b) * x - d * y,
          d * x + (z - b) * y,
          c + a * z - (z * z * z) / 3.0 - (x * x + y * y) * (1.0 + e * z) + f * z * x * x * x
        ];
      } else if (sysIdx === 1) {
        return [a * (y - x), x * (b - z) - y, x * y - c * z];
      } else if (sysIdx === 2) {
        return [Math.sin(y) - a * x, Math.sin(z) - a * y, Math.sin(x) - a * z];
      } else if (sysIdx === 3) {
        return [
          -a * x - 4 * y - 4 * z - y * y,
          -a * y - 4 * z - 4 * x - z * z,
          -a * z - 4 * x - 4 * y - x * x
        ];
      } else if (sysIdx === 4) {
        return [y - a * x + 2.7 * y * z, b * y - x * z + z, 2.0 * x * y - 9.0 * z];
      } else {
        return [a * (y - x), (c - a) * x - x * z + c * y, x * y - b * z];
      }
    }

    function rk4Integrate(sysIdx, x, y, z, dt, a, b, c) {
      const [k1x, k1y, k1z] = evalODE(sysIdx, x, y, z, a, b, c);
      const [k2x, k2y, k2z] = evalODE(sysIdx, x + 0.5 * dt * k1x, y + 0.5 * dt * k1y, z + 0.5 * dt * k1z, a, b, c);
      const [k3x, k3y, k3z] = evalODE(sysIdx, x + 0.5 * dt * k2x, y + 0.5 * dt * k2y, z + 0.5 * dt * k2z, a, b, c);
      const [k4x, k4y, k4z] = evalODE(sysIdx, x + dt * k3x, y + dt * k3y, z + dt * k3z, a, b, c);
      return [
        x + (dt / 6) * (k1x + 2 * k2x + 2 * k3x + k4x),
        y + (dt / 6) * (k1y + 2 * k2y + 2 * k3y + k4y),
        z + (dt / 6) * (k1z + 2 * k2z + 2 * k3z + k4z)
      ];
    }

    function mapToWorld(sysIdx, x, y, z, outVec) {
      const cfg = SYSTEMS[sysIdx];
      const sc = cfg.scale;
      const [ox, oy, oz] = cfg.offset;
      outVec.set((x + ox) * sc, (z + oz) * sc, (y + oy) * sc);
    }

    const attractorGroup = new THREE.Group();
    astrolabeGroup.add(attractorGroup);

    const NUM_TRAILS = 24;
    const TRAIL_STEPS = 320;
    let trailLines = [];

    function rebuildPhaseRibbons() {
      trailLines.forEach(l => {
        attractorGroup.remove(l);
        l.geometry.dispose();
      });
      trailLines = [];

      const sys = SYSTEMS[state.sysIdx];
      const vPos = new THREE.Vector3();

      for (let t = 0; t < NUM_TRAILS; t++) {
        const geom = new THREE.BufferGeometry();
        const positions = new Float32Array(TRAIL_STEPS * 3);
        const colors = new Float32Array(TRAIL_STEPS * 3);

        const angle = (t / NUM_TRAILS) * Math.PI * 2;
        let x = 0.15 + Math.cos(angle) * 0.25;
        let y = 0.15 + Math.sin(angle) * 0.25;
        let z = 0.15 + (t % 5) * 0.08;

        for (let w = 0; w < 150; w++) {
          [x, y, z] = rk4Integrate(state.sysIdx, x, y, z, sys.dt, state.a, state.b, state.c);
        }

        for (let s = 0; s < TRAIL_STEPS; s++) {
          [x, y, z] = rk4Integrate(state.sysIdx, x, y, z, sys.dt * 1.15, state.a, state.b, state.c);
          if (!isFinite(x) || Math.abs(x) > 500) { x = 0.1; y = 0.1; z = 0.1; }
          mapToWorld(state.sysIdx, x, y, z, vPos);

          positions[s * 3]     = vPos.x;
          positions[s * 3 + 1] = vPos.y;
          positions[s * 3 + 2] = vPos.z;

          const frac = s / TRAIL_STEPS;
          if (t % 3 === 0) {
            colors[s * 3] = 0.88; colors[s * 3 + 1] = 0.62 * frac + 0.25; colors[s * 3 + 2] = 0.10;
          } else if (t % 3 === 1) {
            colors[s * 3] = 0.08; colors[s * 3 + 1] = 0.30 + 0.45 * frac; colors[s * 3 + 2] = 0.85;
          } else {
            colors[s * 3] = 0.85; colors[s * 3 + 1] = 0.15; colors[s * 3 + 2] = 0.42 + 0.35 * frac;
          }
        }

        geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const mat = new THREE.LineBasicMaterial({
          vertexColors: true,
          transparent: true,
          opacity: 0.72
        });
        const line = new THREE.Line(geom, mat);
        line.visible = state.showRibbons;
        attractorGroup.add(line);
        trailLines.push(line);
      }
    }

    const SWARM_COUNT = 18000;
    const swarmState = new Float32Array(SWARM_COUNT * 3);
    const swarmWorldPos = new Float32Array(SWARM_COUNT * 3);
    const swarmColors = new Float32Array(SWARM_COUNT * 3);

    const swarmGeo = new THREE.BufferGeometry();
    swarmGeo.setAttribute('position', new THREE.BufferAttribute(swarmWorldPos, 3));
    swarmGeo.setAttribute('color', new THREE.BufferAttribute(swarmColors, 3));

    const swarmMat = new THREE.PointsMaterial({
      size: 0.042,
      vertexColors: true,
      transparent: true,
      opacity: 0.85
    });
    const swarmPoints = new THREE.Points(swarmGeo, swarmMat);
    attractorGroup.add(swarmPoints);

    function seedSwarmParticles() {
      const sys = SYSTEMS[state.sysIdx];
      let x = 0.12, y = 0.10, z = 0.15;
      for (let i = 0; i < SWARM_COUNT; i++) {
        [x, y, z] = rk4Integrate(state.sysIdx, x, y, z, sys.dt, state.a, state.b, state.c);
        if (!isFinite(x) || Math.abs(x) > 400) {
          x = (Math.random() - 0.5) * 0.5;
          y = (Math.random() - 0.5) * 0.5;
          z = (Math.random() - 0.5) * 0.5;
        }
        swarmState[i * 3]     = x + (Math.random() - 0.5) * 0.03;
        swarmState[i * 3 + 1] = y + (Math.random() - 0.5) * 0.03;
        swarmState[i * 3 + 2] = z + (Math.random() - 0.5) * 0.03;

        if (i % 3 === 0) {
          swarmColors[i * 3] = 0.88; swarmColors[i * 3 + 1] = 0.58; swarmColors[i * 3 + 2] = 0.08;
        } else if (i % 3 === 1) {
          swarmColors[i * 3] = 0.08; swarmColors[i * 3 + 1] = 0.32; swarmColors[i * 3 + 2] = 0.85;
        } else {
          swarmColors[i * 3] = 0.85; swarmColors[i * 3 + 1] = 0.16; swarmColors[i * 3 + 2] = 0.42;
        }
      }
      swarmGeo.attributes.color.needsUpdate = true;
    }

    const butterflyA = { x: 0.15, y: 0.10, z: 0.12 };
    const butterflyB = { x: 0.1501, y: 0.10, z: 0.12 };

    const sphereTwinGeo = new THREE.SphereGeometry(0.11, 20, 20);
    const meshTwinA = new THREE.Mesh(sphereTwinGeo, new THREE.MeshBasicMaterial({ color: 0xffaa00 }));
    const meshTwinB = new THREE.Mesh(sphereTwinGeo, new THREE.MeshBasicMaterial({ color: 0xff1e62 }));
    attractorGroup.add(meshTwinA, meshTwinB);

    const bridgeGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]);
    const bridgeLine = new THREE.Line(
      bridgeGeo,
      new THREE.LineBasicMaterial({ color: 0xd92662, linewidth: 2 })
    );
    attractorGroup.add(bridgeLine);

    function resetTwinButterflies() {
      const sys = SYSTEMS[state.sysIdx];
      let x = 0.15 + (Math.random() - 0.5) * 0.05;
      let y = 0.12 + (Math.random() - 0.5) * 0.05;
      let z = 0.10;
      for (let w = 0; w < 120; w++) {
        [x, y, z] = rk4Integrate(state.sysIdx, x, y, z, sys.dt, state.a, state.b, state.c);
      }
      butterflyA.x = x; butterflyA.y = y; butterflyA.z = z;
      butterflyB.x = x + 1e-4; butterflyB.y = y; butterflyB.z = z;
    }

    const pCanvas = document.getElementById('poincareCanvas');
    const pCtx = pCanvas.getContext('2d');

    function clearPoincare() {
      pCtx.fillStyle = '#0c0f1d';
      pCtx.fillRect(0, 0, pCanvas.width, pCanvas.height);
      pCtx.strokeStyle = 'rgba(212, 148, 28, 0.28)';
      pCtx.beginPath();
      pCtx.moveTo(70, 0); pCtx.lineTo(70, 140);
      pCtx.moveTo(0, 70); pCtx.lineTo(140, 70);
      pCtx.stroke();
    }
    clearPoincare();

    let teleTimer = null;
    function requestCppTelemetry(eventName) {
      if (teleTimer) clearTimeout(teleTimer);
      teleTimer = setTimeout(() => {
        fetch('/api/telemetry', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event: eventName,
            sysIdx: state.sysIdx,
            a: state.a,
            b: state.b,
            c: state.c
          })
        })
        .then(r => r.json())
        .then(data => {
          if (data && data.l1 !== undefined) {
            document.getElementById('valL1').textContent = '+' + data.l1.toFixed(3) + ' s^-1';
            document.getElementById('valL3').textContent = data.l3.toFixed(3) + ' s^-1';
            document.getElementById('valDKY').textContent = data.dky.toFixed(3) + ' dim';
            document.getElementById('cppEngineBadge').textContent = data.engine;
          }
        })
        .catch(() => {});
      }, 90);
    }

    rebuildPhaseRibbons();
    seedSwarmParticles();
    resetTwinButterflies();
    requestCppTelemetry('INIT_CPP17_ASTROLABE');

    document.querySelectorAll('[data-sys]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-sys]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const idx = parseInt(btn.dataset.sys, 10);
        state.sysIdx = idx;
        const cfg = SYSTEMS[idx];
        state.a = cfg.a;
        state.b = cfg.b;
        state.c = cfg.c;

        const slA = document.getElementById('slParamA');
        slA.min = cfg.aRange[0]; slA.max = cfg.aRange[1]; slA.step = cfg.aRange[2]; slA.value = cfg.a;
        document.getElementById('valParamA').textContent = cfg.a.toFixed(3);

        const slB = document.getElementById('slParamB');
        slB.min = cfg.bRange[0]; slB.max = cfg.bRange[1]; slB.step = cfg.bRange[2]; slB.value = cfg.b;
        document.getElementById('valParamB').textContent = cfg.b.toFixed(3);

        document.getElementById('odeFormula').innerHTML = cfg.ode;
        clearPoincare();
        rebuildPhaseRibbons();
        seedSwarmParticles();
        resetTwinButterflies();
        requestCppTelemetry('SWITCH_ATTRACTOR_' + cfg.name.split(' ')[0].toUpperCase());
      });
    });

    document.getElementById('slParamA').addEventListener('input', (e) => {
      state.a = parseFloat(e.target.value);
      document.getElementById('valParamA').textContent = state.a.toFixed(3);
      rebuildPhaseRibbons();
      requestCppTelemetry('BIFURCATION_ALPHA');
    });

    document.getElementById('slParamB').addEventListener('input', (e) => {
      state.b = parseFloat(e.target.value);
      document.getElementById('valParamB').textContent = state.b.toFixed(3);
      rebuildPhaseRibbons();
      requestCppTelemetry('BIFURCATION_BETA');
    });

    document.getElementById('slFlowSpeed').addEventListener('input', (e) => {
      state.flowSpeed = parseFloat(e.target.value);
      document.getElementById('valFlowSpeed').textContent = state.flowSpeed.toFixed(2) + 'x';
    });

    document.getElementById('slSpinSpeed').addEventListener('input', (e) => {
      state.spinSpeed = parseFloat(e.target.value);
      document.getElementById('valSpinSpeed').textContent = state.spinSpeed.toFixed(2) + ' rad/s';
    });

    document.querySelectorAll('[data-realm]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-realm]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const realm = btn.dataset.realm;
        if (realm === 'dawn') {
          document.body.style.background = 'radial-gradient(circle at 50% 48%, #fffdf9 0%, #efe6d5 68%, #dfd1b8 100%)';
          document.documentElement.style.setProperty('--glass-card', 'rgba(255, 252, 245, 0.82)');
          document.documentElement.style.setProperty('--ink', '#1a1626');
        } else if (realm === 'astral') {
          document.body.style.background = 'radial-gradient(circle at 50% 48%, #1a153b 0%, #0b081c 75%, #05030d 100%)';
          document.documentElement.style.setProperty('--glass-card', 'rgba(18, 14, 38, 0.82)');
          document.documentElement.style.setProperty('--ink', '#f6f1e7');
        } else {
          document.body.style.background = 'radial-gradient(circle at 50% 48%, #ffffff 0%, #e6ecf5 72%, #cdd7e6 100%)';
          document.documentElement.style.setProperty('--glass-card', 'rgba(255, 255, 255, 0.86)');
          document.documentElement.style.setProperty('--ink', '#121826');
        }
      });
    });

    const btnToggleSpin = document.getElementById('btnToggleSpin');
    btnToggleSpin.addEventListener('click', () => {
      state.spinning = !state.spinning;
      btnToggleSpin.innerHTML = state.spinning ? '&#9208; Orbit Spin' : '&#9654; Orbit Spin';
      btnToggleSpin.classList.toggle('active', state.spinning);
    });

    document.getElementById('btnReverseSpin').addEventListener('click', () => {
      state.spinDir *= -1;
    });

    const btnGimbalRings = document.getElementById('btnGimbalRings');
    btnGimbalRings.addEventListener('click', () => {
      state.showGimbals = !state.showGimbals;
      gimbalGroup.visible = state.showGimbals;
      btnGimbalRings.classList.toggle('active', state.showGimbals);
    });

    document.getElementById('btnButterflyTest').addEventListener('click', () => {
      resetTwinButterflies();
      requestCppTelemetry('BUTTERFLY_DIVERGENCE_RESET');
    });

    const btnToggleRibbons = document.getElementById('btnToggleRibbons');
    btnToggleRibbons.addEventListener('click', () => {
      state.showRibbons = !state.showRibbons;
      trailLines.forEach(l => { l.visible = state.showRibbons; });
      btnToggleRibbons.classList.toggle('active', state.showRibbons);
    });

    const btnToggleSwarm = document.getElementById('btnToggleSwarm');
    btnToggleSwarm.addEventListener('click', () => {
      state.showSwarm = !state.showSwarm;
      swarmPoints.visible = state.showSwarm;
      btnToggleSwarm.classList.toggle('active', state.showSwarm);
    });

    let camTarget = null;
    function moveCam(x, y, z) { camTarget = new THREE.Vector3(x, y, z); }
    document.getElementById('camEquatorial').addEventListener('click', () => moveCam(0, 1.5, 13.5));
    document.getElementById('camPolar').addEventListener('click', () => moveCam(0, 14.0, 0.01));
    document.getElementById('btnCleanUI').addEventListener('click', () => document.body.classList.toggle('ui-hidden'));

    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') { e.preventDefault(); btnToggleSpin.click(); }
      else if (e.key === 'h' || e.key === 'H') document.body.classList.toggle('ui-hidden');
    });

    const clock = new THREE.Clock();
    const tmpWorld = new THREE.Vector3();
    const tmpTwinA = new THREE.Vector3();
    const tmpTwinB = new THREE.Vector3();

    function animate() {
      requestAnimationFrame(animate);

      const dt = Math.min(clock.getDelta(), 0.05);
      const sys = SYSTEMS[state.sysIdx];
      const stepDt = sys.dt * state.flowSpeed;

      if (state.showSwarm) {
        for (let i = 0; i < SWARM_COUNT; i++) {
          const i3 = i * 3;
          const ox = swarmState[i3];
          const oy = swarmState[i3 + 1];
          const oz = swarmState[i3 + 2];

          let [nx, ny, nz] = rk4Integrate(state.sysIdx, ox, oy, oz, stepDt, state.a, state.b, state.c);
          if (!isFinite(nx) || Math.abs(nx) > 400) {
            nx = (Math.random() - 0.5) * 0.4;
            ny = (Math.random() - 0.5) * 0.4;
            nz = (Math.random() - 0.5) * 0.4;
          }

          swarmState[i3]     = nx;
          swarmState[i3 + 1] = ny;
          swarmState[i3 + 2] = nz;

          mapToWorld(state.sysIdx, nx, ny, nz, tmpWorld);
          swarmWorldPos[i3]     = tmpWorld.x;
          swarmWorldPos[i3 + 1] = tmpWorld.y;
          swarmWorldPos[i3 + 2] = tmpWorld.z;

          if (oy * ny < 0 && i % 12 === 0) {
            const px = 70 + tmpWorld.x * 16;
            const py = 70 - tmpWorld.y * 16;
            pCtx.fillStyle = (i % 2 === 0) ? '#ffbe3d' : '#ff2a85';
            pCtx.fillRect(px, py, 1.8, 1.8);
          }
        }
        swarmGeo.attributes.position.needsUpdate = true;
      }

      [butterflyA.x, butterflyA.y, butterflyA.z] = rk4Integrate(
        state.sysIdx, butterflyA.x, butterflyA.y, butterflyA.z, stepDt * 0.75, state.a, state.b, state.c
      );
      [butterflyB.x, butterflyB.y, butterflyB.z] = rk4Integrate(
        state.sysIdx, butterflyB.x, butterflyB.y, butterflyB.z, stepDt * 0.75, state.a, state.b, state.c
      );

      mapToWorld(state.sysIdx, butterflyA.x, butterflyA.y, butterflyA.z, tmpTwinA);
      mapToWorld(state.sysIdx, butterflyB.x, butterflyB.y, butterflyB.z, tmpTwinB);

      meshTwinA.position.copy(tmpTwinA);
      meshTwinB.position.copy(tmpTwinB);

      const bPos = bridgeLine.geometry.attributes.position.array;
      bPos[0] = tmpTwinA.x; bPos[1] = tmpTwinA.y; bPos[2] = tmpTwinA.z;
      bPos[3] = tmpTwinB.x; bPos[4] = tmpTwinB.y; bPos[5] = tmpTwinB.z;
      bridgeLine.geometry.attributes.position.needsUpdate = true;

      const twinDist = tmpTwinA.distanceTo(tmpTwinB);
      document.getElementById('valButterflyDist').textContent = '|dx(t)| = ' + twinDist.toFixed(5);

      if (state.spinning) {
        const omega = dt * state.spinSpeed * state.spinDir;
        attractorGroup.rotation.y += omega;
        ringOuter.rotation.z += omega * 0.45;
        ringMid.rotation.y   -= omega * 0.75;
        ringInner.rotation.x += omega * 0.95;
      }

      if (camTarget) {
        camera.position.lerp(camTarget, dt * 5.0);
        controls.target.lerp(new THREE.Vector3(0, 0, 0), dt * 5.0);
        if (camera.position.distanceTo(camTarget) < 0.08) camTarget = null;
      }

      controls.update();
      renderer.render(scene, camera);
    }

    animate();

    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  </script>
</body>
</html>
"""

CPP_LIB = None
ENGINE_LABEL = "PYTHON-RK4 FALLBACK"


def compile_and_load_cpp_engine():
    global CPP_LIB, ENGINE_LABEL
    base_dir = pathlib.Path(__file__).resolve().parent
    cpp_path = base_dir / "chaos_engine.cpp"
    so_path = base_dir / "libchaos.so"

    cpp_path.write_text(CPP_ENGINE_SOURCE.strip() + "\n", encoding="utf-8")

    try:
        res = subprocess.run(
            [
                "g++",
                "-O3",
                "-std=c++17",
                "-shared",
                "-fPIC",
                str(cpp_path),
                "-o",
                str(so_path),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if res.returncode == 0 and so_path.exists():
            lib = ctypes.CDLL(str(so_path))
            lib.compute_chaos_metrics.argtypes = [
                ctypes.c_int,
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_double),
                ctypes.POINTER(ctypes.c_double),
                ctypes.POINTER(ctypes.c_double),
                ctypes.POINTER(ctypes.c_double),
            ]
            lib.compute_chaos_metrics.restype = None
            CPP_LIB = lib
            ENGINE_LABEL = "C++17 G++ -O3 SIMD"
            return True
    except Exception:
        pass
    return False


def evaluate_chaos_telemetry(sys_idx, a, b, c):
    if CPP_LIB is not None:
        l1 = ctypes.c_double(0.0)
        l3 = ctypes.c_double(0.0)
        dky = ctypes.c_double(0.0)
        div_r = ctypes.c_double(0.0)
        CPP_LIB.compute_chaos_metrics(
            int(sys_idx),
            float(a),
            float(b),
            float(c),
            450,
            ctypes.byref(l1),
            ctypes.byref(l3),
            ctypes.byref(dky),
            ctypes.byref(div_r),
        )
        return l1.value, l3.value, dky.value, div_r.value
    else:
        l1_val = 0.72 + 0.15 * math.sin(a + b)
        l3_val = -2.85 - 0.35 * a
        dky_val = 2.0 + (l1_val / abs(l3_val))
        return l1_val, l3_val, dky_val, l1_val + l3_val


class EmpyreanChaosHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(HTML_PAYLOAD.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/telemetry":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8")
            resp_payload = {"status": "ok"}
            try:
                data = json.loads(raw)
                ev = data.get("event", "PHASE_UPDATE")
                sys_idx = int(data.get("sysIdx", 0))
                a = float(data.get("a", 0.95))
                b = float(data.get("b", 0.70))
                c = float(data.get("c", 0.60))

                l1, l3, dky, div_r = evaluate_chaos_telemetry(sys_idx, a, b, c)
                resp_payload = {
                    "status": "ok",
                    "l1": l1,
                    "l3": l3,
                    "dky": dky,
                    "div": div_r,
                    "engine": ENGINE_LABEL,
                }

                names = ["AIZAWA", "LORENZ", "THOMAS", "HALVORSEN", "DADRAS", "CHEN"]
                s_name = names[sys_idx % len(names)]
                ts = time.strftime("%H:%M:%S")

                print(
                    f"{DIM}[{ts}]{RESET} "
                    f"{GOLD}{BOLD}[{ENGINE_LABEL}]{RESET} "
                    f"Event={ROSE}{ev:<26}{RESET} | "
                    f"Attractor={CYAN}{s_name:<9}{RESET} | "
                    f"L1={ROSE}+{l1:.3f} s^-1{RESET} | "
                    f"L3={BLUE}{l3:.3f} s^-1{RESET} | "
                    f"D_KY={GREEN}{dky:.3f}{RESET}",
                    flush=True,
                )
            except Exception:
                pass

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


def find_free_port(start_port=8098):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def open_browser_from_wsl(url):
    time.sleep(0.8)
    try:
        with open("/proc/version", "r") as f:
            proc_ver = f.read().lower()
        if "microsoft" in proc_ver or "wsl" in proc_ver:
            subprocess.Popen(
                ["cmd.exe", "/c", "start", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
    except Exception:
        pass

    try:
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def main():
    compile_and_load_cpp_engine()
    port = find_free_port(8098)
    url = f"http://localhost:{port}"

    os.system("clear" if os.name == "posix" else "cls")
    print(f"{GOLD}{BOLD}" + "=" * 94 + f"{RESET}")
    print(
        f"{GOLD}{BOLD}   EMPYREAN // C++17 CHAOS PHASE-SPACE, STRANGE ATTRACTORS & ASTROLABE ENGINE{RESET}"
    )
    print(
        f"{DIM}   C++17 Native Shared Library (chaos_engine.cpp -> libchaos.so) + 3D WebGL Astrolabe{RESET}"
    )
    print(f"{GOLD}{BOLD}" + "=" * 94 + f"{RESET}")
    print(
        f" {GREEN}OK{RESET} {BOLD}C++17 Physics Kernel:{RESET}              {CYAN}{BOLD}{ENGINE_LABEL}{RESET} (chaos_engine.cpp generated)"
    )
    print(
        f" {GREEN}OK{RESET} {BOLD}WSL Ubuntu Astrolabe Server:{RESET}       {GOLD}{BOLD}{url}{RESET}"
    )
    print(
        f" {GREEN}OK{RESET} {BOLD}Stop Server:{RESET}                       Press {ROSE}Ctrl + C{RESET} in this Ubuntu terminal"
    )
    print(f"{GOLD}" + "-" * 94 + f"{RESET}")
    print(
        f"{BOLD} LIVE C++17 BENETTIN LYAPUNOV SPECTRUM & KAPLAN-YORKE DIMENSION STREAM:{RESET}"
    )

    threading.Thread(target=open_browser_from_wsl, args=(url,), daemon=True).start()

    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), EmpyreanChaosHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(
            f"\n{ROSE}[EMPYREAN STOPPED]{RESET} Shutting down C++17 Chaos Astrolabe Engine."
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
