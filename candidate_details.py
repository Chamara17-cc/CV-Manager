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

DARK_BG = "#0f1117"
CARD_BG = "#1a1d27"
TEXT_MUTED = "#94a3b8"
TEXT_PRIMARY = "#f1f5f9"

STATUSES = ["Reviewing", "Active", "Hired", "Rejected"]

DEFAULT_BODY = """\
Dear {name},

Interview Details:
Date : {date}
Time : {time}
Mode : {mode}
Link : {link}

Regards,
ProStyle Technologies
"""

def _lbl(p, t, size=12, color=TEXT_PRIMARY):
    return ctk.CTkLabel(p, text=t, text_color=color, font=(None, size))


class CandidateDetailPanel(ctk.CTkToplevel):

    def __init__(self, master, candidate, refresh):
        super().__init__(master)
        self.candidate = candidate
        self.refresh = refresh

        self.geometry("850x650")
        self.configure(fg_color=DARK_BG)

        self._build()

    def _build(self):
        main = ctk.CTkFrame(self, fg_color=DARK_BG)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Profile
        profile = ctk.CTkFrame(main, fg_color=CARD_BG)
        profile.pack(fill="x", pady=10)

        _lbl(profile, self.candidate["full_name"], 16).pack(anchor="w", padx=10)
        _lbl(profile, self.candidate["email"], 12, TEXT_MUTED).pack(anchor="w", padx=10)

        self.status = ctk.CTkOptionMenu(profile, values=STATUSES,
                                        command=self._change_status)
        self.status.set(self.candidate.get("status", "Reviewing"))
        self.status.pack(padx=10, pady=10)

        self.body = ctk.CTkScrollableFrame(main, fg_color=CARD_BG)
        self.body.pack(fill="both", expand=True)

        self._render()

    def _render(self):
        for w in self.body.winfo_children():
            w.destroy()

        if self.candidate.get("status") != "Active":
            _lbl(self.body, "Set Active to proceed").pack(pady=50)
            return

        wrapper = ctk.CTkFrame(self.body, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        # ── AFTER CALL ─────────────────────────
        after = ctk.CTkFrame(wrapper, fg_color="#111827")
        after.pack(fill="x", pady=10)

        _lbl(after, "After Call Details", 14).pack(anchor="w", padx=10)

        self.salary = ctk.CTkEntry(after, placeholder_text="Expected Salary")
        self.salary.pack(fill="x", padx=10, pady=5)

        self.notice = ctk.CTkEntry(after, placeholder_text="Notice Period")
        self.notice.pack(fill="x", padx=10, pady=5)

        self.client = ctk.CTkEntry(after, placeholder_text="Target Clients")
        self.client.pack(fill="x", padx=10, pady=5)

        self.interview_dt = ctk.CTkEntry(after, placeholder_text="YYYY-MM-DD HH:MM")
        self.interview_dt.pack(fill="x", padx=10, pady=5)

        self.comment = ctk.CTkTextbox(after, height=80)
        self.comment.pack(fill="x", padx=10, pady=5)

        # ── SCHEDULE ─────────────────────────
        schedule = ctk.CTkFrame(wrapper)
        schedule.pack(fill="x", pady=10)

        _lbl(schedule, "Schedule Interview", 14).pack(anchor="w", padx=10)

        self.date = ctk.CTkEntry(schedule, placeholder_text="Date")
        self.date.pack(fill="x", padx=10, pady=5)

        self.time = ctk.CTkEntry(schedule, placeholder_text="Time")
        self.time.pack(fill="x", padx=10, pady=5)

        self.mode = ctk.CTkOptionMenu(schedule, values=["Online", "In-person"])
        self.mode.pack(fill="x", padx=10, pady=5)

        self.link = ctk.CTkEntry(schedule, placeholder_text="Meet Link")
        self.link.pack(fill="x", padx=10, pady=5)

        self.email = ctk.CTkEntry(schedule)
        self.email.insert(0, self.candidate["email"])
        self.email.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(schedule, text="Send Email",
                      command=self._send).pack(pady=10)

    def _change_status(self, s):
        db.update_candidate(self.candidate["id"], {"status": s})
        self.candidate["status"] = s
        self.refresh()
        self._render()

    def _send(self):
        db.update_candidate(self.candidate["id"], {
            "expected_salary": self.salary.get(),
            "notice_period": self.notice.get(),
            "target_clients": self.client.get(),
            "interview_datetime": self.interview_dt.get(),
            "comments": self.comment.get("1.0", "end"),
        })

        body = DEFAULT_BODY.format(
            name=self.candidate["full_name"],
            date=self.date.get(),
            time=self.time.get(),
            mode=self.mode.get(),
            link=self.link.get()
        )

        threading.Thread(target=self._smtp,
                         args=(self.email.get(), body),
                         daemon=True).start()

    def _smtp(self, to, body):
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_CONFIG["username"]
            msg["To"] = to
            msg["Subject"] = "Interview"

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as s:
                s.starttls()
                s.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
                s.send_message(msg)

            self.after(0, lambda: messagebox.showinfo("Done", "Sent"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))