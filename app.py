"""
app.py  —  CV Manager Desktop App
Built with CustomTkinter + MySQL (via database.py)

Install dependencies:
    pip install customtkinter mysql-connector-python

Run:
    python app.py
"""

import customtkinter as ctk
from tkinter import messagebox
import database as db
from candidate_details import CandidateDetailPanel


# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DARK_BG      = "#0f1117"
CARD_BG      = "#1a1d27"
CARD_BORDER  = "#2d3548"
ACCENT       = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
TEXT_PRIMARY = "#f1f5f9"
TEXT_MUTED   = "#94a3b8"
TEXT_DIM     = "#64748b"

STATUS_COLORS = {
    "Active":    ("#14532d", "#4ade80"),
    "Reviewing": ("#1e3a5f", "#60a5fa"),
    "Hired":     ("#3b0764", "#a78bfa"),
    "Rejected":  ("#450a0a", "#f87171"),
}

STATUSES    = ["Reviewing", "Active", "Hired", "Rejected"]
EXPERIENCES = ["", "0-2", "3-5", "6+"]


# ── Sort helper ───────────────────────────────────────────────────────────────

def sort_candidates(candidates: list) -> list:
    STATUS_RANK = {"Active": 0, "Reviewing": 1, "Hired": 2, "Rejected": 3}

    def _key(c):
        has_interview = bool(
            c.get("interview_date") or c.get("interview_datetime")
        )
        status = c.get("status", "Reviewing")
        if status == "Active" and has_interview:
            group = 0
        elif status == "Active":
            group = 1
        else:
            group = STATUS_RANK.get(status, 9) + 2
        return group

    return sorted(candidates, key=_key)


# ── Helper widgets ────────────────────────────────────────────────────────────

def make_label(parent, text, size=13, weight="normal", color=TEXT_PRIMARY, **kw):
    return ctk.CTkLabel(parent, text=text, font=(None, size, weight),
                        text_color=color, **kw)


def make_entry(parent, placeholder="", width=220, **kw):
    return ctk.CTkEntry(parent, placeholder_text=placeholder, width=width,
                        fg_color=DARK_BG, border_color=CARD_BORDER,
                        text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_DIM,
                        **kw)


def make_combo(parent, values, width=180, **kw):
    return ctk.CTkComboBox(parent, values=values, width=width,
                           fg_color=DARK_BG, border_color=CARD_BORDER,
                           button_color=ACCENT, dropdown_fg_color=CARD_BG,
                           text_color=TEXT_PRIMARY, **kw)


def make_btn(parent, text, command, width=120, color=ACCENT, hover=ACCENT_HOVER, **kw):
    return ctk.CTkButton(parent, text=text, command=command, width=width,
                         fg_color=color, hover_color=hover,
                         text_color="#ffffff", corner_radius=8, **kw)


# ── Add / Edit Form ───────────────────────────────────────────────────────────

