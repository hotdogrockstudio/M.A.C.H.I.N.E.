import requests, random, hashlib, os, numpy as np, json, re, socket
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageChops
import urllib3.util.connection as urllib3_cn

# Force IPv4 to prevent some API timeout issues
def allowed_gai_family(): return socket.AF_INET
urllib3_cn.allowed_gai_family = allowed_gai_family

# --- ｧ MEMORY ---
MEMORY_FILE = "factory_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f: return json.load(f)
    return {"generation": 1, "old_seed": 442, "word_pool": ["MECHANICAL"]}

def save_memory(gen, seed, pool):
    with open(MEMORY_FILE, 'w') as f:
        json.dump({"generation": gen, "old_seed": seed, "word_pool": pool[-50:]}, f)

# --- 少 SOURCES ---
DATA_SOURCES = [
    {"name": "Crypto", "url": "https://api.coingecko.com/api/v3/ping"}, # fast ping endpoint
    {"name": "Weather", "url": "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true"},
    {"name": "Identity", "url": "https://randomuser.me/api/"},
    {"name": "News", "url": "https://hacker-news.firebaseio.com/v0/topstories.json"},
    {"name": "ISS", "url": "http://api.open-notify.org/iss-now.json"},
    {"name": "Facts", "url": "https://uselessfacts.jsph.pl/random.json?language=en"},
    {"name": "Network", "url": "http://ip-api.com/json"},
    {"name": "Jokes", "url": "https://official-joke-api.appspot.com/random_joke"},
    {"name": "Insult", "url": "https://evilinsult.com/generate_insult.php?lang=en&type=json"},
    {"name": "Uni", "url": "http://universities.hipolabs.com/search?country=United+States"},
    {"name": "Stats", "url": "https://api.genderize.io?name=lucy"},
    {"name": "Nation", "url": "https://api.nationalize.io?name=nathaniel"},
    {"name": "Bio", "url": "https://dog.ceo/api/breeds/image/random"}
]

# --- 屏ｸFLUID TOOLBOX ---

def op_organic_stamp(img, s, raw_data=None):
    draw = ImageDraw.Draw(img)
    for _ in range((s % 5) + 2):
        color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        choice = s % 3
        coords = [random.randint(0,800) for _ in range(4)]
        x0, y0, x1, y1 = min(coords[0], coords[2]), min(coords[1], coords[3]), max(coords[0], coords[2]), max(coords[1], coords[3])
        if choice == 0: draw.ellipse([x0, y0, x1, y1], fill=color)
        elif choice == 1: draw.polygon([(x0,y0), (x1,y1), (x0,y1)], fill=color)
        else: draw.rectangle([x0, y0, x1, y1], fill=color)
    return img

def op_channel_split(img, s, raw_data=None):
    r, g, b = img.split()
    r = ImageOps.posterize(r, (s % 3) + 1)
    g = ImageChops.offset(g, s % 20, (s*2) % 20)
    return Image.merge("RGB", (r, g, b))

def op_pixel_sort(img, s, raw_data=None):
    a = np.array(img)
    # Sort pixels by brightness in intervals
    for i in range(0, a.shape[0], max(1, s % 15)):
        row = a[i]
        a[i] = row[row[:, 0].argsort()]
    return Image.fromarray(a)

