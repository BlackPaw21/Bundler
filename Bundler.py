from flask import Flask, request, render_template_string, url_for, send_from_directory
import requests, os, time, re, json, threading, webbrowser
from bs4 import BeautifulSoup
import tkinter as tk

app = Flask(__name__)

# Create directory for bundle HTML and JSON files (at project root)
BUNDLE_DIR = os.path.join(os.getcwd(), 'bundles')
os.makedirs(BUNDLE_DIR, exist_ok=True)

def sanitize_filename(filename):
    return re.sub(r'[^A-Za-z0-9_.-]', '_', filename)

def get_price(soup):
    price = None
    for tag in [soup.find("meta", property="product:price:amount"),
                soup.find("meta", property="og:price:amount"),
                soup.find("meta", itemprop="price")]:
        if tag and tag.get("content"):
            price = tag.get("content")
            break
    if not price:
        tag = soup.find("span", id="j-sku-discount-price")
        if tag and tag.text:
            price = tag.text.strip()
    if not price:
        container = soup.find("div", class_="product-price-current")
        if container:
            price = "".join([span.text.strip() for span in container.find_all("span")])
    if price:
        clean = re.sub(r'[^\d\.]', '', price)
        try:
            return float(clean)
        except:
            return None
    return None

def get_metadata(url):
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return {'url': url, 'title': url, 'image': None, 'price': None}
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = soup.find("meta", property="og:title")
        img = soup.find("meta", property="og:image")
        return {
            'url': url,
            'title': title["content"] if title and title.get("content") else url,
            'image': img["content"] if img and img.get("content") else None,
            'price': get_price(soup)
        }
    except:
        return {'url': url, 'title': url, 'image': None, 'price': None}

def build_bundle_html(html_title, products):
    cards = ""
    for p in products:
        price = f"${p['price']:.2f}" if p['price'] is not None else "N/A"
        cards += f"""
        <div class="col-lg-3 col-md-4 col-sm-6 mb-4">
          <div class="card">
            <a href="{p['url']}" target="_blank">
              <img src="{p['image'] or 'https://via.placeholder.com/300x250?text=No+Image'}"
                   class="card-img-top" alt="Thumbnail">
            </a>
            <div class="card-body">
              <p class="card-text">{p['title']}</p>
              <p class="price-text">Price: {price}</p>
            </div>
          </div>
        </div>"""
    return f"""<!DOCTYPE html>
<html><head>
  <meta charset="UTF-8">
  <title>{html_title}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {{ background: linear-gradient(135deg,#2c2f33,#23272a);padding:30px;
           font-family:'Courier New',monospace;color:#fff }}
    .container {{ max-width:1200px;margin:auto }}
    h1 {{ text-align:center;margin-bottom:40px;color:#ff4757 }}
    .card {{ border:none;border-radius:15px;overflow:hidden;
             box-shadow:0 4px 12px rgba(255,71,87,0.3);
             transition:transform .3s,box-shadow .3s;background:#36393f }}
    .card:hover {{ transform:translateY(-5px);
                   box-shadow:0 8px 20px rgba(255,71,87,0.5) }}
    .card-img-top {{ object-fit:cover;height:250px;width:100% }}
    .card-body {{ padding:10px;text-align:center }}
    .card-text {{ margin:0;color:#fff;font-weight:bold }}
    .price-text {{ margin:0;color:#ff4757 }}
  </style>
</head><body>
  <div class="container">
    <h1>{html_title}</h1>
    <div class="row">{cards}
    </div>
  </div>
</body></html>"""

def save_bundle_data(filename, bundle_name, links, titles):
    data = {"bundle_name": bundle_name, "links": links, "titles": titles}
    jf = os.path.join(BUNDLE_DIR, filename.rsplit(".", 1)[0] + ".json")
    with open(jf, "w", encoding="utf-8") as f:
        json.dump(data, f)

