# Install Python and verify
brew install python@3.11
/opt/homebrew/opt/python@3.11/bin/python3.11 --version

# Form: python3 -m venv [YOUR_CUSTOM_NAME]
python3 -m venv .venv
python3: Tells your Mac to use Python 3.
 -m venv: Tells Python to run its built-in venv tool module (the environment creator).

 # 1. Create a virtual environment named "venv" using Python 3
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Upgrade pip directly inside .venv - remember -m is important to put while installing inside virtual environments,
python -m pip install --upgrade pip

# 4. Install your requirements - remember -m is important to install modules under virtual environment
python -m pip install -r requirements.txt

# do this before the virtual environment installation - the second command should point to virtual environment isntallation and not global
unalias python python3
python -c "import sys; print(sys.executable)"

# list all python versions
which -a python3 

# to get with actual python version details
for p in $(which -a python3); do echo "$p -> $($p --version)"; done

# Start the uvicorn server with 
python -m uvicorn multi_agent_http_webhook_demo_server:app --reload --port 8001

# Start Streamlit App - here Demo5.py is the script of python
streamlit run Demo5.py 

# Stop Streamlit app
Control + C

# 1. Remove the corrupted virtual environment folder
rm -rf .venv

# Kill any processes if virtual environment is not empty
pkill -9 python