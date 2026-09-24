import os
import socket
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import photo_engine
import video_engine

app = FastAPI(title="JK Reels and Snap")

UPLOAD_DIR = "static/uploads"
TEMP_DIR = "temp_cache"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mock database for uploaded reels/snaps
reels_db = [
    {
        "id": "reel_demo",
        "title": "Welcome to JK Reels & Snap! 🚀",
        "user": "@JK_Admin",
        "url": "https://assets.mixkit.co/videos/preview/mixkit-vertical-view-of-a-neon-sign-41484-large.mp4",
        "likes": 1204
    }
]

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# --- MASTER FRONTEND UI (Tailwind + Theme Switcher + Modals + Feed + Chatbot) ---
APP_UI = """
<!DOCTYPE html>
<html lang="en" data-theme="cyber">
<head>
    <title>JK Reels & Snap - AI Photo Cutout & Video Shorts Studio</title>
    <meta name="description" content="JK Reels & Snap par AI image banayein, photo background remove karein aur shorts reels edit karein free me.">
    <meta name="keywords" content="jk reels, ai photo editor, reel generator, photo cutout, video shorts">
    <meta name="robots" content="index, follow">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>JK Reels and Snap</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        /* Themes */
        html[data-theme="cyber"] { --bg: #090d16; --card: #131b2e; --accent: #3b82f6; --text: #ffffff; }
        html[data-theme="snapchat"] { --bg: #000000; --card: #181818; --accent: #FFFC00; --text: #ffffff; }
        html[data-theme="sunset"] { --bg: #1a0b16; --card: #2e1127; --accent: #ec4899; --text: #ffffff; }
        
        body { background-color: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .theme-card { background-color: var(--card); }
        .theme-accent { background-color: var(--accent); }
        .theme-accent-text { color: var(--accent); }

        /* Reel Snapping Scroll */
        .reels-container {
            scroll-snap-type: y mandatory;
            overflow-y: scroll;
            height: calc(100vh - 130px);
        }
        .reel-item {
            scroll-snap-align: start;
            height: calc(100vh - 130px);
        }
        /* Hide scrollbars */
        ::-webkit-scrollbar { display: none; }
    </style>
</head>
<body class="flex justify-center select-none">

    <!-- Mobile Wrapper View -->
    <div class="w-full max-w-md h-screen flex flex-col justify-between relative overflow-hidden border-x border-slate-800 shadow-2xl">
        
        <!-- Top Navigation -->
        <header class="p-3 flex justify-between items-center border-b border-slate-800/80 z-10 backdrop-blur-md">
            <h1 class="font-extrabold text-xl tracking-wider theme-accent-text flex items-center gap-2">
                <i class="fa-solid fa-bolt"></i> JK REELS
            </h1>
            <div class="flex items-center gap-3">
                <!-- Theme Switcher -->
                <button onclick="cycleTheme()" class="text-sm bg-slate-800 p-2 rounded-full hover:bg-slate-700">
                    <i class="fa-solid fa-palette text-amber-400"></i>
                </button>
                <button onclick="openModal('auth-modal')" class="text-xs bg-blue-600 px-3 py-1.5 rounded-full font-bold">
                    Login
                </button>
            </div>
        </header>

        <!-- Dynamic Main Views -->
        <main id="app-viewport" class="flex-1 overflow-hidden relative">
            
            <!-- VIEW 1: REELS FEED (Like TikTok/Snapchat) -->
            <section id="view-reels" class="reels-container w-full h-full">
                <!-- Feed items rendered by JS -->
            </section>

            <!-- VIEW 2: ALL-IN-ONE STUDIO (Editing Tools) -->
            <section id="view-studio" class="hidden p-4 h-full overflow-y-auto space-y-4">
                <h2 class="text-xl font-bold theme-accent-text mb-2">⚡ JK Creation Studio</h2>

                <!-- 1. AI Image Generator -->
                <div class="theme-card p-4 rounded-2xl border border-slate-700/40">
                    <h3 class="font-bold text-sm mb-1 text-blue-400"><i class="fa-solid fa-wand-magic-sparkles"></i> Text to AI Image</h3>
                    <form action="/api/generate-image" method="post" target="_blank" class="flex gap-2 mt-2">
                        <input type="text" name="prompt" placeholder="e.g. Glowing neon tiger in Mumbai" required
                               class="flex-1 bg-black/40 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white">
                        <button class="bg-blue-600 px-4 py-2 rounded-xl text-xs font-bold">Create</button>
                    </form>
                </div>

                <!-- 2. Photo Editor & Filters -->
                <div class="theme-card p-4 rounded-2xl border border-slate-700/40">
                    <h3 class="font-bold text-sm mb-1 text-pink-400"><i class="fa-solid fa-image"></i> Photo Cutout & Snap Filters</h3>
                    <form action="/api/edit-photo" method="post" enctype="multipart/form-data" target="_blank" class="space-y-2 mt-2">
                        <input type="file" name="file" accept="image/*" required class="text-xs text-slate-400 w-full">
                        <select name="action" class="w-full bg-black/40 border border-slate-700 rounded-xl px-2 py-2 text-xs text-white">
                            <option value="cutout">✂️ Hand-Safe Clean Cutout (Alpha Matting)</option>
                            <option value="cyberpunk">🌆 Cyberpunk Glow Filter</option>
                            <option value="vintage">🎞️ Vintage Sepia Tone</option>
                            <option value="bw">🖤 High-Contrast B&W</option>
                            <option value="upscale">✨ 2X HD AI Upscale</option>
                        </select>
                        <button class="w-full bg-pink-600 py-2 rounded-xl text-xs font-bold">Process Photo</button>
                    </form>
                </div>

                <!-- 3. Video Shorts 9:16 Re-Framer -->
                <div class="theme-card p-4 rounded-2xl border border-slate-700/40">
                    <h3 class="font-bold text-sm mb-1 text-amber-400"><i class="fa-solid fa-video"></i> Landscape to 9:16 Shorts</h3>
                    <form action="/api/crop-video" method="post" enctype="multipart/form-data" target="_blank" class="space-y-2 mt-2">
                        <input type="file" name="file" accept="video/*" required class="text-xs text-slate-400 w-full">
                        <button class="w-full bg-amber-600 py-2 rounded-xl text-xs font-bold">Crop to 9:16</button>
                    </form>
                </div>
            </section>

            <!-- VIEW 3: UPLOAD REEL / SNAP -->
            <section id="view-upload" class="hidden p-4 h-full flex flex-col justify-center">
                <div class="theme-card p-6 rounded-3xl border border-slate-700 text-center">
                    <div class="w-16 h-16 bg-blue-600/20 text-blue-400 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                        <i class="fa-solid fa-cloud-arrow-up"></i>
                    </div>
                    <h2 class="text-lg font-bold">Post a Reel or Snap</h2>
                    <p class="text-xs text-slate-400 mb-4">Post directly to JK Reels Community feed</p>
                    <form id="upload-reel-form" class="space-y-3">
                        <input type="text" id="reel-title" placeholder="Caption / Title..." required
                               class="w-full bg-black/40 border border-slate-700 rounded-xl px-4 py-3 text-xs text-white">
                        <input type="file" id="reel-file" accept="video/*" required
                               class="w-full text-xs text-slate-400">
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 py-3 rounded-xl font-bold text-xs">
                            Upload Reel
                        </button>
                    </form>
                </div>
            </section>

            <!-- VIEW 4: AI GUIDE ASSISTANT (Chatbot) -->
            <section id="view-chat" class="hidden h-full flex flex-col justify-between p-4">
                <div class="border-b border-slate-800 pb-2 mb-2">
                    <h3 class="font-bold text-sm text-emerald-400 flex items-center gap-2">
                        <i class="fa-solid fa-robot"></i> JK AI Creative Copilot
                    </h3>
                    <p class="text-[10px] text-slate-400">Mujhse pucho: "Photo kaise cut karein?" ya "Reel viral kaise banayein?"</p>
                </div>
                <div id="chat-box" class="flex-1 overflow-y-auto space-y-3 text-xs pr-1">
                    <div class="bg-slate-800/80 p-3 rounded-2xl rounded-tl-none max-w-[85%]">
                        Hello! Main JK Studio ka AI guide hoon. Aap photo filter, background remove, video editing ya reel generation ke baare mein kuch bhi pooch sakte hain!
                    </div>
                </div>
                <div class="flex gap-2 pt-2">
                    <input type="text" id="chat-input" placeholder="Type prompt / sawal..." 
                           class="flex-1 bg-black/50 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white">
                    <button onclick="sendChatMessage()" class="bg-emerald-600 px-4 py-2 rounded-xl text-xs font-bold">
                        <i class="fa-solid fa-paper-plane"></i>
                    </button>
                </div>
            </section>

        </main>

        <!-- Bottom Navigation Bar (Snapchat & Insta Style) -->
        <nav class="h-16 theme-card border-t border-slate-800 flex justify-around items-center px-4 z-20">
            <button onclick="switchTab('reels')" class="nav-btn flex flex-col items-center gap-1 text-blue-400">
                <i class="fa-solid fa-film text-lg"></i>
                <span class="text-[10px] font-semibold">Reels</span>
            </button>
            <button onclick="switchTab('studio')" class="nav-btn flex flex-col items-center gap-1 text-slate-400">
                <i class="fa-solid fa-wand-magic-sparkles text-lg"></i>
                <span class="text-[10px] font-semibold">Studio</span>
            </button>
            <!-- Snap Action Button -->
            <button onclick="switchTab('upload')" class="w-11 h-11 bg-gradient-to-tr from-blue-600 to-indigo-500 rounded-full flex items-center justify-center text-white text-lg shadow-lg -translate-y-3 border-4 border-slate-950">
                <i class="fa-solid fa-plus"></i>
            </button>
            <button onclick="switchTab('chat')" class="nav-btn flex flex-col items-center gap-1 text-slate-400">
                <i class="fa-solid fa-comments text-lg"></i>
                <span class="text-[10px] font-semibold">AI Guide</span>
            </button>
        </nav>

    </div>

    <!-- 1. WELCOME & TERMS MODAL (First time visit) -->
    <div id="welcome-modal" class="fixed inset-0 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 z-50">
        <div class="theme-card max-w-sm w-full p-6 rounded-3xl border border-slate-800 text-center space-y-4">
            <div class="w-14 h-14 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center mx-auto text-2xl">
                <i class="fa-solid fa-hand-sparkles"></i>
            </div>
            <h2 class="text-xl font-black">Welcome to JK Reels & Snap!</h2>
            <div class="text-xs text-slate-300 text-left bg-black/30 p-3 rounded-xl space-y-2 max-h-36 overflow-y-auto border border-slate-800">
                <p class="font-bold text-white">Terms & Privacy Guidelines:</p>
                <p>1. Local Processing: Aapka data aapke computer ke hardware par locally run hota hai.</p>
                <p>2. Community Safety: Reels feed par kisi bhi tarah ka hateful ya illegal content upload karna prohibited hai.</p>
                <p>3. 100% Free: Is platform ke basic tools hamesha free rahenge.</p>
            </div>
            <div class="flex items-center gap-2 text-xs text-slate-400 justify-center">
                <input type="checkbox" id="agree-terms" class="accent-blue-500">
                <label for="agree-terms">Main in sharto se agree karta hoon</label>
            </div>
            <button onclick="acceptTerms()" class="w-full bg-blue-600 hover:bg-blue-500 py-3 rounded-xl font-bold text-xs">
                Enter Studio & Reels 🚀
            </button>
        </div>
    </div>

    <!-- 2. LOGIN MODAL (Google & Mobile SMS Verification) -->
    <div id="auth-modal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div class="theme-card max-w-sm w-full p-6 rounded-3xl border border-slate-800 text-center relative">
            <button onclick="closeModal('auth-modal')" class="absolute top-4 right-4 text-slate-400"><i class="fa-solid fa-xmark"></i></button>
            <h2 class="text-lg font-black mb-1">Login to JK Studio</h2>
            <p class="text-xs text-slate-400 mb-6">Cloud sync aur custom profile ke liye</p>

            <!-- Google OAuth Mock -->
            <button onclick="mockGoogleLogin()" class="w-full bg-white text-black font-semibold py-2.5 rounded-xl text-xs flex items-center justify-center gap-3 mb-4">
                <i class="fa-brands fa-google text-red-500 text-sm"></i> Continue with Google
            </button>
            
            <div class="flex items-center gap-2 my-4">
                <div class="flex-1 h-px bg-slate-800"></div>
                <span class="text-[10px] text-slate-500">OR MOBILE OTP</span>
                <div class="flex-1 h-px bg-slate-800"></div>
            </div>

            <!-- Mobile Verification -->
            <div class="space-y-3 text-left">
                <input type="tel" id="mobile-number" placeholder="Mobile Number (+91...)" 
                       class="w-full bg-black/40 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white">
                <button onclick="sendOtp()" class="w-full bg-slate-800 hover:bg-slate-700 py-2.5 rounded-xl text-xs font-semibold">
                    Send Code (OTP)
                </button>
                <div id="otp-group" class="hidden space-y-2">
                    <input type="text" id="otp-input" placeholder="Enter 4-Digit Code" 
                           class="w-full bg-black/40 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white text-center tracking-widest font-bold">
                    <button onclick="verifyOtp()" class="w-full bg-blue-600 py-2.5 rounded-xl text-xs font-bold">
                        Verify & Login
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
    async function handleGoogleCredentialResponse(response) {
    const idToken = response.credential;
    
    // Token ko Python backend pe bhejna
    const res = await fetch('/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: idToken })
    });
    
    const data = await res.json();
    if(data.status === "success") {
        alert(`Welcome ${data.user.name}! Login successful 🎉`);
        closeModal('auth-modal');
        
        // Header me login button ki jagah profile photo lagana
        const authBtn = document.querySelector("header button[onclick*='auth-modal']");
        if(authBtn) {
            authBtn.outerHTML = `
                <div class="flex items-center gap-2 bg-slate-800 px-3 py-1 rounded-full border border-blue-500">
                    <img src="${data.user.picture}" class="w-6 h-6 rounded-full">
                    <span class="text-xs font-bold text-slate-200">${data.user.name.split(' ')[0]}</span>
                </div>
            `;
        }
    } else {
        alert("Google Verification Failed!");
    }
}
        // Check Terms
        if(localStorage.getItem('jk_terms_agreed') === 'true') {
            document.getElementById('welcome-modal').classList.add('hidden');
        }
        function acceptTerms() {
            if(document.getElementById('agree-terms').checked) {
                localStorage.setItem('jk_terms_agreed', 'true');
                document.getElementById('welcome-modal').classList.add('hidden');
            } else {
                alert("Kripya pehle terms agree karein!");
            }
        }

        // Modal Helpers
        function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
        function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

        // Themes
        const themes = ['cyber', 'snapchat', 'sunset'];
        let curTheme = 0;
        function cycleTheme() {
            curTheme = (curTheme + 1) % themes.length;
            document.documentElement.setAttribute('data-theme', themes[curTheme]);
        }

        // Tabs
        function switchTab(tabId) {
            ['reels', 'studio', 'upload', 'chat'].forEach(t => {
                document.getElementById('view-' + t).classList.add('hidden');
            });
            document.getElementById('view-' + tabId).classList.remove('hidden');
            if(tabId === 'reels') loadReels();
        }

        // Reels Feed Loader
        async function loadReels() {
            const container = document.getElementById('view-reels');
            const res = await fetch('/api/reels');
            const reels = await res.json();
            container.innerHTML = reels.map(r => `
                <div class="reel-item relative flex items-center justify-center bg-black">
                    <video src="${r.url}" class="w-full h-full object-cover" loop autoplay muted playsinline></video>
                    <div class="absolute bottom-4 left-4 right-14 text-white drop-shadow-md">
                        <div class="font-bold text-sm">${r.user}</div>
                        <div class="text-xs text-slate-200 mt-1">${r.title}</div>
                    </div>
                    <!-- Right Actions like Instagram -->
                    <div class="absolute right-3 bottom-6 flex flex-col gap-4 text-center">
                        <button class="flex flex-col items-center gap-1 text-white">
                            <i class="fa-solid fa-heart text-2xl text-red-500"></i>
                            <span class="text-[10px]">${r.likes}</span>
                        </button>
                        <button class="flex flex-col items-center gap-1 text-white">
                            <i class="fa-solid fa-comment text-2xl"></i>
                            <span class="text-[10px]">Reply</span>
                        </button>
                        <button class="flex flex-col items-center gap-1 text-white">
                            <i class="fa-solid fa-share-nodes text-2xl"></i>
                            <span class="text-[10px]">Share</span>
                        </button>
                    </div>
                </div>
            `).join('');
        }
        loadReels();

        // Reel Upload Form
        document.getElementById('upload-reel-form').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData();
            formData.append('title', document.getElementById('reel-title').value);
            formData.append('file', document.getElementById('reel-file').files[0]);
            const res = await fetch('/api/upload-reel', { method: 'POST', body: formData });
            if(res.ok) {
                alert("🎉 Reel successfully posted to JK Feed!");
                switchTab('reels');
            }
        };

        // AI Chat Engine
        async function sendChatMessage() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if(!text) return;
            const chatBox = document.getElementById('chat-box');
            chatBox.innerHTML += `<div class="bg-blue-600 text-white p-3 rounded-2xl rounded-tr-none ml-auto max-w-[85%]">${text}</div>`;
            input.value = '';
            
            const res = await fetch('/api/ai-guide', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: text })
            });
            const data = await res.json();
            chatBox.innerHTML += `<div class="bg-slate-800/80 p-3 rounded-2xl rounded-tl-none max-w-[85%] text-slate-200">${data.reply}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        // Auth Mocks
        function mockGoogleLogin() {
            alert("✅ Google Verification Successful: Logged in as User");
            closeModal('auth-modal');
        }
        function sendOtp() {
            const num = document.getElementById('mobile-number').value;
            if(!num) return alert("Enter valid phone number");
            document.getElementById('otp-group').classList.remove('hidden');
            alert("Verification code 7788 sent to " + num);
        }
        function verifyOtp() {
            const code = document.getElementById('otp-input').value;
            if(code === "7788" || code.length === 4) {
                alert("✅ Mobile Verified! Welcome.");
                closeModal('auth-modal');
            } else {
                alert("Invalid verification code");
            }
        }
    </script>
</body>
</html>
"""

