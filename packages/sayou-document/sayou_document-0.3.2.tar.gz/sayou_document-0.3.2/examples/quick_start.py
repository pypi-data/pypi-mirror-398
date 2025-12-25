import logging
import os

from sayou.document.pipeline import DocumentPipeline

logging.basicConfig(level=logging.INFO, format="%(message)s")


def create_dummy_text_image(filename="test_image.png"):
    """Pillow를 사용하여 텍스트가 적힌 더미 이미지를 생성합니다."""
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (400, 100), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((10, 40), "Hello Sayou OCR World!", fill=(0, 0, 0))
        img.save(filename)
        return True
    except ImportError:
        print("Pillow not installed. Skipping image creation.")
        return False


def run_demo():
    print(">>> Initializing Sayou Document Pipeline...")

    pipeline = DocumentPipeline(use_default_ocr=True)
    pipeline.initialize()

    # --- Scenario: Image to Document (Auto Conversion + OCR) ---
    img_path = "examples/image_demo.png"
    if create_dummy_text_image(img_path):
        print(f"\n=== Processing Image: {img_path} ===")

        with open(img_path, "rb") as f:
            file_bytes = f.read()

        try:
            ocr_config = {"engine_path": "", "lang": "kor+eng"}

            # doc = pipeline.run(file_bytes, img_path, ocr=ocr_config)
            doc = pipeline.run(file_bytes, img_path)

            if doc:
                print(f"✅ Parsed Successfully: {doc.file_name}")
                print(f"   Type: {doc.doc_type}")
                print(f"   Pages: {doc.page_count}")

                first_page = doc.pages[0]
                if first_page.elements:
                    print(f"   Content: {first_page.elements[0].text[:50]}...")

                output_path = f"{img_path}_demo.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(doc.model_dump_json(indent=2))
                print(f"   Saved to {output_path}")
            else:
                print("❌ Parsing returned None.")

        except Exception as e:
            print(f"❌ Error during processing: {e}")

        if os.path.exists(img_path):
            os.remove(img_path)


if __name__ == "__main__":
    run_demo()
