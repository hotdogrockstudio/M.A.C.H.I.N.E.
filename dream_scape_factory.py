import os, random, hashlib, requests, math, numpy as np, re, socket, datetime
from PIL import Image, ImageDraw, ImageFilter, ImageChops

# --- SYSTEM OVERRIDE ---
Image.MAX_IMAGE_PIXELS = 150000000 

# --- CONFIGURATION ---
MASTER_CANVAS = "master_canvas.png"
TARGET_MAP = "target_map.jpg"
ART_FOLDER = "Art"
TIMELAPSE_FOLDER = "TimeLapse"
DAYPICS_FOLDER = "Daypics"
LOG_FILE = "mosaic_log.txt"
ARCHIVE_FOLDER = "Finished_Projects"

MAP_DIM = 1000
TILE_DIM = 10
CANVAS_DIM = MAP_DIM * TILE_DIM 
TOTAL_SLOTS = MAP_DIM * MAP_DIM

# Force IPv4
def allowed_gai_family(): return socket.AF_INET
import urllib3.util.connection as urllib3_cn
urllib3_cn.allowed_gai_family = allowed_gai_family

# --- 1. THE FLUID COLLAGE TARGET ---
def ensure_target_exists():
    if os.path.exists(TARGET_MAP): return Image.open(TARGET_MAP)
    
    print("🛰️ TARGET MISSING: Creating 10-shard fluid collage...")
    try:
        joke = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=5).json()
        entropy = joke['setup'] + joke['punchline']
    except: entropy = "FLUID_CHAOS_SEED"

    chaos_seed = int(hashlib.md5(entropy.encode()).hexdigest(), 16)
    random.seed(chaos_seed)

    urls = {
        "nasa": "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY",
        "cat": "https://api.thecatapi.com/v1/images/search",
        "robot": f"https://robohash.org/{random.getrandbits(32)}.png",
        "picsum": f"https://picsum.photos/seed/{random.getrandbits(32)}/1000/1000"
    }
    
    imgs = []
    for name, url in urls.items():
        try:
            r = requests.get(url, timeout=10)
            if "json" in r.headers.get("content-type", ""):
                data = r.json()
                u = data[0]['url'] if isinstance(data, list) else data.get('url', url)
                r = requests.get(u, timeout=10)
            imgs.append(Image.open(requests.get(u, stream=True).raw).convert('RGB').resize((MAP_DIM, MAP_DIM)))
        except: imgs.append(Image.new('RGB', (MAP_DIM, MAP_DIM), (random.randint(0,100), 0, 100)))

    # Phase A: Randomized Alpha Blending (Weighted Visibility)
    base = imgs[0]
    for i in range(1, 4):
        # Generate random visibility for this layer
        visibility = random.uniform(0.2, 0.8)
        mask = Image.new('L', (MAP_DIM, MAP_DIM), 0)
        draw = ImageDraw.Draw(mask)
        for _ in range(5):
            x, y = random.randint(0, MAP_DIM), random.randint(0, MAP_DIM)
            r = random.randint(300, 700)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=int(255 * visibility))
        
        mask = mask.filter(ImageFilter.GaussianBlur(radius=random.randint(150, 250)))
        base = Image.composite(imgs[i], base, mask)

    # Phase B: 10 Random Shards
    shards = []
    for _ in range(10):
        sw, sh = random.randint(200, 600), random.randint(200, 600)
        sx, sy = random.randint(0, MAP_DIM-sw), random.randint(0, MAP_DIM-sh)
        shard = base.crop((sx, sy, sx+sw, sy+sh)).rotate(random.choice([0, 90, 180, 270]))
        shards.append({'img': shard, 'pos': (sx, sy)})

    # Phase C: Reassemble with Overlaps
    collage = Image.new('RGB', (MAP_DIM, MAP_DIM))
    random.shuffle(shards)
    for s in shards:
        # Paste them back at random coordinates to increase chaos
        rx, ry = random.randint(0, MAP_DIM-s['img'].width), random.randint(0, MAP_DIM-s['img'].height)
        collage.paste(s['img'], (rx, ry))
    
    final_target = collage.filter(ImageFilter.GaussianBlur(radius=60))
    final_target.save(TARGET_MAP)
    random.seed() 
    return final_target

