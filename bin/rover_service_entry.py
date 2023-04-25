import sys
import os

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Import the function you want to run
from services import rover_service

if __name__ == "__main__":
    rover_service.main()
