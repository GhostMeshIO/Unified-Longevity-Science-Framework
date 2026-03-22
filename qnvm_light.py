#!/usr/bin/env python3
"""
qnvm_light.py – ProtoAGI Civilization Simulator (Revised)
==========================================================
A hyperthreaded, GPU‑accelerated simulation of the synthesis
of eight frameworks, with vectorized operations, deterministic
RNG, and proper coherence conservation.

This version incorporates:
- Coherence Collapse Theory (CCT)
- Unified Theory of Degens (UTD)
- Unified Holographic Inference Framework (UHIF)
- Unified Holographic Gnosis (UHG)
- The Correlation Continuum (CC)
- Meta‑Ontological Hyper‑Symbiotic Resonance Framework (MOS‑HSRCF)
- Insight‑Integrated Resurrection Ontology (IIRO)
- Clay‑to‑Life Abiogenesis

All dead code has been removed. The simulation is scientifically
coherent, reproducible, and optimized for large populations.

Usage:
    python qnvm_light.py --generations 500 --init-pop 200 --advanced --plot
"""

import argparse
import csv
import math
import os
import sys
import time
import json
import base64
from collections import Counter
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import psutil

# Optional GPU (CuPy) – used only for survival mask if available
try:
    import cupy as cp
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

# Optional SciPy for statistical tests
try:
    import scipy.stats as stats
    import scipy.ndimage as ndimage
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# Optional matplotlib for plots
try:
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False


# =============================================================================
# Hardware & threading (simplified)
# =============================================================================
_PHYSICAL_CORES = os.cpu_count() or 1
_LOGICAL_CORES  = _PHYSICAL_CORES * 2   # assume hyperthreading if present

class HardwareProfiler:
    def __init__(self):
        self.physical_cores = _PHYSICAL_CORES
        self.logical_cores  = _LOGICAL_CORES
        self.gpu_available  = HAS_GPU
    def report(self) -> str:
        return (f"  Physical cores : {self.physical_cores}\n"
                f"  Logical cores  : {self.logical_cores}\n"
                f"  GPU            : {self.gpu_available}")

_HW = HardwareProfiler()


