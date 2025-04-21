# 📦 Bundler 📦
![Python](https://img.shields.io/badge/Python-blue.svg) ![Flask](https://img.shields.io/badge/Flask-blue.svg) ![Windows](https://img.shields.io/badge/Windows-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg)  
---
A **universal link bundler** for everyday use

---

## 🚀 Features

- **Dynamic Link Rows**  
  Add as many URL + custom‑title pairs as you like with a single click.

- **Metadata Fetching**  
  Automatically grabs title, image, and price (when available).

- **Bundle Manager**  
  On launch, lists all existing bundles in `/bundles/` with **View** & **Edit** actions.

- **Persistent Edits**  
  JSON metadata stored alongside each HTML—edit any bundle any time, even after reboot.

---

## 📦 Installation

### OPTION #1: (preset)

```Download the repo and run the .exe file```

### OPTION #2 (open source)

1. **Clone the repo**  
   ```bash
   git clone https://github.com/BlackPaw21/Bundler.git
   cd Bundler
   ```

2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**  
   ```bash
   python Bundler.py
   ```

---

## 🛠 Usage

1. **Create a bundle**  
   - Enter an optional **Bundle Name**.  
   - Fill in one or more **Link** + **Custom Title** rows.  
   - Click **Generate Bundle**.

2. **Manage bundles**  
   - Scroll down to **Existing Bundles**.  
   - Click **View** to open the generated HTML.  
   - Click **Edit** to tweak URLs or titles (data is pre‑populated).

3. **Share**  
   - Each bundle HTML is stored in `bundles/`.  
   - Simply send to whoever you want and enjoy an offline collection.

---

## 🔒 License

MIT © [BlackPaw](https://github.com/BlackPaw21)  
Feel free to fork, improve, and redistribute!
