import requests, random, hashlib, os, numpy as np, json, re, socket
from PIL import Image, ImageOps, ImageDraw, ImageFilter
import urllib3.util.connection as urllib3_cn

def allowed_gai_family(): return socket.AF_INET
urllib3_cn.allowed_gai_family = allowed_gai_family

# --- 🧠 MEMORY ---
MEMORY_FILE = "factory_memory.json"
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f: return json.load(f)
    return {"generation": 1, "old_seed": 442, "word_pool": ["MECHANICAL"]}

def save_memory(gen, seed, pool):
    with open(MEMORY_FILE, 'w') as f:
        json.dump({"generation": gen, "old_seed": seed, "word_pool": pool[-50:]}, f)

# --- 🏭 SOURCES ---
DATA_SOURCES = [
    {"name": "Crypto", "url": "https://api.coingecko.com"},
    {"name": "Weather", "url": "https://api.open-meteo.com"},
    {"name": "Identity", "url": "https://randomuser.me"},
    {"name": "News", "url": "https://hacker-news.firebaseio.com"},
    {"name": "ISS", "url": "http://api.open-notify.org"},
    {"name": "Facts", "url": "https://uselessfacts.jsph.pl"},
    {"name": "Network", "url": "http://ip-api.com"},
    {"name": "Jokes", "url": "https://official-joke-api.appspot.com"},
    {"name": "Insult", "url": "https://evilinsult.com"},
    {"name": "Uni", "url": "http://universities.hipolabs.com"},
    {"name": "Stats", "url": "https://api.genderize.io"},
    {"name": "Nation", "url": "https://api.nationalize.io"},
    {"name": "Bio", "url": "https://dog.ceo"}
]

# --- 🛠️ FLUID TOOLBOX ---

def op_organic_stamp(img, s):
    draw = ImageDraw.Draw(img)
    for _ in range((s % 5) + 2):
        color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        choice = s % 3
        # Use data to pick Ellipses or Triangles instead of just Rectangles
        coords = [random.randint(0,800) for _ in range(4)]
        x0, y0, x1, y1 = min(coords[0], coords[2]), min(coords[1], coords[3]), max(coords[0], coords[2]), max(coords[1], coords[3])
        if choice == 0: draw.ellipse([x0, y0, x1, y1], fill=color)
        elif choice == 1: draw.polygon([(x0,y0), (x1,y1), (x0,y1)], fill=color)
        else: draw.rectangle([x0, y0, x1, y1], fill=color)
    return img

def op_channel_split(img, s):
    # This separates RGB channels and shifts them individually (Chromatic Aberration)
    r, g, b = img.split()
    r = ImageOps.posterize(r, (s % 3) + 1)
    g = ImageChops.offset(g, s % 20, (s*2) % 20)
    return Image.merge("RGB", (r, g, b))

def op_pixel_sort(img, s):
    # "Melting glass" effect - sorts pixels based on their brightness
    a = np.array(img)
    for i in range(0, a.shape[0], max(1, s % 10)):
        row = a[i]
        a[i] = row[row[:, 0].argsort()]
    return Image.fromarray(a)

from PIL import ImageChops # Needed for channel split

def run_factory():
    memory = load_memory()
    old_seed, gen, word_pool = memory['old_seed'], memory['generation'], memory['word_pool']
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. NAME & GHOST HARVEST
    print(f"🏭 SHIFT {gen}...")
    source = random.choice(DATA_SOURCES)
    try: 
        raw = requests.get(source['url'], headers=headers, timeout=5).text
        found = [w for w in re.sub(r'[^a-zA-Z\s]', ' ', raw).split() if 4 < len(w) < 10]
        new_word = random.choice(found).upper() if found else "VOID"
    except: new_word = "STATIC"
    word_pool.append(new_word)
    ghost_word = random.choice(word_pool[:-1]) if len(word_pool) > 1 else "FACTORY"
    locked_name = f"{new_word}-{ghost_word}"
    current_seed = int(hashlib.md5(locked_name.encode()).hexdigest(), 16) % 10000
    
    # 2. CANVAS - Start with a data-gradient, not just a solid color
    img = Image.new('RGB', (800, 800), color=(current_seed % 255, 50, 100))
    
    # 3. PRODUCTION
    random.shuffle(DATA_SOURCES)
    toolbox = [op_organic_stamp, op_channel_split, op_pixel_sort, ImageOps.solarize, ImageOps.invert, ImageFilter.GaussianBlur]

    for i, s in enumerate(DATA_SOURCES):
        try:
            r = requests.get(s['url'], headers=headers, timeout=5).text
            d_val = int(hashlib.md5(r.encode()).hexdigest(), 16) % 1000
        except: d_val = random.randint(0, 1000)

        # THE HAUNTING (Modifier)
        if random.random() > 0.5: d_val += (current_seed % 500)

        op = random.choice(toolbox)
        if op == ImageOps.solarize: img = op(img, threshold=d_val % 255)
        elif op == ImageFilter.GaussianBlur: img = img.filter(op(radius=d_val % 5))
        elif op == ImageOps.invert: img = op(img)
        else: img = op(img, d_val)

    # 4. SAVE
    filename = f"gen{gen}_{locked_name}.png"
    img.save(filename)
    print(f"📦 CRATED: {filename} | HYBRID: {locked_name}")
    save_memory(gen + 1, current_seed + old_seed, word_pool)

if __name__ == "__main__":
    run_factory()
