from __future__ import annotations

import os
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox
import tkinter.font as tkfont

import pandas as pd
import joblib
from catboost import CatBoostClassifier

from importlib.resources import files as pkg_files


def _resource_path(*parts: str) -> str:
    # récupère un chemin absolu vers un fichier inclus dans le package
    return str(pkg_files("pof").joinpath(*parts))


def main() -> None:
    # ============================== Config ==============================
    MODEL_PATH = _resource_path("models", "catboost.cbm")
    ISO_VALID_PATH = _resource_path("models", "iso_calibrator_valid.pkl")
    ISO_GLOBAL_PATH = _resource_path("models", "iso_calibrator_global.pkl")
    SCHEMA_PATH = _resource_path("models", "model_schema.pkl")

    THRESHOLD = 0.5  # si tu l’utilises plus tard

    # ============================== Load ==============================
    schema = joblib.load(SCHEMA_PATH)
    FEATURES = schema["features"]
    CAT_COLS = schema["cat_cols"]
    CHOICES = schema["choices"]
    AGE_COL = schema.get("age_col")

    model = CatBoostClassifier()
    model.load_model(MODEL_PATH)

    iso_valid = joblib.load(ISO_VALID_PATH)
    iso_global = joblib.load(ISO_GLOBAL_PATH)

    # ============================== UI =================================
    root = tk.Tk()
    root.title("Fraud Scoring — CatBoost + Isotonic")
    root.geometry("1100x820")
    root.minsize(980, 640)



    # ============================ UI helpers ===========================

    def safe_get(var: tk.StringVar) -> str:
        return (var.get() or "").strip()

    def build_row_from_ui():
        row = {}

        for feat in FEATURES:
            v = safe_get(vars_map[feat])

            if AGE_COL and feat == AGE_COL:
                try:
                    age = int(v)
                except ValueError:
                    raise ValueError("L'âge doit être un nombre entier.")

                if not (16 <= age <= 80):
                    raise ValueError("L'âge doit être compris entre 16 et 80 ans.")

                row[feat] = age
            else:
                row[feat] = v

        return row

    def predict():
        try:
            row = build_row_from_ui()
            X_new = pd.DataFrame([row], columns=FEATURES)

            p_raw = float(model.predict_proba(X_new)[0, 1])

            p_cal_valid  = float(iso_valid.transform([p_raw])[0])
            p_cal_global = float(iso_global.transform([p_raw])[0])


            result_lbl.config(
                text=f"ISO (VALID+TEST)  -> Proba calibrée: {p_cal_global*100:.1f}%"
            )


        except Exception as e:
            messagebox.showerror("Erreur", str(e))


    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


    # ----------- Tech Pro theme (Dauphine blue) -----------
    DEFAULT_FONT_FAMILY = "Segoe UI"
    BASE_SIZE = 14

    # Softer darks (moins “gothique”)
    BG        = "#0e1424"   # background
    PANEL     = "#111a2e"   # sidebar
    CARD      = "#141f38"   # cards
    CARD2     = "#172447"   # action card (un peu plus punchy)

    # Text
    TEXT      = "#e7ecff"   # texte principal (clair)
    MUTED     = "#b7c3e6"   # sous-texte

    # Dauphine
    DAU_BLUE  = "#2f4486"   # officiel (Pantone 7687C)
    DAU_CYAN  = "#5cedff"   # complémentaire charte
    DAU_GRAY  = "#434148"   # complémentaire charte

    ACCENT    = DAU_BLUE
    ACCENT2   = "#3b5bb8"   # hover un poil plus clair
    ACCENT3   = DAU_CYAN    # micro highlight (rare)

    # Status colors
    WARN      = "#fbbf24"
    BAD       = "#fb7185"
    GOOD      = "#34d399"



    root.configure(bg=BG)

    style = ttk.Style(root)
    style.theme_use("clam")

    default_font = tkfont.Font(family=DEFAULT_FONT_FAMILY, size=BASE_SIZE)
    root.option_add("*Font", default_font)

    # Base
    style.configure(".", font=(DEFAULT_FONT_FAMILY, BASE_SIZE), background=BG, foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT)

    # Sidebar / cards
    style.configure("Sidebar.TFrame", background=PANEL)
    style.configure("Card.TFrame", background=CARD, relief="flat")
    style.configure("Card2.TFrame", background=CARD2, relief="flat")

    style.configure("H1.TLabel", font=(DEFAULT_FONT_FAMILY, BASE_SIZE + 10, "bold"),
                    background=PANEL, foreground=TEXT)
    style.configure("H2.TLabel", font=(DEFAULT_FONT_FAMILY, BASE_SIZE + 2, "bold"),
                    background=CARD, foreground=TEXT)
    style.configure("Muted.TLabel", font=(DEFAULT_FONT_FAMILY, BASE_SIZE - 1),
                    foreground=MUTED)

    style.configure("Field.TLabel", background=CARD, foreground=MUTED)
    style.configure("Result.TLabel", font=(DEFAULT_FONT_FAMILY, BASE_SIZE, "bold"),
                    background=CARD, foreground=TEXT)


    # Inputs
    style.configure("TEntry", padding=(10, 8))
    style.configure("TCombobox", padding=(10, 8))



    # Inputs: fond clair + texte foncé (sinon c’est illisible sur blanc)
    style.configure("TEntry",
        padding=(10, 8),
        foreground="#111827",
        fieldbackground="#ffffff",
        insertcolor="#111827"
    )

    style.configure("TCombobox",
        padding=(10, 8),
        foreground="#111827",
        fieldbackground="#ffffff"
    )

    style.map("TCombobox",
        foreground=[("readonly", "#111827")],
        fieldbackground=[("readonly", "#ffffff")]
    )

    style.configure("Primary.TButton", padding=(14, 10), background=ACCENT, foreground="#ffffff")
    style.map("Primary.TButton",
              background=[("active", ACCENT2), ("disabled", "#2a334a")],
              foreground=[("disabled", "#9aa6c9")])

    style.configure("Ghost.TButton", padding=(14, 10), background=PANEL, foreground=TEXT)
    style.map("Ghost.TButton",
              background=[("active", "#1b2746")])

    # ----------- Human labels (optional) -----------
    LABELS = {
        # tu peux compléter petit à petit
        "Days:Policy-Accident": "Jours (police → accident)",
        "Days:Policy-Claim": "Jours (police → déclaration)",
        "PastNumberOfClaims": "Nb sinistres passés",
        "NumberOfSuppliments": "Nb suppléments",
        "AddressChange-Claim": "Changement d’adresse (claim)",
    }

    def nice_label(feat: str) -> str:
        return LABELS.get(feat, feat.replace("_", " "))

    # ----------- Feature grouping (heuristique) -----------
    def group_for(feat: str) -> str:
        f = feat.lower()
        if "vehicle" in f or "car" in f or "price" in f:
            return "Vehicle"
        if "policy" in f or "basepolicy" in f or "deductible" in f:
            return "Policy"
        if "accident" in f or "claim" in f or "witness" in f or "policereport" in f:
            return "Accident / Claim"
        if "age" in f or "sex" in f or "marital" in f or "fault" in f or "agent" in f:
            return "Insured / Agent"
        return "Other"

    # ----------- Logo loader -----------
    def load_logo(path: str, height: int = 34):
        """
        Retourne une PhotoImage (ou None si fichier absent).
        Si Pillow est dispo -> resize propre.
        """
        if not os.path.exists(path):
            return None

        try:
            from PIL import Image, ImageTk
            img = Image.open(path).convert("RGBA")
            w, h = img.size
            new_w = max(1, int(w * (height / h)))
            img = img.resize((new_w, height))
            return ImageTk.PhotoImage(img)
        except Exception:
            try:
                img = tk.PhotoImage(file=path)
                return img
            except Exception:
                return None

    # ========================= Variables UI ============================

    vars_map = {}

    for feat in FEATURES:
        vars_map[feat] = tk.StringVar()

    # valeur par défaut pour l'âge (si défini)
    if AGE_COL and AGE_COL in vars_map:
        vars_map[AGE_COL].set("30")

    # valeurs par défaut pour les catégories
    for feat in CAT_COLS:
        if feat in CHOICES and CHOICES[feat]:
            vars_map[feat].set(CHOICES[feat][0])


    # ----------- Outer layout -----------
    outer = ttk.Frame(root, style="TFrame")
    outer.pack(fill="both", expand=True)

    outer.columnconfigure(0, weight=0)  # sidebar
    outer.columnconfigure(1, weight=1)  # content
    outer.rowconfigure(0, weight=1)

    # Sidebar
    sidebar = ttk.Frame(outer, style="Sidebar.TFrame", padding=18)
    sidebar.grid(row=0, column=0, sticky="nsw")

    # Header in sidebar (logos + title)
    logos_row = ttk.Frame(sidebar, style="Sidebar.TFrame")
    logos_row.pack(fill="x", pady=(0, 14))

    dau_img = load_logo(_resource_path("assets", "dauphine.png"), height=50)
    ag_img = load_logo(_resource_path("assets", "AG.png"), height=80)
    root._ag_img = ag_img


    # IMPORTANT: garder une référence sinon Tkinter “perd” l’image
    root._dau_img = dau_img

    if dau_img:
        ttk.Label(logos_row, image=dau_img, background=PANEL).pack(side="left", padx=(0, 10))
    else:
        ttk.Label(logos_row, text="Dauphine", background=PANEL, foreground=MUTED).pack(side="left", padx=(0, 10))



    ttk.Label(sidebar, text="Fraud Scoring", style="H1.TLabel").pack(anchor="w")
    ttk.Label(sidebar, text="CatBoost • Isotonic Calibration", style="Muted.TLabel",
              background=PANEL).pack(anchor="w", pady=(6, 18))

    # Actions card
    actions = ttk.Frame(sidebar, style="Card2.TFrame", padding=14)
    actions.pack(fill="x", pady=(0, 14))

    ttk.Label(actions, text="Actions", font=(DEFAULT_FONT_FAMILY, BASE_SIZE + 2, "bold"),
              background=CARD2, foreground=TEXT).pack(anchor="w", pady=(0, 10))

    predict_btn = ttk.Button(actions, text="Run prediction", style="Primary.TButton", command=predict)
    predict_btn.pack(fill="x")

    # Quick reset
    def reset_form():
        for feat, var in vars_map.items():
            var.set("")
        if AGE_COL and AGE_COL in vars_map:
            vars_map[AGE_COL].set("30")
        # remettre les defaults des cat cols
        for feat in CAT_COLS:
            if feat in CHOICES and CHOICES[feat]:
                vars_map[feat].set(CHOICES[feat][0])

    ttk.Button(actions, text="Reset inputs", style="Ghost.TButton", command=reset_form).pack(fill="x", pady=(10, 0))

    # Results card (dans sidebar)
    results = ttk.Frame(sidebar, style="Card.TFrame", padding=14)
    results.pack(fill="x", pady=(0, 14))

    ttk.Label(results, text="Results", font=(DEFAULT_FONT_FAMILY, BASE_SIZE + 2, "bold"),
              background=CARD, foreground=TEXT).pack(anchor="w", pady=(0, 10))

    result_lbl = ttk.Label(results, text="ISO (VALID+TEST) -> -", style="Result.TLabel")
    result_lbl.pack(anchor="w", pady=(6, 0))

    # Spacer pour pousser le footer en bas
    ttk.Frame(sidebar, style="Sidebar.TFrame").pack(fill="both", expand=True)

    # Footer (bottom-left)
    footer = ttk.Frame(sidebar, style="Sidebar.TFrame")
    footer.pack(fill="x", side="bottom", pady=(10, 0))

    # Logo AG
    if ag_img:
        ttk.Label(footer, image=ag_img, background=PANEL).pack(side="left")
    else:
        ttk.Label(footer, text="AG Algo Lab", background=PANEL, foreground=MUTED).pack(side="left")

    # Lien cliquable
    def open_details(event=None):
        webbrowser.open("https://ag-algolab.github.io/#/fraud-risk-scoring")

    link = tk.Label(
        footer,
        text="See details",
        fg=DAU_CYAN,
        bg=PANEL,
        cursor="hand2",
        font=(DEFAULT_FONT_FAMILY, BASE_SIZE - 1, "underline")
    )
    link.pack(side="left", padx=(10, 0))
    link.bind("<Button-1>", open_details)


    # Content area (right) — scrollable cards
    content = ttk.Frame(outer, style="TFrame", padding=18)
    content.grid(row=0, column=1, sticky="nsew")
    content.rowconfigure(1, weight=1)
    content.columnconfigure(0, weight=1)

    title_row = ttk.Frame(content, style="TFrame")
    title_row.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    ttk.Label(title_row, text="Questionnaire", font=(DEFAULT_FONT_FAMILY, BASE_SIZE + 8, "bold"),
              background=BG, foreground=TEXT).pack(side="left")

    container = ttk.Frame(content, style="TFrame")
    container.grid(row=1, column=0, sticky="nsew")
    container.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=1)

    canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    scrollable = ttk.Frame(canvas, style="TFrame")
    canvas_window = canvas.create_window((0, 0), window=scrollable, anchor="nw")

    def _resize_canvas(event):
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", _resize_canvas)

    def _on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable.bind("<Configure>", _on_configure)

    def _on_mousewheel(event):
        # Windows
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # mieux: bind uniquement quand la souris est sur la zone scroll
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    # ---- Build cards by group ----
    from collections import defaultdict
    groups = defaultdict(list)
    for feat in FEATURES:
        groups[group_for(feat)].append(feat)

    # ordre “pro” (sinon tri alpha)
    GROUP_ORDER = ["Insured / Agent", "Policy", "Accident / Claim", "Vehicle", "Other"]
    ordered_groups = [g for g in GROUP_ORDER if g in groups] + [g for g in groups if g not in GROUP_ORDER]

    def add_field(parent, r, feat):
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=1)

        lbl = ttk.Label(parent, text=nice_label(feat), style="Field.TLabel")
        lbl.grid(row=r, column=0, sticky="w", padx=(0, 12), pady=6)

        var = vars_map[feat]
        if feat in CAT_COLS:
            w = ttk.Combobox(parent, textvariable=var, values=CHOICES.get(feat, []), state="readonly")
            if CHOICES.get(feat):
                var.set(CHOICES[feat][0])
        else:
            w = ttk.Entry(parent, textvariable=var)

        w.grid(row=r, column=1, sticky="ew", pady=6)
        return w

    row_cursor = 0
    widgets_order = []

    for g in ordered_groups:
        card = ttk.Frame(scrollable, style="Card.TFrame", padding=16)
        card.grid(row=row_cursor, column=0, sticky="ew", pady=(0, 14))
        row_cursor += 1

        ttk.Label(card, text=g, style="H2.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        body = ttk.Frame(card, style="Card.TFrame")
        body.grid(row=1, column=0, columnspan=2, sticky="ew")
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)

        for i, feat in enumerate(groups[g], start=0):
            w = add_field(body, i, feat)
            widgets_order.append(w)

    # Keyboard: Enter = predict ; Tab = normal
    root.bind("<Return>", lambda e: predict())
    root.mainloop()


def run() -> None:
    main()