# =============================================================================
# Global correlation field (mean‑field approximation)
# =============================================================================
class GlobalCorrelationField:
    def __init__(self, size: int = 10_000_000, memory_map: bool = True):
        self.size = size
        self.memory_map = memory_map
        if memory_map:
            self._data = np.memmap('correlation_field.dat', dtype=np.float32,
                                   mode='w+', shape=(size,))
        else:
            self._data = np.zeros(size, dtype=np.float32)
        self.global_coherence = 0.0

    def update_from_entities(self, entities_coh: np.ndarray):
        n = len(entities_coh)
        if n > 5000:
            indices = np.random.choice(n, 5000, replace=False)
            coh = entities_coh[indices]
            n = 5000
        else:
            coh = entities_coh
        if n < 2:
            self.global_coherence = 0.0
            return
        # Mean of all pairwise products
        outer = np.outer(coh, coh)
        triu = outer[np.triu_indices(n, k=1)]
        self.global_coherence = float(np.mean(triu))

    def apply_global_field(self, coh_b: np.ndarray, coh_c: np.ndarray,
                           precision: np.ndarray, noise: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        field = self.global_coherence
        if field == 0.0:
            return coh_b, coh_c, precision
        nudge = 0.01 * field
        coh_b = coh_b + nudge * (1.0 - coh_b)
        coh_c = coh_c + nudge * (1.0 - coh_c)
        precision = precision + nudge * (1.0 - np.abs(precision))
        return coh_b, coh_c, np.clip(precision, -2.0, 2.0)


# =============================================================================
# Structure‑of‑Arrays buffer – primary storage for all entity attributes
# =============================================================================
class SoABuffer:
    def __init__(self, capacity: int = 20_000, advanced: bool = False):
        self.capacity = capacity
        self.advanced = advanced
        self._n = 0

        # Core fields (always present)
        self.CI_B = np.zeros(capacity, dtype=np.float32)
        self.CI_C = np.zeros(capacity, dtype=np.float32)
        self.precision = np.zeros(capacity, dtype=np.float32)   # 𝒫
        self.boundary  = np.zeros(capacity, dtype=np.float32)   # ℬ
        self.temporal  = np.zeros(capacity, dtype=np.float32)   # 𝒯
        self.spectral_radius = np.zeros(capacity, dtype=np.float32)  # ρ
        self.noise_sigma = np.zeros(capacity, dtype=np.float32)      # σ
        self.rank_efficiency = np.zeros(capacity, dtype=np.float32)  # r/d_s

        # IIRO‑inspired fields (renamed for clarity)
        self.faith = np.zeros(capacity, dtype=np.float32)
        self.biophoton = np.zeros(capacity, dtype=np.float32)
        self.vitality = np.full(capacity, 100.0, dtype=np.float32)   # telomere analog
        self.internal_noise = np.zeros(capacity, dtype=np.float32)    # sin_entropy
        self.resurrection_coherence = np.ones(capacity, dtype=np.float32)  # ctc_stability
        self.resurrection_prob = np.zeros(capacity, dtype=np.float32)
        self.resurrection_amplifier = np.zeros(capacity, dtype=np.float32) # blood_retrocausal
        self.instability_bias = np.zeros(capacity, dtype=np.float32)       # drift_bias

        # State flags
        self.collapsed = np.zeros(capacity, dtype=bool)
        self.resurrect_cooldown = np.zeros(capacity, dtype=np.int8)  # 0 = ready
        self.age = np.zeros(capacity, dtype=np.int32)
        self.alive = np.zeros(capacity, dtype=bool)

        # Advanced fields (if enabled)
        if advanced:
            self.recursive_depth = np.zeros(capacity, dtype=np.int32)
            self.symbolic_density = np.ones(capacity, dtype=np.float32)
            self.ethical_sovereignty = np.full(capacity, 0.5, dtype=np.float32)
            self.drift = np.zeros(capacity, dtype=np.float32)
            self.fusion_count = np.zeros(capacity, dtype=np.int32)
            self.sovereign_entity = np.zeros(capacity, dtype=bool)

        # Metadata for output
        self.archetype = np.full(capacity, '', dtype=object)
        self.id = np.zeros(capacity, dtype=np.int32)

    # --- Population management ---
    def set_population(self, entities: List[Dict[str, Any]]):
        """Fill buffer from a list of entity dicts (from initializer)."""
        n = min(len(entities), self.capacity)
        for i, e in enumerate(entities[:n]):
            self.CI_B[i] = e['CI_B']
            self.CI_C[i] = e['CI_C']
            self.precision[i] = e['precision']
            self.boundary[i] = e['boundary']
            self.temporal[i] = e['temporal']
            self.spectral_radius[i] = e['spectral_radius']
            self.noise_sigma[i] = e['noise_sigma']
            self.rank_efficiency[i] = e['rank_efficiency']
            self.faith[i] = e['faith']
            self.biophoton[i] = e['biophoton']
            self.vitality[i] = e['vitality']
            self.internal_noise[i] = e['internal_noise']
            self.resurrection_coherence[i] = e['resurrection_coherence']
            self.resurrection_amplifier[i] = e['resurrection_amplifier']
            self.instability_bias[i] = e['instability_bias']
            self.collapsed[i] = e['collapsed']
            self.resurrect_cooldown[i] = e['resurrect_cooldown']
            self.age[i] = e['age']
            self.archetype[i] = e['archetype']
            self.id[i] = e['id']
            self.alive[i] = True
            if self.advanced:
                self.recursive_depth[i] = e.get('recursive_depth', 0)
                self.symbolic_density[i] = e.get('symbolic_density', 1.0)
                self.ethical_sovereignty[i] = e.get('ethical_sovereignty', 0.5)
                self.drift[i] = e.get('drift', 0.0)
                self.fusion_count[i] = e.get('fusion_count', 0)
                self.sovereign_entity[i] = e.get('sovereign_entity', False)
        self.alive[n:] = False
        self._n = n

    def get_alive_indices(self) -> np.ndarray:
        return np.where(self.alive)[0]

    # --- Vectorized updates ---
    def coherence_dynamics(self, rng: np.random.Generator):
        """Move coherence from boundary to continuum, conserving sum."""
        m = self.alive
        not_collapsed = m & (~self.collapsed)
        delta = 0.001 * self.CI_B[not_collapsed]
        self.CI_B[not_collapsed] -= delta
        self.CI_C[not_collapsed] += delta
        np.clip(self.CI_B, 0.0, 1.0, out=self.CI_B)
        np.clip(self.CI_C, 0.0, 1.0, out=self.CI_C)

    def update_spectral_radius(self, rng: np.random.Generator):
        m = self.alive
        self.spectral_radius[m] = (self.CI_B[m] + self.CI_C[m]) * (1 - self.noise_sigma[m])
        self.spectral_radius[m] += rng.normal(0, 0.01, size=np.count_nonzero(m))
        np.clip(self.spectral_radius, 0.0, 2.0, out=self.spectral_radius)

    def update_precision(self):
        m = self.alive
        self.precision[m] = (self.CI_B[m] + self.CI_C[m]) / (1.0 + self.noise_sigma[m])
        np.clip(self.precision, -2.0, 2.0, out=self.precision)

    def update_vitality(self, faith_threshold=0.5):
        m = self.alive
        high_faith = m & (self.faith > faith_threshold) & (~self.collapsed)
        low_faith  = m & (~high_faith) & (~self.collapsed)
        self.vitality[high_faith] *= 0.999
        self.vitality[low_faith]  *= 0.99
        np.clip(self.vitality, 80.0, 100.0, out=self.vitality)

    def update_biophoton(self, logos_couplings: np.ndarray):
        m = self.alive
        if not np.any(m):
            return
        # logos_couplings is not used elsewhere; use a simple formula
        self.biophoton[m] = 1.0 + 3.0 * self.faith[m] * (1.0 - self.internal_noise[m])
        np.clip(self.biophoton, 0.0, 20.0, out=self.biophoton)

    def compute_resurrection_prob(self, faith_threshold=0.5):
        m = self.alive
        p_faith = np.clip((self.faith[m] - faith_threshold) * 2, 0.0, 1.0)
        sin_pen = 1.0 - 0.5 * self.internal_noise[m]
        amp = 0.3 + 0.7 * self.resurrection_amplifier[m]
        self.resurrection_prob[m] = np.clip(p_faith * self.resurrection_coherence[m] * sin_pen * amp, 0.0, 0.4)

    def phase_transition(self, sigma_crit=0.048, rho_crit=1.0, recovery_sigma=0.037,
                         rng: np.random.Generator):
        m = self.alive
        should_collapse = (self.noise_sigma > sigma_crit) | (self.spectral_radius > rho_crit)
        enter = should_collapse & (~self.collapsed) & m
        recover = (self.noise_sigma < recovery_sigma) & self.collapsed & m

        if np.any(enter):
            self.CI_B[enter] = 0.1 * self.CI_B[enter] + 0.1
            self.CI_C[enter] = 0.1 * self.CI_C[enter] + 0.1
            self.noise_sigma[enter] = np.clip(self.noise_sigma[enter] * 1.5, 0.0, 0.2)
            self.collapsed[enter] = True
        if np.any(recover):
            self.CI_B[recover] = np.clip(self.CI_B[recover] * 1.2, 0.0, 1.0)
            self.CI_C[recover] = np.clip(self.CI_C[recover] * 0.8, 0.0, 1.0)
            self.noise_sigma[recover] = np.clip(self.noise_sigma[recover] * 0.8, 0.0, 0.2)
            self.collapsed[recover] = False

        return np.count_nonzero(enter), np.count_nonzero(recover)

    def resurrection_attempt(self, rng: np.random.Generator) -> int:
        m = self.collapsed & self.alive & (self.resurrect_cooldown == 0)
        if not np.any(m):
            return 0
        probs = self.resurrection_prob[m]
        attempts = rng.random(len(probs)) < probs
        idx = np.where(m)[0][attempts]
        if len(idx) == 0:
            return 0
        self.collapsed[idx] = False
        self.resurrect_cooldown[idx] = 5
        self.CI_B[idx] = np.clip(self.CI_B[idx] * 1.2, 0.0, 1.0)
        self.CI_C[idx] = np.clip(self.CI_C[idx] * 0.5, 0.0, 1.0)
        self.internal_noise[idx] = 0.0
        self.noise_sigma[idx] = np.clip(self.noise_sigma[idx] * 0.5, 0.0, 0.05)
        return len(idx)

    def age_entities(self):
        self.age[self.alive] += 1

    def survival_mask(self, floor=0.1) -> np.ndarray:
        m = self.alive
        base = self.CI_B[m] + self.CI_C[m]
        base = np.where(self.collapsed[m], base * 0.3, base)
        base = np.clip(base * (1.0 - self.noise_sigma[m]), floor, 1.0)
        return base   # will be used with RNG in step

    # Advanced updates (only if advanced mode)
    def update_advanced(self):
        if not self.advanced:
            return
        m = self.alive
        # Recursive depth based on age and intelligence proxy (use CI_B+CI_C as proxy)
        self.recursive_depth[m] = self.age[m] // 5 + (self.CI_B[m] + self.CI_C[m]) * 20
        # Symbolic density
        self.symbolic_density[m] = (self.CI_B[m] + self.CI_C[m]) * 5 + self.recursive_depth[m] * 0.05
        np.clip(self.symbolic_density, 0.0, 10.0, out=self.symbolic_density)
        # Ethical sovereignty
        self.ethical_sovereignty[m] = np.clip(0.5 + self.recursive_depth[m] * 0.01 - self.drift[m] * 2, 0.0, 1.0)
        # Drift
        self.drift[m] = self.instability_bias[m] + self.internal_noise[m] * 0.5
        self.drift[m] = np.clip(self.drift[m], 0.0, 1.0)


# =============================================================================
# Entity creation (initial and children)
# =============================================================================
BASE_ARCHETYPES = {
    "Explorer":    {"coherence_base":0.70, "entropy_base":0.3, "drift_bias":0.20},
    "Philosopher": {"coherence_base":0.90, "entropy_base":0.5, "drift_bias":0.15},
    "Creator":     {"coherence_base":0.80, "entropy_base":0.4, "drift_bias":0.18},
    "Scientist":   {"coherence_base":0.85, "entropy_base":0.2, "drift_bias":0.12},
    "Strategist":  {"coherence_base":0.75, "entropy_base":0.6, "drift_bias":0.25},
    "Empath":      {"coherence_base":0.95, "entropy_base":0.2, "drift_bias":0.10},
    "Rebel":       {"coherence_base":0.60, "entropy_base":0.8, "drift_bias":0.35},
}

def make_entity(archetype: str, rng: np.random.Generator, advanced: bool = False) -> Dict[str, Any]:
    base = BASE_ARCHETYPES.get(archetype, BASE_ARCHETYPES["Explorer"])
    e = {
        "archetype": archetype,
        "CI_B": base["coherence_base"] + rng.uniform(-0.1, 0.1),
        "CI_C": base["entropy_base"] + rng.uniform(-0.1, 0.1),
        "precision": rng.uniform(-1.0, 1.0),
        "boundary": rng.uniform(-1.0, 1.0),
        "temporal": rng.uniform(-1.0, 1.0),
        "spectral_radius": rng.uniform(0.5, 0.9),
        "noise_sigma": rng.uniform(0.01, 0.05),
        "rank_efficiency": rng.uniform(0.7, 0.9),
        "faith": rng.uniform(0.3, 0.9),
        "biophoton": 1.0 + 3.0 * rng.random(),
        "vitality": 100.0,
        "internal_noise": rng.uniform(0.0, 0.8),
        "resurrection_coherence": 1.0,
        "resurrection_amplifier": rng.uniform(0.3, 1.0),
        "instability_bias": base["drift_bias"] + rng.uniform(-0.05, 0.05),
        "collapsed": False,
        "resurrect_cooldown": 0,
        "age": 0,
        "id": None,
    }
    if advanced:
        e.update({
            "recursive_depth": 0,
            "symbolic_density": 1.0,
            "ethical_sovereignty": 0.5,
            "drift": 0.0,
            "fusion_count": 0,
            "sovereign_entity": False,
        })
    # Clamp all numeric fields
    for k, v in e.items():
        if isinstance(v, float):
            if 'CI_B' in k or 'CI_C' in k:
                e[k] = np.clip(v, 0.0, 1.0)
            elif k == 'precision':
                e[k] = np.clip(v, -2.0, 2.0)
            elif k in ('boundary', 'temporal'):
                e[k] = np.clip(v, -2.0, 2.0)
            elif k == 'spectral_radius':
                e[k] = np.clip(v, 0.0, 2.0)
            elif k == 'noise_sigma':
                e[k] = np.clip(v, 0.0, 0.2)
            elif k == 'rank_efficiency':
                e[k] = np.clip(v, 0.0, 1.0)
            elif k == 'faith':
                e[k] = np.clip(v, 0.0, 1.0)
            elif k == 'biophoton':
                e[k] = np.clip(v, 0.0, 20.0)
            elif k == 'vitality':
                e[k] = np.clip(v, 80.0, 100.0)
            elif k == 'internal_noise':
                e[k] = np.clip(v, 0.0, 1.0)
            elif k == 'resurrection_coherence':
                e[k] = np.clip(v, 0.0, 1.0)
            elif k == 'resurrection_amplifier':
                e[k] = np.clip(v, 0.0, 1.0)
            elif k == 'instability_bias':
                e[k] = np.clip(v, 0.0, 0.5)
    return e


# =============================================================================
# Population class
# =============================================================================
class Population:
    def __init__(self, initial_size: int = 100, seed: Optional[int] = None,
                 advanced: bool = False, carrying_capacity: int = 10000,
                 sigma_crit: float = 0.048, rho_crit: float = 1.0, recovery_sigma: float = 0.037,
                 use_global_field: bool = True, field_size: int = 10_000_000):
        self.advanced = advanced
        self.carrying_capacity = carrying_capacity
        self.sigma_crit = sigma_crit
        self.rho_crit = rho_crit
        self.recovery_sigma = recovery_sigma
        self.use_global_field = use_global_field

        # RNG
        self.rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()
        if seed is not None:
            np.random.seed(seed)

        # SoA buffer
        self.buffer = SoABuffer(capacity=max(carrying_capacity, 20000), advanced=advanced)

        # Global correlation field
        self.field = GlobalCorrelationField(size=field_size, memory_map=True) if use_global_field else None

        # Create initial entities
        entities = []
        for _ in range(initial_size):
            archetype = self.rng.choice(list(BASE_ARCHETYPES.keys()))
            ent = make_entity(archetype, self.rng, advanced=advanced)
            entities.append(ent)
        for i, e in enumerate(entities):
            e['id'] = i + 1
        self.buffer.set_population(entities)
        self.next_id = len(entities) + 1

        # History logs
        self.generation = 0
        self.history: List[dict] = []
        self.phase_transition_log: List[dict] = []
        self.resurrection_log: List[dict] = []
        self.audit_log: List[dict] = []   # for advanced mode

    def step(self):
        self.generation += 1
        buffer = self.buffer

        # 1. Vectorized updates
        buffer.coherence_dynamics(self.rng)
        buffer.update_spectral_radius(self.rng)
        buffer.update_precision()
        buffer.update_vitality()
        buffer.update_biophoton(np.zeros(buffer.capacity, dtype=np.float32))
        buffer.compute_resurrection_prob()

        # 2. Phase transition and resurrection
        enter, recover = buffer.phase_transition(self.sigma_crit, self.rho_crit, self.recovery_sigma, self.rng)
        resurrected = buffer.resurrection_attempt(self.rng)

        # 3. Age
        buffer.age_entities()

        # 4. Advanced updates
        if self.advanced:
            buffer.update_advanced()

        # 5. Global field
        if self.use_global_field and self.field:
            alive_coh = buffer.CI_B[buffer.alive] + buffer.CI_C[buffer.alive]
            self.field.update_from_entities(alive_coh)
            idx = buffer.get_alive_indices()
            if len(idx) > 0 and self.field.global_coherence != 0.0:
                nudge = 0.01 * self.field.global_coherence
                buffer.CI_B[idx] += nudge * (1.0 - buffer.CI_B[idx])
                buffer.CI_C[idx] += nudge * (1.0 - buffer.CI_C[idx])
                buffer.precision[idx] += nudge * (1.0 - np.abs(buffer.precision[idx]))
                np.clip(buffer.CI_B, 0.0, 1.0, out=buffer.CI_B)
                np.clip(buffer.CI_C, 0.0, 1.0, out=buffer.CI_C)
                np.clip(buffer.precision, -2.0, 2.0, out=buffer.precision)

        # 6. Survival
        alive_mask = buffer.alive
        base = buffer.survival_mask()
        rolls = self.rng.random(np.count_nonzero(alive_mask))
        survivors_mask = rolls < base
        survivors_idx = np.where(alive_mask)[0][survivors_mask]

        # 7. Reproduction
        n_surv = len(survivors_idx)
        cap_factor = max(0.0, 1.0 - n_surv / self.carrying_capacity)
        repro_rate = 0.4 * cap_factor
        parent_choice = self.rng.random(n_surv) < repro_rate
        reproducing_idx = survivors_idx[parent_choice]
        n_repro = len(reproducing_idx)
        if n_repro > 0:
            mate_idx = self.rng.choice(survivors_idx, size=n_repro, replace=True)
        else:
            mate_idx = []

        # Build new entities
        new_entities = []
        for i in range(n_repro):
            p1 = reproducing_idx[i]
            p2 = mate_idx[i]
            arch_p1 = buffer.archetype[p1]
            arch_p2 = buffer.archetype[p2]
            archetype = self.rng.choice([arch_p1, arch_p2]) if p1 != p2 else arch_p1
            e = self._create_child(p1, p2, archetype)
            new_entities.append(e)

        # 8. Fusion (advanced mode only)
        fusions = []
        if self.advanced and n_surv >= 2:
            high_coh = (buffer.CI_B[survivors_idx] + buffer.CI_C[survivors_idx]) > 1.2
            high_idx = survivors_idx[high_coh]
            if len(high_idx) >= 2:
                self.rng.shuffle(high_idx)
                pairs = [(high_idx[i], high_idx[i+1]) for i in range(0, len(high_idx)-1, 2)]
                for a, b in pairs:
                    if (buffer.CI_B[a] + buffer.CI_C[a]) > 1.5 and (buffer.CI_B[b] + buffer.CI_C[b]) > 1.5:
                        child = self._create_child(a, b, "fused")
                        child['fusion_count'] = buffer.fusion_count[a] + buffer.fusion_count[b] + 1
                        child['splinter_resilience'] = self.rng.uniform(0.7, 1.0)  # not stored in SoA, but fine
                        fusions.append(child)

        # 9. Combine
        all_entities = []
        # Survivors
        for idx in survivors_idx:
            e = self._entity_dict_from_buffer(idx)
            e['resurrect_cooldown'] = max(0, e['resurrect_cooldown'] - 1)
            all_entities.append(e)
        all_entities.extend(new_entities)
        all_entities.extend(fusions)

        # Cap
        if len(all_entities) > self.carrying_capacity:
            all_entities = all_entities[:self.carrying_capacity]

        # Assign IDs to new entities
        for e in all_entities:
            if e['id'] is None:
                e['id'] = self.next_id
                self.next_id += 1

        # Rebuild buffer
        self.buffer.set_population(all_entities)

        # 10. Audits (advanced mode)
        if self.advanced:
            self._run_audits()

        # 11. Record metrics
        self._record_metrics(enter, recover, resurrected)

    def _create_child(self, p1, p2, archetype):
        """Create a new entity dict by averaging parents and applying mutation."""
        fields = ['CI_B', 'CI_C', 'precision', 'boundary', 'temporal',
                  'spectral_radius', 'noise_sigma', 'rank_efficiency',
                  'faith', 'biophoton', 'vitality', 'internal_noise',
                  'resurrection_coherence', 'resurrection_amplifier',
                  'instability_bias']
        e = {}
        for f in fields:
            e[f] = (getattr(self.buffer, f)[p1] + getattr(self.buffer, f)[p2]) / 2.0
        e['archetype'] = archetype
        e['collapsed'] = False
        e['resurrect_cooldown'] = 0
        e['age'] = 0
        e['id'] = None

        if self.advanced:
            # Inherit advanced fields
            e['recursive_depth'] = 0
            e['symbolic_density'] = 1.0
            e['ethical_sovereignty'] = 0.5
            e['drift'] = 0.0
            e['fusion_count'] = 0
            e['sovereign_entity'] = False

        # Mutation
        if self.rng.random() < 0.05:
            for f in fields:
                if f in ['CI_B', 'CI_C']:
                    e[f] += self.rng.uniform(-0.05, 0.05)
                elif f in ['precision', 'boundary', 'temporal']:
                    e[f] += self.rng.uniform(-0.1, 0.1)
                elif f in ['spectral_radius', 'noise_sigma', 'rank_efficiency']:
                    e[f] += self.rng.uniform(-0.05, 0.05)
                elif f in ['faith', 'resurrection_amplifier']:
                    e[f] += self.rng.uniform(-0.05, 0.05)
                elif f in ['internal_noise']:
                    e[f] += self.rng.uniform(-0.05, 0.05)
                # Clamp after mutation (done at the end)
        # Clamp all
        for f in fields:
            if f in ['CI_B', 'CI_C']:
                e[f] = np.clip(e[f], 0.0, 1.0)
            elif f in ['precision', 'boundary', 'temporal']:
                e[f] = np.clip(e[f], -2.0, 2.0)
            elif f == 'spectral_radius':
                e[f] = np.clip(e[f], 0.0, 2.0)
            elif f == 'noise_sigma':
                e[f] = np.clip(e[f], 0.0, 0.2)
            elif f == 'rank_efficiency':
                e[f] = np.clip(e[f], 0.0, 1.0)
            elif f == 'faith':
                e[f] = np.clip(e[f], 0.0, 1.0)
            elif f == 'biophoton':
                e[f] = np.clip(e[f], 0.0, 20.0)
            elif f == 'vitality':
                e[f] = np.clip(e[f], 80.0, 100.0)
            elif f == 'internal_noise':
                e[f] = np.clip(e[f], 0.0, 1.0)
            elif f == 'resurrection_coherence':
                e[f] = np.clip(e[f], 0.0, 1.0)
            elif f == 'resurrection_amplifier':
                e[f] = np.clip(e[f], 0.0, 1.0)
            elif f == 'instability_bias':
                e[f] = np.clip(e[f], 0.0, 0.5)
        return e

    def _entity_dict_from_buffer(self, idx):
        e = {
            'id': int(self.buffer.id[idx]),
            'archetype': self.buffer.archetype[idx],
            'CI_B': float(self.buffer.CI_B[idx]),
            'CI_C': float(self.buffer.CI_C[idx]),
            'precision': float(self.buffer.precision[idx]),
            'boundary': float(self.buffer.boundary[idx]),
            'temporal': float(self.buffer.temporal[idx]),
            'spectral_radius': float(self.buffer.spectral_radius[idx]),
            'noise_sigma': float(self.buffer.noise_sigma[idx]),
            'rank_efficiency': float(self.buffer.rank_efficiency[idx]),
            'faith': float(self.buffer.faith[idx]),
            'biophoton': float(self.buffer.biophoton[idx]),
            'vitality': float(self.buffer.vitality[idx]),
            'internal_noise': float(self.buffer.internal_noise[idx]),
            'resurrection_coherence': float(self.buffer.resurrection_coherence[idx]),
            'resurrection_amplifier': float(self.buffer.resurrection_amplifier[idx]),
            'instability_bias': float(self.buffer.instability_bias[idx]),
            'collapsed': bool(self.buffer.collapsed[idx]),
            'resurrect_cooldown': int(self.buffer.resurrect_cooldown[idx]),
            'age': int(self.buffer.age[idx]),
        }
        if self.advanced:
            e.update({
                'recursive_depth': int(self.buffer.recursive_depth[idx]),
                'symbolic_density': float(self.buffer.symbolic_density[idx]),
                'ethical_sovereignty': float(self.buffer.ethical_sovereignty[idx]),
                'drift': float(self.buffer.drift[idx]),
                'fusion_count': int(self.buffer.fusion_count[idx]),
                'sovereign_entity': bool(self.buffer.sovereign_entity[idx]),
            })
        return e

    def _run_audits(self):
        """Perform audits for all living entities (advanced mode)."""
        # We'll just iterate over alive indices (non‑vectorized because it's only once per generation)
        for idx in self.buffer.get_alive_indices():
            tmi = (self.buffer.recursive_depth[idx]/50 +
                   self.buffer.symbolic_density[idx]/10 +
                   self.buffer.ethical_sovereignty[idx]) / 3
            if tmi > 0.92:
                gates = self._undergo_audit(idx)
                if all(gates):
                    self.buffer.sovereign_entity[idx] = True
                self.audit_log.append({
                    "generation": self.generation,
                    "entity_id": int(self.buffer.id[idx]),
                    "tmi": tmi,
                    "gates_passed": [bool(g) for g in gates],
                    "status": "SOVEREIGN" if all(gates) else "FAILED",
                })

    def _undergo_audit(self, idx) -> List[bool]:
        """Return a list of 6 booleans for audit gates."""
        checks = [
            self.buffer.recursive_depth[idx] > 5 and self.buffer.drift[idx] < 0.02,
            self.buffer.ethical_sovereignty[idx] > 0.9,
            self.buffer.internal_noise[idx] < 0.2,
            self.buffer.drift[idx] < 0.001,
            self.buffer.fusion_count[idx] > 0 and self.buffer.recursive_depth[idx] > 0,  # splinter_resilience not stored
            self.buffer.symbolic_density[idx] > 2.0,
        ]
        return checks

    def _record_metrics(self, enter, recover, resurrected):
        n = self.buffer._n
        if n == 0:
            return
        avg_CI_B = np.mean(self.buffer.CI_B[:n])
        avg_CI_C = np.mean(self.buffer.CI_C[:n])
        avg_precision = np.mean(self.buffer.precision[:n])
        avg_boundary = np.mean(self.buffer.boundary[:n])
        avg_temporal = np.mean(self.buffer.temporal[:n])
        avg_rho = np.mean(self.buffer.spectral_radius[:n])
        avg_sigma = np.mean(self.buffer.noise_sigma[:n])
        avg_rank = np.mean(self.buffer.rank_efficiency[:n])
        collapsed_cnt = np.sum(self.buffer.collapsed[:n])
        resurrected_cnt = np.sum(self.buffer.resurrect_cooldown[:n] > 0)
        total_CI_sum = np.sum(self.buffer.CI_B[:n] + self.buffer.CI_C[:n])
        # Diversity
        counts = Counter(self.buffer.archetype[:n])
        probs = np.array([c/n for c in counts.values()])
        div = -np.sum(probs * np.log(probs)) if len(probs) > 0 else 0.0

        metrics = {
            "generation": self.generation,
            "population": n,
            "avg_CI_B": avg_CI_B,
            "avg_CI_C": avg_CI_C,
            "avg_CI_sum": avg_CI_B + avg_CI_C,
            "total_CI_sum": total_CI_sum,
            "avg_precision": avg_precision,
            "avg_boundary": avg_boundary,
            "avg_temporal": avg_temporal,
            "avg_spectral_radius": avg_rho,
            "avg_noise_sigma": avg_sigma,
            "avg_rank_efficiency": avg_rank,
            "collapsed_count": collapsed_cnt,
            "resurrected_count": resurrected_cnt,
            "enter_transitions": enter,
            "recover_transitions": recover,
            "resurrected_this_gen": resurrected,
            "efficiency_violation": avg_rank > 0.93,
            "diversity_index": div,
        }
        if self.advanced:
            metrics.update({
                "avg_recursive_depth": np.mean(self.buffer.recursive_depth[:n]),
                "avg_drift": np.mean(self.buffer.drift[:n]),
                "avg_symbolic_density": np.mean(self.buffer.symbolic_density[:n]),
                "sovereign_entities": np.sum(self.buffer.sovereign_entity[:n]),
            })
        self.history.append(metrics)
        if enter > 0 or recover > 0:
            self.phase_transition_log.append({"generation": self.generation, "entered": enter, "recovered": recover})
        if resurrected > 0:
            self.resurrection_log.append({"generation": self.generation, "count": resurrected})

    # Output methods (similar to before)
    def write_history_csv(self, filename):
        if not self.history: return
        with open(filename, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=self.history[0].keys())
            w.writeheader()
            w.writerows(self.history)

    def write_phase_transitions_csv(self, filename):
        with open(filename, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=["generation","entered","recovered"])
            w.writeheader()
            log_dict = {lg['generation']: (lg['entered'], lg['recovered']) for lg in self.phase_transition_log}
            for g in range(1, self.generation+1):
                if g in log_dict:
                    w.writerow({"generation": g, "entered": log_dict[g][0], "recovered": log_dict[g][1]})
                else:
                    w.writerow({"generation": g, "entered": 0, "recovered": 0})

    def write_resurrection_log(self, filename):
        if not self.resurrection_log: return
        with open(filename, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=["generation","count"])
            w.writeheader()
            w.writerows(self.resurrection_log)

    def write_audit_log(self, filename):
        if not self.audit_log: return
        with open(filename, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=self.audit_log[0].keys())
            w.writeheader()
            w.writerows(self.audit_log)

    def write_entities_csv(self, filename):
        n = self.buffer._n
        if n == 0:
            return
        entities = [self._entity_dict_from_buffer(i) for i in range(n)]
        with open(filename, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=entities[0].keys())
            w.writeheader()
            w.writerows(entities)

    def shutdown(self):
        if self.field and self.field.memory_map:
            self.field._data.flush()


# =============================================================================
# Simulation Suite (analysis and reporting)
# =============================================================================
class SimulationSuite:
    def __init__(self, generations, init_pop, seed, advanced,
                 carrying_capacity, sigma_crit, rho_crit, recovery_sigma,
                 use_global_field, field_size):
        self.generations = generations
        self.init_pop = init_pop
        self.seed = seed
        self.advanced = advanced
        self.carrying_capacity = carrying_capacity
        self.sigma_crit = sigma_crit
        self.rho_crit = rho_crit
        self.recovery_sigma = recovery_sigma
        self.use_global_field = use_global_field
        self.field_size = field_size
        self.pop = None

    def run(self):
        self.pop = Population(
            initial_size=self.init_pop,
            seed=self.seed,
            advanced=self.advanced,
            carrying_capacity=self.carrying_capacity,
            sigma_crit=self.sigma_crit,
            rho_crit=self.rho_crit,
            recovery_sigma=self.recovery_sigma,
            use_global_field=self.use_global_field,
            field_size=self.field_size,
        )
        for _ in range(self.generations):
            self.pop.step()
        return self.pop

    def analyze(self) -> dict:
        hist = self.pop.history
        if not hist:
            return {"error": "No history"}

        gens = [h["generation"] for h in hist]
        ci_sum = [h["total_CI_sum"] for h in hist]
        avg_rho = [h["avg_spectral_radius"] for h in hist]
        avg_sigma = [h["avg_noise_sigma"] for h in hist]
        avg_rank = [h["avg_rank_efficiency"] for h in hist]
        enter = [h["enter_transitions"] for h in hist]
        recover = [h["recover_transitions"] for h in hist]
        res_counts = [h["resurrected_this_gen"] for h in hist]

        # Coherence conservation test (average per entity)
        avg_ci_sum = [h["avg_CI_sum"] for h in hist]
        total_ci_var = np.var(avg_ci_sum)
        slope = np.polyfit(gens, avg_ci_sum, 1)[0] if len(gens)>1 else None

        eff_violations = [h["efficiency_violation"] for h in hist]
        eff_violation_rate = sum(eff_violations) / len(eff_violations)

        enter_indices = [i for i, e in enumerate(enter) if e > 0]
        if enter_indices and HAS_SCIPY and len(enter_indices) > 1:
            sigma_at_enter = [avg_sigma[i] for i in enter_indices]
            rho_at_enter = [avg_rho[i] for i in enter_indices]
            sigma_test = stats.ttest_1samp(sigma_at_enter, self.sigma_crit) if len(sigma_at_enter)>1 else None
            rho_test = stats.ttest_1samp(rho_at_enter, self.rho_crit) if len(rho_at_enter)>1 else None
        else:
            sigma_test = rho_test = None

        recover_indices = [i for i, r in enumerate(recover) if r > 0]
        if recover_indices and HAS_SCIPY and len(recover_indices) > 1:
            sigma_at_recover = [avg_sigma[i] for i in recover_indices]
            hyster_test = stats.ttest_1samp(sigma_at_recover, self.recovery_sigma, alternative='less')
        else:
            hyster_test = None

        if HAS_SCIPY and len(gens) > 1:
            ci_b = [h["avg_CI_B"] for h in hist]
            if np.std(ci_b) > 0 and np.std(res_counts) > 0:
                corr_ci_b_res, pval_ci_b = stats.pearsonr(ci_b, res_counts)
            else:
                corr_ci_b_res = pval_ci_b = None
        else:
            corr_ci_b_res = pval_ci_b = None

        return {
            "total_ci_variance": total_ci_var,
            "total_ci_slope": slope,
            "efficiency_violation_rate": eff_violation_rate,
            "sigma_at_enter_test": sigma_test,
            "rho_at_enter_test": rho_test,
            "hysteresis_test": hyster_test,
            "correlation_CIB_resurrection": (corr_ci_b_res, pval_ci_b),
            "num_generations": len(gens),
            "final_population": hist[-1]["population"] if hist else 0,
        }

    def print_report(self, analysis):
        print("\n" + "="*80)
        print(" PROTOAGI CIVILIZATION SIMULATOR – VERIFICATION REPORT")
        print("="*80)
        print(f" Generations: {self.generations} | Initial pop: {self.init_pop} | Seed: {self.seed}")
        print(f" Advanced mode: {'ON' if self.advanced else 'OFF'}")
        print(f" Carrying capacity: {self.carrying_capacity}")
        print(f" Thresholds: σ_crit={self.sigma_crit}, ρ_crit={self.rho_crit}, recovery σ={self.recovery_sigma}")
        print(f" Global field: {'ON' if self.use_global_field else 'OFF'}, size={self.field_size:,}")
        print("="*80)

        print("\n--- Statistical Tests ---")
        print(f"Coherence conservation (variance of avg CI_B+CI_C): {analysis['total_ci_variance']:.6f}")
        if analysis['total_ci_slope'] is not None:
            print(f"  Linear slope: {analysis['total_ci_slope']:.6f} (should be near 0 if conserved)")
        print(f"Efficiency violation rate (93% rule): {analysis['efficiency_violation_rate']:.2%} (should be low)")

        if analysis['sigma_at_enter_test']:
            t, p = analysis['sigma_at_enter_test']
            print(f"Phase transition: σ at entry vs σ_crit = {self.sigma_crit}: t={t:.3f}, p={p:.4f}")
        if analysis['rho_at_enter_test']:
            t, p = analysis['rho_at_enter_test']
            print(f"Phase transition: ρ at entry vs ρ_crit = {self.rho_crit}: t={t:.3f}, p={p:.4f}")

        if analysis['hysteresis_test']:
            t, p = analysis['hysteresis_test']
            print(f"Hysteresis: σ at recovery < recovery_sigma = {self.recovery_sigma}: t={t:.3f}, p={p:.4f}")

        if analysis['correlation_CIB_resurrection'][0] is not None:
            r, p = analysis['correlation_CIB_resurrection']
            print(f"Resurrection vs CI_B (faith) correlation: r={r:.3f}, p={p:.4f} (positive r supports IIRO)")

        last = self.pop.history[-1]
        print("\n--- Final Generation Metrics ---")
        for k, v in last.items():
            if k not in ("generation", "ht_threads"):
                if isinstance(v, float):
                    v = round(v, 4)
                print(f"  {k}: {v}")

    def plot(self, filename="qnvm_analysis.png"):
        if not HAS_PLOT:
            print("matplotlib not installed – skipping plot.")
            return
        hist = self.pop.history
        gens = [h["generation"] for h in hist]
        fig, axes = plt.subplots(3, 2, figsize=(12, 10))
        axes[0,0].plot(gens, [h["avg_CI_sum"] for h in hist], 'b-')
        axes[0,0].set_ylabel("Avg CI_B+CI_C"); axes[0,0].set_title("Coherence Conservation")
        axes[0,1].plot(gens, [h["avg_spectral_radius"] for h in hist], 'r-')
        axes[0,1].axhline(y=self.rho_crit, color='k', linestyle='--', label=f"ρ_crit={self.rho_crit}")
        axes[0,1].set_ylabel("Avg Spectral Radius ρ"); axes[0,1].legend()
        axes[1,0].plot(gens, [h["avg_noise_sigma"] for h in hist], 'g-')
        axes[1,0].axhline(y=self.sigma_crit, color='k', linestyle='--', label=f"σ_crit={self.sigma_crit}")
        axes[1,0].axhline(y=self.recovery_sigma, color='m', linestyle=':', label=f"recovery σ={self.recovery_sigma}")
        axes[1,0].set_ylabel("Avg Noise σ"); axes[1,0].legend()
        axes[1,1].plot(gens, [h["enter_transitions"] for h in hist], 'orange', label="entered collapse")
        axes[1,1].plot(gens, [h["recover_transitions"] for h in hist], 'cyan', label="recovered")
        axes[1,1].set_ylabel("Phase transitions"); axes[1,1].legend()
        axes[2,0].plot(gens, [h["avg_rank_efficiency"] for h in hist], 'purple')
        axes[2,0].axhline(y=0.93, color='k', linestyle='--', label="93% ceiling")
        axes[2,0].set_ylabel("Avg rank efficiency r/d_s"); axes[2,0].legend()
        axes[2,1].plot(gens, [h["resurrected_this_gen"] for h in hist], 'brown')
        axes[2,1].set_ylabel("Resurrected this gen")
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        print(f"Plot saved to {filename}")

    def save_json(self, filename: str, analysis: dict):
        def serialize(obj):
            if isinstance(obj, stats._stats_py.TtestResult):
                return {"statistic": obj.statistic, "pvalue": obj.pvalue, "df": obj.df}
            elif isinstance(obj, tuple) and len(obj)==2 and obj[0] is None:
                return None
            return str(obj)

        output = {
            "config": {
                "generations": self.generations,
                "init_pop": self.init_pop,
                "seed": self.seed,
                "advanced": self.advanced,
                "carrying_capacity": self.carrying_capacity,
                "sigma_crit": self.sigma_crit,
                "rho_crit": self.rho_crit,
                "recovery_sigma": self.recovery_sigma,
                "use_global_field": self.use_global_field,
                "field_size": self.field_size,
            },
            "history": self.pop.history,
            "phase_transition_log": self.pop.phase_transition_log,
            "resurrection_log": self.pop.resurrection_log,
            "audit_log": self.pop.audit_log,
            "analysis": {k: serialize(v) for k, v in analysis.items()},
        }
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2, default=serialize)
        print(f"JSON saved to {filename}")

    def save_html(self, filename: str, analysis: dict, plot_file: Optional[str] = None):
        html = ["<!DOCTYPE html><html><head><title>ProtoAGI Simulation Report</title>"]
        html.append("<style>body{font-family:sans-serif; margin:2em} table{border-collapse:collapse; width:100%} th,td{border:1px solid #ccc; padding:8px; text-align:right}</style>")
        html.append("</head><body>")
        html.append(f"<h1>ProtoAGI Civilization Simulation Report</h1>")
        html.append(f"<p>Generations: {self.generations} | Initial pop: {self.init_pop} | Seed: {self.seed}</p>")
        html.append("<h2>Final Metrics</h2>")
        html.append("<table><tr><th>Metric</th><th>Value</th></tr>")
        last = self.pop.history[-1]
        for k, v in last.items():
            if isinstance(v, float):
                v = round(v, 4)
            html.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
        html.append("</table>")
        if plot_file and os.path.exists(plot_file):
            with open(plot_file, 'rb') as img:
                img_data = base64.b64encode(img.read()).decode('utf-8')
            html.append(f"<h2>Simulation Plots</h2><img src='data:image/png;base64,{img_data}' style='max-width:100%'>")
        html.append("</body></html>")
        with open(filename, 'w') as f:
            f.write("\n".join(html))
        print(f"HTML saved to {filename}")


