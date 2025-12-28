"""Helpers to load example datasets for the documentation tutorials."""

import pathlib

from sklearn.preprocessing import KBinsDiscretizer
from sklearn import datasets


DATASETS_DIR = pathlib.Path(__file__).parent / "data"


def housing():
    ames_dataset = datasets.fetch_openml(data_id=43926)
    data = ames_dataset["data"].assign(Sale_Price=ames_dataset["target"])
    X = data.drop("Sale_Price", axis=1)
    y = (
        KBinsDiscretizer(encode="ordinal")
        .fit_transform(data[["Sale_Price"]])
        .squeeze()
        .astype("int32")
    )
    return X, y



def best_buy(subsample=False):
    suffix = "_small" if subsample else ""
    return {
        "train_path": str(DATASETS_DIR / f"best_buy_train{suffix}.parquet"),
        "test_path": str(DATASETS_DIR / f"best_buy_test{suffix}.parquet"),
        "target_columns": [
            "neuralk categorization level 1",
            "neuralk categorization level 2",
            "neuralk categorization level 3",
            "neuralk categorization level 4",
            "neuralk categorization level 5",
        ],
        "feature_columns": ["name", "description"],
    }


def two_moons():
    return {
        "path": str(DATASETS_DIR / "moons.csv"),
        "target_columns": ["label"],
        "feature_columns": ["feature1", "feature2"],
    }
