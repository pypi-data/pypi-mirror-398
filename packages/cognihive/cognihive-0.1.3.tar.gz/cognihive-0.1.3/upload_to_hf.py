"""
Script to create and upload CogniHive to HuggingFace Spaces.
"""

from huggingface_hub import HfApi, create_repo, upload_folder
import os

# Initialize API
api = HfApi()

# Space details
SPACE_NAME = "cognihive"
REPO_ID = f"vrushket/{SPACE_NAME}"

print(f"Creating Space: {REPO_ID}")

# Create the Space repository
try:
    repo_url = create_repo(
        repo_id=REPO_ID,
        repo_type="space",
        space_sdk="gradio",
        private=False,
        exist_ok=True
    )
    print(f"Space created/exists: {repo_url}")
except Exception as e:
    print(f"Note: {e}")

# Upload the demo folder
demo_path = r"c:\Users\vrush\OneDrive\Documents\CogniHive\demo"
src_path = r"c:\Users\vrush\OneDrive\Documents\CogniHive\src"

print(f"\nUploading demo files from: {demo_path}")

# Upload demo folder contents
api.upload_folder(
    folder_path=demo_path,
    repo_id=REPO_ID,
    repo_type="space",
    path_in_repo=".",
    commit_message="Initial CogniHive demo upload"
)

print("Demo files uploaded!")

# Upload src/cognihive folder
print(f"\nUploading cognihive package from: {src_path}")

api.upload_folder(
    folder_path=src_path,
    repo_id=REPO_ID,
    repo_type="space",
    path_in_repo="src",
    commit_message="Add cognihive package source"
)

print("Package source uploaded!")

print(f"\n========================================")
print(f"SUCCESS! Space is live at:")
print(f"https://huggingface.co/spaces/{REPO_ID}")
print(f"========================================")
