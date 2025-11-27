"""
Utility script to gauge how predictive the wishlist dataset is regarding
whether a wishlist contains products in the cart dataset.

It trains a simple pipeline (scaler + decision tree) and prints key metrics.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from tqdm import tqdm

BASE_DIR = Path(__file__).parent
WISHLIST_CSV = BASE_DIR / "Wishlist.csv"
CART_CSV = BASE_DIR / "CartProducts.csv"


def _load_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
    wishlist = pd.read_csv(WISHLIST_CSV, parse_dates=["created_at"])
    cart_products = pd.read_csv(CART_CSV)
    return wishlist, cart_products


def _feature_engineering(
    wishlist: pd.DataFrame, cart_products: pd.DataFrame
) -> tuple[pd.DataFrame, List[str]]:
    cart_agg = (
        cart_products.groupby("wishlist_id")
        .agg(
            cart_size=("product_id", "count"),
            unique_products=("product_id", "nunique"),
            total_quantity=("quantity", "sum"),
            avg_quantity=("quantity", "mean"),
        )
        .reset_index()
    )

    dataset = wishlist.merge(
        cart_agg, left_on="id", right_on="wishlist_id", how="left"
    )
    dataset.drop(columns=["wishlist_id"], inplace=True)

    numeric_cols = ["cart_size", "unique_products", "total_quantity", "avg_quantity"]
    dataset[numeric_cols] = dataset[numeric_cols].fillna(0)

    dataset["created_at"] = pd.to_datetime(dataset["created_at"], utc=True, errors="coerce")
    dataset["wishlist_age_days"] = (
        pd.Timestamp.utcnow() - dataset["created_at"]
    ).dt.total_seconds() / 86_400
    dataset["wishlist_age_days"].fillna(dataset["wishlist_age_days"].median(), inplace=True)

    dataset["user_bucket"] = dataset["user_id"] % 50

    dataset["has_products"] = (dataset["cart_size"] > 0).astype(int)

    feature_cols = [
        "cart_size",
        "unique_products",
        "total_quantity",
        "avg_quantity",
        "wishlist_age_days",
        "user_bucket",
    ]

    return dataset, feature_cols


def evaluate(test_size: float = 0.1, random_state: int = 42) -> None:
    steps = [
        "Loading data",
        "Feature engineering",
        "Train/test split",
        "Model training",
        "Prediction",
        "Metrics",
    ]

    with tqdm(total=len(steps), desc="Evaluating datasets", unit="step") as bar:
        wishlist, cart_products = _load_datasets()
        bar.update()

        dataset, feature_cols = _feature_engineering(wishlist, cart_products)
        bar.update()

        X = dataset[feature_cols]
        y = dataset["has_products"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        bar.update()

        pipeline = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", DecisionTreeClassifier(max_depth=6, random_state=random_state)),
            ]
        )

        pipeline.fit(X_train, y_train)
        bar.update()

        y_pred = pipeline.predict(X_test)
        bar.update()

        accuracy = accuracy_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred)
        report = classification_report(y_test, y_pred, digits=4)
        bar.update()

    print(f"\nAccuracy: {accuracy * 100:.2f}%")
    print("Confusion matrix:")
    print(cm)
    print("\nDetailed report:")
    print(report)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure how well wishlist features predict having cart products."
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.1,
        help="Portion of the dataset to reserve for evaluation (default: 0.1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random state for the train/test split and model (default: 42).",
    )
    args = parser.parse_args()

    evaluate(test_size=args.test_size, random_state=args.seed)


if __name__ == "__main__":
    main()

