import os
import boto3
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── JWT ──────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET")
if JWT_SECRET and JWT_SECRET != "your_random_jwt_secret_here":
    print("✓ JWT_SECRET found")
else:
    print("✗ WARNING: JWT_SECRET not set - using default (not secure for production)")

# ── System materials ─────────────────────────────────────────
# Materials with this user_id are accessible to all users
SYSTEM_USER_ID = "SYSTEM"

# ── OpenAI ───────────────────────────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key and openai_api_key != "your_openai_api_key_here":
    openai_client = OpenAI(api_key=openai_api_key)
    print("✓ OpenAI client initialized")
else:
    openai_client = None
    print("✗ WARNING: OpenAI client not initialized (missing OPENAI_API_KEY)")

# ── AWS S3 ───────────────────────────────────────────────────
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "clyvara-uploads")

if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
    print(f"✓ S3 client initialized (Region: {AWS_REGION}, Bucket: {S3_BUCKET_NAME})")
else:
    s3_client = None
    print("✗ WARNING: S3 client not initialized (missing AWS credentials)")
