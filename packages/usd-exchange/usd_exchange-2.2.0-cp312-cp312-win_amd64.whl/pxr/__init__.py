import os

# Set environment variable for USD Windows DLL path
dll_path = os.path.join(os.path.dirname(__file__), "../usd_exchange.libs")
os.environ["PXR_USD_WINDOWS_DLL_PATH"] = os.path.abspath(dll_path)