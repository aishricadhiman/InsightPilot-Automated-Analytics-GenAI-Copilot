import pandas as pd

from load_data import load_raw_data


def profile_dataset(name: str, df: pd.DataFrame) -> None:
    """Print a basic profiling summary for a dataset."""

    print(f"\n{'=' * 60}")
    print(f"DATASET: {name.upper()}")
    print(f"{'=' * 60}")

    print(f"Rows: {len(df):,}")
    print(f"Columns: {df.shape[1]}")
    print(f"Duplicate rows: {df.duplicated().sum():,}")

    print("\nData types:")
    print(df.dtypes)

    missing = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "missing_pct": (df.isna().mean() * 100).round(2),
    })

    missing = missing[missing["missing_count"] > 0]

    print("\nMissing values:")
    if missing.empty:
        print("None")
    else:
        print(missing)

    print("\nNumeric summary:")
    print(df.describe(include="number"))


def main():
    datasets = load_raw_data()

    for name, df in datasets.items():
        profile_dataset(name, df)


if __name__ == "__main__":
    main()