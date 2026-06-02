import cv2
from pyzbar.pyzbar import decode
from product_lookup import get_product_info

def scan_barcodes():
    cap = cv2.VideoCapture(0)
    print("📷 Point your camera at a barcode... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        barcodes = decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type

            if barcode_type in ["EAN13", "EAN8", "UPCA", "UPCE"]:
                print(f"Detected {barcode_type}: {barcode_data}")

                name, ingredients = get_product_info(barcode_data)
                if name:
                    print(f"🍫 Product: {name}")
                    print("🧾 Ingredients:")
                    for ing in ingredients:
                        print(f" - {ing}")
                else:
                    print("❌ Product not found in database.")

        cv2.imshow('Barcode Scanner', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    scan_barcodes()
