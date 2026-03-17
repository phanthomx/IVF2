# applications/reminder.py
"""
Appointment reminder scheduler.
Runs a background job every 5 minutes.
Finds appointments starting in the 55–65 minute window from now (IST)
and sends a reminder email to the patient — once per appointment.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask_mail import Message

IST = ZoneInfo("Asia/Kolkata")

# Track which appointment IDs have already been reminded this run
# (in-memory set — resets on server restart, which is fine since the
#  time-window check prevents double-sending within a single server session)
_reminded = set()


def send_appointment_reminders(app):
    """
    Called by the scheduler every 5 minutes.
    Queries appointments whose start time falls in [now+55min, now+65min].
    Sends one reminder email per appointment.
    """
    with app.app_context():
        from applications.database import db
        from applications.models import Appointment
        from applications.audit_helper import log_action

        now        = datetime.now(IST).replace(tzinfo=None)
        window_lo  = now + timedelta(minutes=55)
        window_hi  = now + timedelta(minutes=65)

        # Find waiting/in-session appointments in the 1-hour window
        upcoming = Appointment.query.filter(
            Appointment.status.in_(['waiting']),
        ).all()

        reminders_sent = 0

        for appt in upcoming:
            if appt.id in _reminded:
                continue

            appt_dt = datetime.combine(appt.date, appt.start_time)

            if not (window_lo <= appt_dt <= window_hi):
                continue

            patient = appt.patient
            doctor  = appt.doctor

            if not patient or not patient.email:
                continue

            try:
                mail = app.mail
                msg  = Message(
                    subject="⏰ Reminder: Your Ivy Clinic appointment is in 1 hour",
                    recipients=[patient.email],
                    html=_build_email_html(patient, doctor, appt),
                    body=_build_email_text(patient, doctor, appt)
                )
                mail.send(msg)

                _reminded.add(appt.id)
                reminders_sent += 1

                log_action(
                    user_id=patient.id,
                    action=f"Appointment reminder sent to {patient.email} for appointment #{appt.id} at {appt.start_time}",
                    endpoint="scheduler/reminder"
                )

            except Exception as e:
                # Log but don't crash the scheduler
                app.logger.error(f"[Reminder] Failed to send to {patient.email}: {e}")

        if reminders_sent:
            db.session.commit()
            app.logger.info(f"[Reminder] {reminders_sent} reminder(s) sent at {now.strftime('%H:%M')}")


def start_reminder_scheduler(app):
    """
    Call this once after the Flask app is created.
    Starts a background thread that fires every 5 minutes.
    """
    scheduler = BackgroundScheduler(timezone=str(IST))
    scheduler.add_job(
        func=send_appointment_reminders,
        args=[app],
        trigger=IntervalTrigger(minutes=5),
        id="appointment_reminder",
        name="Send 1-hour appointment reminders",
        replace_existing=True,
        max_instances=1       # prevent overlap if a run takes long
    )
    scheduler.start()
    app.logger.info("[Reminder] Scheduler started — checking every 5 minutes.")
    return scheduler


# ── Email templates ────────────────────────────────────────────────────────

def _build_email_html(patient, doctor, appt):
    time_str  = appt.start_time.strftime('%I:%M %p')
    date_str  = appt.date.strftime('%A, %d %B %Y')
    stage_str = appt.stage_at_visit or patient.current_cycle_stage or '—'

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;background:#f0f5f9;font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:#0a7ea4;padding:28px 32px;">
      <div style="font-size:22px;font-weight:700;color:#fff;">Ivy Clinic</div>
      <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:2px;letter-spacing:0.08em;text-transform:uppercase;">IVF &amp; Reproductive Medicine</div>
    </div>

    <!-- Body -->
    <div style="padding:32px;">
      <div style="font-size:28px;margin-bottom:8px;">⏰</div>
      <h2 style="font-size:20px;font-weight:700;color:#1a2535;margin:0 0 6px;">Your appointment is in <span style="color:#0a7ea4;">1 hour</span></h2>
      <p style="font-size:14px;color:#64748b;margin:0 0 24px;">Hi {patient.name.split()[0]}, this is a friendly reminder from Ivy Clinic.</p>

      <!-- Appointment card -->
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-bottom:24px;">
        <table style="width:100%;border-collapse:collapse;">
          <tr>
            <td style="padding:8px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;width:120px;">Date</td>
            <td style="padding:8px 0;font-size:14px;font-weight:600;color:#1a2535;">{date_str}</td>
          </tr>
          <tr>
            <td style="padding:8px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;">Time</td>
            <td style="padding:8px 0;font-size:14px;font-weight:600;color:#0a7ea4;">{time_str}</td>
          </tr>
          <tr>
            <td style="padding:8px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;">Doctor</td>
            <td style="padding:8px 0;font-size:14px;font-weight:600;color:#1a2535;">Dr. {doctor.name}</td>
          </tr>
          <tr>
            <td style="padding:8px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;">Stage</td>
            <td style="padding:8px 0;">
              <span style="background:#eff9fc;color:#0a7ea4;border:1px solid #bae6fd;padding:3px 10px;border-radius:4px;font-size:12px;font-weight:600;">{stage_str}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;">Service ID</td>
            <td style="padding:8px 0;font-size:13px;font-family:monospace;color:#64748b;">{patient.service_id}</td>
          </tr>
        </table>
      </div>

      <p style="font-size:13px;color:#94a3b8;line-height:1.6;">
        Please arrive 10 minutes early. If you need to cancel, you can do so through the patient portal or by contacting the clinic directly.
      </p>
    </div>

    <!-- Footer -->
    <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:16px 32px;text-align:center;">
      <p style="font-size:11px;color:#94a3b8;margin:0;">
        Ivy Clinic &nbsp;·&nbsp; This is an automated reminder. Please do not reply to this email.
      </p>
    </div>
  </div>
</body>
</html>"""


def _build_email_text(patient, doctor, appt):
    """Plain-text fallback for email clients that don't render HTML."""
    time_str = appt.start_time.strftime('%I:%M %p')
    date_str = appt.date.strftime('%A, %d %B %Y')
    return f"""Hi {patient.name},

This is a reminder from Ivy Clinic. Your appointment is in 1 hour.

  Date      : {date_str}
  Time      : {time_str}
  Doctor    : Dr. {doctor.name}
  Stage     : {appt.stage_at_visit or '—'}
  Service ID: {patient.service_id}

Please arrive 10 minutes early.
If you need to cancel, please contact the clinic or use the patient portal.

— Ivy Clinic
"""
