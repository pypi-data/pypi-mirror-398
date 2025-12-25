import io
import logging
import tempfile

import ocrmypdf
from pdf2image import convert_from_bytes
from pdf2image.pdf2image import pdfinfo_from_bytes

from rara_digitizer.utils.constants import DESKEW_AND_CLEAN_PDF

logger = logging.getLogger("rara-digitizer")


class PDFToCleanedIMGConverter:
    """
    Handles the pre-processing of objects requiring OCR, including deskewing and cleaning using OCRmyPDF.
    Converts cleaned objects into temporary image files for further processing.
    """

    def __init__(self, **kwargs) -> None:
        """
        Initializes the PDFToCleanedIMGConverter.
        """
        self.deskew_and_clean_pdf = kwargs.get("deskew_and_clean_pdf", DESKEW_AND_CLEAN_PDF)

    def clean_convert_document_to_temp_imgs(self, input_bytes: io.BytesIO) -> list[str]:
        """
        Runs deskewing and cleaning on the PDF/JPG/PNG using OCRmyPDF and saves each page as a temporary image file.

        Parameters
        ----------
        input_bytes : io.BytesIO
            The in-memory bytes of the input PDF or image.

        Returns
        -------
        list[str]
            List of file paths to the saved images.
        """
        if self.deskew_and_clean_pdf:
            input_bytes = self._deskew_and_clean_with_ocrmypdf(input_bytes)
        page_image_paths = self._save_pdf_pages_as_temp_images(input_bytes)
        return page_image_paths

    def _deskew_and_clean_with_ocrmypdf(
        self, input_pdf_bytes: io.BytesIO
    ) -> io.BytesIO:
        """
        Processes the PDF/JPG/PNG file with OCRmyPDF and creates an image-based PDF.

        Parameters
        ----------
        input_pdf_bytes : io.BytesIO
            The in-memory bytes of the input PDF or image.

        Returns
        -------
        io.BytesIO
            The in-memory bytes of the processed PDF.
        """
        input_pdf_bytes.seek(0)
        output_pdf_bytes = io.BytesIO()

        try:
            logger.info("Running OCRmyPDF cleaning without OCR on the in-memory input PDF.")
            ocrmypdf.ocr(
                input_pdf_bytes,
                output_pdf_bytes,
                deskew=True,
                force_ocr=True,
                output_type="pdf",
                clean_final=True,
                progress_bar=False,
                tesseract_timeout=0,
                optimize=0,
            )
            output_pdf_bytes.seek(0)
            return output_pdf_bytes
        except Exception:
            logger.warning(f"OCRmyPDF failed during PDF cleaning. Falling back to rasterization without cleaning.")
            input_pdf_bytes.seek(0)
            return input_pdf_bytes

    def _save_pdf_pages_as_temp_images(self, pdf_bytes: io.BytesIO) -> list[str]:
        """
        Converts the processed PDF to individual image files for each page and saves them as temporary files.

        Parameters
        ----------
        pdf_bytes : io.BytesIO
            The in-memory bytes of the processed PDF.

        Returns
        -------
        list[str]
            A list of file paths to the temporary image files for each page of the PDF.
        """
        pdf_bytes.seek(0)

        info = pdfinfo_from_bytes(pdf_bytes.read())
        n_pages = info["Pages"]

        paths = []

        for page in range(1, n_pages + 1):
            pdf_bytes.seek(0)
            img = convert_from_bytes(
                pdf_bytes.read(),
                dpi=300,
                first_page=page,
                last_page=page
            )[0]

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            img.save(tmp, "PNG")
            tmp.close()
            paths.append(tmp.name)

            logger.info(
                f"Saved temporary image for page {page} at {tmp.name}"
            )

        return paths
