"""
candidate_details.py  —  Candidate detail panel
Now a CTkFrame (embedded in the main window) instead of a CTkToplevel.
Accepts go_back callback to return to the dashboard.
"""

import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tkinter import messagebox

import customtkinter as ctk
import database as db

SMTP_CONFIG = {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "your_gmail@gmail.com",
    "password": "xxxx xxxx xxxx xxxx",
}

DARK_BG      = "#0f1117"
CARD_BG      = "#1a1d27"
CARD_BORDER  = "#2d3548"
ACCENT       = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
TEXT_PRIMARY = "#f1f5f9"
TEXT_MUTED   = "#94a3b8"
TEXT_DIM     = "#64748b"

STATUSES = ["Reviewing", "Active", "Hired", "Rejected"]

STATUS_COLORS = {
    "Active":    ("#14532d", "#4ade80"),
    "Reviewing": ("#1e3a5f", "#60a5fa"),
    "Hired":     ("#3b0764", "#a78bfa"),
    "Rejected":  ("#450a0a", "#f87171"),
}

DEFAULT_BODY = """\
Dear {name},

As Confirmed, your {role} Interview has been scheduled for {time} on {date}. Kindly reply to this email to confirm your attendance.

Please ensure that you join the interview from a quiet and comfortable environment, with a stable internet connection, a laptop, pc or etc. We look forward to speaking with you.

Interview - {role} - {name}
{datetime_label}
Time zone: Asia/Colombo

Google Meet joining info
Video call link: {link}

Thanks and Regards
Piyumika Madhushani
Prostyle Technology (pvt) Ltd.
platinum1, 1st floor, No.1, Bagatale Road, Colombo 03
"""


def _lbl(parent, text, size=12, color=TEXT_PRIMARY, weight="normal"):
    return ctk.CTkLabel(parent, text=text, text_color=color,
                        font=(None, size, weight))


def _entry(parent, placeholder="", **kw):
    return ctk.CTkEntry(parent, placeholder_text=placeholder,
                        fg_color=DARK_BG, border_color=CARD_BORDER,
                        text_color=TEXT_PRIMARY,
                        placeholder_text_color=TEXT_DIM, **kw)


def _section(parent, title):
    """Titled card section."""
    frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=10,
                         border_color=CARD_BORDER, border_width=1)
    frame.pack(fill="x", pady=(0, 12))
    _lbl(frame, title, size=13, weight="bold",
         color=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(12, 6))
    ctk.CTkFrame(frame, height=1, fg_color=CARD_BORDER).pack(
        fill="x", padx=16, pady=(0, 10))
    return frame


