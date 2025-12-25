'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-05-15 09:38:27 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-06 14:11:04 +0100
FilePath     : track_combination_mass_calculator.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

import os, sys, argparse
from typing import List, Optional, Tuple, Set, Dict

import itertools
import multiprocessing

from pathlib import Path

import ROOT as r
from ROOT import RDataFrame
from particle import Particle
from particle.exceptions import MatchingIDNotFound

from rich import print as rprint

# Use rich backend for logging
import logging
from rich.logging import RichHandler

# Configure rich logging globally
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%x %X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)  # or "DEBUG"/"WARNING" as needed
logger = logging.getLogger(__name__)


def get_all_evtgen_names():
    """
    Retrieves and returns a list of all available EvtGen names.
    """
    # Particle.findall() with no arguments returns a list of all particles
    # known to the package's database.
    all_particles = Particle.findall()

    evtgen_names = set()
    # We iterate through all particles and try to access the evtgen_name.
    # If a particle does not have an EvtGen name, a MatchingIDNotFound
    # exception is raised, which we catch and simply ignore.
    for p in all_particles:
        try:
            evtgen_names.add(p.evtgen_name)
        except MatchingIDNotFound:
            continue  # Skip particles without an EvtGen name

    # Return a sorted list for consistent output
    return sorted(list(evtgen_names))


# Constants
AVAILABLE_PARTICLE_NAMES = get_all_evtgen_names()


def sanitize_name(name: str) -> str:
    """
    Convert particle names to valid column names by replacing special characters.

    Args:
        name: Particle name that may contain special characters (e.g., 'K+', 'pi-')

    Returns:
        Sanitized name suitable for column names (e.g., 'Kp', 'pim')
    """
    # Replace '+' with 'p' and '-' with 'm' to create valid column names
    return name.replace('+', 'p').replace('-', 'm')


def create_lorentz_vectors(
    rdf: r.RDF.RNode,
    track_names: List[str],
    kinematics: List[str],
    particles: List[str],
) -> Tuple[r.RDF.RNode, List[str]]:
    """
    Create Lorentz vectors for each track under different particle hypotheses.

    Args:
        rdf: RDataFrame object from CERN ROOT
        track_names: List of track names in the RDataFrame (e.g., ['Kminus', 'piplus'])
        kinematics: List of kinematic variables ['PX', 'PY', 'PZ']
        particles: List of particle hypotheses (e.g., ['pi+', 'K+'])

    Returns:
        Tuple of:
            - Modified RDataFrame with Lorentz vector columns added
            - List of Lorentz vector column names
    """

    # Check if the track-kinematics columns exist
    for track in track_names:
        for kin in kinematics:
            if f"{track}_{kin}" not in rdf.GetColumnNames():
                raise ValueError(f"Track {track} does not have the kinematic variable {kin}")

    # Define Lorentz vectors for each track under different particle hypotheses
    vector_name_list = []
    for track in track_names:
        for particle in particles:

            # Validate the particle name by checking if it is in the particle package
            if particle not in AVAILABLE_PARTICLE_NAMES:
                logger.error(f"Invalid particle: [bold red]'{particle}'[/]. All available particles are: {AVAILABLE_PARTICLE_NAMES}", extra={"markup": True})
                raise ValueError(f"Invalid particle: {particle}")

            # Get particle mass from the particle package
            mass = Particle.from_evtgen_name(particle).mass

            # Define a new column with a Lorentz vector using PxPyPzM constructor
            # Format: track_PxPyPzMVector_MassHypo_particle
            vector_name = f"{track}_PxPyPzMVector_MassHypo_{sanitize_name(particle)}"

            # Use ROOT::Math::PxPyPzMVector constructor with the track's momentum components
            # and the mass from the particle hypothesis
            rdf = rdf.Define(vector_name, f"ROOT::Math::PxPyPzMVector({track}_{kinematics[0]}, {track}_{kinematics[1]}, {track}_{kinematics[2]}, {mass})")

            vector_name_list.append(vector_name)

    return rdf, vector_name_list


