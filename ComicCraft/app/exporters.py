from pathlib import Path

from fpdf import FPDF

from .config import EXPORTS_DIR, PANELS_DIR
from .utils import slugify, unique_id


def _pdf_text(value: str) -> str:
	return value.encode("latin-1", "replace").decode("latin-1")


def save_pdf(
	layout: list[dict],
	title: str,
) -> tuple[str, str]:
	filename = f"{slugify(title)}_{unique_id()}.pdf"
	output_path = EXPORTS_DIR / filename

	pdf = FPDF()
	pdf.set_auto_page_break(auto=True, margin=14)

	for panel in layout:
		pdf.add_page()
		pdf.set_font("Helvetica", "B", 18)
		pdf.multi_cell(0, 10, _pdf_text(title), align="C")
		pdf.ln(3)

		pdf.set_font("Helvetica", "B", 14)
		pdf.multi_cell(
			0,
			8,
			_pdf_text(
				f"Panel {panel['panel_number']}: {panel['title']}"
			),
		)

		image_path = PANELS_DIR / Path(panel["image_path"]).name
		if not image_path.is_file():
			raise FileNotFoundError(
				f"Comic panel image not found: {image_path.name}"
			)

		image_size = 150
		image_x = (pdf.w - image_size) / 2
		pdf.image(
			str(image_path),
			x=image_x,
			w=image_size,
			h=image_size,
		)
		pdf.ln(5)

		for label, key in (
			("Scene", "scene_description"),
			("Caption", "caption"),
			("Narration", "narration"),
			("Dialogue", "dialogue"),
		):
			text = panel.get(key)
			if text:
				pdf.set_font("Helvetica", "B", 11)
				pdf.write(6, f"{label}: ")
				pdf.set_font("Helvetica", size=11)
				pdf.multi_cell(0, 6, _pdf_text(str(text)))

	pdf.output(str(output_path))
	return filename, f"/download/{filename}"
