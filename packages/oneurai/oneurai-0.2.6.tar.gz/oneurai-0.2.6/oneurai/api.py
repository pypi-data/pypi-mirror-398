import requests
import os
import torch
import torch.nn as nn
import zipfile
import colorama
from colorama import Fore, Style

# Enable colors
colorama.init(autoreset=True)

API_TOKEN = None
BASE_URL = "https://oneurai.com/api"

# ✅ WAF Bypass: User-Agent Header
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# =====================================================
# 1. Authentication
# =====================================================
def login(token):
    global API_TOKEN
    API_TOKEN = token
    COMMON_HEADERS["Authorization"] = f"Bearer {API_TOKEN}"
    
    print(f"""{Fore.CYAN}{Style.BRIGHT}
    ____                             _ 
   / __ \                           (_)
  | |  | |_ __   ___ _   _ _ __ __ _ _   
  | |  | | '_ \ / _ \ | | | '__/ _` | |  
  | |__| | | | |  __/ |_| | | | (_| | |  
   \____/|_| |_|\___|\__,_|_|  \__,_|_|  
      {Fore.GREEN}>> AI & MLOps Library <<{Style.RESET_ALL}
""")
    print(f"{Fore.CYAN}📡 Checking connection...{Style.RESET_ALL}")
    
    try:
        response = requests.get(f"{BASE_URL}/user", headers=COMMON_HEADERS, timeout=10)
        if response.status_code == 200:
            user = response.json()
            name = user.get('username') or user.get('name')
            print(f"{Fore.GREEN}✅ Connected successfully as: {name}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  Warning: Could not fetch username (Code {response.status_code}).{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Connection Warning: {e}{Style.RESET_ALL}")

# =====================================================
# 2. Dataset Management (New & Improved)
# =====================================================
def load_dataset(repo_id, filename=None, cache_dir="datasets"):
    """
    دالة ذكية لتحميل البيانات وتغليفها في مجلد خاص.
    
    Args:
        repo_id (str): معرف المستودع مثل "mtma/wiki-arabic-full"
        filename (str): اسم الملف المراد تحميله (اختياري). إذا لم يحدد، سنفترض "data.zip"
        cache_dir (str): المجلد الرئيسي الذي سيتم حفظ البيانات فيه.
    
    Returns:
        str: مسار المجلد الذي يحتوي على البيانات.
    """
    if "/" not in repo_id:
        print(f"{Fore.RED}❌ Error: Invalid format. Use 'username/dataset'{Style.RESET_ALL}")
        return None

    # 1. تحديد اسم الملف الافتراضي
    if filename is None:
        filename = "data.zip" # الافتراضي إذا لم يحدد المستخدم ملفاً

    # 2. تجهيز المجلد (التغليف)
    # سيتم إنشاء مجلد: datasets/mtma_wiki-arabic-full/
    folder_name = repo_id.replace("/", "_")
    save_dir = os.path.join(cache_dir, folder_name)
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"{Fore.CYAN}📂 Created directory: {save_dir}{Style.RESET_ALL}")

    file_path = os.path.join(save_dir, filename)

    # 3. التحقق مما إذا كان الملف موجوداً مسبقاً
    if os.path.exists(file_path):
        print(f"{Fore.YELLOW}ℹ️  Dataset already exists at: {file_path}{Style.RESET_ALL}")
        # إذا كان zip، نتأكد أنه مفكوك الضغط، وإلا نرجعه كما هو
        return save_dir

    # 4. التحميل
    print(f"⬇️  Downloading {filename} from {repo_id}...")
    url = f"{BASE_URL}/datasets/{repo_id}/download/{filename}"
    
    success = _download_file(url, file_path)
    
    if success:
        # 5. فك الضغط التلقائي (Auto Unzip)
        if filename.endswith(".zip"):
            print(f"📦 Extracting {filename}...")
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(save_dir)
                print(f"{Fore.GREEN}✅ Extracted successfully to: {save_dir}{Style.RESET_ALL}")
                # خيار: حذف ملف الـ zip بعد فك الضغط لتوفير المساحة
                # os.remove(file_path) 
            except zipfile.BadZipFile:
                print(f"{Fore.RED}❌ Error: The downloaded file is not a valid zip file.{Style.RESET_ALL}")
        
        return save_dir
    else:
        return None

def upload_dataset(file_path, full_repo_name, description="Dataset"):
    if not os.path.exists(file_path):
        print(f"{Fore.RED}❌ File not found{Style.RESET_ALL}")
        return
    print(f"📦 Preparing dataset: {file_path} ...")
    _upload_file(full_repo_name, file_path, "datasets", description)

