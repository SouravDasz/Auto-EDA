import uuid
import os
import random
import threading
import time
from itertools import combinations

import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask import (
    Blueprint, render_template, session,
    current_app, url_for, request, redirect, flash
)
from werkzeug.utils import secure_filename

# ================= BLUEPRINTS =================
file_page = Blueprint("file_page", __name__)
eda = Blueprint("eda", __name__)

# ================= CONFIG =================
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv", "xlsx", "json"}

# ================= HELPERS =================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_uploaded_file(file_path, delay=60):
    """Delete uploaded file after delay"""
    time.sleep(delay)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass


def cleanup_generated_files(files, delay=15):
    """Delete generated plot files after delay"""
    time.sleep(delay)
    for f in files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass


# ================= AUTO CLEANUP (GLOBAL, TIME-BASED) =================
def cleanup_old_files(folder_path, max_age_seconds):
    """
    Delete files older than max_age_seconds
    """
    if not os.path.exists(folder_path):
        return

    now = time.time()
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                if now - os.path.getmtime(file_path) > max_age_seconds:
                    os.remove(file_path)
        except Exception:
            pass


def periodic_cleanup(app_root, interval=300):
    """
    Periodically cleans uploads and plots folders
    """
    while True:
        time.sleep(interval)

        uploads_path = os.path.join(app_root, UPLOAD_FOLDER)
        plots_path = os.path.join(app_root, "static", "plots")

        # delete files older than 15 minutes
        cleanup_old_files(uploads_path, 900)
        cleanup_old_files(plots_path, 900)


# ================= FILE UPLOAD =================
@file_page.route("/fill_upload", methods=["GET", "POST"])
def fill_upload():
    upload_dir = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    os.makedirs(upload_dir, exist_ok=True)

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part found", "error")
            return redirect(url_for("file_page.fill_upload"))

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected", "error")
            return redirect(url_for("file_page.fill_upload"))

        if not allowed_file(file.filename):
            flash("Invalid file type", "error")
            return redirect(url_for("file_page.fill_upload"))

        filename = secure_filename(file.filename)
        stored_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(upload_dir, stored_name)
        file.save(file_path)

        session["project_name"] = request.form.get("project_name")
        session["target_column"] = request.form.get("target_column")

        return redirect(url_for("eda.EDA", filename=stored_name))

    return render_template("file_upload.html")