@app.route("/shutdown", methods=["POST"])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return "Not running with the Werkzeug Server", 500
    func()
    return "Server shutting down..."

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        links = request.form.getlist("links[]")
        titles = request.form.getlist("titles[]")
        name = request.form.get("bundle_name", "").strip()
        if name:
            fn = sanitize_filename(name) + ".html"
            title = name
        else:
            fn = f"bundle_{int(time.time())}.html"
            title = "My Bundle"
        prods = []
        for u, t in zip(links, titles):
            u = u.strip()
            t = t.strip()
            if not u:
                continue
            md = get_metadata(u)
            prods.append({
                'url': u,
                'title': t or md['title'],
                'image': md['image'],
                'price': md['price']
            })
        html = build_bundle_html(title, prods)
        with open(os.path.join(BUNDLE_DIR, fn), "w", encoding="utf-8") as f:
            f.write(html)
        save_bundle_data(fn, title, links, titles)
        view = url_for('serve_bundle', filename=fn)
        edit = url_for('edit_bundle', filename=fn)
        return render_template_string(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Done</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>body{{background:linear-gradient(135deg,#2c2f33,#23272a);padding:30px;
font-family:'Courier New',monospace;color:#fff}}.btn{{margin:5px}}</style>
</head><body><div class="container text-center">
<h1>Bundle Generated</h1>
<a href="{view}" class="btn btn-success" target="_blank">View</a>
<a href="{edit}" class="btn btn-secondary">Edit</a>
</div></body></html>""")

    files = sorted(f for f in os.listdir(BUNDLE_DIR) if f.endswith(".html"))
    rows = ""
    for f in files:
        v = url_for('serve_bundle', filename=f)
        e = url_for('edit_bundle', filename=f)
        rows += f"<tr><td>{f}</td><td><a href='{v}' class='btn btn-sm btn-success' target='_blank'>View</a> <a href='{e}' class='btn btn-sm btn-secondary'>Edit</a></td></tr>"
    return render_template_string(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Quick Bundle Tool</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body{{background:linear-gradient(135deg,#2c2f33,#23272a);padding:30px;
font-family:'Courier New',monospace;color:#fff}}
.container{{max-width:800px;margin:auto;background:#2f3136;padding:30px;
border-radius:15px;box-shadow:0 4px 12px rgba(255,71,87,0.3)}}
h1,h2{{color:#ff4757;text-align:center}}
label{{font-weight:bold}}
input,textarea{{background:#36393f;color:#fff;border:1px solid #ff4757}}
.link-row{{margin-bottom:15px;padding:15px;border:1px solid #ff4757;border-radius:10px}}
.btn-primary,.btn-danger{{border:none}}
table{{width:100%;margin-top:30px}}
th,td{{color:#fff}}
</style>
</head><body>
<div class="container">
  <h1>Create Bundle</h1>
  <form method="post" id="bundleForm">
    <div class="mb-3">
      <label>Bundle Name (optional):</label>
      <input type="text" class="form-control" name="bundle_name" placeholder="Custom name">
    </div>
    <div id="linkRows">
      <div class="link-row">
        <div class="mb-3">
          <label>Link:</label>
          <input type="text" class="form-control" name="links[]" placeholder="https://example.com">
        </div>
        <div class="mb-3">
          <label>Custom Title (optional):</label>
          <input type="text" class="form-control" name="titles[]" placeholder="Title">
        </div>
      </div>
    </div>
    <div class="text-center mb-3">
      <button type="button" class="btn btn-danger" onclick="addLinkRow()">Add Another Link</button>
    </div>
    <div class="text-center">
      <button type="submit" class="btn btn-primary">Generate Bundle</button>
    </div>
  </form>

  <h2>Existing Bundles</h2>
  <table class="table table-dark table-striped">
    <thead><tr><th>Filename</th><th>Actions</th></tr></thead>
    <tbody>{rows or '<tr><td colspan="2">No bundles yet.</td></tr>'}</tbody>
  </table>
</div>

<script>
function addLinkRow() {{
  const c = document.getElementById('linkRows');
  const r = document.createElement('div');
  r.className='link-row';
  r.innerHTML=`
    <div class="mb-3"><label>Link:</label>
      <input type="text" class="form-control" name="links[]" placeholder="https://example.com"></div>
    <div class="mb-3"><label>Custom Title (optional):</label>
      <input type="text" class="form-control" name="titles[]" placeholder="Title"></div>`;
  c.appendChild(r);
}}
</script>
</body></html>""")

@app.route("/edit", methods=["GET", "POST"])
def edit_bundle():
    if request.method == "POST":
        fn = request.form.get("existing_filename", "").strip()
        links = request.form.getlist("links[]")
        titles = request.form.getlist("titles[]")
        name = request.form.get("bundle_name", "").strip()
        title = name or "My Bundle"
        prods = []
        for u, t in zip(links, titles):
            u = u.strip()
            t = t.strip()
            if not u:
                continue
            md = get_metadata(u)
            prods.append({'url': u, 'title': t or md['title'], 'image': md['image'], 'price': md['price']})
        html = build_bundle_html(title, prods)
        with open(os.path.join(BUNDLE_DIR, fn), "w", encoding="utf-8") as f:
            f.write(html)
        save_bundle_data(fn, title, links, titles)
        view = url_for('serve_bundle', filename=fn)
        return render_template_string(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Updated</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>body{{background:linear-gradient(135deg,#2c2f33,#23272a);padding:30px;
font-family:'Courier New',monospace;color:#fff}}.btn{{margin:5px}}</style>
</head><body><div class="container text-center">
<h1>Bundle Updated</h1>
<a href="{view}" class="btn btn-success" target="_blank">View</a>
</div></body></html>""")

    fn = request.args.get("filename", "").strip()
    jf = os.path.join(BUNDLE_DIR, fn.rsplit(".", 1)[0] + ".json")
    if not os.path.exists(jf):
        return "Bundle data not found."
    data = json.load(open(jf, "r", encoding="utf-8"))
    rows_html = ""
    for u, t in zip(data["links"], data["titles"]):
        rows_html += f"""
        <div class="link-row">
          <div class="mb-3">
            <label>Link:</label>
            <input type="text" class="form-control" name="links[]" value="{u}">
          </div>
          <div class="mb-3">
            <label>Custom Title (optional):</label>
            <input type="text" class="form-control" name="titles[]" value="{t}">
          </div>
        </div>"""
    return render_template_string(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Edit Bundle</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body{{background:linear-gradient(135deg,#2c2f33,#23272a);padding:30px;
font-family:'Courier New',monospace;color:#fff}}
.container{{max-width:600px;margin:auto;background:#2f3136;padding:30px;
border-radius:15px;box-shadow:0 4px 12px rgba(255,71,87,0.3)}}
h1{{color:#ff4757;text-align:center;margin-bottom:30px}}
label{{font-weight:bold}}
input,textarea{{background:#36393f;color:#fff;border:1px solid #ff4757}}
.link-row{{margin-bottom:15px;padding:15px;border:1px solid #ff4757;border-radius:10px}}
.btn-primary,.btn-danger{{border:none}}
</style></head><body>
<div class="container">
  <h1>Edit Bundle</h1>
  <form method="post">
    <div class="mb-3">
      <label>Bundle Name (optional):</label>
      <input type="text" class="form-control" name="bundle_name" value="{data['bundle_name']}">
    </div>
    <input type="hidden" name="existing_filename" value="{fn}">
    <div id="linkRows">{rows_html}</div>
    <div class="text-center mb-3">
      <button type="button" class="btn btn-danger" onclick="addLinkRow()">Add Another Link</button>
    </div>
    <div class="text-center">
      <button type="submit" class="btn btn-primary">Update Bundle</button>
    </div>
  </form>
</div>
<script>
function addLinkRow() {{
  const c = document.getElementById('linkRows');
  const r = document.createElement('div'); r.className='link-row';
  r.innerHTML=`
    <div class="mb-3"><label>Link:</label>
      <input type="text" class="form-control" name="links[]" placeholder="https://example.com"></div>
    <div class="mb-3"><label>Custom Title (optional):</label>
      <input type="text" class="form-control" name="titles[]" placeholder="Title"></div>`;
  c.appendChild(r);
}}
</script>
</body></html>""")

@app.route("/bundles/<filename>")
def serve_bundle(filename):
    return send_from_directory(BUNDLE_DIR, filename)

if __name__ == "__main__":
    # Start Flask server in a background thread
    threading.Thread(target=lambda: app.run(debug=True, use_reloader=False), daemon=True).start()

    # Auto-open the browser
    threading.Timer(1.0, lambda: webbrowser.open_new("http://127.0.0.1:5000/")).start()

    # Popup window via Tkinter
    root = tk.Tk()
    root.title("Bundle Tool Running")
    root.geometry("300x120")
    label = tk.Label(root,
                     text="App is running on chrom!",
                     font=("Courier New", 10),
                     justify="center")
    label.pack(pady=10)
    def on_exit():
        try:
            requests.post("http://127.0.0.1:5000/shutdown")
        except:
            pass
        root.destroy()
    btn = tk.Button(root, text="Exit", command=on_exit, width=10)
    btn.pack(pady=5)
    root.mainloop()
