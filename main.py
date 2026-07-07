import argparse
import sys
from db.db_setup import init_database
from agents.harvester import DataHarvester
from agents.ingester import DataIngester
from agents.cartographer import GISCartographer

def main():
    parser = argparse.ArgumentParser(description="Wisconsin Spatial Overlay Pipeline - PRD v2.0")
    parser.add_argument("--county", type=str, default="Brown", help="Target county run setup")
    parser.add_argument("--phase", type=int, default=1, help="Execution phase step tracking")
    args = parser.parse_args()

    if args.county.lower() != "brown":
        print(f"[-] Error: County '{args.county}' is out of scope for Phase 1 MVP.")
        sys.exit(1)

    print(f"=========================================================")
    print(f"🚀 LAUNCHING PIPELINE: {args.county.upper()} COUNTY MVP (PRD v2.0)")
    print(f"=========================================================\n")

    # Step 1: Provision DB
    print("[STEP 1/4] Provisioning PostGIS database structures...")
    init_database()

    # Step 2: Download raw vector files
    print("\n[STEP 2/4] Initializing Agent 1: Data Harvester...")
    harvester = DataHarvester()
    harvester.run_all()

    # Step 3: Run spatial geometric intersections
    print("\n[STEP 3/4] Initializing Agent 2: Database Ingester & Spatial Solver...")
    ingester = DataIngester()
    ingester.run_all()

    # Step 4: Output data structures and interactive maps
    print("\n[STEP 4/4] Initializing Agent 3: GIS Cartographer...")
    cartographer = GISCartographer()
    cartographer.run_all()

    print("\n=========================================================")
    print("🏁 PIPELINE SUCCESS: Check /output/ directory for artifacts.")
    print("=========================================================")

if __name__ == "__main__":
    main()