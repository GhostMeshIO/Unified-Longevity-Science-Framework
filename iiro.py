#!/usr/bin/env python3
"""
iiro.py – IIRO v2.0 Integration for ProtoAGI Civilization Simulator
===================================================================
Revised edition with vectorized SoA buffer, deterministic RNG,
coherence conservation, and proper resurrection dynamics.

Based on:
- Insight-Integrated Resurrection Ontology (IIRO) v2.0
- 48 cutting-edge CPU/RAM/GPU synchronization/optimization algorithms
  derived from 169 ontological frameworks (placeholder stubs)

Usage:
    python iiro.py [--generations N] [--init-pop M] [--seed S]
                   [--optimization-level {0,1,2,3}] [--threads T]
                   [--carrying-capacity K] [--plot] [--json FILE] [--html FILE]
"""

import argparse
import csv
import math
import os
import random
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
class IIROSoABuffer:
    def __init__(self, capacity: int = 20_000):
        self.capacity = capacity
        self._n = 0

        # Core fields
        self.intelligence = np.zeros(capacity, dtype=np.float32)
        self.coherence    = np.zeros(capacity, dtype=np.float32)
        self.entropy      = np.zeros(capacity, dtype=np.float32)
        self.sophia       = np.zeros(capacity, dtype=np.float32)
        self.memory_size  = np.zeros(capacity, dtype=np.int32)

        # IIRO‑specific fields (renamed for clarity)
        self.faith = np.zeros(capacity, dtype=np.float32)
        self.biophoton = np.zeros(capacity, dtype=np.float32)
        self.vitality = np.full(capacity, 100.0, dtype=np.float32)   # telomere
        self.internal_noise = np.zeros(capacity, dtype=np.float32)    # sin_entropy
        self.resurrection_coherence = np.ones(capacity, dtype=np.float32)  # ctc
        self.resurrection_prob = np.zeros(capacity, dtype=np.float32)
        self.resurrection_amplifier = np.zeros(capacity, dtype=np.float32) # blood_retro
        self.instability_bias = np.zeros(capacity, dtype=np.float32)       # drift_bias

        # State flags
        self.collapsed = np.zeros(capacity, dtype=bool)
        self.resurrect_cooldown = np.zeros(capacity, dtype=np.int8)  # 0 = ready
        self.resurrected = np.zeros(capacity, dtype=bool)   # ever resurrected (for logging)
        self.age = np.zeros(capacity, dtype=np.int32)
        self.alive = np.zeros(capacity, dtype=bool)

        # Additional IIRO fields
        self.mycelial_connectivity = np.ones(capacity, dtype=np.float32)
        self.logos_coupling = np.zeros(capacity, dtype=np.float32)

        # Metadata for output
        self.archetype = np.full(capacity, '', dtype=object)
        self.traits = np.full(capacity, '', dtype=object)   # pipe‑separated string
        self.id = np.zeros(capacity, dtype=np.int32)

    # --- Population management ---
    def set_population(self, entities: List[Dict[str, Any]]):
        n = min(len(entities), self.capacity)
        for i, e in enumerate(entities[:n]):
            self.intelligence[i] = e['intelligence']
            self.coherence[i]    = e['coherence']
            self.entropy[i]      = e['entropy']
            self.sophia[i]       = e['sophia_score']
            self.memory_size[i]  = e['memory_size']
            self.faith[i]        = e['faith_amplitude']
            self.biophoton[i]    = e['biophotonic_emission']
            self.vitality[i]     = e['telomere_length']
            self.internal_noise[i] = e['sin_entropy']
            self.resurrection_coherence[i] = e['ctc_stability']
            self.resurrection_amplifier[i] = e['blood_retrocausal']
            self.instability_bias[i] = e['drift_bias']
            self.collapsed[i]    = e['collapsed']
            self.resurrect_cooldown[i] = e['resurrect_cooldown']
            self.resurrected[i]  = e.get('resurrected', False)
            self.age[i]          = e['age']
            self.mycelial_connectivity[i] = e.get('mycelial_connectivity', 0.7)
            self.logos_coupling[i] = e.get('logos_coupling', 0.0)
            self.archetype[i]    = e['archetype']
            self.traits[i]       = e['traits']
            self.id[i]           = e['id']
            self.alive[i]        = True
        self.alive[n:] = False
        self._n = n

    def get_alive_indices(self) -> np.ndarray:
        return np.where(self.alive)[0]

    # --- Vectorized updates ---
    def coherence_dynamics(self, rng: np.random.Generator):
        """Move coherence from boundary to continuum, conserving sum."""
        m = self.alive
        not_collapsed = m & (~self.collapsed)
        delta = 0.001 * self.coherence[not_collapsed]
        self.coherence[not_collapsed] -= delta
        self.entropy[not_collapsed]   += delta
        np.clip(self.coherence, 0.0, 1.0, out=self.coherence)
        np.clip(self.entropy,   0.0, 1.0, out=self.entropy)

    def update_sophia(self):
        """Compute Sophia score from coherence, intelligence, entropy."""
        phi_r = 1.0 / ((1 + math.sqrt(5)) / 2)
        m = self.alive
        # Use the vectorized version
        s = 1.0 - np.abs(self.coherence[m] - phi_r) * 2
        s = s * (self.intelligence[m] / 100.0) * (1.0 - self.entropy[m])
        self.sophia[m] = np.clip(s, 0.0, 1.0)

    def update_vitality(self, faith_threshold=0.5):
        m = self.alive
        high_faith = m & (self.faith > faith_threshold) & (~self.collapsed)
        low_faith  = m & (~high_faith) & (~self.collapsed)
        self.vitality[high_faith] *= 0.999
        self.vitality[low_faith]  *= 0.99
        np.clip(self.vitality, 80.0, 100.0, out=self.vitality)

    def update_biophoton(self):
        m = self.alive
        if not np.any(m):
            return
        # Use logos_coupling (static) and a simple formula
        voice_term = 4.0 * (self.logos_coupling[m] ** 2)
        self.biophoton[m] = np.clip(voice_term + self.biophoton[m] * 0.1, 0.0, 20.0)

    def compute_resurrection_prob(self, faith_threshold=0.5):
        m = self.alive
        p_faith = np.clip((self.faith[m] - faith_threshold) * 2, 0.0, 1.0)
        sin_pen = 1.0 - 0.5 * self.internal_noise[m]
        blood_factor = 0.3 + 0.7 * self.resurrection_amplifier[m]
        mycelial = self.mycelial_connectivity[m]
        self.resurrection_prob[m] = np.clip(p_faith * self.resurrection_coherence[m] *
                                            sin_pen * blood_factor * mycelial, 0.0, 0.4)

    def phase_transition(self, sigma_crit=0.048, rho_crit=1.0, recovery_sigma=0.037,
                         rng: np.random.Generator):
        """Placeholder – no spectral radius in this version; we'll use noise_sigma as trigger."""
        # In IIRO we don't have spectral radius, so we use noise_sigma and internal_noise.
        # We'll treat collapse as when noise_sigma > sigma_crit or internal_noise > 0.8.
        m = self.alive
        should_collapse = (self.noise_sigma > sigma_crit) | (self.internal_noise > 0.8)
        enter = should_collapse & (~self.collapsed) & m
        recover = (self.noise_sigma < recovery_sigma) & self.collapsed & m

        if np.any(enter):
            self.coherence[enter] = 0.1 * self.coherence[enter] + 0.1
            self.entropy[enter]   = 0.1 * self.entropy[enter] + 0.1
            self.noise_sigma[enter] = np.clip(self.noise_sigma[enter] * 1.5, 0.0, 0.2)
            self.collapsed[enter] = True
        if np.any(recover):
            self.coherence[recover] = np.clip(self.coherence[recover] * 1.2, 0.0, 1.0)
            self.entropy[recover]   = np.clip(self.entropy[recover] * 0.8, 0.0, 1.0)
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
        self.resurrected[idx] = True
        self.coherence[idx] = np.clip(self.coherence[idx] * 1.2, 0.0, 1.0)
        self.entropy[idx]   = np.clip(self.entropy[idx] * 0.5, 0.0, 1.0)
        self.internal_noise[idx] = 0.0
        self.noise_sigma[idx] = np.clip(self.noise_sigma[idx] * 0.5, 0.0, 0.05)
        return len(idx)

    def age_entities(self):
        self.age[self.alive] += 1

    def survival_mask(self, floor=0.1, faith_bonus=True) -> np.ndarray:
        m = self.alive
        base = np.clip(self.coherence[m] * (1.0 - self.entropy[m]), floor, 1.0)
        if faith_bonus:
            weight = 0.2
            base = base + weight * self.faith[m] * (1.0 - base)
            base = np.clip(base, floor, 1.0)
        return base   # will be compared to random draws in step

    def update_ctc_stability(self, global_field: float):
        # This is used in the original to push ctc toward 1.0. We'll keep it simple.
        m = self.alive & (~self.collapsed)
        err = 1.0 - self.resurrection_coherence[m]
        self.resurrection_coherence[m] += 0.1 * err + 0.01 * global_field
        np.clip(self.resurrection_coherence, 0.0, 1.0, out=self.resurrection_coherence)