def calculate_invariant_masses(
    rdf: r.RDF.RNode,
    track_names: List[str],
    particles: List[str],
    max_combinations: Optional[int] = None,
) -> Tuple[r.RDF.RNode, List[str]]:
    """
    Calculate invariant masses for all valid track combinations with particle hypotheses.

    Args:
        rdf: RDataFrame with Lorentz vector columns already defined
        track_names: List of track names (e.g., ['Kminus', 'piplus'])
        particles: List of particle hypotheses (e.g., ['pi+', 'K+'])
        max_combinations: Maximum number of tracks to combine. Example: -1 means all possible combinations between the given tracks, 2 means all possible combinations between 2 tracks, etc. Default is -1.

    Returns:
        Tuple of:
            - Modified RDataFrame with invariant mass columns added
            - List of invariant mass column names
    """

    if (max_combinations is None) or (max_combinations == -1):
        max_combinations = len(track_names)
    elif (max_combinations < 2) or (max_combinations > len(track_names)):
        logger.warning(
            f"The input max_combinations is not valid, it should be between [bold yellow]2[/] and [bold yellow]{len(track_names)}[/], set to [bold yellow]{len(track_names)}[/]", extra={"markup": True}
        )

        max_combinations = len(track_names)

    mass_column_list = []

    # Iterate over all possible combination lengths, from 2 tracks up to max_combinations
    for k in range(2, max_combinations + 1):
        # Generate all combinations of k tracks without repetition
        # e.g., [('Kminus', 'piplus'), ('Kminus', 'proton'), ...]
        track_combinations = list(itertools.combinations(track_names, k))

        for track_combo in track_combinations:
            # Generate all possible particle hypothesis assignments for these tracks
            # Each track can be assigned any particle hypothesis
            # e.g., [('pi+', 'K+'), ('pi+', 'mu+'), ('K+', 'pi+'), ...]
            hypo_assignments = list(itertools.product(particles, repeat=k))

            for hypo_combo in hypo_assignments:
                # Create column name: m_track1_track2_MassHypo_hypo1_hypo2
                # e.g., m_Kminus_piplus_MassHypo_pip_Kp
                tracks_part = "_".join(track_combo)
                hypos_part = "_".join([sanitize_name(h) for h in hypo_combo])
                mass_column = f"m_{tracks_part}_MassHypo_{hypos_part}"

                # Create expression to sum Lorentz vectors
                # e.g., "Kminus_PxPyPzMVector_MassHypo_pi+ + piplus_PxPyPzMVector_MassHypo_K+"
                vector_sum = " + ".join([f"{track}_PxPyPzMVector_MassHypo_{sanitize_name(hypo)}" for track, hypo in zip(track_combo, hypo_combo)])

                # Define new column with invariant mass calculation using the .M() method
                rdf = rdf.Define(mass_column, f"({vector_sum}).M()")

                # Add the mass column to the list
                mass_column_list.append(mass_column)

    return rdf, mass_column_list


def compute_invariant_masses(
    rdf: r.RDF.RNode,
    track_names: List[str],
    kinematics: List[str],
    particles: Optional[List[str]] = None,
    max_combinations: Optional[int] = None,
) -> Tuple[r.RDF.RNode, List[str], List[str]]:
    """
    Compute invariant masses for track combinations under different particle hypotheses.

    Args:
        rdf: RDataFrame object from CERN ROOT
        track_names: List of track names in the RDataFrame (e.g., ['Kminus', 'piplus'])
        kinematics: List of kinematic variables ['PX', 'PY', 'PZ']
        particles: Optional list of particle hypotheses (e.g., ['pi+', 'K+', 'mu+']). If not provided, particles ['pi+', 'K+'] will be used.
        max_combinations: Maximum number of tracks to combine (defaults to all tracks)

    Returns:
        Tuple of:
            - Modified RDataFrame with added columns for Lorentz vectors and invariant masses
            - List of Lorentz vector column names
            - List of invariant mass column names
    """

    # Check if the particle list is valid
    if particles is None:
        logger.info("The input particles is not provided, use default particles ['pi+', 'K+'] as particle hypotheses")
        particles = ["pi+", "K+"]
    else:
        logger.info(f"The input particles is provided, use {particles} as particle hypotheses")

    for particle in particles:
        if not Particle.from_evtgen_name(particle):
            raise ValueError(f"Invalid particle: {particle}")

    # Step 1: Create Lorentz vectors for all track and particle hypothesis combinations
    rdf, vector_name_list = create_lorentz_vectors(rdf, track_names, kinematics, particles)

    # Step 2: Calculate invariant masses for all valid combinations
    rdf, mass_column_list = calculate_invariant_masses(rdf, track_names, particles, max_combinations)

    return rdf, vector_name_list, mass_column_list


