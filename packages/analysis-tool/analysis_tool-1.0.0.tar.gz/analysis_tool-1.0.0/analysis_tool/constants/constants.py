'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-12-06 09:14:57 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2024-12-06 09:32:41 +0100
FilePath     : constants.py
Description  : 

Copyright (c) 2024 by everyone, All Rights Reserved. 
'''

from particle import Particle

constant_table = {
    # Fundamental constants
    # ---------------------
    'CONSTANTS': {
        # Speed of light in m/ns (commonly used in time-of-flight calculations)
        'C_LIGHT': 0.299792458
    },
    # 1) LEPTONS
    # PDG IDs: e⁻(11), μ⁻(13), τ⁻(15), ν_e(12), ν_μ(14), ν_τ(16)
    # Note: Neutrino masses are extremely small and not well determined by PDG;
    # Particle package will likely return None or 0 for neutrinos.
    'LEPTONS': {
        'E_MASS': Particle.from_pdgid(11).mass,  # electron
        'MU_MASS': Particle.from_pdgid(13).mass,  # muon
        'TAU_MASS': Particle.from_pdgid(15).mass,  # tau
        'NU_E_MASS': Particle.from_pdgid(12).mass,  # electron neutrino (likely 0 or None)
        'NU_MU_MASS': Particle.from_pdgid(14).mass,  # muon neutrino
        'NU_TAU_MASS': Particle.from_pdgid(16).mass,  # tau neutrino
    },
    # 2) GAUGE AND HIGGS BOSONS
    # PDG IDs: photon(22), W⁺(24), Z⁰(23), gluon(21), Higgs(25)
    # Photon and gluon are massless; you'll likely get None or 0.
    'GAUGE_HIGGS_BOSONS': {
        'PHOTON_MASS': Particle.from_pdgid(22).mass,  # photon
        'W_MASS': Particle.from_pdgid(24).mass,  # W+
        'Z_MASS': Particle.from_pdgid(23).mass,  # Z0
        'GLUON_MASS': Particle.from_pdgid(21).mass,  # gluon
        'HIGGS_MASS': Particle.from_pdgid(25).mass,  # Higgs boson
    },
    # 3) LIGHT I=1 MESONS (examples: pions, rhos)
    # PDG IDs: π⁺(211), π⁰(111), ρ⁰(113), ρ⁺(213)
    # You can add more as desired.
    'LIGHT_I=1_MESONS': {
        'PI_PLUS_MASS': Particle.from_pdgid(211).mass,  # pi+
        'PI_ZERO_MASS': Particle.from_pdgid(111).mass,  # pi0
        'RHO_ZERO_MASS': Particle.from_pdgid(113).mass,  # rho0
    },
    # 4) LIGHT I=0 MESONS (examples: eta, eta')
    # PDG IDs: η(221), η'(958)(331)
    'LIGHT_I=0_MESONS': {
        'ETA_MASS': Particle.from_pdgid(221).mass,  # eta
        'ETA_PRIME_MASS': Particle.from_pdgid(331).mass,  # eta'
    },
    # 5) STRANGE MESONS (examples: kaons)
    # PDG IDs: K⁺(321), K⁰(311)
    'STRANGE_MESONS': {
        'K_PLUS_MASS': Particle.from_pdgid(321).mass,  # K+
        'K_ZERO_MASS': Particle.from_pdgid(311).mass,  # K0
    },
    # 6) CHARMED MESONS (examples: D, D_s)
    # PDG IDs: D⁰(421), D⁺(411), D_s⁺(431)
    'CHARMED_MESONS': {
        'D_PLUS_MASS': Particle.from_pdgid(411).mass,  # D+
        'D_ZERO_MASS': Particle.from_pdgid(421).mass,  # D0
        'D_S_PLUS_MASS': Particle.from_pdgid(431).mass,  # D_s+
    },
    # 7) BOTTOM MESONS (B mesons)
    # PDG IDs: B⁰(511), B⁺(521), B_s⁰(531), B_c⁺(541)
    'BOTTOM_MESONS': {
        'B_ZERO_MASS': Particle.from_pdgid(511).mass,  # B0
        'B_PLUS_MASS': Particle.from_pdgid(521).mass,  # B+
        'B_S_ZERO_MASS': Particle.from_pdgid(531).mass,  # B_s0
        'B_C_PLUS_MASS': Particle.from_pdgid(541).mass,  # B_c+
    },
    # 8) cc-bar MESONS (charmonium)
    # PDG IDs: J/ψ(443), ψ(2S)(100443)
    'CCBAR_MESONS': {
        'JPSI_MASS': Particle.from_pdgid(443).mass,  # J/psi
        'PSI_2S_MASS': Particle.from_pdgid(100443).mass,  # psi(2S)
    },
    # 9) bb-bar MESONS (bottomonium)
    # PDG IDs: ϒ(1S)(553), ϒ(2S)(100553)
    'BBBAR_MESONS': {
        'UPSILON_1S_MASS': Particle.from_pdgid(553).mass,  # Upsilon(1S)
        'UPSILON_2S_MASS': Particle.from_pdgid(100553).mass,  # Upsilon(2S)
    },
    # 10) LIGHT BARYONS (examples: nucleons)
    # PDG IDs: p(2212), n(2112)
    'LIGHT_BARYONS': {
        'P_MASS': Particle.from_pdgid(2212).mass,  # proton
        'N_MASS': Particle.from_pdgid(2112).mass,  # neutron
    },
    # 11) STRANGE BARYONS (examples: Lambda, Sigma, Xi)
    # PDG IDs: Λ(1115)(3122), Σ⁺(3222), Ξ⁻(1312)(3312)
    'STRANGE_BARYONS': {
        'LAMBDA_MASS': Particle.from_pdgid(3122).mass,  # Lambda
        'SIGMA_PLUS_MASS': Particle.from_pdgid(3222).mass,  # Sigma+
        'XI_MINUS_MASS': Particle.from_pdgid(3312).mass,  # Xi-
    },
    # 12) CHARMED BARYONS (examples: Λ_c⁺, Σ_c)
    # PDG IDs: Λ_c⁺(4122), Σ_c⁺⁺(4222), Ξ_c⁰(4132)
    'CHARMED_BARYONS': {
        'LAMBDA_C_PLUS_MASS': Particle.from_pdgid(4122).mass,  # Lambda_c+
        'SIGMA_C_PLUS_PLUS_MASS': Particle.from_pdgid(4222).mass,  # Sigma_c++
        'XI_C_ZERO_MASS': Particle.from_pdgid(4132).mass,  # Xi_c0
    },
    # 13) BOTTOM BARYONS (examples: Λ_b⁰, Ξ_b⁻)
    # PDG IDs: Λ_b⁰(5122), Ξ_b⁻(5232)
    'BOTTOM_BARYONS': {
        'LAMBDA_B_ZERO_MASS': Particle.from_pdgid(5122).mass,  # Lambda_b0
        'XI_B_MINUS_MASS': Particle.from_pdgid(5232).mass,  # Xi_b-
    },
}


# Flatten the dictionary for easy access to constants

constant_table_flattened = {
    **constant_table['CONSTANTS'],
    **constant_table['LEPTONS'],
    **constant_table['GAUGE_HIGGS_BOSONS'],
    **constant_table['LIGHT_I=1_MESONS'],
    **constant_table['LIGHT_I=0_MESONS'],
    **constant_table['STRANGE_MESONS'],
    **constant_table['CHARMED_MESONS'],
    **constant_table['BOTTOM_MESONS'],
    **constant_table['CCBAR_MESONS'],
    **constant_table['BBBAR_MESONS'],
    **constant_table['LIGHT_BARYONS'],
    **constant_table['STRANGE_BARYONS'],
    **constant_table['CHARMED_BARYONS'],
    **constant_table['BOTTOM_BARYONS'],
}


# You can add or remove particles as needed for your analysis. Refer to the PDG for
# the most up-to-date particle IDs and masses: https://pdg.lbl.gov/


if __name__ == '__main__':
    from rich.pretty import pprint as rpprint

    print("\nConstants for particle physics analysis:")
    rpprint(constant_table, expand_all=True)

    print("\nFlattened dictionary for easy access:")
    rpprint(constant_table_flattened, expand_all=True)
