from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import cast

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from havij.infrastructure.config import load_config
from havij.infrastructure.persistence.sqlite_db import connect, init_schema
from havij.infrastructure.persistence.meal_repository import SqliteDayLogRepository
from havij.infrastructure.api.openfoodfacts_client import OpenFoodFactsClient, OpenFoodFactsError
from havij.infrastructure.api.catalog_adapter import OpenFoodFactsCatalog
from havij.application.services.meal_service import MealService

def _services() -> MealService:
    cfg = load_config()
    conn = connect(cfg.db_path)
    init_schema(conn)
    repo = SqliteDayLogRepository(conn)
    client = OpenFoodFactsClient()
    catalog = OpenFoodFactsCatalog(client)
    return MealService(repo=repo, catalog=catalog)

def main() -> None:
    st.set_page_config(page_title="Nutrition Scanner + Meal Logger", layout="wide")
    st.title("🥗 Nutrition Scanner + Meal Logger")

    svc = _services()

    tabs = st.tabs(["Log Meal", "Today", "Last 7 Days"])

    with tabs[0]:
        st.subheader("Add a meal entry")
        day = st.date_input("Day", value=date.today())
        barcode = st.text_input("Barcode (digits only)", value="")
        grams = st.number_input("Quantity (grams)", min_value=1.0, value=100.0, step=1.0)

        if st.button("Lookup & Add", type="primary"):
            try:
                entry = svc.add_entry(day=day, barcode=barcode.strip(), grams=float(grams))
                st.success(f"Added: {entry.product_name} ({entry.grams:.0f} g)")
            except OpenFoodFactsError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Error: {exc}")

    with tabs[1]:
        st.subheader("Today log")
        day = st.date_input("Day to view", value=date.today(), key="view_day")
        log = svc.get_day_log(day)
        if not log.entries:
            st.info("No entries yet for this day.")
        else:
            rows = []
            for entry in log.entries:
                rows.append({
                    "time": entry.timestamp.strftime("%H:%M"),
                    "product": entry.product_name,
                    "barcode": entry.barcode,
                    "grams": entry.grams,
                    "kcal": round(entry.nutrients.kcal, 1),
                    "protein_g": round(entry.nutrients.protein_g, 1),
                    "carbs_g": round(entry.nutrients.carbs_g, 1),
                    "fat_g": round(entry.nutrients.fat_g, 1),
                    "entry_id": entry.entry_id,
                })
            df = pd.DataFrame(rows)
            st.dataframe(df.drop(columns=["entry_id"]), use_container_width=True)

            totals = svc.get_day_totals(day)
            st.markdown("### Totals")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("kcal", f"{totals.kcal:.1f}")
            c2.metric("protein (g)", f"{totals.protein_g:.1f}")
            c3.metric("carbs (g)", f"{totals.carbs_g:.1f}")
            c4.metric("fat (g)", f"{totals.fat_g:.1f}")

            st.markdown("### Remove entry")
            entry_ids = [str(r["entry_id"]) for r in rows]
            entry_id = cast(str, st.selectbox("Select entry to remove", options=entry_ids))
            if st.button("Remove selected"):
                removed = svc.remove_entry(day, entry_id)
                if removed:
                    st.success("Removed. Refresh the page/tab to see updates.")
                else:
                    st.warning("Entry not found.")

    with tabs[2]:
        st.subheader("Last 7 days totals")
        end = st.date_input("End day", value=date.today(), key="end_day")
        data = svc.get_last_days_totals(end_day=end, days=7)
        rows = []
        for d, tot in data:
            rows.append({
                "day": d.isoformat(),
                "kcal": tot.kcal,
                "protein_g": tot.protein_g,
                "carbs_g": tot.carbs_g,
                "fat_g": tot.fat_g,
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        st.line_chart(df.set_index("day")[["kcal", "protein_g", "carbs_g", "fat_g"]])

if __name__ == "__main__":
    main()