def track_combination_mass_calculator(
    input_file: str,
    input_tree_name: str,
    output_file: str,
    output_tree_name: str,
    track_names: str,
    kinematics: str,
    particles: str,
    max_combinations: Optional[int] = None,
    keep_all_original_branches: str = 'False',
    branches_to_keep: Optional[str] = None,
    save_vector_columns: str = 'False',
    n_threads: int = 1,
) -> None:
    """
    Process a ROOT file to compute invariant masses for all track combinations with different particle hypotheses.

    Args:
        input_file: Path to the input ROOT file, could be a list of files separated by commas
        input_tree_name: Name of the input tree
        output_file: Path to the output ROOT file
        output_tree_name: Name of the output tree
        track_names: List of track names, separated by commas
        kinematics: List of kinematic variables, separated by commas
        particles: List of particle hypotheses, separated by commas
        max_combinations: Maximum number of tracks to combine
        keep_all_original_branches: Whether to keep all original branches
        branches_to_keep: List of additional branches to keep (e.g. eventNumber, runNumber)
        save_vector_columns: Whether to save the vector columns
        n_threads: Number of threads to use. Default is 1 (No multithreading enabled), set to -1 to use all available cores.
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If input parameters are invalid
    """

    # Configure multithreading
    if n_threads == 1:
        r.ROOT.DisableImplicitMT()
        logger.info("Multithreading is disabled")
    else:
        n_threads = multiprocessing.cpu_count() if n_threads < 0 else n_threads
        r.ROOT.EnableImplicitMT(n_threads)
        logger.info(f"Multithreading is enabled with {n_threads} threads")

    # Validate input file exists
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Create output directory if needed
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse the input arguments
    track_names = [name.strip() for name in track_names.split(',')]
    kinematics = [item.strip() for item in kinematics.split(',')]
    particles = [particle.strip() for particle in particles.split(',')]
    keep_all_original_branches = keep_all_original_branches.upper() == 'TRUE'
    branches_to_keep = [branch.strip() for branch in branches_to_keep.split(',')] if branches_to_keep else None
    save_vector_columns = save_vector_columns.upper() == 'TRUE'

    # Validate the input arguments
    for particle in particles:
        if particle not in AVAILABLE_PARTICLE_NAMES:
            logger.error(f"Invalid particle: [bold red]'{particle}'[/]. All available particles are: {AVAILABLE_PARTICLE_NAMES}", extra={"markup": True})
            raise ValueError(f"Invalid particle: {particle}")

    # Report configuration
    logger.info(f"Processing file: {input_file}")
    logger.info(f"Track names: {track_names}")
    logger.info(f"Particle hypotheses: {particles}")

    # Create RDataFrame from input file
    rdf = RDataFrame(input_tree_name, input_file)

    # Validate tree existence
    if not rdf:
        raise ValueError(f"Tree '{input_tree_name}' not found in file: {input_file}")

    # Process the data
    logger.info("Computing invariant masses...")
    modified_rdf, vector_cols, mass_cols = compute_invariant_masses(rdf, track_names, kinematics, particles, max_combinations)

    # Determine which columns to keep in output
    cols_to_save: List[str] = []

    if keep_all_original_branches:
        cols_to_save = rdf.GetColumnNames()
        cols_to_save += mass_cols
        logger.info("Keeping all original branches plus new calculations")
    else:
        cols_to_save = mass_cols

        if branches_to_keep:
            for branch in branches_to_keep:
                if branch in modified_rdf.GetColumnNames():
                    cols_to_save.append(branch)
                else:
                    logger.warning(f"Branch [bold yellow]'{branch}'[/] not found - skipping", extra={"markup": True})

    if save_vector_columns:
        cols_to_save += vector_cols

    logger.info(f"Keeping {len(cols_to_save)} branches in output")

    # Save the data
    logger.info(f"Writing output to {output_file}...")
    output_file_path = output_path.resolve().as_posix()
    modified_rdf.Snapshot(output_tree_name, output_file_path, cols_to_save)

    # Report summary
    logger.info(f"Success: Created {output_file_path}")
    logger.info(f" - Added {len(vector_cols)} Lorentz vector columns") if save_vector_columns else None
    logger.info(f" - Added {len(mass_cols)} invariant mass columns")
    logger.info(f" - Total branches in output: {len(cols_to_save)}")


