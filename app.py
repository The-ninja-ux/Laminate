## Streamlit-Compatible Laminate Cutting Optimizer

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from rectpack import newPacker
import os
import re
import tempfile
import base64

# === Streamlit Config ===
st.set_page_config(layout="wide")
st.title("🎨 Laminate Cutting Optimizer")
st.sidebar.header("Laminate Inputs")

kerf = 3
laminate_config = {}

# === Input Panel ===
laminate_code = st.sidebar.text_input("Laminate Code", "HGS-WHITE")
sheet_width = st.sidebar.number_input("Sheet Width (mm)", min_value=100, value=1220)
sheet_height = st.sidebar.number_input("Sheet Height (mm)", min_value=100, value=2440)
panels_input = st.sidebar.text_area("Enter panel sizes (Length x Breadth x Qty, one per line)",
    "450x600x2\n300 x 1200 x 3\n750x400x4\n900x500x1")

if st.sidebar.button("Generate Cutting Plan"):
    raw_lines = panels_input.strip().splitlines()
    pieces = []
    for line in raw_lines:
        match = re.match(r"\s*(\d+)\s*[xX]\s*(\d+)\s*[xX\s]*([0-9]*)\s*", line)
        if match:
            w, h = int(match.group(1)), int(match.group(2))
            qty = int(match.group(3)) if match.group(3) else 1
            pieces.append((w, h, qty))

    if not pieces:
        st.error("No valid panel sizes found. Please check your input format.")
        st.stop()

    laminate_config[laminate_code] = {
        "color": "#ffe4e1",
        "sheet_width": sheet_width,
        "sheet_height": sheet_height,
        "pieces": pieces
    }

    styles = getSampleStyleSheet()
    story = []
    sheets_summary = []

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "Laminate_Cutting_Plan.pdf")

        for code, config in laminate_config.items():
            color = config["color"]
            sw, sh = config["sheet_width"], config["sheet_height"]
            piece_list = config["pieces"]

            packer = newPacker(mode=1, bin_algo=2, rotation=False)
            for i, (w, h, qty) in enumerate(piece_list):
                for _ in range(qty):
                    packer.add_rect(w + kerf, h + kerf, rid=i)
            for _ in range(100):
                packer.add_bin(sw, sh)
            packer.pack()

            for sheet_id, abin in enumerate(packer):
                fig, ax = plt.subplots(figsize=(6.5, 9))
                ax.set_xlim(0, sw)
                ax.set_ylim(0, sh)
                ax.set_title(f"{code} — Sheet {sheet_id + 1}", fontsize=14)
                ax.set_aspect('equal')
                ax.invert_yaxis()
                ax.set_facecolor("#fdfdfd")

                used_area = 0
                for rect in abin:
                    x, y = rect.x, rect.y
                    w, h = rect.width - kerf, rect.height - kerf
                    panel = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015", edgecolor='black', facecolor=color, lw=1.2)
                    ax.add_patch(panel)
                    ax.text(x + w/2, y + h/2, f"{int(w)}×{int(h)}", fontsize=9, ha='center', va='center')
                    used_area += w * h

                total_area = sw * sh
                waste = total_area - used_area
                waste_pct = (waste / total_area) * 100 if total_area else 0
                ax.text(10, sh - 40, f"Waste: {waste_pct:.2f}%", fontsize=11, color='red')

                img_path = os.path.join(tmpdir, f"{code}_sheet_{sheet_id + 1}.png")
                plt.tight_layout()
                plt.savefig(img_path, dpi=180, bbox_inches='tight')
                plt.close()

                story.append(Paragraph(f"<b>Laminate:</b> {code} — Sheet {sheet_id + 1}", styles["Heading3"]))
                story.append(Paragraph(f"<b>Waste:</b> {waste_pct:.2f}%", styles["Normal"]))
                story.append(Spacer(1, 8))
                story.append(ReportImage(img_path, width=6.5 * inch, height=8.5 * inch))
                story.append(Spacer(1, 12))

                sheets_summary.append((code, sheet_id + 1, f"{waste_pct:.2f}%"))

        doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=20, bottomMargin=20, leftMargin=30, rightMargin=30)
        doc.build(story)

        st.success("✅ Cutting plan generated!")
        st.write("### Summary")
        for lam, sid, waste in sheets_summary:
            st.write(f"• {lam} - Sheet {sid} → Waste: {waste}")

        with open(pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="Laminate_Cutting_Plan.pdf">📥 Download PDF</a>'
            st.markdown(href, unsafe_allow_html=True)




# # Laminate Cutting Plan Streamlit App (Selectable Code + Size)

# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt
# from matplotlib.patches import Rectangle
# from matplotlib.backends.backend_pdf import PdfPages
# from rectpack import newPacker
# from collections import defaultdict
# from io import BytesIO
# import base64
# import tempfile
# import os

# st.set_page_config(layout="wide")
# st.title("🎨 Laminate Cutting Optimizer")
# st.sidebar.header("Laminate Inputs")

# kerf = st.sidebar.number_input("Saw Blade Thickness (Kerf in mm)", min_value=0, max_value=10, value=3)

# # === Standard Sheet Sizes ===
# sheet_options = {
#     "8x4 ft (1220x2440)": (1220, 2440),
#     "6x4 ft (1830x1220)": (1220, 1830),
#     "7x3 ft (2135x915)": (915, 2135)
# }

# num_laminates = st.sidebar.number_input("Number of Laminate Codes", min_value=1, max_value=5, value=2)

# laminate_config = {}
# for i in range(num_laminates):
#     st.sidebar.markdown("---")
#     code = st.sidebar.text_input(f"Laminate Code {i+1}", key=f"code_{i}")
#     sheet_size_label = st.sidebar.selectbox(f"Sheet Size for {code or f'Code {i+1}'}", options=list(sheet_options.keys()), key=f"sheet_{i}")
#     sheet_width, sheet_height = sheet_options[sheet_size_label]
#     panel_input = st.sidebar.text_area(f"Paste panel sizes for {code or f'Code {i+1}'}", key=f"panels_{i}")

#     if code and panel_input.strip():
#         panels = defaultdict(int)
#         for line in panel_input.strip().splitlines():
#             try:
#                 w, h = map(int, line.lower().replace("mm", "").replace("×", "x").split("x"))
#                 panels[(w, h)] += 1
#             except:
#                 continue
#         laminate_config[code] = {
#             "sheet_width": sheet_width,
#             "sheet_height": sheet_height,
#             "pieces": [(w, h, qty) for (w, h), qty in panels.items()]
#         }

# if not laminate_config:
#     st.warning("Please enter at least one laminate code and dimensions.")
#     st.stop()

# # === Process Cutting Plans ===
# temp_dir = tempfile.TemporaryDirectory()
# pdf_path = os.path.join(temp_dir.name, "Laminate_Cutting_Plan.pdf")
# pdf = PdfPages(pdf_path)

# summary_data = []
# image_buffers = []

# for code, config in laminate_config.items():
#     sheet_width = config["sheet_width"]
#     sheet_height = config["sheet_height"]
#     pieces = config["pieces"]

#     rectangles = []
#     original_dims = []
#     for w, h, qty in pieces:
#         for _ in range(qty):
#             rid = len(original_dims)
#             rectangles.append((w + kerf, h + kerf, rid))
#             original_dims.append((w, h))

#     packer = newPacker(rotation=False)
#     for w, h, rid in rectangles:
#         packer.add_rect(w, h, rid)
#     for _ in range(100):
#         packer.add_bin(sheet_width, sheet_height)
#     packer.pack()

#     used_rects = packer.rect_list()
#     sheets = defaultdict(list)
#     for bin_id, x, y, w, h, rid in used_rects:
#         true_w, true_h = w - kerf, h - kerf
#         ow, oh = original_dims[rid]
#         sheets[bin_id].append((x, y, true_w, true_h, ow, oh))

#     for sheet_id, rects in sheets.items():
#         fig, ax = plt.subplots(figsize=(6, 10))
#         ax.set_xlim(0, sheet_width)
#         ax.set_ylim(0, sheet_height)
#         ax.set_aspect('equal')
#         ax.invert_yaxis()
#         ax.set_facecolor("#f5f5f5")

#         used_area = 0
#         for x, y, w, h, ow, oh in rects:
#             ax.add_patch(Rectangle((x, y), w, h, edgecolor='black', facecolor='#add8e6', lw=1.5))
#             ax.text(x + w/2, y + h/2, f"{ow}×{oh}", fontsize=8, ha='center', va='center', bbox=dict(facecolor='white', edgecolor='none', pad=1))
#             used_area += w * h

#         total_area = sheet_width * sheet_height
#         waste = total_area - used_area
#         waste_pct = (waste / total_area) * 100

#         ax.set_title(f"{code} — Sheet {sheet_id + 1} | Waste: {waste_pct:.2f}%")
#         plt.tight_layout()

#         buf = BytesIO()
#         fig.savefig(buf, format='png', bbox_inches='tight')
#         pdf.savefig(fig)
#         plt.close(fig)

#         buf.seek(0)
#         image_buffers.append((code, sheet_id + 1, waste_pct, buf))

#     summary_data.append({
#         "Laminate Code": code,
#         "Total Panels": len(original_dims),
#         "Total Sheets": len(sheets),
#         "Orderable Sheets (+5%)": int(len(sheets) * 1.05 + 0.99),
#         "Waste % (avg)": f"{sum((sheet_width * sheet_height - sum(w * h for _, _, w, h, *_ in s)) / (sheet_width * sheet_height) for s in sheets.values()) / len(sheets):.2f}%" if len(sheets) > 0 else "N/A"
#     })

# pdf.close()

# # === Display Summary ===
# st.markdown("## 🧾 Laminate Cutting Summary")
# st.dataframe(pd.DataFrame(summary_data))

# # === Layouts ===
# st.markdown("## 📐 Sheet Layouts")
# for code in laminate_config.keys():
#     st.markdown(f"### {code}")
#     scroll_html = '<div style="display:flex;overflow-x:auto;">'
#     for c, sid, waste, buf in image_buffers:
#         if c != code:
#             continue
#         encoded = base64.b64encode(buf.getvalue()).decode()
#         scroll_html += f'''
#             <div style="margin-right:20px;text-align:center;">
#                 <img src="data:image/png;base64,{encoded}" width="300"><br>
#                 <b>Sheet {sid} | Waste: {waste:.2f}%</b>
#             </div>
#         '''
#     scroll_html += '</div>'
#     st.markdown(scroll_html, unsafe_allow_html=True)

# # === Download PDF ===
# if os.path.exists(pdf_path):
#     with open(pdf_path, "rb") as f:
#         b64_pdf = base64.b64encode(f.read()).decode()
#         href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="Laminate_Cutting_Plan.pdf">📥 Download PDF</a>'
#         st.markdown(href, unsafe_allow_html=True)
# else:
#     st.warning("PDF not available. Please check if input was valid.")


# st.success("Done! Adjust laminate codes and dimensions to begin.")




