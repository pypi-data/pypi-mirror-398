import os
from datetime import datetime
from fpdf import FPDF

# Configuration
VERSION_FILE = "VERSION.txt"
OUTPUT_PATH = r"assets\brand\license_agreement.pdf"
OWNER = "Amatak Holdings Pty Ltd"
CURRENT_YEAR = datetime.now().year

def get_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "1.0.0"

class LicensePDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "SOFTWARE LICENSE AGREEMENT", align="C", ln=True)
        self.ln(5)

    def footer(self):
        self.set_y(-25)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Copyright (c) {CURRENT_YEAR} {OWNER}. All Rights Reserved.", align="C")

def generate_license():
    version = get_version()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    pdf = LicensePDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    
    # 1. Purchase Confirmation
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, f"Product Version: {version}", ln=True)
    pdf.set_font("helvetica", size=11)
    pdf.multi_cell(0, 8, (
        f"By using this version of the software (v{version}), you acknowledge that it has been "
        "duly purchased and licensed for your use. This license applies specifically to the current "
        "version as delivered at the time of purchase."
    ))
    pdf.ln(5)

    # 2. Upgrade Clause (30% Price)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 10, "UPGRADE POLICY", ln=True)
    pdf.set_font("helvetica", size=11)
    pdf.multi_cell(0, 8, (
        "Upon the release of a newer major version of this software, you may be eligible for an "
        "upgrade. If you choose to upgrade, the price will be calculated at thirty percent (30%) "
        "of your original current purchase price. All coverage, terms, and conditions from your "
        "initial version remain in full effect for the upgraded version unless otherwise stated."
    ))
    pdf.ln(5)

    # 3. Support Information
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 10, "SUPPORT & AUTHORIZED SALES", ln=True)
    pdf.set_font("helvetica", size=11)
    pdf.multi_cell(0, 8, (
        f"For any technical support or inquiries, please visit our official website at "
        "www.uniqueedge.net or contact the company authorized with the rights to sell and "
        "distribute this software."
    ))
    pdf.ln(20)

    # 4. Signature Line
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 10, "____________________________________________________________", ln=True)
    pdf.cell(0, 10, f"Signed and Copyright by {OWNER}", ln=True)
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(0, 10, f"Dated: {datetime.now().strftime('%d %B %Y')}", ln=True)

    pdf.output(OUTPUT_PATH)
    print(f"[{CURRENT_YEAR}] License Agreement generated: {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_license()