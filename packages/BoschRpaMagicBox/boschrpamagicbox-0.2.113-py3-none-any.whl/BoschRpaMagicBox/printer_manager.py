"""
IPP Printing Module v10.0 (Stable Production Edition).

Highlights:
- Removed unstable Orientation logic.
- Uses PyMuPDF (fitz) for zero-config dependency management.
- Guarantees B&W printing via physical rasterization (The "Nuclear Option").

Author: Lv Zhichao (AI Solutions Architect)
"""

import struct
import os
import io
import logging
import requests
from requests_ntlm import HttpNtlmAuth
from typing import Union, Optional

# Third-party dependencies
# pip install pymupdf pillow requests requests_ntlm
import fitz  # PyMuPDF
from PIL import Image

# Setup Logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)


class SimpleIPP:
    """A robust IPP client for direct printing via HTTP/HTTPS."""

    def __init__(self, printer_url: str, service_user_id: str, service_password: Optional[str] = None):
        """Initializes the SimpleIPP client.

        Args:
            printer_url: The URL of the printer.
            service_user_id: Service account username.
            service_password: Service account password.
        """
        if printer_url.startswith("ipp://"):
            self.url = printer_url.replace("ipp://", "http://")
        else:
            self.url = printer_url

        self.service_user_id = service_user_id
        self.service_password = service_password

    def print_job(self,
                  data: Union[str, bytes, io.BytesIO],
                  job_name: str = "RPA_Job",
                  target_user_id: Optional[str] = None,
                  is_color: bool = True) -> bool:
        """Sends a print job to the IPP printer.

        Args:
            data: Input content (File Path, Bytes, or BytesIO).
            job_name: Name of the job in the queue.
            target_user_id: The SSO User ID for job ownership (Delegation).
            is_color: True for Color (Original), False for Forced Grayscale.

        Returns:
            bool: True if successful, False otherwise.
        """

        # 1. Processing
        # If is_color is False, we use rasterization to enforce Grayscale.
        final_pdf_stream = self._prepare_content(data, is_color)

        if not final_pdf_stream:
            return False

        # 2. Ownership
        final_owner = target_user_id if target_user_id else self.service_user_id

        # 3. Build IPP Packet
        ipp_data = self._build_ipp_request(job_name, final_pdf_stream.getvalue(), final_owner, is_color)

        # 4. Transport
        return self._send_request(ipp_data, final_owner, is_color)

    def _prepare_content(self, data: Union[str, bytes, io.BytesIO], is_color: bool) -> Optional[io.BytesIO]:
        """Prepares content. Triggers rasterization ONLY if B&W is requested."""
        try:
            # Step A: Load Raw Bytes
            raw_bytes = b""
            if isinstance(data, str):
                if not os.path.exists(data):
                    logger.error(f"❌ File not found: {data}")
                    return None
                with open(data, "rb") as f:
                    raw_bytes = f.read()
            elif isinstance(data, io.BytesIO):
                raw_bytes = data.getvalue()
            elif isinstance(data, bytes):
                raw_bytes = data

            if not raw_bytes:
                logger.error("❌ Input data is empty.")
                return None

            # Step B: Check if Image
            try:
                img = Image.open(io.BytesIO(raw_bytes))
                return self._process_single_image(img, is_color)
            except Exception:
                pass  # Not an image, treat as PDF

            # Step C: Handle PDF
            # Logic: If user wants B&W (is_color=False), we MUST rasterize to enforce it.
            # If user wants Color, we pass the original PDF to preserve vector quality/speed.
            if not is_color:
                logger.info("⚙️  Enforcing Grayscale via PyMuPDF Rasterization...")
                return self._rasterize_pdf_with_fitz(raw_bytes)
            else:
                # Color requested -> Pass original file
                return io.BytesIO(raw_bytes)

        except Exception as e:
            logger.exception(f"❌ Preparation Error: {e}")
            return None

    @staticmethod
    def _process_single_image(image: Image.Image, is_color: bool) -> io.BytesIO:
        """Helper to convert raw images to PDF."""
        if not is_color:
            image = image.convert('L')  # Force Grayscale (Physical)
        else:
            if image.mode != 'RGB':
                image = image.convert('RGB')

        output = io.BytesIO()
        image.save(output, "PDF", resolution=150.0)
        output.seek(0)
        return output

    @staticmethod
    def _rasterize_pdf_with_fitz(pdf_bytes: bytes) -> Optional[io.BytesIO]:
        """
        Uses PyMuPDF to render PDF pages to Grayscale Images, then stitches back to PDF.
        This removes all color information physically.
        """
        try:
            doc = fitz.open("pdf", pdf_bytes)
            processed_images = []

            # 1. Render each page to an image
            for page in doc:
                # Matrix(2.0, 2.0) = 144 DPI (Good balance for docs)
                mat = fitz.Matrix(2.0, 2.0)

                # Render directly to Grayscale (csGRAY)
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)

                # Convert to PIL for saving
                img_data = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_data))
                processed_images.append(pil_img)

            doc.close()

            # 2. Stitch back to PDF
            if not processed_images:
                return None

            logger.info(f"   ...Rebuilding PDF from {len(processed_images)} grayscale pages...")
            output_pdf = io.BytesIO()
            processed_images[0].save(
                output_pdf,
                "PDF",
                resolution=150.0,
                save_all=True,
                append_images=processed_images[1:]
            )
            output_pdf.seek(0)
            return output_pdf

        except Exception as e:
            logger.error(f"❌ PyMuPDF Error: {e}")
            return None

    def _build_ipp_request(self, job_name: str, content: bytes, requesting_user_name: str, is_color: bool) -> bytes:
        """Constructs the IPP v1.1 binary packet."""
        version = b'\x01\x01'
        operation_id = b'\x00\x02'
        request_id = b'\x00\x00\x00\x01'
        start_attr = b'\x01'
        end_attr = b'\x03'

        def add_attr(tag: int, name: str, value: str) -> bytes:
            if isinstance(value, str):
                value = value.encode('utf-8')
            return (struct.pack('!b', tag) + struct.pack('!h', len(name)) +
                    name.encode('utf-8') + struct.pack('!h', len(value)) + value)

        attributes = b''
        attributes += add_attr(0x47, 'attributes-charset', 'utf-8')
        attributes += add_attr(0x48, 'attributes-natural-language', 'en-us')
        attributes += add_attr(0x45, 'printer-uri', self.url)
        attributes += add_attr(0x42, 'requesting-user-name', requesting_user_name)
        attributes += add_attr(0x42, 'job-name', job_name)

        # Color Tags (Backup insurance, though content is already physically BW)
        color_val = 'color' if is_color else 'monochrome'
        attributes += add_attr(0x44, 'print-color-mode', color_val)
        attributes += add_attr(0x44, 'output-mode', color_val)

        return version + operation_id + request_id + start_attr + attributes + end_attr + content

    def _send_request(self, ipp_data: bytes, owner: str, is_color: bool) -> bool:
        """Sends the HTTP Request."""
        auth_obj = None
        if self.service_password:
            auth_obj = HttpNtlmAuth(self.service_user_id, self.service_password)

        mode_str = "Color" if is_color else "Mono"
        logger.info(f"🖨️  Sending Job | Owner: {owner} | Settings: {mode_str}")

        try:
            # Increased timeout for rasterized files
            response = requests.post(
                self.url,
                data=ipp_data,
                headers={"Content-Type": "application/ipp"},
                auth=auth_obj,
                verify=False,
                timeout=120
            )

            if response.status_code == 200:
                logger.info("✅ Job queued successfully.")
                return True
            else:
                logger.error(f"❌ Failed. HTTP Status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Network Exception: {e}")
            return False
