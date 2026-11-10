"""Non-destructive read-only catalog inspection for FloodCAT.

Run from Anaconda Prompt after installing earthengine-api and authenticating:
  python scripts/inspect_gee_catalog.py --project YOUR_PROJECT_ID
This script does not download, export, write files or alter Earth Engine assets.
"""
import argparse
import sys


def run(project: str) -> int:
    try:
        import ee
    except ImportError:
        print("Missing earthengine-api. Ask before installing: python -m pip install earthengine-api")
        return 2
    try:
        ee.Initialize(project=project)
        print("EE API:", ee.String("FloodCAT EE OK").getInfo())
        wri = ee.ImageCollection("WRI/Aqueduct_Flood_Hazard_Maps/V2")
        # Discover exact names from returned metadata; avoid silently assuming padded model strings.
        historical = wri.filter(ee.Filter.eq("floodtype", "inunriver")).filter(ee.Filter.eq("climatescenario", "historical"))
        future = wri.filter(ee.Filter.eq("floodtype", "inunriver")).filter(ee.Filter.eq("climatescenario", "rcp4p5"))
        print("Historical river sample model identifiers:", historical.aggregate_array("model").distinct().getInfo())
        print("RCP4.5 river sample model identifiers:", future.aggregate_array("model").distinct().getInfo())
        scenarios = [
            ("historical_T25", "historical", 25, 1980),
            ("historical_T100", "historical", 100, 1980),
            ("historical_T500", "historical", 500, 1980),
            ("rcp4p5_2050_T100", "rcp4p5", 100, 2050),
            ("rcp8p5_2050_T100", "rcp8p5", 100, 2050),
        ]
        for label, climate, rp, year in scenarios:
            candidate = (wri.filter(ee.Filter.eq("floodtype", "inunriver"))
                         .filter(ee.Filter.eq("climatescenario", climate))
                         .filter(ee.Filter.eq("returnperiod", rp))
                         .filter(ee.Filter.eq("year", year)))
            n = candidate.size().getInfo()
            print(f"{label}: {n} candidate image(s), BEFORE model selection")
            if n:
                sample = candidate.limit(8)
                print("  asset_ids:", sample.aggregate_array("system:index").getInfo())
                print("  models:", sample.aggregate_array("model").getInfo())
                print("  first bands:", ee.Image(candidate.first()).bandNames().getInfo())
        wp = (ee.ImageCollection("WorldPop/GP/100m/pop")
              .filter(ee.Filter.eq("country", "IND"))
              .filter(ee.Filter.eq("year", 2020)))
        print("WorldPop 2020 country=IND count:", wp.size().getInfo())
        if wp.size().getInfo():
            print("  WorldPop first metadata:", ee.Image(wp.first()).toDictionary(["system:index", "country", "year"]).getInfo())
            print("  WorldPop first bands:", ee.Image(wp.first()).bandNames().getInfo())
        ghsl = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S/2020")
        print("GHSL 2020 bands:", ghsl.bandNames().getInfo())
        print("All catalog queries completed; no assets or files modified.")
        return 0
    except Exception as exc:
        print(f"Earth Engine catalog inspection FAILED: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True, help="Registered Google Cloud Earth Engine project ID (not credential)")
    args = p.parse_args()
    sys.exit(run(args.project))