# ================= EDA ROUTE =================
@eda.route("/eda/<filename>", methods=["GET"])
def EDA(filename):
    upload_dir = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    file_path = os.path.join(upload_dir, filename)

    if not os.path.exists(file_path):
        flash("Uploaded file no longer exists. Upload again.", "error")
        return redirect(url_for("file_page.fill_upload"))

    # Load data
    if filename.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    elif filename.endswith(".json"):
        df = pd.read_json(file_path)
    else:
        return "Unsupported file type", 400

    project_name = session.get("project_name", "EDA Report")
    target_column = session.get("target_column")

    shape = df.shape
    missing = int(df.isnull().sum().sum())

    columns_info = [
        {
            "index": i,
            "name": col,
            "non_null": int(df[col].notnull().sum()),
            "dtype": str(df[col].dtype)
        }
        for i, col in enumerate(df.columns)
    ]

    # Plot setup
    plot_folder = os.path.join(current_app.static_folder, "plots")
    os.makedirs(plot_folder, exist_ok=True)
    generated_files = []

    palettes = ["magma", "plasma", "mako", "viridis", "rocket", "turbo", "inferno"]
    theme_palette = random.choice(palettes)
    sns.set_palette(theme_palette)

    # ================= TARGET PLOTS =================
    target_plots, target_info, target_list = [], [], []
    target_type = "Not Provided"

    if target_column and target_column in df.columns:
        dtype = df[target_column].dtype
        target_type = "Object" if dtype == "object" else "Number"

        for label, count in df[target_column].value_counts().items():
            target_info.append({"label": label, "count": int(count)})

        plt.figure(figsize=(6, 4))
        if dtype == "object" or df[target_column].nunique() <= 20:
            sns.countplot(x=df[target_column], palette=theme_palette)
            if df[target_column].nunique() == 2:
                target_list = df[target_column].value_counts().tolist()
        else:
            sns.histplot(df[target_column], kde=True,
                         color=sns.color_palette(theme_palette)[0])

        t_name = f"target_{uuid.uuid4().hex}.png"
        t_path = os.path.join(plot_folder, t_name)
        plt.savefig(t_path, bbox_inches="tight")
        plt.close()

        generated_files.append(t_path)
        target_plots.append(url_for("static", filename=f"plots/{t_name}"))

    # ================= DESCRIBE TABLE =================
    describe_table = df.describe(include='all').round(2).to_html(
        classes="w-full text-sm border-collapse", border=0
    )

    # ================= UNIVARIATE PLOTS =================
    feature_plots = []

    for col in df.columns:
        if col == target_column:
            continue

        try:
            plt.figure(figsize=(6, 4))
            is_categorical = df[col].dtype == "object" or df[col].nunique() <= 20

            if is_categorical:
                if df[col].nunique() > 20:
                    plt.close()
                    continue
                sns.countplot(x=df[col], palette=theme_palette)
                plt.xticks(rotation=45)
            elif pd.api.types.is_numeric_dtype(df[col]):
                sns.histplot(df[col], kde=True,
                             color=sns.color_palette(theme_palette)[0])
            else:
                plt.close()
                continue

            f_name = f"feature_{uuid.uuid4().hex}.png"
            f_path = os.path.join(plot_folder, f_name)
            plt.savefig(f_path, bbox_inches="tight")
            plt.close()

            generated_files.append(f_path)
            feature_plots.append({
                "name": col,
                "path": url_for("static", filename=f"plots/{f_name}")
            })
        except Exception:
            plt.close()

    # ================= BIVARIATE NUMERIC PLOTS =================
    numerical_cols = df.select_dtypes(include="number").columns.tolist()
    bivariate_plots = []

    for c1, c2 in combinations(numerical_cols, 2):
        plt.figure(figsize=(6, 4))
        sns.scatterplot(x=df[c1], y=df[c2],
                        color=sns.color_palette(theme_palette)[0])
        b_name = f"bivar_{uuid.uuid4().hex}.png"
        b_path = os.path.join(plot_folder, b_name)
        plt.savefig(b_path, bbox_inches="tight")
        plt.close()

        generated_files.append(b_path)
        bivariate_plots.append({
            "pair": f"{c1} vs {c2}",
            "path": url_for("static", filename=f"plots/{b_name}")
        })

    # ================= TARGET vs NUMERIC FEATURES =================
    target_bivariate = []
    if target_column in numerical_cols:
        for col in numerical_cols:
            if col == target_column:
                continue
            plt.figure(figsize=(6, 4))
            sns.scatterplot(x=df[col], y=df[target_column],
                            color=sns.color_palette(theme_palette)[0])
            tb_name = f"target_bivar_{uuid.uuid4().hex}.png"
            tb_path = os.path.join(plot_folder, tb_name)
            plt.savefig(tb_path, bbox_inches="tight")
            plt.close()

            generated_files.append(tb_path)
            target_bivariate.append({
                "name": col,
                "path": url_for("static", filename=f"plots/{tb_name}")
            })

    # ================= CORRELATION HEATMAP =================
    heatmap_url = None
    if len(numerical_cols) >= 2:
        plt.figure(figsize=(10, 8))
        sns.heatmap(df[numerical_cols].corr(), annot=True, fmt=".2f",
                    cmap=theme_palette, linewidths=0.5, square=True)
        plt.title("Correlation Heatmap (Numerical Features)")
        h_name = f"heatmap_{uuid.uuid4().hex}.png"
        h_path = os.path.join(plot_folder, h_name)
        plt.savefig(h_path, bbox_inches="tight")
        plt.close()

        generated_files.append(h_path)
        heatmap_url = url_for("static", filename=f"plots/{h_name}")

    # ================= OUTLIER DETECTION =================
    outlier_info = []
    outlier_plots = []

    for col in numerical_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1

        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        outlier_info.append({
            "col": col,
            "lower_limit": lower,
            "upper_limit": upper
        })

        plt.figure(figsize=(6, 4))
        sns.boxplot(x=df[col], palette=theme_palette)
        plt.title(f"Outlier Detection: {col}")
        o_name = f"outlier_{uuid.uuid4().hex}.png"
        o_path = os.path.join(plot_folder, o_name)
        plt.savefig(o_path, bbox_inches="tight")
        plt.close()

        generated_files.append(o_path)
        outlier_plots.append({
            "col": col,
            "path": url_for("static", filename=f"plots/{o_name}")
        })

    # ================= CLEANUP THREADS (PER REQUEST) =================
    threading.Thread(
        target=cleanup_uploaded_file,
        args=(file_path,),
        daemon=True
    ).start()

    threading.Thread(
        target=cleanup_generated_files,
        args=(generated_files,),
        daemon=True
    ).start()

    # ================= RENDER =================
    return render_template(
        "eda.html",
        p_name=project_name,
        shape=shape,
        missing=missing,
        columns_info=columns_info,
        target_type=df[session['target_column']].dtype,
        target_plots=target_plots,
        target_list=target_list,
        target_info=target_info,
        describe_table=describe_table,
        feature_plots=feature_plots,
        bivariate_plots=bivariate_plots,
        target_bivariate=target_bivariate,
        outlier_info=outlier_info,
        outlier_plots=outlier_plots,
        heatmap_url=heatmap_url,
        has_heatmap=True if heatmap_url else False
    )
