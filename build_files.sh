pip install -r requirements.txt
python3.9 manage.py collectstatic
# !/bin/bash

# # Ensure Python and pip are installed
# if ! command -v pip &> /dev/null; then
#     echo "pip not found. Installing Python and pip..."
#     apt-get update && apt-get install -y python3-pip
# fi

# # Install requirements
# pip install -r requirements.txt

# # Collect static files
# python3.9 manage.py collectstatic --noinput
