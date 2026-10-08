

# Download the latest release
gh release download --repo "dofusdude/dofus3-main" --pattern "*" --dir "data"

# Parse items as a dataframe to look up IDs and names
python -m scripts.data