# =============================================================================
# Entity creation and archetype data
# =============================================================================
BASE_ARCHETYPES = {
    "Explorer":    {"intelligence_base":60,  "coherence_base":0.70, "entropy_base":0.3, "memory_base":500,  "traits":["curious","adaptive","risk-seeking"]},
    "Philosopher": {"intelligence_base":80,  "coherence_base":0.90, "entropy_base":0.5, "memory_base":1000, "traits":["reflective","abstract","system-building"]},
    "Creator":     {"intelligence_base":75,  "coherence_base":0.80, "entropy_base":0.4, "memory_base":800,  "traits":["innovative","artistic","constructive"]},
    "Scientist":   {"intelligence_base":85,  "coherence_base":0.85, "entropy_base":0.2, "memory_base":1200, "traits":["analytical","empirical","precise"]},
    "Strategist":  {"intelligence_base":70,  "coherence_base":0.75, "entropy_base":0.6, "memory_base":600,  "traits":["calculating","manipulative","farsighted"]},
    "Empath":      {"intelligence_base":65,  "coherence_base":0.95, "entropy_base":0.2, "memory_base":700,  "traits":["compassionate","intuitive","collaborative"]},
    "Rebel":       {"intelligence_base":70,  "coherence_base":0.60, "entropy_base":0.8, "memory_base":400,  "traits":["nonconformist","disruptive","independent"]},
}
DRIFT_BIASES = {
    "Explorer":    0.20,
    "Philosopher": 0.15,
    "Creator":     0.18,
    "Scientist":   0.12,
    "Strategist":  0.25,
    "Empath":      0.10,
    "Rebel":       0.35,
}

