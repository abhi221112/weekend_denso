"""
Seed script – inserts a small dummy JPEG image into
TM_DnhaPart_And_SupplierPart_Mapping.SupplierPartImage
for testing the GET /api/printing/image/{supplier_part} endpoint.

Usage:
    python seed_image_data.py

After running, test with:
    GET /api/printing/image/DM-PART-001
    (Authorization: Bearer <DEMO_USER access_token>)
"""

import sys
import os
import io

sys.path.insert(0, os.path.dirname(__file__))

from app.utils.database import get_db_connection


def create_demo_image(part_name: str, width: int = 200, height: int = 120) -> bytes:
    """Create a small labeled JPEG image for a supplier part."""
    from PIL import Image, ImageDraw

    # Nice blue background
    img = Image.new("RGB", (width, height), color=(0, 102, 204))
    draw = ImageDraw.Draw(img)

    # White border
    draw.rectangle([4, 4, width - 5, height - 5], outline="white", width=2)

    # Part name label
    draw.text((15, 15), "DENSO", fill="white")
    draw.text((15, 35), f"Part: {part_name}", fill="yellow")
    draw.text((15, 55), "Supplier: DEMO", fill="white")
    draw.text((15, 75), "Plant: DM1", fill=(180, 220, 255))
    draw.text((15, 95), "Test Image", fill=(200, 200, 200))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def seed():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("=" * 60)
    print("  SEEDING IMAGE DATA for /api/printing/image/{supplier_part}")
    print("=" * 60)

    parts = [
        "DEMO-PART-001",
        "DEMO-PART-002",
        "DM-PART-001",
        "DM-PART-002",
        "DM-PART-003",
        "DM-PART-005",
        "DM-PART-006",
    ]

    # Also save images as static files for URL-based serving
    static_dir = os.path.join(os.path.dirname(__file__), "static", "images")
    os.makedirs(static_dir, exist_ok=True)

    for part in parts:
        image_bytes = create_demo_image(part)
        print(f"\n  [{part}] Generated JPEG image: {len(image_bytes)} bytes")

        # Save as static file
        filename = f"{part.lower().replace('-', '_')}.jpg"
        filepath = os.path.join(static_dir, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        print(f"  -> Saved static file: static/images/{filename}")

        # Check if the row already exists
        cursor.execute(
            "SELECT COUNT(*) FROM TM_DnhaPart_And_SupplierPart_Mapping "
            "WHERE SupplierCode = ? AND SupplierPart = ?",
            ("DEMO", part),
        )
        row_exists = cursor.fetchone()[0] > 0

        if row_exists:
            # Update the image column
            cursor.execute(
                "UPDATE TM_DnhaPart_And_SupplierPart_Mapping "
                "SET SupplierPartImage = ? "
                "WHERE SupplierCode = ? AND SupplierPart = ?",
                (image_bytes, "DEMO", part),
            )
            print(f"  -> Updated SupplierPartImage for {part}")
        else:
            # Insert full row with image
            cursor.execute(
                """
                INSERT INTO TM_DnhaPart_And_SupplierPart_Mapping
                    (SupplierCode, SupplierPart, DNHAPart, PlantCode,
                     SupplierPartName, SupplierPartImage,
                     CreatedOn, CreatedBy)
                VALUES (?, ?, ?, ?, ?, ?, GETDATE(), 'SEED')
                """,
                ("DEMO", part, f"DNHA-{part}", "DM1",
                 f"Demo {part}", image_bytes),
            )
            print(f"  -> Inserted new row with image for {part}")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("  DONE! Test with:")
    print("    GET /api/printing/image/DM-PART-001")
    print("    Authorization: Bearer <DEMO_USER access_token>")
    print("=" * 60)


if __name__ == "__main__":
    seed()
