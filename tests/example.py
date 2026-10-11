from pathlib import Path

import farmpypl as fpl

DATA = Path(__file__).parent / "data"


def main():
    manager = fpl.FarmManager.from_csv(DATA / "farm.csv")

    print(manager.farm_summary())
    print("#"*40)
    print(manager.herd_summary())
    print("#"*40)
    print(manager.herd_cohorts())
    print("#"*40)
    print(manager.costs())
    print("#"*40)
    print(manager.price_summary().drop(columns="file"))
    print("#"*40)


if __name__ == "__main__":
    main()
