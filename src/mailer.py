import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import markdown as md
from datetime import date

# ---------------------------------------------------------------------------
# Inline-styled HTML email template (email clients require inline CSS only)
# ---------------------------------------------------------------------------
_EMAIL_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:32px 0;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#1a1a2e;padding:28px 36px;">
            <p style="margin:0;color:#a5b4fc;font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;">Daily PM Interview Prep</p>
            <h1 style="margin:8px 0 0;color:#ffffff;font-size:20px;font-weight:700;line-height:1.3;">{company}</h1>
            <p style="margin:6px 0 0;color:#818cf8;font-size:13px;">{category}</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:32px 36px;color:#374151;font-size:15px;line-height:1.75;">
            <style>
              /* Scoped heading styles — rendered inline by many clients */
            </style>
            {styled_body}
          </td>
        </tr>

        <!-- Divider -->
        <tr><td style="padding:0 36px;"><hr style="border:none;border-top:1px solid #e5e7eb;margin:0;"></td></tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f8fafc;padding:18px 36px;text-align:center;color:#94a3b8;font-size:12px;line-height:1.6;">
            PM Interview Prep Agent &nbsp;·&nbsp; {today}
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _style_html_body(raw_html: str) -> str:
    """Apply inline styles to markdown-generated HTML tags for email compatibility."""
    replacements = [
        # Headings
        ('<h1>', '<h1 style="color:#4f46e5;font-size:22px;font-weight:700;margin:28px 0 10px;padding-bottom:8px;border-bottom:2px solid #e0e7ff;">'),
        ('<h2>', '<h2 style="color:#4f46e5;font-size:18px;font-weight:700;margin:24px 0 8px;padding-bottom:6px;border-bottom:1px solid #e0e7ff;">'),
        ('<h3>', '<h3 style="color:#1e293b;font-size:15px;font-weight:700;margin:20px 0 6px;">'),
        ('<h4>', '<h4 style="color:#1e293b;font-size:14px;font-weight:600;margin:16px 0 4px;">'),
        # Paragraphs
        ('<p>', '<p style="margin:0 0 14px;">'),
        # Lists
        ('<ul>', '<ul style="margin:0 0 14px;padding-left:24px;">'),
        ('<ol>', '<ol style="margin:0 0 14px;padding-left:24px;">'),
        ('<li>', '<li style="margin-bottom:6px;">'),
        # Blockquotes — callout style
        ('<blockquote>', '<blockquote style="margin:16px 0;padding:12px 16px;background:#eef2ff;border-left:4px solid #4f46e5;border-radius:0 6px 6px 0;color:#3730a3;">'),
        # Code
        ('<code>', '<code style="background:#f1f5f9;color:#be185d;padding:2px 5px;border-radius:4px;font-size:13px;font-family:\'SFMono-Regular\',Consolas,monospace;">'),
        ('<pre>', '<pre style="background:#1e293b;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6;margin:0 0 16px;">'),
        # Strong / em
        ('<strong>', '<strong style="color:#1e293b;">'),
        # Tables
        ('<table>', '<table style="width:100%;border-collapse:collapse;margin:0 0 16px;font-size:14px;">'),
        ('<th>', '<th style="background:#f1f5f9;padding:10px 12px;text-align:left;font-weight:600;color:#374151;border:1px solid #e5e7eb;">'),
        ('<td>', '<td style="padding:10px 12px;border:1px solid #e5e7eb;color:#374151;">'),
        ('<tr>', '<tr style="background:#ffffff;">'),
    ]
    for tag, styled in replacements:
        raw_html = raw_html.replace(tag, styled)
    return raw_html


def send_email(subject, body, to_email, smtp_server, smtp_port, smtp_username, smtp_password):
    """
    Sends an email using SMTP with the solution in the body and as a PDF attachment.
    Requires an App Password if using Gmail.
    """
    msg = MIMEMultipart('mixed')
    msg['From'] = smtp_username
    msg['To'] = to_email
    msg['Subject'] = subject

    # Parse company + category from subject: "Daily PM Question: {company} - {category}"
    company, category = "PM Interview", "General"
    if ": " in subject and " - " in subject:
        try:
            rest = subject.split(": ", 1)[1]
            company, category = rest.split(" - ", 1)
        except ValueError:
            pass

    raw_html = md.markdown(body, extensions=['extra', 'nl2br', 'tables'])
    styled_body = _style_html_body(raw_html)
    html_email = _EMAIL_TEMPLATE.format(
        company=company,
        category=category,
        styled_body=styled_body,
        today=date.today().strftime("%B %d, %Y"),
    )

    # Attach plain text + styled HTML as the email body
    body_part = MIMEMultipart('alternative')
    body_part.attach(MIMEText(body, 'plain'))
    body_part.attach(MIMEText(html_email, 'html'))
    msg.attach(body_part)

    # Attach as PDF for phone-friendly viewing
    try:
        from fpdf import FPDF
        import re

        def _ascii_safe(text):
            replacements = {
                '\u2013': '-', '\u2014': '--', '\u2018': "'", '\u2019': "'",
                '\u201c': '"', '\u201d': '"', '\u2022': '*', '\u2026': '...',
                '\u00a0': ' ',
            }
            for char, sub in replacements.items():
                text = text.replace(char, sub)
            return text.encode('latin-1', errors='replace').decode('latin-1')

        pdf = FPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        W = pdf.w - 30  # page width minus left+right margins

        for line in body.splitlines():
            pdf.set_x(15)
            # Basic markdown heading detection
            if line.startswith("### "):
                pdf.set_font("Helvetica", style="B", size=12)
                pdf.multi_cell(W, 7, _ascii_safe(line[4:]))
                pdf.set_font("Helvetica", size=11)
            elif line.startswith("## "):
                pdf.set_font("Helvetica", style="B", size=14)
                pdf.multi_cell(W, 8, _ascii_safe(line[3:]))
                pdf.set_font("Helvetica", size=11)
            elif line.startswith("# "):
                pdf.set_font("Helvetica", style="B", size=16)
                pdf.multi_cell(W, 10, _ascii_safe(line[2:]))
                pdf.set_font("Helvetica", size=11)
            elif line.strip() == "":
                pdf.ln(4)
            else:
                # Strip inline markdown (bold/italic/code)
                clean = re.sub(r'[*_`]+', '', line)
                clean = _ascii_safe(clean)
                pdf.multi_cell(W, 6, clean)

        pdf_bytes = pdf.output()
        attachment = MIMEBase('application', 'pdf')
        attachment.set_payload(bytes(pdf_bytes))
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename='solution.pdf')
        msg.attach(attachment)
    except ImportError:
        print("fpdf2 not installed — PDF attachment skipped. Run: pip install fpdf2")

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

if __name__ == "__main__":
    pass
