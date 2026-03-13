import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import markdown as md

def send_email(subject, body, to_email, smtp_server, smtp_port, smtp_username, smtp_password):
    """
    Sends an email using SMTP with the solution in the body and as a PDF attachment.
    Requires an App Password if using Gmail.
    """
    msg = MIMEMultipart('mixed')
    msg['From'] = smtp_username
    msg['To'] = to_email
    msg['Subject'] = subject

    html_body = md.markdown(body, extensions=['extra', 'nl2br'])

    # Attach plain text + HTML as the email body
    body_part = MIMEMultipart('alternative')
    body_part.attach(MIMEText(body, 'plain'))
    body_part.attach(MIMEText(html_body, 'html'))
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