class CVForm(ctk.CTkToplevel):
    """Modal window for adding or editing a candidate."""

    def __init__(self, master, on_save, candidate: dict | None = None):
        super().__init__(master)
        self.on_save   = on_save
        self.candidate = candidate
        self.editing   = candidate is not None

        self.title("Edit Candidate" if self.editing else "Add New Candidate")
        self.geometry("520x620")
        self.resizable(False, False)
        self.configure(fg_color=DARK_BG)
        self.grab_set()

        self._build()
        if self.editing:
            self._populate()

    def _row(self, label, widget, parent, pady=(4, 0)):
        make_label(parent, label, size=11, color=TEXT_MUTED).pack(
            anchor="w", padx=24, pady=pady)
        widget.pack(fill="x", padx=24, pady=(2, 8))

    def _build(self):
        make_label(self, "Edit Candidate" if self.editing else "New Candidate",
                   size=17, weight="bold").pack(anchor="w", padx=24, pady=(20, 4))
        make_label(self, "Fill in the candidate details below.", size=12,
                   color=TEXT_MUTED).pack(anchor="w", padx=24, pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(self, fg_color=DARK_BG)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self.e_name     = make_entry(scroll, "Full name *",             width=460)
        self.e_email    = make_entry(scroll, "Email *",                 width=460)
        self.e_phone    = make_entry(scroll, "Phone",                   width=460)
        self.e_role     = make_entry(scroll, "Job role / position *",   width=460)
        self.c_exp      = make_combo(scroll, ["", "0-2", "3-5", "6+"], width=460)
        self.c_status   = make_combo(scroll, STATUSES,                  width=460)
        self.e_location = make_entry(scroll, "Location",                width=460)
        self.e_skills   = make_entry(scroll, "Skills (comma separated)",width=460)
        self.t_notes    = ctk.CTkTextbox(scroll, height=90, width=460,
                                         fg_color=DARK_BG, border_color=CARD_BORDER,
                                         text_color=TEXT_PRIMARY)

        for lbl, wid in [
            ("FULL NAME *",              self.e_name),
            ("EMAIL *",                  self.e_email),
            ("PHONE",                    self.e_phone),
            ("ROLE / POSITION *",        self.e_role),
            ("YEARS OF EXPERIENCE",      self.c_exp),
            ("STATUS",                   self.c_status),
            ("LOCATION",                 self.e_location),
            ("SKILLS (comma separated)", self.e_skills),
            ("NOTES",                    self.t_notes),
        ]:
            self._row(lbl, wid, scroll)

        btn_frame = ctk.CTkFrame(self, fg_color=DARK_BG)
        btn_frame.pack(fill="x", padx=24, pady=12)
        make_btn(btn_frame, "Cancel", self.destroy, color=CARD_BG, hover="#252836").pack(side="left")
        make_btn(btn_frame, "Save",   self._save,   color=ACCENT).pack(side="right")

    def _populate(self):
        c = self.candidate
        self.e_name.insert(0,   c.get("full_name", ""))
        self.e_email.insert(0,  c.get("email", ""))
        self.e_phone.insert(0,  c.get("phone", ""))
        self.e_role.insert(0,   c.get("role", ""))
        self.c_exp.set(          c.get("experience", ""))
        self.c_status.set(       c.get("status", "Reviewing"))
        self.e_location.insert(0,c.get("location", ""))
        self.e_skills.insert(0,  c.get("skills", ""))
        self.t_notes.insert("1.0", c.get("notes", ""))

    def _save(self):
        data = {
            "full_name":  self.e_name.get().strip(),
            "email":      self.e_email.get().strip(),
            "phone":      self.e_phone.get().strip(),
            "role":       self.e_role.get().strip(),
            "experience": self.c_exp.get(),
            "status":     self.c_status.get(),
            "location":   self.e_location.get().strip(),
            "skills":     self.e_skills.get().strip(),
            "notes":      self.t_notes.get("1.0", "end").strip(),
        }
        if not data["full_name"] or not data["email"] or not data["role"]:
            messagebox.showerror("Required fields",
                                 "Name, Email, and Role are required.", parent=self)
            return
        try:
            if self.editing:
                db.update_candidate(self.candidate["id"], data)
            else:
                db.add_candidate(data)
            self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Database error", str(e), parent=self)


# ── Candidate Card ────────────────────────────────────────────────────────────

class CandidateCard(ctk.CTkFrame):
    def __init__(self, parent, candidate: dict, on_refresh, on_open_detail, **kw):
        super().__init__(parent, fg_color=CARD_BG, border_color=CARD_BORDER,
                         border_width=1, corner_radius=12, **kw)
        self.candidate      = candidate
        self.on_refresh     = on_refresh
        self.on_open_detail = on_open_detail
        self._build()

    def _build(self):
        c      = self.candidate
        status = c.get("status", "Reviewing")
        bg_col, fg_col = STATUS_COLORS.get(status, ("#1e293b", "#94a3b8"))

        has_interview = bool(
            c.get("interview_date") or c.get("interview_datetime")
        )
        if has_interview and status == "Active":
            banner = ctk.CTkFrame(self, fg_color="#0f2d1a", corner_radius=0,
                                  height=28)
            banner.pack(fill="x")
            banner.pack_propagate(False)
            ctk.CTkLabel(banner, text="●", font=(None, 10),
                         text_color="#4ade80").pack(side="left", padx=(10, 4))
            interview_val = c.get("interview_date") or c.get("interview_datetime", "")
            date_str = str(interview_val)[:16] if interview_val else ""
            ctk.CTkLabel(banner,
                         text=f"Interview scheduled  {('· ' + date_str) if date_str else ''}",
                         font=(None, 11, "bold"),
                         text_color="#4ade80").pack(side="left")

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 0))

        initials = "".join(w[0].upper() for w in c["full_name"].split()[:2])
        av_color = "#0f2d1a" if (has_interview and status == "Active") else "#1e3a5f"
        av_text  = "#4ade80" if (has_interview and status == "Active") else "#60a5fa"
        av = ctk.CTkFrame(top, width=42, height=42, corner_radius=21,
                          fg_color=av_color)
        av.pack(side="left")
        av.pack_propagate(False)
        ctk.CTkLabel(av, text=initials, font=(None, 14, "bold"),
                     text_color=av_text).place(relx=.5, rely=.5, anchor="center")

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", padx=(10, 0), fill="x", expand=True)
        make_label(info, c["full_name"], size=14, weight="bold").pack(anchor="w")
        make_label(info, c["role"], size=12, color="#60a5fa").pack(anchor="w")

        badge = ctk.CTkLabel(top, text=status, font=(None, 11, "bold"),
                             text_color=fg_col, fg_color=bg_col,
                             corner_radius=10, padx=8, pady=2)
        badge.pack(side="right", anchor="ne")

        meta = ctk.CTkFrame(self, fg_color="transparent")
        meta.pack(fill="x", padx=14, pady=(8, 0))
        for val, ico in [
            (c.get("email", ""),    "✉"),
            (c.get("phone", ""),    "☏"),
            (c.get("location", ""), "⌖"),
            ((c.get("experience", "") + " yrs exp") if c.get("experience") else "", "◷"),
        ]:
            if val:
                row = ctk.CTkFrame(meta, fg_color="transparent")
                row.pack(anchor="w")
                make_label(row, ico + "  " + val, size=12,
                           color=TEXT_MUTED).pack(side="left")

        if has_interview and status == "Active":
            iv_date = c.get("interview_date") or c.get("interview_datetime", "")
            iv_time = c.get("interview_time", "")
            iv_mode = c.get("interview_mode", "")
            parts   = []
            if iv_date: parts.append(str(iv_date)[:10])
            if iv_time: parts.append(str(iv_time))
            if iv_mode: parts.append(iv_mode.split("–")[0].strip())
            if parts:
                iv_row = ctk.CTkFrame(meta, fg_color="transparent")
                iv_row.pack(anchor="w", pady=(2, 0))
                make_label(iv_row, "📅  " + "  ·  ".join(parts),
                           size=12, color="#4ade80").pack(side="left")

        skills_raw = c.get("skills", "")
        if skills_raw:
            tags_frame = ctk.CTkFrame(self, fg_color="transparent")
            tags_frame.pack(fill="x", padx=14, pady=(8, 0))
            for sk in skills_raw.split(",")[:5]:
                sk = sk.strip()
                if sk:
                    ctk.CTkLabel(tags_frame, text=sk, font=(None, 11),
                                 fg_color="#1e293b", text_color=TEXT_MUTED,
                                 corner_radius=8, padx=7, pady=2).pack(
                                     side="left", padx=(0, 4))

        notes = c.get("notes", "")
        if notes:
            preview = notes[:90] + ("..." if len(notes) > 90 else "")
            make_label(self, preview, size=11, color=TEXT_DIM,
                       wraplength=280).pack(anchor="w", padx=14, pady=(6, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(10, 14))

        make_btn(btn_row, "View",   self._open_detail, width=80,
                 color=ACCENT, hover=ACCENT_HOVER).pack(side="left")
        make_btn(btn_row, "Edit",   self._edit,   width=80,
                 color="#1e293b", hover="#252d3d").pack(side="left", padx=(6, 0))
        make_btn(btn_row, "Delete", self._delete, width=80,
                 color="#450a0a", hover="#7f1d1d").pack(side="right")

        date_str = str(c.get("created_at", ""))[:10]
        if date_str:
            make_label(btn_row, date_str, size=11, color=TEXT_DIM).pack(
                side="left", padx=8)

        # Make whole card clickable (opens detail)
        self.bind("<Button-1>", lambda e: self._open_detail())
        for child in self.winfo_children():
            child.bind("<Button-1>", lambda e: self._open_detail())
            for grandchild in child.winfo_children():
                grandchild.bind("<Button-1>", lambda e: self._open_detail())

    def _open_detail(self):
        self.on_open_detail(self.candidate)

    def _edit(self):
        CVForm(self.winfo_toplevel(), self.on_refresh, self.candidate)

    def _delete(self):
        if messagebox.askyesno("Delete",
                               f"Remove {self.candidate['full_name']}?"):
            try:
                db.delete_candidate(self.candidate["id"])
                self.on_refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))


