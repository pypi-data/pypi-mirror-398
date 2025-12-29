# DigPipe

Modular Decimal-Digit Input Pipeline for GBA Emulation

## Overview

**DigPipe** is a utility for decimal-digit generation, storage, mapping, and emulator-agnostic input rendering.
 
***Contextual note**: This is part of a larger project which aims to allow consecutive digits of pi to "play" video games. The gameplay will then be analyzed in an attempt to identify any emergent behaviors or patterns observed.*


### High-Level Goal

Design and implement a **modular, chunk-based pipeline** that:

1. Generates **decimal digits (0–9)** from a mathematical source (initially π).
2. Stores digits efficiently in **chunked, compact binary form**.
3. Maps digits to **abstract input actions** (e.g., 10 GBA controls).
4. Emits emulator-agnostic or emulator-specific input streams (later).

This system is intended to scale to **hundreds of millions or billions of digits**, while remaining:

* memory-bounded
* resumable
* verifiable
* and emulator-agnostic.

## Agents

Coding agents and other automated tools should refer to [AGENTS.md](AGENTS.md) for complete project requirements and instructions