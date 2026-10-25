import pdfplumber

from app.services.pdf_import.extractors.base import BasePdfExtractor, ExtractedPDFData


class PdfplumberExtractor(BasePdfExtractor):
    def extract(self, file_path: str, password: str | None = None) -> ExtractedPDFData:
        tables: list[list[list[str | None]]] = []
        all_text: list[str] = []
        raw_pages: list[dict] = []

        try:
            pdf = pdfplumber.open(file_path, password=password or None)
        except Exception as e:
            msg = str(e) or "Erro desconhecido ao abrir o PDF (arquivo pode estar corrompido ou protegido)"
            raise RuntimeError(f"Não foi possível abrir o PDF: {msg}")

        try:
            for page in pdf.pages:
                try:
                    text = page.extract_text() or ""
                except Exception as e:
                    text = ""
                    raw_pages.append({
                        "page_number": page.page_number,
                        "width": page.width,
                        "height": page.height,
                        "text": f"[erro ao extrair texto: {e}]",
                        "table_count": 0,
                        "chars": 0,
                    })
                    continue

                all_text.append(text)

                try:
                    page_tables = page.extract_tables()
                except Exception:
                    page_tables = []

                for t in page_tables:
                    tables.append(t)

                raw_pages.append({
                    "page_number": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "text": text,
                    "table_count": len(page_tables),
                    "chars": len(page.chars),
                })

            return ExtractedPDFData(
                text="\n".join(all_text),
                tables=tables,
                pages=len(pdf.pages),
                raw_pages=raw_pages,
            )
        finally:
            pdf.close()

    def extract_tables_only(self, file_path: str) -> list[list[list[str | None]]]:
        tables: list[list[list[str | None]]] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                tables.extend(page_tables)
        return tables

    def extract_text_only(self, file_path: str) -> str:
        texts: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                texts.append(text)
        return "\n".join(texts)
