"""
Hotel Management System - Mini Project (Flask + CSV)

The CSV file is the database. It is re-read on EVERY request, so if you
edit hotel_data.csv (in Excel / Notepad) and refresh the browser,
the website shows the changes instantly.
"""
import csv
import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "hotel-mini-project"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "hotel_data.csv")

FIELDS = ["Hotel_ID", "Hotel_Name", "City", "Hotel_Type", "Rating", "Cleanliness",
          "Location", "Service", "Room_Quality", "Food_Quality", "Staff_Behaviour",
          "Value_for_Money", "Amenities", "WiFi", "Room_Service", "Swimming_Pool",
          "Parking", "Breakfast", "Price_Category", "Suitable_For", "Popularity"]

SCORE_FIELDS = ["Cleanliness", "Location", "Service", "Room_Quality", "Food_Quality",
                "Staff_Behaviour", "Value_for_Money", "Amenities", "WiFi",
                "Room_Service", "Swimming_Pool", "Parking", "Breakfast"]


# ---------- CSV helpers ----------
def read_hotels():
    """Read the CSV fresh each time (this is what makes CSV edits show up live)."""
    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        return [row for row in csv.DictReader(f) if row.get("Hotel_ID")]


def write_hotels(hotels):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(hotels)


def next_id(hotels):
    ids = [int(h["Hotel_ID"]) for h in hotels if h["Hotel_ID"].isdigit()]
    return max(ids, default=0) + 1


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------- Routes ----------
@app.route("/")
def index():
    hotels = read_hotels()

    q = request.args.get("q", "").strip().lower()
    city = request.args.get("city", "")
    htype = request.args.get("type", "")
    pop = request.args.get("popularity", "")
    sort = request.args.get("sort", "id")

    cities = sorted({h["City"] for h in hotels})
    types = sorted({h["Hotel_Type"] for h in hotels})

    result = hotels
    if q:
        result = [h for h in result if q in h["Hotel_Name"].lower()
                  or q in h["City"].lower() or q in h["Suitable_For"].lower()]
    if city:
        result = [h for h in result if h["City"] == city]
    if htype:
        result = [h for h in result if h["Hotel_Type"] == htype]
    if pop:
        result = [h for h in result if h["Popularity"] == pop]

    if sort == "rating":
        result = sorted(result, key=lambda h: to_float(h["Rating"]), reverse=True)
    elif sort == "name":
        result = sorted(result, key=lambda h: h["Hotel_Name"].lower())
    else:
        result = sorted(result, key=lambda h: int(h["Hotel_ID"]))

    stats = {
        "total": len(hotels),
        "cities": len(cities),
        "avg_rating": round(sum(to_float(h["Rating"]) for h in hotels) / len(hotels), 2) if hotels else 0,
        "luxury": sum(1 for h in hotels if h["Hotel_Type"] == "Luxury"),
    }
    return render_template("index.html", hotels=result, cities=cities, types=types,
                           stats=stats, args=request.args)


@app.route("/hotel/<hotel_id>")
def detail(hotel_id):
    hotel = next((h for h in read_hotels() if h["Hotel_ID"] == hotel_id), None)
    if not hotel:
        flash("Hotel not found.", "danger")
        return redirect(url_for("index"))
    scores = [(f.replace("_", " "), int(to_float(hotel[f]))) for f in SCORE_FIELDS]
    return render_template("detail.html", h=hotel, scores=scores)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        hotels = read_hotels()
        new = {f: request.form.get(f, "").strip() for f in FIELDS}
        new["Hotel_ID"] = str(next_id(hotels))
        hotels.append(new)
        write_hotels(hotels)
        flash(f"'{new['Hotel_Name']}' added successfully.", "success")
        return redirect(url_for("index"))
    return render_template("form.html", h=None, fields=FIELDS, score_fields=SCORE_FIELDS)


@app.route("/edit/<hotel_id>", methods=["GET", "POST"])
def edit(hotel_id):
    hotels = read_hotels()
    hotel = next((h for h in hotels if h["Hotel_ID"] == hotel_id), None)
    if not hotel:
        flash("Hotel not found.", "danger")
        return redirect(url_for("index"))
    if request.method == "POST":
        for f in FIELDS:
            if f != "Hotel_ID":
                hotel[f] = request.form.get(f, "").strip()
        write_hotels(hotels)
        flash(f"'{hotel['Hotel_Name']}' updated.", "success")
        return redirect(url_for("detail", hotel_id=hotel_id))
    return render_template("form.html", h=hotel, fields=FIELDS, score_fields=SCORE_FIELDS)


@app.route("/delete/<hotel_id>", methods=["POST"])
def delete(hotel_id):
    hotels = read_hotels()
    remaining = [h for h in hotels if h["Hotel_ID"] != hotel_id]
    write_hotels(remaining)
    flash("Hotel deleted.", "warning")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
