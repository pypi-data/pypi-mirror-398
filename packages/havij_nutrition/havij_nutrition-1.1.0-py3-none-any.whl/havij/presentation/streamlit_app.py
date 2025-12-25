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
from havij.infrastructure.persistence.user_repository import SqliteUserRepository
from havij.infrastructure.api.openfoodfacts_client import OpenFoodFactsClient, OpenFoodFactsError
from havij.infrastructure.api.catalog_adapter import OpenFoodFactsCatalog
from havij.application.services.meal_service import MealService
from havij.application.services.product_service import ProductService
from havij.application.services.user_service import UserService
from havij.domain.model.nutrients import Nutrients

def _services() -> tuple[MealService, ProductService, UserService]:
    cfg = load_config()
    conn = connect(cfg.db_path)
    init_schema(conn)
    repo = SqliteDayLogRepository(conn)
    user_repo = SqliteUserRepository(conn)
    client = OpenFoodFactsClient()
    catalog = OpenFoodFactsCatalog(client)
    return MealService(repo=repo), ProductService(catalog=catalog), UserService(repo=user_repo)

def main() -> None:
    st.set_page_config(page_title="Nutrition Scanner + Meal Logger", layout="wide")
    st.title("🥗 Nutrition Scanner + Meal Logger")

    meal_svc, product_svc, user_svc = _services()

    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("username", "")

    with st.sidebar:
        st.subheader("Account")
        if not st.session_state["user_id"]:
            mode = st.radio("Choose", options=["Login", "Sign up"], horizontal=True)
            if mode == "Login":
                login_username = st.text_input("Username", key="login_username")
                login_password = st.text_input("Password", type="password", key="login_password")
                if st.button("Login"):
                    profile = user_svc.authenticate(login_username, login_password)
                    if profile:
                        st.session_state["user_id"] = profile.user_id
                        st.session_state["username"] = profile.username
                        st.success("Logged in.")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
            else:
                signup_username = st.text_input("Username", key="signup_username")
                signup_password = st.text_input("Password", type="password", key="signup_password")
                signup_confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
                if st.button("Create account"):
                    if signup_password != signup_confirm:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            had_users = user_svc.count_users() > 0
                            profile = user_svc.signup(signup_username, signup_password)
                            st.session_state["user_id"] = profile.user_id
                            st.session_state["username"] = profile.username
                            if not had_users:
                                meal_svc.assign_unowned_entries(profile.user_id)
                            st.success("Account created.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
        else:
            st.write(f"Signed in as **{st.session_state['username']}**")
            if st.button("Log out"):
                st.session_state["user_id"] = None
                st.session_state["username"] = ""
                st.rerun()

    tabs = st.tabs(["Log Meal", "Today", "Last 7 Days", "Profile"])

    with tabs[0]:
        if not st.session_state["user_id"]:
            st.info("Log in or sign up to add entries.")
        else:
            st.subheader("Add a meal entry")
            day = st.date_input("Day", value=date.today())
            st.session_state.setdefault("product_name", "")
            st.session_state.setdefault("kcal_per_100g", 0.0)
            st.session_state.setdefault("protein_per_100g", 0.0)
            st.session_state.setdefault("carbs_per_100g", 0.0)
            st.session_state.setdefault("fat_per_100g", 0.0)
            st.session_state.setdefault("lookup_barcode", "")

            barcode = st.text_input("Barcode (digits only)", value="", key="barcode_input")
            if st.button("Lookup barcode"):
                try:
                    product = product_svc.lookup_product(barcode.strip())
                    st.session_state["product_name"] = product.name
                    st.session_state["kcal_per_100g"] = float(product.nutrients_per_100g.kcal)
                    st.session_state["protein_per_100g"] = float(product.nutrients_per_100g.protein_g)
                    st.session_state["carbs_per_100g"] = float(product.nutrients_per_100g.carbs_g)
                    st.session_state["fat_per_100g"] = float(product.nutrients_per_100g.fat_g)
                    st.session_state["lookup_barcode"] = product.barcode
                    st.success(f"Found: {product.name}")
                except OpenFoodFactsError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Error: {exc}")

            product_name = st.text_input("Product name", key="product_name")
            grams = st.number_input("Quantity (grams)", min_value=1.0, value=100.0, step=1.0)
            st.markdown("**Nutrients per 100 g**")
            c1, c2, c3, c4 = st.columns(4)
            kcal = c1.number_input(
                "kcal",
                min_value=0.0,
                value=st.session_state["kcal_per_100g"],
                step=1.0,
                key="kcal_per_100g",
            )
            protein = c2.number_input(
                "protein (g)",
                min_value=0.0,
                value=st.session_state["protein_per_100g"],
                step=0.1,
                key="protein_per_100g",
            )
            carbs = c3.number_input(
                "carbs (g)",
                min_value=0.0,
                value=st.session_state["carbs_per_100g"],
                step=0.1,
                key="carbs_per_100g",
            )
            fat = c4.number_input(
                "fat (g)",
                min_value=0.0,
                value=st.session_state["fat_per_100g"],
                step=0.1,
                key="fat_per_100g",
            )

            if st.button("Add entry", type="primary"):
                try:
                    nutrients_per_100g = Nutrients(
                        kcal=float(kcal),
                        protein_g=float(protein),
                        carbs_g=float(carbs),
                        fat_g=float(fat),
                    )
                    entry = meal_svc.add_entry(
                        user_id=st.session_state["user_id"],
                        day=day,
                        product_name=product_name.strip(),
                        grams=float(grams),
                        nutrients_per_100g=nutrients_per_100g,
                        barcode=st.session_state.get("lookup_barcode", ""),
                    )
                    st.success(f"Added: {entry.product_name} ({entry.grams:.0f} g)")
                except Exception as exc:
                    st.error(f"Error: {exc}")

    with tabs[1]:
        if not st.session_state["user_id"]:
            st.info("Log in or sign up to view your log.")
        else:
            st.subheader("Today log")
            day = st.date_input("Day to view", value=date.today(), key="view_day")
            log = meal_svc.get_day_log(st.session_state["user_id"], day)
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

                totals = meal_svc.get_day_totals(st.session_state["user_id"], day)
                st.markdown("### Totals")
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("kcal", f"{totals.kcal:.1f}")
                c2.metric("protein (g)", f"{totals.protein_g:.1f}")
                c3.metric("carbs (g)", f"{totals.carbs_g:.1f}")
                c4.metric("fat (g)", f"{totals.fat_g:.1f}")

                st.markdown("### Remove entry")
                entry_ids = [str(r["entry_id"]) for r in rows]
                entry_labels = {
                    str(r["entry_id"]): f'{r["time"]} - {r["product"]}'
                    for r in rows
                }
                entry_id = cast(
                    str,
                    st.selectbox(
                        "Select entry to remove",
                        options=entry_ids,
                        format_func=lambda entry: entry_labels.get(entry, entry),
                    ),
                )
                if st.button("Remove selected"):
                    removed = meal_svc.remove_entry(st.session_state["user_id"], day, entry_id)
                    if removed:
                        st.success("Removed. Refresh the page/tab to see updates.")
                    else:
                        st.warning("Entry not found.")

    with tabs[2]:
        if not st.session_state["user_id"]:
            st.info("Log in or sign up to view history.")
        else:
            st.subheader("Last 7 days totals")
            end = st.date_input("End day", value=date.today(), key="end_day")
            data = meal_svc.get_last_days_totals(st.session_state["user_id"], end_day=end, days=7)
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

    with tabs[3]:
        if not st.session_state["user_id"]:
            st.info("Log in or sign up to view your profile.")
        else:
            st.subheader("Your profile")
            profile = user_svc.get_profile(st.session_state["user_id"])
            if not profile:
                st.error("Profile not found.")
            else:
                st.write(f"**Username:** {profile.username}")
                st.write(f"**Created:** {profile.created_at.strftime('%Y-%m-%d %H:%M UTC')}")

if __name__ == "__main__":
    main()
