<p align="center">
  <img
    src="https://raw.githubusercontent.com/BerndStechauner/coolpy/main/src/coolpy/logo/coolpy_logo.png"
    alt="CoolPy logo"
    width="300"
  >
</p>


# coolpy

CoolPy is a Python package for **muon beam cooling studies**, with a particular
focus on **solenoid matching and ionization cooling lattices**.

The package combines high-level Python workflows with performance-critical
components written in C++ to accelerate optimization and beam dynamics
calculations.

---

## About

CoolPy provides numerical tools for realistic modeling and optimization of
solenoid-based ionization cooling channels. It is designed for **research and prototyping**
in low accelerator and muon beam physics, rather than as a turnkey simulation code.

Key features include:

- Realistic solenoid magnetic field calculations based on a **semi-analytic
  current sheet model**
- Evaluation of elliptical integrals for off-axis field components, with
  optimized analytic expressions on the solenoid axis
- Optimization routines based on the **Nelder–Mead algorithm**, implemented in
  C++ for ultra fast performance
- Solution of the transverse beam envelope equation using a **fourth-order
  Runge–Kutta integrator**, implemented in C++ for accelerating computation

The code is intended to complement existing accelerator simulation tools by
providing lightweight, flexible, and transparent matching and optimization
routines.

---

## Installation

CoolPy supports **Python 3.8 – 3.12**.

Install CoolPy from PyPI using:

```bash
pip install coolpy