def op_text_interference(img, s, raw_data):
    """
    Takes raw data, corrupts it, and stamps it as a chaotic texture.
    """
    if not raw_data: return img
    
    # 1. Harvest & Corrupt Text
    # Clean non-alphanumeric but keep it looking like code
    txt = re.sub(r'[^a-zA-Z0-9]', ' ', raw_data)[:300]
    if len(txt) < 10: txt = "NO_SIGNAL_DETECTED_ERROR_404" * 5
    
    # Randomly convert to Binary or Hex for "Machine Code" look
    # 50% chance to be HEX, 50% chance to be Plain Text
    if random.random() > 0.5:
        # Convert first chunk to Hex
        txt = ' '.join(format(ord(c), 'x') for c in txt[:50]) 
    
    # 2. Create a Text Layer
    # We create a larger temporary layer to allow for rotation without cutting off corners
    temp_size = (1200, 1200)
    txt_layer = Image.new('RGBA', temp_size, (0,0,0,0))
    draw = ImageDraw.Draw(txt_layer)
    
    # 3. Stamp the text repeatedly in a cluster
    # Number of stamps depends on seed 's'
    for _ in range(15 + (s % 25)):
        x = random.randint(100, 1100)
        y = random.randint(100, 1100)
        
        # Random faint color (High transparency 20-100 alpha)
        color = (random.randint(150,255), random.randint(150,255), random.randint(150,255), random.randint(20, 100))
        
        # Grab a random chunk of the corrupted text
        if len(txt) > 20:
            start = random.randint(0, len(txt)-20)
            chunk = txt[start:start+25]
        else:
            chunk = txt
            
        draw.text((x, y), chunk, fill=color)

    # 4. Distort the layer (Rotate)
    angle = random.choice([0, 90, 45, -45, 180, 270])
    txt_layer = txt_layer.rotate(angle)
    
    # 5. Merge with center crop
    # Crop back to 800x800 center
    left = (1200 - 800)/2
    top = (1200 - 800)/2
    txt_layer = txt_layer.crop((left, top, left+800, top+800))
    
    base = img.convert("RGBA")
    return Image.alpha_composite(base, txt_layer).convert("RGB")

def run_factory():
    memory = load_memory()
    old_seed, gen, word_pool = memory['old_seed'], memory['generation'], memory['word_pool']
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. NAME & GHOST HARVEST
    print(f"少 SHIFT {gen} INITIALIZING...")
    
    # Pick a random source to generate the name
    name_source = random.choice(DATA_SOURCES)
    try: 
        raw = requests.get(name_source['url'], headers=headers, timeout=5).text
        found = [w for w in re.sub(r'[^a-zA-Z\s]', ' ', raw).split() if 4 < len(w) < 10]
        new_word = random.choice(found).upper() if found else "VOID"
    except: new_word = "STATIC"
    
    word_pool.append(new_word)
    ghost_word = random.choice(word_pool[:-1]) if len(word_pool) > 1 else "FACTORY"
    locked_name = f"{new_word}-{ghost_word}"
    current_seed = int(hashlib.md5(locked_name.encode()).hexdigest(), 16) % 10000
    
    print(f"板 TARGET ID: {locked_name} | SEED: {current_seed}")
    
    # 2. CANVAS
    # Background color is derived from the seed
    img = Image.new('RGB', (800, 800), color=(current_seed % 50, (current_seed*2) % 50, (current_seed*3) % 50))
    
    # 3. PRODUCTION LINE
    random.shuffle(DATA_SOURCES)
    
    # Toolbox includes the new text interference
    toolbox = [op_organic_stamp, op_channel_split, op_pixel_sort, op_text_interference]

    for i, s in enumerate(DATA_SOURCES):
        # Fetch Data for this layer
        try:
            r_text = requests.get(s['url'], headers=headers, timeout=3).text
            # Create a unique value 'd_val' for this specific layer based on the data content
            d_val = int(hashlib.md5(r_text.encode()).hexdigest(), 16) % 1000
        except: 
            r_text = "CONNECTION_LOST_SIGNAL_DECAY_RETRYING..."
            d_val = random.randint(0, 1000)

        # THE HAUNTING (Modifier)
        if random.random() > 0.5: d_val += (current_seed % 500)

        # Pick a random tool
        op = random.choice(toolbox)
        
        # Apply Logic based on tool type
        if op == op_text_interference:
            # Passes the raw text to be turned into glitch art
            img = op(img, d_val, r_text) 
        elif op == op_organic_stamp or op == op_channel_split or op == op_pixel_sort:
            img = op(img, d_val, r_text)
        
        # Occasional Global Filters (Blur or Solarize) to blend layers
        if random.random() > 0.85:
             img = img.filter(ImageFilter.GaussianBlur(radius=d_val % 4))
        if random.random() > 0.90:
             img = ImageOps.solarize(img, threshold=d_val % 255)

    # 4. SAVE TO FOLDER
    output_dir = "art"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = f"gen{gen}_{locked_name}.png"
    filepath = os.path.join(output_dir, filename)
    
    img.save(filepath)
    print(f"逃 CRATED: {filepath}")
    
    save_memory(gen + 1, current_seed + old_seed, word_pool)

if __name__ == "__main__":
    run_factory()