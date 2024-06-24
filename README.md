# Investment World

## Overview: -
**Invest in stock market**

# Data
  - Description: [here]()
  - Local data: [here]()
  - Web data: [here]()

# Setup Environment: -
  - Create virtual environment
    - > conda create -p venv python=3.10 -y
  - Activate environment
    - > conda activate venv/
  - Install requirements : -
    - > pip install -r requirements.txt
  - Run the application: -
  - > streamlit run app.py
  - Access in browser: -
  - > localhost:8501
  - Create docker image: -
    - > docker build -t ranjitkundu/amazon_sales:v1 .
    - Show docker images: -
      - > docker images
    - Run the docker image in container: - 
      - > docker run -p 8501:8501 ranjitkundu/name