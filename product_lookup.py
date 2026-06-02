import requests

def get_product_info(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data.get("status") == 1:
            product = data["product"]
            name = product.get("product_name", "Unknown Product")
            ingredients = [ing.get("text", "") for ing in product.get("ingredients", [])]
            return name, ingredients
        else:
            return None, []
    else:
        return None, []