# --- API ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    return APP_UI

@app.get("/api/reels")
async def get_reels():
    return reels_db

@app.post("/api/upload-reel")
async def upload_reel(title: str = Form(...), file: UploadFile = File(...)):
    filename = f"{uuid.uuid4().hex[:6]}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
        
    reel_entry = {
        "id": filename,
        "title": title,
        "user": "@creator_" + uuid.uuid4().hex[:4],
        "url": f"/static/uploads/{filename}",
        "likes": 1
    }
    reels_db.insert(0, reel_entry)
    return {"status": "success", "reel": reel_entry}

class ChatRequest(BaseModel):
    query: str

@app.post("/api/ai-guide")
async def ai_copilot(req: ChatRequest):
    q = req.query.lower()
    if "photo" in q or "cutout" in q or "background" in q:
        ans = "Photo se background remove karne ke liye Studio tab me 'Alpha Matting Cutout' select karein. Isse aapke haath aur baal bilkul safe rahenge."
    elif "reel" in q or "short" in q or "viral" in q:
        ans = "Viral reel ke liye Studio me 'Landscape to 9:16 Shorts' use karein. Video upload karke pehle 3 second me strong hook dalein!"
    elif "filter" in q:
        ans = "Studio tab me jaakar 'Cyberpunk Glow' ya 'Vintage Sepia' filter chunein taaki photo Snapchat jaise cool colors me badal jaye."
    else:
        ans = f"JK Studio me aap AI image generate kar sakte hain, photos me filter laga sakte hain aur direct Reels upload kar sakte hain. Batayein aapko kis tool ki help chahiye?"
    return {"reply": ans}

