import os
from dotenv import load_dotenv

def setup_secrets():
    """Generate .streamlit/secrets.toml from environment variables"""
    load_dotenv()
    # Create .streamlit directory
    os.makedirs('.streamlit', exist_ok=True)
   
    # Generate secrets.toml content
    secrets_content = f'''[auth]
    enable = true
    client_id = "{os.getenv('client_id', '')}"
    client_secret = "{os.getenv('client_secret', '')}"
    cookie_secret = "{os.getenv('cookie_secret', '')}"
    redirect_uri = "{os.getenv('redirect_uri', '')}"
    server_metadata_url = "{os.getenv('server_metadata_url', '')}"
    '''
   
    # Write the secrets file
    with open('.streamlit/secrets.toml', 'w') as f:
        f.write(secrets_content)

if __name__ == "__main__":
    setup_secrets()