class CandidateDetailPanel(ctk.CTkFrame):
    """
    Embedded detail panel — rendered inside the main window.

    Parameters
    ----------
    master   : parent CTkFrame (the detail wrapper in App)
    candidate: dict of candidate data
    refresh  : callback to refresh sidebar stats (stays on detail page)
    go_back  : callback to navigate back to dashboard
    """

    def __init__(self, master, candidate: dict, refresh, go_back):
        super().__init__(master, fg_color=DARK_BG, corner_radius=0)
        self.candidate = candidate
        self.refresh   = refresh
        self.go_back   = go_back

        self._build()

    # ─────────────────────────────────────────────────────────────────────────

    def _build(self):
        # Make self fill its parent completely
        self.pack_propagate(False)

        # Two-column layout: left = profile + meta, right = actions
        cols = ctk.CTkFrame(self, fg_color=DARK_BG)
        cols.pack(fill="both", expand=True, padx=16, pady=12)

        # Column 0: fixed-width left panel, Column 1: expands to fill rest
        cols.grid_columnconfigure(0, weight=0, minsize=260)
        cols.grid_columnconfigure(1, weight=1)
        # Row 0 must expand to fill full height
        cols.grid_rowconfigure(0, weight=1)

        self._build_left(cols)
        self._build_right(cols)

    # ── Left column: profile card ─────────────────────────────────────────────

    def _build_left(self, parent):
        left = ctk.CTkScrollableFrame(parent, fg_color=CARD_BG,
                                      corner_radius=10, width=260,
                                      border_color=CARD_BORDER, border_width=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        c      = self.candidate
        status = c.get("status", "Reviewing")
        bg_col, fg_col = STATUS_COLORS.get(status, ("#1e293b", "#94a3b8"))

        # Avatar
        av_frame = ctk.CTkFrame(left, fg_color="transparent")
        av_frame.pack(pady=(8, 12))
        initials = "".join(w[0].upper() for w in c["full_name"].split()[:2])
        av = ctk.CTkFrame(av_frame, width=72, height=72, corner_radius=36,
                          fg_color="#1e3a5f")
        av.pack()
        av.pack_propagate(False)
        ctk.CTkLabel(av, text=initials, font=(None, 26, "bold"),
                     text_color="#60a5fa").place(relx=.5, rely=.5, anchor="center")

        _lbl(left, c["full_name"], size=16, weight="bold").pack(pady=(4, 0))
        _lbl(left, c["role"], size=13, color="#60a5fa").pack(pady=(2, 8))

        # Status badge
        badge_row = ctk.CTkFrame(left, fg_color="transparent")
        badge_row.pack(pady=(0, 12))
        ctk.CTkLabel(badge_row, text=status, font=(None, 12, "bold"),
                     text_color=fg_col, fg_color=bg_col,
                     corner_radius=12, padx=12, pady=4).pack()

        # Status changer
        status_card = _section(left, "Change Status")
        self._status_menu = ctk.CTkOptionMenu(
            status_card, values=STATUSES,
            fg_color=DARK_BG, button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=CARD_BG,
            text_color=TEXT_PRIMARY,
            command=self._change_status,
        )
        self._status_menu.set(status)
        self._status_menu.pack(fill="x", padx=16, pady=(0, 12))

        # Meta info
        info_card = _section(left, "Contact & Info")
        for ico, key, label in [
            ("✉", "email",      "Email"),
            ("☏", "phone",      "Phone"),
            ("⌖", "location",   "Location"),
            ("◷", "experience", "Experience"),
        ]:
            val = c.get(key, "")
            if key == "experience" and val:
                val = val + " yrs"
            if val:
                row = ctk.CTkFrame(info_card, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=2)
                _lbl(row, ico, size=13, color=TEXT_DIM).pack(side="left")
                _lbl(row, "  " + val, size=12, color=TEXT_MUTED).pack(side="left")
        ctk.CTkFrame(info_card, height=4, fg_color="transparent").pack()

        # Skills
        skills_raw = c.get("skills", "")
        if skills_raw:
            sk_card = _section(left, "Skills")
            tags = ctk.CTkFrame(sk_card, fg_color="transparent")
            tags.pack(fill="x", padx=16, pady=(0, 12))
            for sk in skills_raw.split(","):
                sk = sk.strip()
                if sk:
                    ctk.CTkLabel(tags, text=sk, font=(None, 11),
                                 fg_color="#1e293b", text_color=TEXT_MUTED,
                                 corner_radius=8, padx=7, pady=3).pack(
                                     side="left", padx=(0, 4), pady=2)

        # Notes
        notes = c.get("notes", "")
        if notes:
            n_card = _section(left, "Notes")
            _lbl(n_card, notes, size=12, color=TEXT_MUTED).pack(
                anchor="w", padx=16, pady=(0, 12), wraplength=240)

        # Created at
        date_str = str(c.get("created_at", ""))[:10]
        if date_str:
            _lbl(left, f"Added {date_str}", size=11, color=TEXT_DIM).pack(pady=(4, 0))

    # ── Right column: action panels ───────────────────────────────────────────

    def _build_right(self, parent):
        self._right_scroll = ctk.CTkScrollableFrame(parent, fg_color=DARK_BG,
                                                    corner_radius=0)
        self._right_scroll.grid(row=0, column=1, sticky="nsew", padx=(0, 0))
        self._render_right()

    def _render_right(self):
        for w in self._right_scroll.winfo_children():
            w.destroy()

        if self.candidate.get("status") != "Active":
            ctk.CTkFrame(self._right_scroll, height=80,
                         fg_color="transparent").pack()
            info = ctk.CTkFrame(self._right_scroll, fg_color=CARD_BG,
                                corner_radius=10, border_color=CARD_BORDER,
                                border_width=1)
            info.pack(fill="x", pady=8)
            _lbl(info, "ℹ  Set candidate status to Active to schedule an interview\n"
                       "and send email invitations.",
                 size=13, color=TEXT_MUTED).pack(padx=20, pady=20)
            return

        # ── After-call details ────────────────────────────────────────────────
        after = _section(self._right_scroll, "📞  After Call Notes")

        self._salary = _entry(after, "Expected Salary")
        self._salary.pack(fill="x", padx=16, pady=(0, 8))
        if self.candidate.get("expected_salary"):
            self._salary.insert(0, self.candidate["expected_salary"])

        self._notice = _entry(after, "Notice Period (e.g. 2 weeks)")
        self._notice.pack(fill="x", padx=16, pady=(0, 8))
        if self.candidate.get("notice_period"):
            self._notice.insert(0, self.candidate["notice_period"])

        self._client = _entry(after, "Target Clients")
        self._client.pack(fill="x", padx=16, pady=(0, 8))
        if self.candidate.get("target_clients"):
            self._client.insert(0, self.candidate["target_clients"])

        self._interview_dt = _entry(after, "Interview date/time (YYYY-MM-DD HH:MM)")
        self._interview_dt.pack(fill="x", padx=16, pady=(0, 8))
        iv = self.candidate.get("interview_datetime") or self.candidate.get("interview_date", "")
        if iv:
            self._interview_dt.insert(0, str(iv)[:16])

        _lbl(after, "Comments", size=11, color=TEXT_DIM).pack(
            anchor="w", padx=16, pady=(0, 4))
        self._comment = ctk.CTkTextbox(after, height=90,
                                       fg_color=DARK_BG, border_color=CARD_BORDER,
                                       text_color=TEXT_PRIMARY)
        self._comment.pack(fill="x", padx=16, pady=(0, 12))
        if self.candidate.get("comments"):
            self._comment.insert("1.0", self.candidate["comments"])

        ctk.CTkButton(after, text="Save Notes", command=self._save_notes,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      text_color="#fff", corner_radius=8,
                      width=140).pack(anchor="e", padx=16, pady=(0, 12))

        # ── Schedule & email ──────────────────────────────────────────────────
        schedule = _section(self._right_scroll, "📅  Schedule Interview & Send Email")

        self._date = _entry(schedule, "Interview Date (YYYY-MM-DD)")
        self._date.pack(fill="x", padx=16, pady=(0, 8))

        self._time = _entry(schedule, "Interview Time (e.g. 14:00)")
        self._time.pack(fill="x", padx=16, pady=(0, 8))

        self._mode = ctk.CTkOptionMenu(
            schedule,
            values=["Online – Google Meet", "Online – Zoom",
                    "Online – MS Teams", "In-person", "Phone call"],
            fg_color=DARK_BG, button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=CARD_BG, text_color=TEXT_PRIMARY,
        )
        self._mode.pack(fill="x", padx=16, pady=(0, 8))

        self._link = _entry(schedule, "Meeting link (if online)")
        self._link.pack(fill="x", padx=16, pady=(0, 8))

        self._to_email = _entry(schedule, "Recipient email")
        self._to_email.pack(fill="x", padx=16, pady=(0, 8))
        self._to_email.insert(0, self.candidate.get("email", ""))

        _lbl(schedule, "Email body (editable)", size=11,
             color=TEXT_DIM).pack(anchor="w", padx=16, pady=(0, 4))
        self._email_body = ctk.CTkTextbox(schedule, height=160,
                                          fg_color=DARK_BG, border_color=CARD_BORDER,
                                          text_color=TEXT_PRIMARY)
        self._email_body.pack(fill="x", padx=16, pady=(0, 8))
        self._email_body.insert("1.0", DEFAULT_BODY.format(
            name=self.candidate["full_name"],
            role=self.candidate.get("role", "[Role]"),
            date="[Date e.g. March 25, 2026]",
            time="[Time e.g. 03:30 PM]",
            link="[Meeting Link]",
            datetime_label="[Day, Date · Time – End Time]",
        ))

        # Send button with status label
        send_row = ctk.CTkFrame(schedule, fg_color="transparent")
        send_row.pack(fill="x", padx=16, pady=(0, 12))
        self._send_status = _lbl(send_row, "", size=11, color="#4ade80")
        self._send_status.pack(side="left")
        ctk.CTkButton(send_row, text="Send Interview Email",
                      command=self._send,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      text_color="#fff", corner_radius=8,
                      width=180).pack(side="right")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _change_status(self, new_status: str):
        try:
            db.update_candidate(self.candidate["id"], {"status": new_status})
            self.candidate["status"] = new_status
            self.refresh()
            self._render_right()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_notes(self):
        try:
            db.update_candidate(self.candidate["id"], {
                "expected_salary":    self._salary.get(),
                "notice_period":      self._notice.get(),
                "target_clients":     self._client.get(),
                "interview_datetime": self._interview_dt.get(),
                "comments":           self._comment.get("1.0", "end").strip(),
            })
            self.refresh()
            messagebox.showinfo("Saved", "Notes saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _send(self):
        date = self._date.get().strip()
        time = self._time.get().strip()
        mode = self._mode.get()
        link = self._link.get().strip()
        to   = self._to_email.get().strip()

        if not to:
            messagebox.showerror("Missing", "Recipient email is required.")
            return

        # Build datetime label  e.g. "Wednesday, 25 March · 3:30 – 4:00pm"
        datetime_label = f"{date} · {time}" if (date and time) else (date or time)

        # Regenerate body from template so date/time/link are filled in;
        # if user has manually edited the body, use their version instead.
        raw_body = self._email_body.get("1.0", "end").strip()
        # Check if still contains empty placeholders (unedited preview)
        if "{date}" in raw_body or not raw_body:
            body = DEFAULT_BODY.format(
                name=self.candidate["full_name"],
                role=self.candidate.get("role", ""),
                date=date,
                time=time,
                link=link,
                datetime_label=datetime_label,
            )
        else:
            body = raw_body

        # Persist interview details
        try:
            db.update_candidate(self.candidate["id"], {
                "expected_salary":    self._salary.get(),
                "notice_period":      self._notice.get(),
                "target_clients":     self._client.get(),
                "interview_datetime": f"{date} {time}".strip(),
                "interview_date":     date,
                "interview_time":     time,
                "interview_mode":     mode,
                "comments":           self._comment.get("1.0", "end").strip(),
            })
            self.refresh()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        self._send_status.configure(text="Sending…", text_color="#facc15")
        threading.Thread(
            target=self._smtp, args=(to, body), daemon=True
        ).start()

    def _smtp(self, to: str, body: str):
        try:
            msg = MIMEMultipart()
            msg["From"]    = SMTP_CONFIG["username"]
            msg["To"]      = to
            msg["Subject"] = f"Interview - {self.candidate.get('role', 'Interview')} - {self.candidate['full_name']}"
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as s:
                s.starttls()
                s.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
                s.send_message(msg)

            self.after(0, lambda: self._send_status.configure(
                text="✓ Email sent!", text_color="#4ade80"))
        except Exception as e:
            self.after(0, lambda: self._send_status.configure(
                text=f"✗ {e}", text_color="#f87171"))