# =====================================================
# 3. Models Logic (Standard)
# =====================================================
class SimpleNN(nn.Module):
    def __init__(self, layers_config):
        super(SimpleNN, self).__init__()
        layers = []
        for i in range(len(layers_config) - 1):
            layers.append(nn.Linear(layers_config[i], layers_config[i+1]))
            if i < len(layers_config) - 2:
                layers.append(nn.ReLU())
            else:
                layers.append(nn.Sigmoid())
        self.model = nn.Sequential(*layers)
        self.config = layers_config

    def forward(self, x): return self.model(x)
    
    def train_model(self, X, y, epochs=1000): pass 

    def save(self, path):
        torch.save({'state_dict': self.state_dict(), 'config': self.config}, path)

    def load(self, path):
        checkpoint = torch.load(path)
        self.load_state_dict(checkpoint['state_dict'])
        self.config = checkpoint['config']
        self.eval()

class Model:
    def __init__(self, layers):
        self.engine = SimpleNN(layers)
    
    def train(self, X, y, epochs=1000):
        self.engine.train_model(X, y, epochs)

    def predict(self, val):
        with torch.no_grad():
            return self.engine(torch.tensor(val, dtype=torch.float32)).tolist()

    def push_to_hub(self, full_repo_name, description="AI Model uploaded via Oneurai"):
        if "/" not in full_repo_name:
            print(f"{Fore.RED}❌ Format Error{Style.RESET_ALL}")
            return
        _, repo_name = full_repo_name.split("/", 1)
        
        pt_filename = f"{repo_name}.pt"
        zip_filename = f"{repo_name}.zip"

        self.engine.save(pt_filename)
        
        print(f"📦 Compressing model to {zip_filename}...")
        try:
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                zipf.write(pt_filename)
        except Exception as e:
            print(f"{Fore.RED}❌ Compression Failed: {e}{Style.RESET_ALL}")
            return

        _upload_file(full_repo_name, zip_filename, "models", description)
        
        if os.path.exists(pt_filename): os.remove(pt_filename)
        if os.path.exists(zip_filename): os.remove(zip_filename)

def create_model(layers): return Model(layers)

def load_model(full_repo_name, layers):
    _, repo_name = full_repo_name.split("/", 1)
    filename = f"{repo_name}.zip" 
    url = f"{BASE_URL}/models/{full_repo_name}/download/{filename}"
    return _download_and_load_model(url, filename, layers)

# =====================================================
# 4. Helper Internal Functions
# =====================================================
def _upload_file(full_repo_name, file_path, type_category, description):
    if "/" not in full_repo_name: return

    username, repo_name = full_repo_name.split("/", 1)
    url = f"{BASE_URL}/{type_category}/{username}/{repo_name}/upload"
    data = {'description': description}
    filename = os.path.basename(file_path)
    
    print(f"☁️ Uploading to [{type_category.upper()}] -> {Fore.BLUE}{full_repo_name}{Style.RESET_ALL} ...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            response = requests.post(url, headers=COMMON_HEADERS, files=files, data=data)
        
        if response.status_code in [200, 201]:
            print(f"{Fore.GREEN}✅ Upload Successful!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Server Error ({response.status_code}): {response.text}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Connection Failed: {e}{Style.RESET_ALL}")

def _download_file(url, save_path):
    try:
        r = requests.get(url, headers=COMMON_HEADERS, stream=True)
        if r.status_code == 200:
            total_size = int(r.headers.get('content-length', 0))
            # هنا ممكن نضيف Progress Bar مستقبلاً باستخدام tqdm
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"{Fore.GREEN}✅ Downloaded: {save_path}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Failed to download (Code {r.status_code}): {r.text}{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        return False

def _download_and_load_model(url, zip_filename, layers):
    print(f"⬇️ Downloading Model Package...")
    if _download_file(url, zip_filename):
        pt_filename = zip_filename.replace('.zip', '.pt')
        print("📦 Extracting model...")
        try:
            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                extracted_name = zip_ref.namelist()[0]
                zip_ref.extractall()
                if extracted_name != pt_filename and extracted_name.endswith('.pt'):
                        if os.path.exists(pt_filename): os.remove(pt_filename)
                        os.rename(extracted_name, pt_filename)
        except Exception as z_err:
            print(f"{Fore.RED}❌ Extraction Error: {z_err}{Style.RESET_ALL}")
            return None

        m = Model(layers)
        m.engine.load(pt_filename)
        print(f"{Fore.GREEN}✅ Model loaded successfully.{Style.RESET_ALL}")
        
        if os.path.exists(zip_filename): os.remove(zip_filename)
        if os.path.exists(pt_filename): os.remove(pt_filename)
        return m
    return None