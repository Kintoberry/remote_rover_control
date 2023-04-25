import os 
import sys

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from services import http_server

if __name__ == "__main__":
    http_server.main()