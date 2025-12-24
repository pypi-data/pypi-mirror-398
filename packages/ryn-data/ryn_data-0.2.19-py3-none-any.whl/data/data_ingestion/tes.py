from clearml.config import config


S3_KEY = "YOUR_S3_ACCESS_KEY"
S3_SECRET = "YOUR_S3_SECRET_KEY"
S3_ENDPOINT = "https://your-s3-endpoint.com" # Set to None if using AWS S3

# This is equivalent to setting sdk.storage.s3.* in clearml.conf
config['sdk.storage.s3.key'] = S3_KEY
config['sdk.storage.s3.secret'] = S3_SECRET

# Force the configuration to be reloaded with the new settings
config.load()
print("ClearML S3 Storage has been configured programmatically.")