# load packages
import sys
import importlib
import logging
import os
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
import pandas as pd

execute_functions = False

if execute_functions:

    # define login credentials
    load_dotenv()
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    # define logger
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s - %(name)s - %(levelname)s - ID=%(id)s - URL=%(url)s - %(message)s"
    )

    # define object to be passed onto functions
    iteration = 1385

    matches = [
        232434,
        202485
    ]

    positions = [
        "GOALKEEPER",
        "LEFT_WINGBACK_DEFENDER",
        "RIGHT_WINGBACK_DEFENDER",
        "CENTRAL_DEFENDER",
        "DEFENSE_MIDFIELD",
        "CENTRAL_MIDFIELD",
        "ATTACKING_MIDFIELD",
        "LEFT_WINGER",
        "RIGHT_WINGER",
        "CENTER_FORWARD"
    ]

    # define envs
    envs = ["source", "test"]

    def load_impect(env: str):
        # remove existing impectPy from cache
        if "impectPy" in sys.modules:
            del sys.modules["impectPy"]

        # clean up any previously injected local paths
        sys.path = [p for p in sys.path if "impectPy" not in p]

        if env == "test":
            # adjust if your repo layout differs
            local_repo_root = Path(__file__).resolve().parents[2]
            sys.path.insert(0, str(local_repo_root))

        return importlib.import_module("impectPy")

    # iterate over envs
    for env in envs:

        impectPy = load_impect(env)

        config = impectPy.Config()
        api = impectPy.Impect(config=config)
        api.login(username, password)

        with tqdm(total=20, desc=f"{env}: Executing functions...", unit="chunk") as pbar:

            # get iterations
            iterations = api.getIterations()
            iterations.to_csv(f"files/{env}/iterations.csv")
            pbar.update()

            # get squad ratings
            ratings = api.getSquadRatings(iteration)
            ratings.to_csv(f"files/{env}/ratings.csv")
            pbar.update()

            # get squad coefficients
            coefficients = api.getSquadCoefficients(iteration)
            coefficients.to_csv(f"files/{env}/coefficients.csv")
            pbar.update()

            # get matches
            matchplan = api.getMatches(iteration)
            matchplan.to_csv(f"files/{env}/matchplan.csv")
            pbar.update()

            # get match info
            formations = api.getFormations(matches)
            formations.to_csv(f"files/{env}/formations.csv")
            pbar.update()
            substitutions = api.getSubstitutions(matches)
            substitutions.to_csv(f"files/{env}/substitutions.csv")
            pbar.update()
            startingPositions = api.getStartingPositions(matches)
            startingPositions.to_csv(f"files/{env}/startingPositions.csv")
            pbar.update()

            # get match events
            events = api.getEvents(matches, include_kpis=True, include_set_pieces=True)
            events.to_csv(f"files/{env}/events.csv")
            pbar.update()

            # get set pieces
            set_pieces = api.getSetPieces(matches)
            set_pieces.to_csv(f"files/{env}/set_pieces.csv")
            pbar.update()

            # get player iteration averages
            playerIterationAverages = api.getPlayerIterationAverages(iteration)
            playerIterationAverages.to_csv(f"files/{env}/playerIterationAverages.csv")
            pbar.update()

            # get player matchsums
            playerMatchsums = api.getPlayerMatchsums(matches)
            playerMatchsums.to_csv(f"files/{env}/playerMatchsums.csv")
            pbar.update()

            # get squad iteration averages
            squadIterationAverages = api.getSquadIterationAverages(iteration)
            squadIterationAverages.to_csv(f"files/{env}/squadIterationAverages.csv")
            pbar.update()

            # get squad matchsums
            squadMatchsums = api.getSquadMatchsums(matches)
            squadMatchsums.to_csv(f"files/{env}/squadMatchsums.csv")
            pbar.update()

            # get player match scores
            playerMatchScores = api.getPlayerMatchScores(matches)
            playerMatchScores.to_csv(f"files/{env}/playerMatchScores.csv")
            pbar.update()
            playerMatchScores_2 = api.getPlayerMatchScores(matches, positions)
            playerMatchScores_2.to_csv(f"files/{env}/playerMatchScores_2.csv")
            pbar.update()

            # get squad match scores
            squadMatchScores = api.getSquadMatchScores(matches)
            squadMatchScores.to_csv(f"files/{env}/squadMatchScores.csv")
            pbar.update()

            # get player iteration scores
            playerIterationScores = api.getPlayerIterationScores(iteration)
            playerIterationScores.to_csv(f"files/{env}/playerIterationScores.csv")
            pbar.update()
            playerIterationScores_2 = api.getPlayerIterationScores(iteration, positions)
            playerIterationScores_2.to_csv(f"files/{env}/playerIterationScores_2.csv")
            pbar.update()

            # get squad iteration scores
            squadIterationScores = api.getSquadIterationScores(iteration)
            squadIterationScores.to_csv(f"files/{env}/squadIterationScores.csv")
            pbar.update()

            # get player profile scores
            playerProfileScores = api.getPlayerProfileScores(iteration, positions)
            playerProfileScores.to_csv(f"files/{env}/playerProfileScores.csv")
            pbar.update()

print("\nRunning auto-diff between source and test outputs...\n")

base_path = Path(__file__).parent / "files"
source_path = base_path / "source"
test_path = base_path / "test"

failed = False

for src_file in source_path.glob("*.csv"):
    test_file = test_path / src_file.name

    if not test_file.exists():
        print(f"[MISSING] {src_file.name} not found in test/")
        failed = True
        continue

    src_df = pd.read_csv(src_file, low_memory=False)
    test_df = pd.read_csv(test_file, low_memory=False)

    try:
        pd.testing.assert_frame_equal(
            src_df,
            test_df,
            check_dtype=False,
            check_like=True
        )
        print(f"[OK] {src_file.name}")
    except AssertionError as e:
        print(f"[DIFF] {src_file.name}")
        print(str(e).splitlines()[0])
        failed = True

if failed:
    raise AssertionError("Auto-diff failed: source and test outputs differ")

print("\nAll source vs test outputs are identical ✅")