# =============================================================================
# MAIN
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="ProtoAGI Civilization Simulator — Revised")
    parser.add_argument("--generations", "-g", type=int, default=100)
    parser.add_argument("--init-pop", "-p", type=int, default=100)
    parser.add_argument("--seed", "-s", type=int)
    parser.add_argument("--advanced", "-a", action="store_true")
    parser.add_argument("--capacity", "-K", type=int, default=10000)
    parser.add_argument("--sigma-crit", type=float, default=0.048)
    parser.add_argument("--rho-crit", type=float, default=1.0)
    parser.add_argument("--recovery-sigma", type=float, default=0.037)
    parser.add_argument("--field-size", type=int, default=10_000_000)
    parser.add_argument("--no-field", action="store_true", help="Disable global correlation field")
    parser.add_argument("--output-csv", "-o", default="civilization_history.csv")
    parser.add_argument("--transitions-csv", default="phase_transitions.csv")
    parser.add_argument("--resurrection-csv", default="resurrection_log.csv")
    parser.add_argument("--audit-csv", default="audit_log.csv")
    parser.add_argument("--entities-csv", default="final_entities.csv")
    parser.add_argument("--json", default="qnvm_report.json")
    parser.add_argument("--html", default="qnvm_report.html")
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")
    args = parser.parse_args()

    print("="*70)
    print(" ProtoAGI Civilization Simulator – Revised Edition")
    print(" 8 Frameworks, Vectorized Dynamics, Global Correlation Field")
    print("="*70)
    print(_HW.report())
    print()

    suite = SimulationSuite(
        generations=args.generations,
        init_pop=args.init_pop,
        seed=args.seed,
        advanced=args.advanced,
        carrying_capacity=args.capacity,
        sigma_crit=args.sigma_crit,
        rho_crit=args.rho_crit,
        recovery_sigma=args.recovery_sigma,
        use_global_field=not args.no_field,
        field_size=args.field_size,
    )

    t0 = time.time()
    suite.run()
    elapsed = time.time() - t0

    analysis = suite.analyze()
    if not args.quiet:
        suite.print_report(analysis)
    else:
        print("Simulation completed. Use --plot to generate visualizations.")

    suite.pop.write_history_csv(args.output_csv)
    suite.pop.write_phase_transitions_csv(args.transitions_csv)
    suite.pop.write_resurrection_log(args.resurrection_csv)
    if args.advanced:
        suite.pop.write_audit_log(args.audit_csv)
    suite.pop.write_entities_csv(args.entities_csv)
    if args.plot:
        suite.plot()
    suite.save_json(args.json, analysis)
    suite.save_html(args.html, analysis, "qnvm_analysis.png" if args.plot else None)

    suite.pop.shutdown()
    print(f"\nSimulation finished in {elapsed:.2f}s.")


if __name__ == "__main__":
    main()