# --------------------------------  Validation --------------------------------
def validate_invariant_mass_calculation() -> None:
    """
    Self-contained validation function to test the invariant mass calculation.
    Creates a dummy RDataFrame with track data, applies the mass calculation,
    and verifies the results.
    """
    print("Starting validation of invariant mass calculation...")

    # Create a ROOT RDataFrame with a single entry (one event)
    rdf = RDataFrame(1)

    # Add momentum components for two tracks: 'Kminus' and 'piplus'
    # These values represent typical momenta in GeV
    rdf = rdf.Define("Kminus_PX", "1.5")
    rdf = rdf.Define("Kminus_PY", "0.5")
    rdf = rdf.Define("Kminus_PZ", "3.0")
    rdf = rdf.Define("piplus_PX", "2.0")
    rdf = rdf.Define("piplus_PY", "-0.7")
    rdf = rdf.Define("piplus_PZ", "4.5")
    rdf = rdf.Define("proton_PX", "1.0")
    rdf = rdf.Define("proton_PY", "0.5")
    rdf = rdf.Define("proton_PZ", "3.0")

    # Define tracks, kinematics, and particle hypotheses
    track_names = ["Kminus", "piplus", "proton"]
    kinematics = ["PX", "PY", "PZ"]
    particles = ["pi+", "K+", "p+"]

    # Apply the compute_invariant_masses function
    modified_rdf, vector_name_list, mass_column_list = compute_invariant_masses(rdf, track_names, kinematics, particles)

    # Get all columns
    columns = modified_rdf.GetColumnNames()

    # Get list of all columns to verify the outputs
    print("\nCreated vector columns:")
    for col in vector_name_list:
        if col in columns:
            logger.info(f"  - {col}")
        else:
            logger.warning(f"  - [bold yellow]{col}[/] (not found)", extra={"markup": True})

    print("\nCreated mass columns:")
    for col in mass_column_list:
        if col in columns:
            logger.info(f"  - {col}")
        else:
            logger.warning(f"  - [bold yellow]{col}[/] (not found)", extra={"markup": True})

    # Print the full columns
    print("\nFull columns:")
    logger.info(columns)

    print("\nValidation complete!")


# --------------------------------  parse arguments --------------------------------
def get_parser() -> argparse.ArgumentParser:
    """Create and configure command line argument parser."""
    parser = argparse.ArgumentParser(description="Create track combination mass hypothesis")

    parser.add_argument("--input-file", type=str, required=True, help="Input ROOT file path, could be a list of files separated by commas")
    parser.add_argument("--input-tree-name", type=str, default="DecayTree", help="Name of the input tree")
    parser.add_argument("--output-file", type=str, required=True, help="Output ROOT file path")
    parser.add_argument("--output-tree-name", type=str, default="DecayTree", help="Name of the output tree")
    parser.add_argument(
        "--track-names",
        type=str,
        required=True,
        help="Track names, separated by commas, e.g. if the track is stored as branch [Kminus_PX, Kminus_PY, Kminus_PZ], then the track name is Kminus. Multiple track names should be separated by commas, like Kminus,piplus,proton",
    )
    parser.add_argument(
        "--kinematics",
        type=str,
        required=True,
        help="Kinematics (in MeV, to be aligned with the mass unit), separated by commas, e.g. if the kinematics is stored as branch [Kminus_PX, Kminus_PY, Kminus_PZ], then the kinematics is PX,PY,PZ",
    )
    parser.add_argument(
        "--particles",
        type=str,
        required=True,
        help=f"Particles for the mass hypothesis calculation, separated by commas, e.g. pi+,K+,p+,mu+,e+. All available particles are: {AVAILABLE_PARTICLE_NAMES}",
    )
    parser.add_argument("--max-combinations", type=int, required=True, help="Maximum number of combinations, e.g. 2")

    # Control the output
    parser.add_argument('--keep-all-original-branches', type=str, default='False', help="Keep all original branches")
    parser.add_argument(
        "--branches-to-keep", type=str, required=False, help="Additional branches to keep (only work when keep_all_original_branches is False), separated by commas, e.g. eventNumber,runNumber"
    )

    parser.add_argument('--save-vector-columns', type=str, default='False', help="Save the vector columns")

    # Control the performance
    parser.add_argument('--n-threads', type=int, default=1, help='Number of threads to use. Default is 1 (No multithreading enabled), set to -1 to use all available cores.')

    return parser


def main(args=None):
    """Main entry point for the script."""
    if args is None:
        args = get_parser().parse_args()
    track_combination_mass_calculator(**vars(args))


if __name__ == '__main__':
    main()

    # validate_invariant_mass_calculation()
