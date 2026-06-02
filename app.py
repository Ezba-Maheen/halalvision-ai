from flask import Flask, render_template, request
import requests
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)

# Load haram keywords dataset
with open("ingredients.json", "r") as f:
    data = json.load(f)
haram_keywords = [item.lower() for item in data["haram"]]

# Load local test products dataset
if os.path.exists("test_products.json"):
    with open("test_products.json", "r") as f:
        test_data = json.load(f)
        local_products = {p["barcode"]: p for p in test_data["products"]}
else:
    local_products = {}

# Keep track of all scanned products in this session
scanned_products = []

def get_product_info(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    print(f"🔍 Fetching: {url}")
    headers = {"User-Agent": "HalalVisionAI/1.0 (https://127.0.0.1:5000)"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print("📡 Status:", response.status_code)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data["product"]
                name = product.get("product_name", "Unknown Product")
                ingredients = []
                if "ingredients" in product:
                    ingredients = [
                        ing.get("text", "").strip()
                        for ing in product["ingredients"]
                        if ing.get("text")
                    ]
                image = product.get("image_front_url")
                return name, ingredients, image
            else:
                print("❌ Product not found in OpenFoodFacts")
                return None, [], None
        else:
            print("❌ API request failed")
            return None, [], None
    except Exception as e:
        print("❌ Error fetching product:", e)
        return None, [], None

def classify_ingredients(ingredients, haram_keywords):
    classified = []
    for ing in ingredients:
        ing_lower = ing.lower()
        if any(haram in ing_lower for haram in haram_keywords):
            classified.append(("haram", ing))
        else:
            classified.append(("halal", ing))
    return classified

@app.route("/", methods=["GET", "POST"])
def home():
    product_name, classified_ingredients, product_image = None, [], None
    graph_paths = {}

    if request.method == "POST":
        barcode = request.form.get("barcode")
        print("🔎 Barcode entered:", barcode)

        # Try OpenFoodFacts first
        product_name, ingredients, product_image = get_product_info(barcode)

        # If not found, fallback to local dataset
        if not product_name or not ingredients:
            if barcode in local_products:
                product = local_products[barcode]
                product_name = product["name"]
                ingredients = product["ingredients"]
                product_image = product.get("image", None)
                print("📦 Fallback Product:", product_name)
                print("🧾 Ingredients:", ingredients)

        classified_ingredients = classify_ingredients(ingredients, haram_keywords)

        # --- Add product stats to cumulative list ---
        haram_count = sum(1 for ing in ingredients if any(h in ing.lower() for h in haram_keywords))
        halal_ratio = 1 - (haram_count / len(ingredients)) if ingredients else 1

        scanned_products.append({
            "barcode": barcode,
            "name": product_name,
            "haram_count": haram_count,
            "halal_ratio": halal_ratio
        })

        # --- Generate cumulative graphs ---
        if not os.path.exists("static/graphs"):
            os.makedirs("static/graphs")

        df = pd.DataFrame(scanned_products)

        # Pie chart (all scanned products)
        plt.pie([sum(df.haram_count==0), sum(df.haram_count>0)], labels=["Halal","Haram"], autopct='%1.1f%%')
        plt.title("Halal vs Haram (All Scanned)")
        pie_path = "static/graphs/pie.png"
        plt.savefig(pie_path)
        plt.close()

        # Regression plot (all scanned products)
        sns.regplot(x="haram_count", y="halal_ratio", data=df, line_kws={"color":"red"})
        plt.title("Regression: Haram Count vs Halal Ratio (All Scanned)")
        reg_path = "static/graphs/regression.png"
        plt.savefig(reg_path)
        plt.close()

        graph_paths = {"pie": pie_path, "regression": reg_path}

    return render_template(
        "index.html",
        product_name=product_name,
        ingredients=classified_ingredients,
        product_image=product_image,
        graphs=graph_paths
    )

if __name__ == "__main__":
    app.run(debug=True)