# ── Main App ──────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CV Manager")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=DARK_BG)

        self._check_db()
        self._build_ui()
        self.refresh()

    def _check_db(self):
        try:
            db.get_connection()
        except ConnectionError as e:
            messagebox.showerror(
                "Database connection failed",
                f"{e}\n\nMake sure MySQL is running and update DB_CONFIG in database.py"
            )

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.selected_skills: list[str] = []

        # ── Sidebar ──────────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=CARD_BG,
                                    corner_radius=0, border_width=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        make_label(self.sidebar, "CV Manager", size=18, weight="bold",
                   color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(24, 4))
        make_label(self.sidebar, "Candidate tracker", size=12,
                   color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(0, 16))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=CARD_BORDER).pack(
            fill="x", padx=20, pady=(0, 14))

        make_btn(self.sidebar, "+ Add Candidate",
                 lambda: CVForm(self, self.refresh),
                 width=190, color=ACCENT).pack(padx=20, pady=(0, 18))

        make_label(self.sidebar, "OVERVIEW", size=10, weight="bold",
                   color=TEXT_DIM).pack(anchor="w", padx=20, pady=(0, 6))
        self.stat_total      = self._stat_row("Total CVs",    "0")
        self.stat_scheduled  = self._stat_row("Interviews 📅", "0")
        self.stat_reviewing  = self._stat_row("Reviewing",     "0")
        self.stat_active     = self._stat_row("Active",        "0")
        self.stat_hired      = self._stat_row("Hired",         "0")
        self.stat_rejected   = self._stat_row("Rejected",      "0")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=CARD_BORDER).pack(
            fill="x", padx=20, pady=(14, 10))

        make_label(self.sidebar, "FILTER BY SKILL", size=10, weight="bold",
                   color=TEXT_DIM).pack(anchor="w", padx=20, pady=(0, 6))

        self.skill_search_var = ctk.StringVar()
        self.skill_search_var.trace_add("write", lambda *_: self._render_skill_list())
        ctk.CTkEntry(self.sidebar, placeholder_text="Type a skill...",
                     textvariable=self.skill_search_var, width=190,
                     fg_color=DARK_BG, border_color=CARD_BORDER,
                     text_color=TEXT_PRIMARY,
                     placeholder_text_color=TEXT_DIM).pack(padx=20, pady=(0, 8))

        self.skill_list_frame = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent", height=180)
        self.skill_list_frame.pack(fill="x", padx=12, pady=(0, 6))

        make_label(self.sidebar, "ACTIVE SKILL FILTERS", size=10, weight="bold",
                   color=TEXT_DIM).pack(anchor="w", padx=20, pady=(4, 4))
        self.active_tags_frame = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent", height=60)
        self.active_tags_frame.pack(fill="x", padx=12, pady=(0, 8))

        make_btn(self.sidebar, "Clear skill filters", self._clear_skill_filters,
                 width=190, color=CARD_BG, hover="#252836", height=28).pack(
                     padx=20, pady=(0, 12))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=CARD_BORDER).pack(
            fill="x", padx=20, pady=(0, 10))

        make_label(self.sidebar, "FILTER BY EXPERIENCE", size=10, weight="bold",
                   color=TEXT_DIM).pack(anchor="w", padx=20, pady=(0, 6))

        self.filter_exp = make_combo(self.sidebar, ["All"] + EXPERIENCES[1:], width=190)
        self.filter_exp.set("All")
        self.filter_exp.configure(command=lambda _: self.refresh())
        self.filter_exp.pack(padx=20, pady=(0, 12))

        # ── Main content area (holds dashboard OR detail view) ────────────────
        self.main_container = ctk.CTkFrame(self, fg_color=DARK_BG, corner_radius=0)
        self.main_container.pack(side="right", fill="both", expand=True)

        # Build the dashboard frame (persistent)
        self._build_dashboard()

        # Detail frame placeholder (built on demand)
        self._detail_frame = None

        self._skill_vars: dict[str, ctk.BooleanVar] = {}

    def _build_dashboard(self):
        """Build the dashboard panel (search bar + card grid)."""
        self._dashboard_frame = ctk.CTkFrame(self.main_container,
                                             fg_color=DARK_BG, corner_radius=0)
        self._dashboard_frame.pack(fill="both", expand=True)

        topbar = ctk.CTkFrame(self._dashboard_frame, fg_color=DARK_BG)
        topbar.pack(fill="x", padx=20, pady=(20, 0))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ctk.CTkEntry(topbar, placeholder_text="Search name or role...",
                     textvariable=self.search_var, width=260,
                     fg_color=CARD_BG, border_color=CARD_BORDER,
                     text_color=TEXT_PRIMARY,
                     placeholder_text_color=TEXT_DIM).pack(side="left")

        self.filter_status = make_combo(topbar, ["All statuses"] + STATUSES, width=160)
        self.filter_status.set("All statuses")
        self.filter_status.configure(command=lambda _: self.refresh())
        self.filter_status.pack(side="left", padx=(10, 0))

        make_btn(topbar, "Clear all", self._clear_all_filters,
                 width=90, color=CARD_BG, hover="#252836").pack(
                     side="left", padx=(10, 0))

        self.count_label = make_label(topbar, "", size=12, color=TEXT_DIM)
        self.count_label.pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(self._dashboard_frame,
                                                   fg_color=DARK_BG)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=16)

    def show_detail(self, candidate: dict):
        """Hide dashboard, show candidate detail panel inside main window."""
        # Hide dashboard
        self._dashboard_frame.pack_forget()

        # Destroy previous detail frame if any
        if self._detail_frame is not None:
            self._detail_frame.destroy()

        # Wrapper frame with back button header
        self._detail_frame = ctk.CTkFrame(self.main_container,
                                          fg_color=DARK_BG, corner_radius=0)
        self._detail_frame.pack(fill="both", expand=True)

        # ── Back navigation bar ───────────────────────────────────────────────
        nav = ctk.CTkFrame(self._detail_frame, fg_color=CARD_BG,
                           corner_radius=0, height=52)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        make_btn(nav, "← Back to Dashboard",
                 self.show_dashboard,
                 width=180, color="transparent",
                 hover=CARD_BORDER).pack(side="left", padx=16, pady=10)

        # Breadcrumb
        make_label(nav, "Dashboard", size=12, color=TEXT_DIM).pack(
            side="left", pady=10)
        make_label(nav, "  /  ", size=12, color=TEXT_DIM).pack(
            side="left", pady=10)
        make_label(nav, candidate["full_name"], size=12,
                   color=TEXT_PRIMARY, weight="bold").pack(side="left", pady=10)

        # ── Embed the detail panel (now a CTkFrame, not CTkToplevel) ──────────
        detail = CandidateDetailPanel(
            self._detail_frame,
            candidate,
            refresh=self._refresh_and_back_if_needed,
            go_back=self.show_dashboard,
        )
        detail.pack(fill="both", expand=True)

    def show_dashboard(self):
        """Hide detail panel, show dashboard again."""
        if self._detail_frame is not None:
            self._detail_frame.destroy()
            self._detail_frame = None

        self._dashboard_frame.pack(fill="both", expand=True)
        self.refresh()

    def _refresh_and_back_if_needed(self):
        """Called by detail panel when it needs a data refresh."""
        # Stay on detail — just refresh sidebar stats quietly
        try:
            stats = db.get_stats()
            self.stat_total.configure(text=str(stats["total"]))
            self.stat_reviewing.configure(text=str(stats.get("Reviewing", 0)))
            self.stat_active.configure(text=str(stats.get("Active", 0)))
            self.stat_hired.configure(text=str(stats.get("Hired", 0)))
            self.stat_rejected.configure(text=str(stats.get("Rejected", 0)))
        except Exception:
            pass

    def _stat_row(self, label, value):
        row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=2)
        make_label(row, label, size=12, color=TEXT_MUTED).pack(side="left")
        val_lbl = make_label(row, value, size=12, weight="bold", color=TEXT_PRIMARY)
        val_lbl.pack(side="right")
        return val_lbl

    # ── Skill list rendering ──────────────────────────────────────────────────

    def _render_skill_list(self):
        query = self.skill_search_var.get().lower().strip()
        try:
            all_skills = db.get_all_skills()
        except Exception:
            all_skills = []

        visible = [s for s in all_skills if query in s.lower()] if query else all_skills

        for w in self.skill_list_frame.winfo_children():
            w.destroy()

        if not visible:
            make_label(self.skill_list_frame, "No skills found.", size=11,
                       color=TEXT_DIM).pack(anchor="w", padx=4)
            return

        for skill in visible:
            if skill not in self._skill_vars:
                self._skill_vars[skill] = ctk.BooleanVar(value=False)

            ctk.CTkCheckBox(
                self.skill_list_frame,
                text=skill,
                variable=self._skill_vars[skill],
                command=self._on_skill_toggle,
                font=(None, 12),
                text_color=TEXT_PRIMARY,
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                border_color=CARD_BORDER,
                checkmark_color="#ffffff",
            ).pack(anchor="w", pady=2, padx=4)

    def _on_skill_toggle(self):
        self.selected_skills = [s for s, var in self._skill_vars.items() if var.get()]
        self._render_active_tags()
        self.refresh()

    def _render_active_tags(self):
        for w in self.active_tags_frame.winfo_children():
            w.destroy()

        if not self.selected_skills:
            make_label(self.active_tags_frame, "None selected", size=11,
                       color=TEXT_DIM).pack(anchor="w", padx=4)
            return

        for skill in self.selected_skills:
            pill = ctk.CTkFrame(self.active_tags_frame, fg_color="#1e3a5f",
                                corner_radius=10)
            pill.pack(side="left", padx=(0, 4), pady=2)
            ctk.CTkLabel(pill, text=skill, font=(None, 11),
                         text_color="#60a5fa").pack(side="left", padx=(8, 2), pady=2)
            s = skill
            ctk.CTkButton(pill, text="×", width=18, height=18,
                          font=(None, 12), fg_color="transparent",
                          text_color="#60a5fa", hover_color="#1e3a5f",
                          command=lambda sk=s: self._remove_skill(sk)).pack(
                              side="left", padx=(0, 4))

    def _remove_skill(self, skill: str):
        if skill in self._skill_vars:
            self._skill_vars[skill].set(False)
        self._on_skill_toggle()

    # ── Filter helpers ────────────────────────────────────────────────────────

    def _clear_skill_filters(self):
        for var in self._skill_vars.values():
            var.set(False)
        self.selected_skills = []
        self._render_active_tags()
        self._render_skill_list()
        self.refresh()

    def _clear_all_filters(self):
        self.search_var.set("")
        self.filter_status.set("All statuses")
        self.filter_exp.set("All")
        self._clear_skill_filters()

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        search = self.search_var.get().strip()
        status = self.filter_status.get()
        if status in ("All statuses", "All", ""):
            status = ""
        exp = self.filter_exp.get()
        if exp in ("All", ""):
            exp = ""

        try:
            candidates = db.search_candidates(
                search=search, status=status,
                experience=exp, skills=self.selected_skills,
            )
            stats = db.get_stats()
        except Exception as e:
            messagebox.showerror("Database error", str(e))
            return

        candidates = sort_candidates(candidates)

        self._render_skill_list()
        self._render_active_tags()

        scheduled_count = sum(
            1 for c in candidates
            if c.get("status") == "Active" and
               (c.get("interview_date") or c.get("interview_datetime"))
        )
        self.stat_total.configure(text=str(stats["total"]))
        self.stat_scheduled.configure(text=str(scheduled_count))
        self.stat_reviewing.configure(text=str(stats.get("Reviewing", 0)))
        self.stat_active.configure(text=str(stats.get("Active", 0)))
        self.stat_hired.configure(text=str(stats.get("Hired", 0)))
        self.stat_rejected.configure(text=str(stats.get("Rejected", 0)))

        active_filters = []
        if search:               active_filters.append(f'"{search}"')
        if status:               active_filters.append(status)
        if exp:                  active_filters.append(f"{exp} yrs")
        if self.selected_skills: active_filters.append(", ".join(self.selected_skills))

        n       = len(candidates)
        summary = f"{n} result{'s' if n != 1 else ''}"
        if active_filters:
            summary += "  ·  " + "  ·  ".join(active_filters)
        if scheduled_count:
            summary += f"  ·  {scheduled_count} interview{'s' if scheduled_count != 1 else ''} scheduled"
        self.count_label.configure(text=summary)

        for w in self.scroll_frame.winfo_children():
            w.destroy()

        if not candidates:
            msg = ("No CVs match your filters." if active_filters
                   else "No candidates yet. Click '+ Add Candidate' to get started.")
            make_label(self.scroll_frame, msg, size=14, color=TEXT_DIM).pack(pady=60)
            return

        scheduled   = [c for c in candidates
                       if c.get("status") == "Active"
                       and (c.get("interview_date") or c.get("interview_datetime"))]
        unscheduled = [c for c in candidates if c not in scheduled]

        cols = 3
        row_idx = 0

        if scheduled:
            sec = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            sec.grid(row=row_idx, column=0, columnspan=cols,
                     sticky="w", padx=8, pady=(4, 2))
            ctk.CTkLabel(sec, text="● INTERVIEW SCHEDULED",
                         font=(None, 11, "bold"), text_color="#4ade80").pack(side="left")
            ctk.CTkLabel(sec, text=f"  {len(scheduled)} candidate{'s' if len(scheduled)!=1 else ''}",
                         font=(None, 11), text_color=TEXT_DIM).pack(side="left")
            row_idx += 1

            for i, c in enumerate(scheduled):
                card = CandidateCard(self.scroll_frame, c,
                                     on_refresh=self.refresh,
                                     on_open_detail=self.show_detail)
                card.grid(row=row_idx + i // cols, column=i % cols,
                          padx=8, pady=6, sticky="nsew")
            row_idx += (len(scheduled) + cols - 1) // cols

        if unscheduled:
            if scheduled:
                sep = ctk.CTkFrame(self.scroll_frame, height=1,
                                   fg_color=CARD_BORDER)
                sep.grid(row=row_idx, column=0, columnspan=cols,
                         sticky="ew", padx=8, pady=(8, 6))
                row_idx += 1

            sec2 = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            sec2.grid(row=row_idx, column=0, columnspan=cols,
                      sticky="w", padx=8, pady=(0, 2))
            ctk.CTkLabel(sec2, text="ALL CANDIDATES",
                         font=(None, 11, "bold"), text_color=TEXT_DIM).pack(side="left")
            ctk.CTkLabel(sec2, text=f"  {len(unscheduled)}",
                         font=(None, 11), text_color=TEXT_DIM).pack(side="left")
            row_idx += 1

            for i, c in enumerate(unscheduled):
                card = CandidateCard(self.scroll_frame, c,
                                     on_refresh=self.refresh,
                                     on_open_detail=self.show_detail)
                card.grid(row=row_idx + i // cols, column=i % cols,
                          padx=8, pady=6, sticky="nsew")

        for col in range(cols):
            self.scroll_frame.grid_columnconfigure(col, weight=1)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()