@app.post("/api/generate-image")
async def gen_image(prompt: str = Form(...)):
    out = os.path.join(TEMP_DIR, f"ai_{uuid.uuid4().hex[:6]}.png")
    photo_engine.generate_ai_image(prompt, out)
    return FileResponse(out, media_type="image/png")

@app.post("/api/edit-photo")
async def edit_photo(file: UploadFile = File(...), action: str = Form(...)):
    in_p = os.path.join(TEMP_DIR, f"in_{file.filename}")
    out_p = os.path.join(TEMP_DIR, f"out_{file.filename}.png")
    with open(in_p, "wb") as f:
        f.write(await file.read())
        
    if action == "cutout":
        photo_engine.clean_remove_background(in_p, out_p)
    elif action == "upscale":
        photo_engine.upscale_image(in_p, out_p)
    else:
        photo_engine.apply_photo_filter(in_p, out_p, filter_type=action)
        
    return FileResponse(out_p, media_type="image/png")

@app.post("/api/crop-video")
async def crop_video(file: UploadFile = File(...)):
    in_p = os.path.join(TEMP_DIR, f"in_{file.filename}")
    out_p = os.path.join(TEMP_DIR, f"vertical_{file.filename}")
    with open(in_p, "wb") as f:
        f.write(await file.read())
    video_engine.crop_vertical_reel(in_p, out_p)
    return FileResponse(out_p, media_type="video/mp4")

if __name__ == "__main__":
    ip = get_local_ip()
    print("="*50)
    print("⚡ JK REELS AND SNAP IS RUNNING")
    print(f"🖥️ PC Browser: http://localhost:8000")
    print(f"📱 Phone Link:  http://{ip}:8000")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pydantic import BaseModel

class GoogleTokenBody(BaseModel):
    token: str

@app.post("/api/auth/google")
async def google_auth_verify(body: GoogleTokenBody):
    try:
        # Token verify karna
        idinfo = id_token.verify_oauth2_token(body.token, google_requests.Request())
        
        # User details extract karna
        user_info = {
            "name": idinfo.get("name"),
            "email": idinfo.get("email"),
            "picture": idinfo.get("picture"),
            "google_id": idinfo.get("sub")
        }
        return {"status": "success", "user": user_info}
    except Exception as e:
        print(f"Auth Error: {e}")
        return {"status": "error", "message": "Invalid Token"}
   