# --- 2. LOGGING & PROGRESS ---
def get_used_data():
    files, coords = set(), set()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            content = f.read()
            files.update(re.findall(r'gen\d+\.png', content))
            c_hits = re.findall(r'at (\d+),(\d+)', content)
            for c in c_hits: coords.add((int(c[0]), int(c[1])))
    return files, coords

def archive_project():
    if not os.path.exists(ARCHIVE_FOLDER): os.makedirs(ARCHIVE_FOLDER)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    folder = os.path.join(ARCHIVE_FOLDER, f"Project_{ts}")
    os.makedirs(folder)
    for f in [MASTER_CANVAS, TARGET_MAP, LOG_FILE]:
        if os.path.exists(f): os.rename(f, os.path.join(folder, f))
    print("🏆 PROJECT ARCHIVED.")

# --- 3. THE DAILY SHIFT (24 PICS, 6 AT A TIME) ---
def process_day(canvas, target_img):
    all_f = [f for f in os.listdir(ART_FOLDER) if f.startswith('gen')]
    all_f.sort(key=lambda x: int(re.findall(r'\d+', x)[-1]))
    used_f, used_c = get_used_data()
    
    if len(used_c) >= TOTAL_SLOTS:
        archive_project()
        return

    daily_batch = [f for f in all_f if f not in used_f][:24]
    if len(daily_batch) < 24:
        print(f"⌛ Need 24 unique images. Found {len(daily_batch)}.")
        return

    t_array = np.array(target_img)
    daypic_tiles = []

    for shift in range(4):
        shift_batch = daily_batch[shift*6 : (shift+1)*6]
        with open(LOG_FILE, "a") as log:
            for filename in shift_batch:
                raw_tile = Image.open(os.path.join(ART_FOLDER, filename)).convert('RGB')
                daypic_tiles.append(raw_tile.resize((200, 200)))
                
                mini = raw_tile.resize((TILE_DIM, TILE_DIM))
                avg_c = np.array(mini.resize((1,1)).getpixel((0,0)))
                
                best_c, min_d = (0,0), float('inf')
                for _ in range(2000): 
                    rx, ry = random.randint(0, MAP_DIM-1), random.randint(0, MAP_DIM-1)
                    if (rx, ry) not in used_c:
                        d = np.sum((t_array[ry, rx] - avg_c)**2)
                        if d < min_d: min_d, best_c = d, (rx, ry)
                
                canvas.paste(mini, (best_c[0] * TILE_DIM, best_c[1] * TILE_DIM))
                used_c.add(best_c)
                log.write(f"{datetime.datetime.now()} | {filename} at {best_c[0]},{best_c[1]}\n")

        # Save Snap
        if not os.path.exists(TIMELAPSE_FOLDER): os.makedirs(TIMELAPSE_FOLDER)
        snap_id = len(os.listdir(TIMELAPSE_FOLDER)) + 1
        canvas.save(os.path.join(TIMELAPSE_FOLDER, f"snap_{snap_id:05d}.png"))
        canvas.save(MASTER_CANVAS)
        print(f"📸 SNAP {shift+1}/4 SAVED.")

    # Save Daypic Summary
    if not os.path.exists(DAYPICS_FOLDER): os.makedirs(DAYPICS_FOLDER)
    day_id = len(os.listdir(DAYPICS_FOLDER)) + 1
    grid = Image.new('RGB', (800, 1200))
    for idx, t in enumerate(daypic_tiles):
        grid.paste(t, ((idx % 4) * 200, (idx // 4) * 200))
    grid.save(os.path.join(DAYPICS_FOLDER, f"day_summary_{day_id:04d}.png"))
    print(f"📦 DAYPIC {day_id} SAVED.")

if __name__ == "__main__":
    if os.path.exists(".git"): os.system("git pull")
    target = ensure_target_exists()
    canvas = Image.open(MASTER_CANVAS) if os.path.exists(MASTER_CANVAS) else Image.new('RGB', (CANVAS_DIM, CANVAS_DIM), (0,0,0))
    process_day(canvas, target)