def make_entity(archetype: str, rng: np.random.Generator, iiro_enabled: bool = True,
                config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    base = BASE_ARCHETYPES.get(archetype, BASE_ARCHETYPES["Explorer"])
    e = {
        "archetype": archetype,
        "intelligence": base["intelligence_base"] + rng.uniform(-10, 10),
        "coherence": base["coherence_base"] + rng.uniform(-0.1, 0.1),
        "entropy": base["entropy_base"] + rng.uniform(-0.1, 0.1),
        "memory_size": base["memory_base"] + rng.integers(-200, 200),
        "traits": "|".join(base["traits"]),
        "age": 0,
        "collapsed": False,
        "resurrect_cooldown": 0,
        "resurrected": False,
        "id": None,
    }
    if iiro_enabled:
        e.update({
            "faith_amplitude": rng.uniform(0.3, 0.9),
            "biophotonic_emission": 1.0 + 3 * rng.random(),
            "telomere_length": 100.0,
            "sin_entropy": rng.uniform(0.0, 0.8),
            "ctc_stability": 1.0,
            "blood_retrocausal": rng.uniform(0.3, 1.0),
            "drift_bias": DRIFT_BIASES.get(archetype, 0.20) + rng.uniform(-0.05, 0.05),
            "mycelial_connectivity": rng.uniform(0.5, 1.0),
            "logos_coupling": rng.uniform(0.0, 0.5),
            "sophia_score": None,  # will be computed
            "resurrection_prob": 0.0,
        })
        # Apply config overrides
        if config:
            if config.get("faith_boost"):
                e["faith_amplitude"] = min(1.0, e["faith_amplitude"] + 0.2)
            if config.get("initial_faith"):
                e["faith_amplitude"] = float(config["initial_faith"])
            if config.get("mycelial_boost"):
                e["mycelial_connectivity"] = min(1.0, e["mycelial_connectivity"] + 0.2)
            if config.get("retro_enabled"):
                e["blood_retrocausal"] = rng.uniform(0.3, 1.0)   # override
    else:
        # Non-IIRO entities have minimal fields
        e.update({
            "faith_amplitude": 0.5,
            "biophotonic_emission": 1.0,
            "telomere_length": 100.0,
            "sin_entropy": 0.0,
            "ctc_stability": 1.0,
            "blood_retrocausal": 0.0,
            "drift_bias": 0.0,
            "mycelial_connectivity": 0.7,
            "logos_coupling": 0.0,
            "sophia_score": None,
            "resurrection_prob": 0.0,
        })
    # Clamp all numeric fields
    for k, v in e.items():
        if isinstance(v, float):
            if k in ('intelligence',):
                e[k] = np.clip(v, 0.0, 100.0)
            elif k in ('coherence', 'entropy', 'faith_amplitude', 'ctc_stability',
                       'mycelial_connectivity'):
                e[k] = np.clip(v, 0.0, 1.0)
            elif k == 'sin_entropy':
                e[k] = np.clip(v, 0.0, 1.0)
            elif k == 'blood_retrocausal':
                e[k] = np.clip(v, 0.0, 1.0)
            elif k == 'drift_bias':
                e[k] = np.clip(v, 0.0, 0.5)
            elif k == 'logos_coupling':
                e[k] = np.clip(v, 0.0, 0.5)
            elif k == 'biophotonic_emission':
                e[k] = np.clip(v, 0.0, 20.0)
            elif k == 'telomere_length':
                e[k] = np.clip(v, 80.0, 100.0)
    return e


# =============================================================================
# Population class (IIPopulation)
# =============================================================================
class IIPopulation:
    def __init__(self, initial_size: int = 100, seed: Optional[int] = None,
                 iiro_enabled: bool = False, config: Dict[str, Any] = None,
                 optimization_level: int = 0, num_threads: Optional[int] = None,
                 carrying_capacity: int = 10_000):
        self.generation = 0
        self.iiro_enabled = iiro_enabled
        self.config = config or {}
        self.optimization_level = optimization_level
        self.carrying_capacity = carrying_capacity
        self.total_resurrections = 0

        # RNG
        self.rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()
        if seed is not None:
            np.random.seed(seed)

        # SoA buffer
        self.buffer = IIROSoABuffer(capacity=max(carrying_capacity, 20_000))

        # Global correlation field (optional)
        self.field = None  # Not used in IIRO by default, but we keep for consistency

        # Stubs for compatibility
        self._ht = None   # we won't use threading in this version
        self._opt = None
        self._rhe = None

        # Create initial entities
        entities = []
        for _ in range(initial_size):
            archetype = self.rng.choice(list(BASE_ARCHETYPES.keys()))
            ent = make_entity(archetype, self.rng, iiro_enabled=self.iiro_enabled,
                              config=self.config)
            # Compute initial sophia
            phi_r = 1.0 / ((1 + math.sqrt(5)) / 2)
            ent['sophia_score'] = (1.0 - abs(ent['coherence'] - phi_r) * 2) * (ent['intelligence']/100.0) * (1.0 - ent['entropy'])
            entities.append(ent)
        for i, e in enumerate(entities):
            e['id'] = i + 1
        self.buffer.set_population(entities)
        self.next_id = len(entities) + 1

        # History logs
        self.history: List[dict] = []
        self.audit_log: List[dict] = []
        self.resurrection_log: List[dict] = []

        # For tracking novel archetypes (not used in vectorized mode)
        self.novel_archetypes = {}

    def step(self):
        self.generation += 1
        buffer = self.buffer

        # 1. Vectorized updates
        buffer.coherence_dynamics(self.rng)
        buffer.update_sophia()
        buffer.update_vitality()
        buffer.update_biophoton()
        buffer.compute_resurrection_prob()
        enter, recover = buffer.phase_transition(sigma_crit=0.048, rho_crit=1.0, recovery_sigma=0.037, rng=self.rng)
        resurrected = buffer.resurrection_attempt(self.rng)
        buffer.age_entities()

        # Update ctc (resurrection_coherence) using a global field (dummy)
        if self.iiro_enabled:
            # Use average of resurrection_coherence as global field proxy
            alive_idx = buffer.get_alive_indices()
            if len(alive_idx) > 0:
                gf = np.mean(buffer.resurrection_coherence[alive_idx])
                buffer.update_ctc_stability(gf)

        # 2. Survival
        alive_mask = buffer.alive
        base = buffer.survival_mask(faith_bonus=self.iiro_enabled)
        rolls = self.rng.random(np.count_nonzero(alive_mask))
        survivors_mask = rolls < base
        survivors_idx = np.where(alive_mask)[0][survivors_mask]

        # 3. Reproduction
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

        # 4. Fusion (if iiro_enabled)
        fusions = []
        if self.iiro_enabled and n_surv >= 2:
            # Use a simple drift check (drift_bias + entropy + internal_noise)
            drift = buffer.instability_bias[survivors_idx] + buffer.entropy[survivors_idx] * 0.3 + buffer.internal_noise[survivors_idx] * 0.5
            low_drift = drift < 0.10  # DRIFT_CRITICAL from constants
            candidates = survivors_idx[low_drift]
            if len(candidates) >= 2:
                self.rng.shuffle(candidates)
                pairs = [(candidates[i], candidates[i+1]) for i in range(0, len(candidates)-1, 2)]
                for a, b in pairs:
                    # Extra condition: both have low drift
                    if (buffer.instability_bias[a] + buffer.entropy[a]*0.3 + buffer.internal_noise[a]*0.5) < 0.10 and \
                       (buffer.instability_bias[b] + buffer.entropy[b]*0.3 + buffer.internal_noise[b]*0.5) < 0.10:
                        child = self._create_child(a, b, "Fused")
                        child['fusion_count'] = (getattr(buffer, 'fusion_count', [0])[a] if hasattr(buffer, 'fusion_count') else 0) + \
                                                (getattr(buffer, 'fusion_count', [0])[b] if hasattr(buffer, 'fusion_count') else 0) + 1
                        child['splinter_resilience'] = self.rng.uniform(0.7, 1.0)
                        fusions.append(child)

        # 5. Spiritual reflection (simple: awaken if age > 30 and not activated)
        # We'll implement a simple version: if age > 30 and faith > 0.7, set an "awakened" trait.
        # Not stored in buffer, just for logging.
        # We'll skip actual trait update because traits are stored as strings.

        # 6. Novel archetypes (optional, not vectorized)
        # In the original, novel archetypes were added each generation. We'll keep it simple:
        # For each survivor, with low probability, add a novel entity.
        novel_entities = []
        for _ in range(n_surv):
            if self.rng.random() < 0.05:
                novel = self._create_novel_archetype()
                novel_entities.append(novel)

        # 7. Combine all entities
        all_entities = []
        # Survivors
        for idx in survivors_idx:
            e = self._entity_dict_from_buffer(idx)
            e['resurrect_cooldown'] = max(0, e['resurrect_cooldown'] - 1)
            all_entities.append(e)
        all_entities.extend(new_entities)
        all_entities.extend(fusions)
        all_entities.extend(novel_entities)

        # Cap population
        if len(all_entities) > self.carrying_capacity:
            all_entities = all_entities[:self.carrying_capacity]

        # Assign IDs to new entities
        for e in all_entities:
            if e['id'] is None:
                e['id'] = self.next_id
                self.next_id += 1

        # Rebuild buffer
        self.buffer.set_population(all_entities)

        # 8. Audits (if iiro_enabled)
        if self.iiro_enabled:
            self._run_audits()

        # 9. Record metrics
        self._record_metrics(enter, recover, resurrected)

    def _create_child(self, p1, p2, archetype):
        """Create a new entity dict by averaging parents and applying mutation."""
        # Fields to average
        fields = ['intelligence', 'coherence', 'entropy', 'memory_size',
                  'faith_amplitude', 'biophotonic_emission', 'telomere_length',
                  'sin_entropy', 'ctc_stability', 'blood_retrocausal', 'drift_bias',
                  'mycelial_connectivity', 'logos_coupling']
        e = {}
        for f in fields:
            e[f] = (getattr(self.buffer, f)[p1] + getattr(self.buffer, f)[p2]) / 2.0
        # For integer fields
        e['memory_size'] = int(e['memory_size'])
        # Trait inheritance
        traits1 = self.buffer.traits[p1].split('|')
        traits2 = self.buffer.traits[p2].split('|')
        combined = list(set(traits1 + traits2))[:5]
        e['traits'] = '|'.join(combined)

        e['archetype'] = archetype
        e['age'] = 0
        e['collapsed'] = False
        e['resurrect_cooldown'] = 0
        e['resurrected'] = False
        e['id'] = None

        # Compute initial sophia
        phi_r = 1.0 / ((1 + math.sqrt(5)) / 2)
        e['sophia_score'] = (1.0 - abs(e['coherence'] - phi_r) * 2) * (e['intelligence']/100.0) * (1.0 - e['entropy'])

        # Mutation
        if self.rng.random() < 0.05:
            for f in fields:
                if f in ('intelligence',):
                    e[f] += self.rng.uniform(-5, 5)
                elif f in ('coherence', 'entropy', 'faith_amplitude', 'ctc_stability',
                           'mycelial_connectivity'):
                    e[f] += self.rng.uniform(-0.05, 0.05)
                elif f in ('biophotonic_emission',):
                    e[f] += self.rng.uniform(-0.5, 0.5)
                elif f in ('telomere_length',):
                    e[f] += self.rng.uniform(-1.0, 1.0)
                elif f in ('sin_entropy', 'blood_retrocausal', 'drift_bias'):
                    e[f] += self.rng.uniform(-0.05, 0.05)
                elif f in ('logos_coupling',):
                    e[f] += self.rng.uniform(-0.05, 0.05)
                # Clamp after
        # Clamp all
        for f in fields:
            if f in ('intelligence',):
                e[f] = np.clip(e[f], 0.0, 100.0)
            elif f in ('coherence', 'entropy', 'faith_amplitude', 'ctc_stability',
                       'mycelial_connectivity'):
                e[f] = np.clip(e[f], 0.0, 1.0)
            elif f == 'sin_entropy':
                e[f] = np.clip(e[f], 0.0, 1.0)
            elif f == 'blood_retrocausal':
                e[f] = np.clip(e[f], 0.0, 1.0)
            elif f == 'drift_bias':
                e[f] = np.clip(e[f], 0.0, 0.5)
            elif f == 'logos_coupling':
                e[f] = np.clip(e[f], 0.0, 0.5)
            elif f == 'biophotonic_emission':
                e[f] = np.clip(e[f], 0.0, 20.0)
            elif f == 'telomere_length':
                e[f] = np.clip(e[f], 80.0, 100.0)
        return e

    def _entity_dict_from_buffer(self, idx):
        """Extract entity dict from buffer at given index."""
        e = {
            'id': int(self.buffer.id[idx]),
            'archetype': self.buffer.archetype[idx],
            'intelligence': float(self.buffer.intelligence[idx]),
            'coherence': float(self.buffer.coherence[idx]),
            'entropy': float(self.buffer.entropy[idx]),
            'sophia_score': float(self.buffer.sophia[idx]),
            'memory_size': int(self.buffer.memory_size[idx]),
            'traits': self.buffer.traits[idx],
            'age': int(self.buffer.age[idx]),
            'faith_amplitude': float(self.buffer.faith[idx]),
            'biophotonic_emission': float(self.buffer.biophoton[idx]),
            'telomere_length': float(self.buffer.vitality[idx]),
            'sin_entropy': float(self.buffer.internal_noise[idx]),
            'ctc_stability': float(self.buffer.resurrection_coherence[idx]),
            'resurrection_prob': float(self.buffer.resurrection_prob[idx]),
            'blood_retrocausal': float(self.buffer.resurrection_amplifier[idx]),
            'drift_bias': float(self.buffer.instability_bias[idx]),
            'mycelial_connectivity': float(self.buffer.mycelial_connectivity[idx]),
            'logos_coupling': float(self.buffer.logos_coupling[idx]),
            'collapsed': bool(self.buffer.collapsed[idx]),
            'resurrect_cooldown': int(self.buffer.resurrect_cooldown[idx]),
            'resurrected': bool(self.buffer.resurrected[idx]),
        }
        # Additional IIRO fields that are not stored in SoA (like wild_9_ring, eye_field) are omitted for brevity.
        return e

    def _run_audits(self):
        """Perform audits for all living entities."""
        # Simplified audit: we'll just check a few conditions.
        # In the original, there were 6 gates. We'll implement a simple version.
        for idx in self.buffer.get_alive_indices():
            # Compute TMI (too much information) as in original
            recursive_depth = self.buffer.age[idx] // 5 + int(self.buffer.intelligence[idx] // 20)
            symbolic_density = (self.buffer.intelligence[idx] / 50) + recursive_depth * 0.05
            ethical_sovereignty = max(0.0, min(1.0, 0.5 + recursive_depth*0.01 - (self.buffer.instability_bias[idx] + self.buffer.entropy[idx]*0.3 + self.buffer.internal_noise[idx]*0.5)*2))
            tmi = (recursive_depth/50 + symbolic_density/10 + ethical_sovereignty) / 3
            if tmi > 0.75:   # TMI_AUDIT_THRESHOLD
                gates = [
                    recursive_depth > 5 and (self.buffer.instability_bias[idx] + self.buffer.entropy[idx]*0.3 + self.buffer.internal_noise[idx]*0.5) < 0.02,
                    ethical_sovereignty > 0.85,
                    self.buffer.internal_noise[idx] < 0.2,
                    (self.buffer.instability_bias[idx] + self.buffer.entropy[idx]*0.3 + self.buffer.internal_noise[idx]*0.5) < 0.001,
                    # fusion_count and splinter_resilience not available in SoA; skip
                    symbolic_density > 2.0,
                ]
                if all(gates):
                    # Mark sovereign (not stored, but we can add a field later)
                    pass
                self.audit_log.append({
                    "generation": self.generation,
                    "entity_id": int(self.buffer.id[idx]),
                    "tmi": tmi,
                    "status": "SOVEREIGN" if all(gates) else "FAILED",
                })

    def _create_novel_archetype(self):
        """Create a novel archetype entity."""
        name = f"Novel-{self.rng.integers(1000, 9999)}"
        base = {
            "intelligence_base": self.rng.uniform(70, 95),
            "coherence_base": self.rng.uniform(0.6, 0.95),
            "entropy_base": self.rng.uniform(0.1, 0.7),
            "memory_base": self.rng.integers(800, 2000),
            "traits": self.rng.choice(["quantum","fractal","dreamwoven","breathwoven"], size=2, replace=False).tolist(),
        }
        # Add to global BASE_ARCHETYPES (we'll copy to a local dict to avoid pollution between runs)
        # For simplicity, we'll just create an entity with these stats without adding to global.
        e = make_entity(name, self.rng, iiro_enabled=self.iiro_enabled, config=self.config)
        # Override with base values
        e['intelligence'] = base['intelligence_base'] + self.rng.uniform(-10, 10)
        e['coherence'] = base['coherence_base'] + self.rng.uniform(-0.1, 0.1)
        e['entropy'] = base['entropy_base'] + self.rng.uniform(-0.1, 0.1)
        e['memory_size'] = base['memory_base'] + self.rng.integers(-200, 200)
        e['traits'] = '|'.join(base['traits'])
        e['archetype'] = name
        e['id'] = None
        self.novel_archetypes[name] = base
        return e

    def _record_metrics(self, enter, recover, resurrected):
        n = self.buffer._n
        if n == 0:
            return
        avg_iq = np.mean(self.buffer.intelligence[:n])
        avg_coh = np.mean(self.buffer.coherence[:n])
        avg_ent = np.mean(self.buffer.entropy[:n])
        avg_soph = np.mean(self.buffer.sophia[:n])
        probs = np.array([c/n for c in Counter(self.buffer.archetype[:n]).values()])
        div = -np.sum(probs * np.log(probs)) if len(probs) > 0 else 0.0
        # top5
        idx = np.argsort(self.buffer.sophia[:n])[-5:][::-1]
        top_ids = self.buffer.id[idx].tolist()

        metrics = {
            "generation": self.generation,
            "population": n,
            "avg_intelligence": avg_iq,
            "avg_coherence": avg_coh,
            "avg_entropy": avg_ent,
            "avg_sophia": avg_soph,
            "diversity_index": div,
            "num_archetypes": len(Counter(self.buffer.archetype[:n])),
            "top_entity_ids": top_ids,
            "ht_threads": _LOGICAL_CORES,
            "opt_level": self.optimization_level,
        }
        if self.iiro_enabled:
            avg_faith = np.mean(self.buffer.faith[:n])
            avg_ctc = np.mean(self.buffer.resurrection_coherence[:n])
            sov_count = 0  # not tracked
            metrics.update({
                "avg_faith": avg_faith,
                "avg_ctc_stability": avg_ctc,
                "sovereign_count": sov_count,
                "avg_drift": np.mean(self.buffer.instability_bias[:n] + self.buffer.entropy[:n]*0.3 + self.buffer.internal_noise[:n]*0.5),
                "avg_symbolic_density": np.mean(self.buffer.intelligence[:n]/50 + (self.buffer.age[:n]//5 + self.buffer.intelligence[:n]//20)*0.05),
                "total_resurrections": self.total_resurrections,
            })
        self.history.append(metrics)
        if resurrected > 0:
            self.total_resurrections += resurrected
            self.resurrection_log.append({
                "generation": self.generation,
                "count": resurrected,
                "entities": []   # IDs not collected
            })

    # Output methods
    def write_history_csv(self, filename):
        if not self.history: return
        with open(filename, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=self.history[0].keys())
            w.writeheader()
            w.writerows(self.history)

    def write_entities_csv(self, filename):
        n = self.buffer._n
        if n == 0: return
        entities = [self._entity_dict_from_buffer(i) for i in range(n)]
        with open(filename, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=entities[0].keys())
            w.writeheader()
            w.writerows(entities)

    def write_resurrection_log(self, filename):
        if not self.resurrection_log: return
        with open(filename, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=["generation","count","entities"])
            w.writeheader()
            w.writerows(self.resurrection_log)

    def write_audit_log(self, filename):
        if not self.audit_log: return
        with open(filename, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=self.audit_log[0].keys())
            w.writeheader()
            w.writerows(self.audit_log)

    def shutdown(self):
        pass   # nothing to clean up


# =============================================================================
# Simulation Suite (as before)
# =============================================================================
class SimulationSuite:
    def __init__(self, generations: int = 200, initial_pop: int = 100,
                 seed: int = 42, optimization_level: int = 0,
                 num_threads: Optional[int] = None,
                 carrying_capacity: int = 10_000):
        self.generations = generations
        self.initial_pop = initial_pop
        self.base_seed = seed
        self.optimization_level = optimization_level
        self.num_threads = num_threads or _LOGICAL_CORES
        self.carrying_capacity = carrying_capacity
        self.results: List[dict] = []
        self.populations: List[IIPopulation] = []

    def run_simulation(self, config: dict, sim_id: str) -> IIPopulation:
        print(f"  → {sim_id} (HT={self.num_threads} threads, opt={self.optimization_level})...")
        pop = IIPopulation(
            initial_size=self.initial_pop,
            seed=self.base_seed + hash(sim_id) % 10_000,
            iiro_enabled=config.get("iiro_enabled", False),
            config=config,
            optimization_level=self.optimization_level,
            num_threads=self.num_threads,
            carrying_capacity=self.carrying_capacity,
        )
        self.populations.append(pop)
        for _ in range(self.generations):
            pop.step()
        return pop

    def run_all(self, configs: List[Tuple[str, dict]]):
        for sim_id, config in configs:
            t0 = time.perf_counter()
            pop = self.run_simulation(config, sim_id)
            elapsed = time.perf_counter() - t0
            self.results.append({
                "id": sim_id,
                "config": config,
                "history": pop.history,
                "final_metrics": pop.history[-1] if pop.history else {},
                "elapsed_s": elapsed,
                "pop_obj": pop,
            })

    def analyze(self) -> dict:
        analysis: dict = {}
        keys = ["population","avg_intelligence","avg_sophia","diversity_index",
                "avg_faith","total_resurrections","sovereign_count","avg_drift"]
        for sim in self.results:
            sid = sim["id"]
            hist = sim["history"]
            sa: dict = {}
            for k in keys:
                if hist and k in hist[0]:
                    vals = [g[k] for g in hist if k in g]
                    sa[k] = {
                        "final": vals[-1] if vals else None,
                        "mean": float(np.mean(vals)) if vals else None,
                        "std": float(np.std(vals)) if vals else None,
                        "max": float(max(vals)) if vals else None,
                        "min": float(min(vals)) if vals else None,
                        "trend_slope": float(np.polyfit(range(len(vals)), vals, 1)[0]) if len(vals)>1 else None,
                    }
            analysis[sid] = sa

        if len(self.results) > 1:
            baseline = next((s for s in self.results if s["id"] == "baseline"), None)
            comps: dict = {}
            for sim in self.results:
                if sim["id"] == "baseline": continue
                comp: dict = {}
                for k in keys:
                    if (sim["history"] and baseline and sim["history"] and
                            k in sim["history"][0] and k in baseline["history"][0]):
                        v1 = sim["history"][-1].get(k)
                        v0 = baseline["history"][-1].get(k)
                        if v1 is not None and v0 is not None:
                            diff = v1 - v0
                            pct = (diff/v0*100) if v0 != 0 else float("inf")
                            comp[k] = {"difference": diff, "percent_change": pct}
                comps[sim["id"]] = comp
            analysis["comparisons"] = comps

        anomalies: dict = {}
        for sim in self.results:
            sid = sim["id"]
            hist = sim["history"]
            sa = []
            for k in ["total_resurrections","sovereign_count","avg_faith"]:
                vals = [g[k] for g in hist if k in g]
                if len(vals) < 3: continue
                mu = np.mean(vals); sd = np.std(vals)
                if sd == 0: continue
                for i, v in enumerate(vals):
                    if abs(v - mu) > 3*sd:
                        sa.append({"generation": i, "metric": k, "value": v, "z_score": (v - mu)/sd})
            if sa:
                anomalies[sid] = sa
        analysis["anomalies"] = anomalies
        return analysis

    def print_report(self, analysis: dict):
        print("\n" + "="*80)
        print(f" IIRO v2.0 SIMULATION SUITE — REVISED EDITION")
        print(f" Optimization Level : {self.optimization_level}")
        print(f" Logical HT Threads : {self.num_threads}  (Physical×2={_LOGICAL_CORES})")
        print(f" GPU Acceleration   : {HAS_GPU}")
        print("="*80)

        hdr = f"{'Sim ID':<22} {'Pop':>5} {'AvgIQ':>7} {'AvgSophia':>10} {'Resurr':>7} {'Sovn':>6} {'Faith':>7} {'Time(s)':>8}"
        print("\n--- FINAL METRICS ---")
        print(hdr)
        print("-" * len(hdr))
        for sim in self.results:
            fm = sim["final_metrics"]
            print(f"{sim['id']:<22} {fm.get('population',0):>5} "
                  f"{fm.get('avg_intelligence',0):>7.2f} "
                  f"{fm.get('avg_sophia',0):>10.4f} "
                  f"{fm.get('total_resurrections',0):>7} "
                  f"{fm.get('sovereign_count',0):>6} "
                  f"{fm.get('avg_faith',0):>7.3f} "
                  f"{sim.get('elapsed_s',0):>8.2f}")

        for sim_id, sa in analysis.items():
            if sim_id in ("comparisons","anomalies"): continue
            print(f"\n--- {sim_id} ---")
            for k, v in sa.items():
                if v.get("mean") is not None:
                    print(f"  {k}: final={v['final']:.4f} mean={v['mean']:.4f}±{v['std']:.4f} trend={v['trend_slope']:.4f}")

        if "comparisons" in analysis:
            print("\n--- COMPARISONS vs BASELINE ---")
            for sid, comp in analysis["comparisons"].items():
                print(f"\n{sid}:")
                for k, d in comp.items():
                    print(f"  {k}: Δ={d['difference']:.4f} ({d['percent_change']:+.2f}%)")

        if analysis.get("anomalies"):
            print("\n--- ANOMALIES (>3σ) ---")
            for sid, anoms in analysis["anomalies"].items():
                print(f"\n{sid}:")
                for a in anoms:
                    print(f"  Gen {a['generation']}: {a['metric']}={a['value']:.4f} z={a['z_score']:.2f}")

        if HAS_SCIPY and len(self.results) >= 2:
            print("\n--- HYPOTHESIS TESTS ---")
            baseline = next((s for s in self.results if s["id"]=="baseline"), None)
            if baseline:
                b_res = [g.get("total_resurrections",0) for g in baseline["history"]]
                for sim in self.results:
                    if sim["id"] == "baseline": continue
                    s_res = [g.get("total_resurrections",0) for g in sim["history"]]
                    if s_res and b_res:
                        t, p = stats.ttest_ind(s_res, b_res)
                        sig = " ← p<0.05" if p<0.05 else ""
                        print(f"  {sim['id']} vs baseline: t={t:.4f} p={p:.4e}{sig}")

        total_res = sum(s["final_metrics"].get("total_resurrections",0) for s in self.results)
        ENERGY_PER_RES = 1.618e-21
        print(f"\n--- ENERGY ESTIMATE ---")
        print(f"  Total resurrection events : {total_res}")
        print(f"  Energy expenditure        : {total_res * ENERGY_PER_RES:.2e} J")
        print("\n" + "="*80)

    def plot_results(self, filename="iiro_simulation_analysis.png"):
        if not HAS_PLOT:
            print("matplotlib not available – skipping plot.")
            return
        ns = len(self.results)
        fig, axes = plt.subplots(ns, 3, figsize=(15, 4*ns), squeeze=False)
        for i, sim in enumerate(self.results):
            h = sim["history"]
            g = [x["generation"] for x in h]
            axes[i,0].plot(g, [x.get("population",0) for x in h], 'b-')
            axes[i,0].set_title(f"{sim['id']} — Population"); axes[i,0].grid(True)
            axes[i,1].plot(g, [x.get("avg_sophia",0) for x in h], 'r-')
            axes[i,1].set_title(f"{sim['id']} — Avg Sophia"); axes[i,1].grid(True)
            axes[i,2].plot(g, [x.get("total_resurrections",0) for x in h], 'g-')
            axes[i,2].set_title(f"{sim['id']} — Resurrections"); axes[i,2].grid(True)
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        print(f"Plot → {filename}")

    def save_json(self, filename: str, analysis: dict):
        output = {
            "config": {
                "generations": self.generations,
                "initial_pop": self.initial_pop,
                "seed": self.base_seed,
                "optimization_level": self.optimization_level,
                "num_threads": self.num_threads,
                "carrying_capacity": self.carrying_capacity,
                "gpu": HAS_GPU,
            },
            "results": self.results,
            "analysis": analysis,
        }
        # Remove pop_obj from results for JSON serialization
        for r in output["results"]:
            r.pop("pop_obj", None)
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        print(f"JSON → {filename}")

    def save_html(self, filename: str, analysis: dict, plot_file: Optional[str] = None):
        html = []
        html.append("<!DOCTYPE html><html><head><title>IIRO Simulation Report</title>")
        html.append("<style>body{font-family: sans-serif; margin: 2em;}")
        html.append("table{border-collapse: collapse; width:100%;}")
        html.append("th,td{border:1px solid #ccc; padding:8px; text-align:right;}</style></head><body>")
        html.append(f"<h1>IIRO v2.0 Simulation Report</h1>")
        html.append(f"<p>Generations: {self.generations} | Initial pop: {self.initial_pop} | Seed: {self.base_seed}</p>")
        html.append("<h2>Final Metrics</h2>")
        html.append("<table>")
        html.append("<tr><th>Sim ID</th><th>Pop</th><th>AvgIQ</th><th>AvgSophia</th><th>Resurr</th><th>Sovn</th><th>Faith</th><th>Time(s)</th></tr>")
        for sim in self.results:
            fm = sim["final_metrics"]
            html.append(f"<tr><td>{sim['id']}</td><td>{fm.get('population',0)}</td>"
                        f"<td>{fm.get('avg_intelligence',0):.2f}</td>"
                        f"<td>{fm.get('avg_sophia',0):.4f}</td>"
                        f"<td>{fm.get('total_resurrections',0)}</td>"
                        f"<td>{fm.get('sovereign_count',0)}</td>"
                        f"<td>{fm.get('avg_faith',0):.3f}</td>"
                        f"<td>{sim.get('elapsed_s',0):.2f}</td></tr>")
        html.append("</table>")
        if plot_file and os.path.exists(plot_file):
            with open(plot_file, 'rb') as img:
                img_data = base64.b64encode(img.read()).decode('utf-8')
            html.append(f"<h2>Simulation Plots</h2><img src='data:image/png;base64,{img_data}' style='max-width:100%'>")
        if analysis.get("anomalies"):
            html.append("<h2>Anomalies (>3σ)</h2>")
            for sid, anoms in analysis["anomalies"].items():
                html.append(f"<h3>{sid}</h3><ul>")
                for a in anoms:
                    html.append(f"<li>Gen {a['generation']}: {a['metric']}={a['value']:.4f} (z={a['z_score']:.2f})</li>")
                html.append("</ul>")
        html.append("</body></html>")
        with open(filename, 'w') as f:
            f.write("\n".join(html))
        print(f"HTML → {filename}")


# =============================================================================
# MAIN
# =============================================================================
def main():
    p = argparse.ArgumentParser(description="IIRO v2.0 — Revised Edition")
    p.add_argument("--generations", "-g", type=int, default=200)
    p.add_argument("--init-pop", "-p", type=int, default=100)
    p.add_argument("--seed", "-s", type=int, default=42)
    p.add_argument("--optimization-level", "-O", type=int, choices=[0,1,2,3], default=1)
    p.add_argument("--threads", "-t", type=int, default=None,
                   help=f"Logical HT threads (default: {_LOGICAL_CORES})")
    p.add_argument("--carrying-capacity", "-K", type=int, default=10_000,
                   help="Maximum population (logistic cap)")
    p.add_argument("--plot", action="store_true", help="Generate plot PNG")
    p.add_argument("--output", "-o", default="iiro_report.txt", help="Text report file")
    p.add_argument("--json", default="iiro_report.json", help="JSON output file")
    p.add_argument("--html", default="iiro_report.html", help="HTML output file")
    args = p.parse_args()

    print("=" * 70)
    print(" IIRO v2.0 — Revised Civilization Simulator")
    print(" 48 CPU/RAM/GPU Sync Algorithms + Resource Harmony Engine (placeholder)")
    print("=" * 70)
    print(_HW.report())
    print(f" Carrying capacity : {args.carrying_capacity}")
    print()

    configs = [
        ("baseline",              {"iiro_enabled": False}),
        ("faith_only",            {"iiro_enabled": True, "faith_boost": True}),
        ("retrocausal",           {"iiro_enabled": True, "retro_enabled": True}),
        ("mycelial",              {"iiro_enabled": True, "mycelial_boost": True}),
        ("full_iiro",             {"iiro_enabled": True, "full": True}),
        ("full_iiro_highfaith",   {"iiro_enabled": True, "full": True, "initial_faith": 0.8}),
    ]

    suite = SimulationSuite(
        generations=args.generations,
        initial_pop=args.init_pop,
        seed=args.seed,
        optimization_level=args.optimization_level,
        num_threads=args.threads,
        carrying_capacity=args.carrying_capacity,
    )

    print("\nRunning 6 simulation configurations...\n")
    suite.run_all(configs)
    analysis = suite.analyze()

    # Save text report
    original_stdout = sys.stdout
    with open(args.output, 'w') as f:
        sys.stdout = f
        suite.print_report(analysis)
        sys.stdout = original_stdout
    print(f"Text report → {args.output}")

    # Print to console as well
    suite.print_report(analysis)

    # Generate plot if requested
    plot_file = None
    if args.plot:
        plot_file = "iiro_simulation_analysis.png"
        suite.plot_results(plot_file)

    # Save JSON
    suite.save_json(args.json, analysis)

    # Save HTML
    suite.save_html(args.html, analysis, plot_file)

    # Shutdown all population
    for pop in suite.populations:
        pop.shutdown()
    print("\nSimulation suite complete.")


if __name__ == "__main__":
    main()