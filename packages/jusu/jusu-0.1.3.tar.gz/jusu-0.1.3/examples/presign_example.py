"""Example FastAPI app demonstrating presigned upload flow (demo only).

Run with:

    pip install -e .[web]
    uvicorn examples.presign_example:app --reload

The example uses a dummy client when boto3 is not available to avoid adding a hard
dependency; in production replace `DummyClient` with `boto3.client('s3')`.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from JUSU.storage import generate_s3_presigned_post

app = FastAPI()


class DummyClient:
    def generate_presigned_post(self, bucket, key, ExpiresIn=3600):
        return {"url": f"https://s3.example/{bucket}/{key}", "fields": {"key": key}}


@app.post('/presign')
async def presign(bucket: str = 'my-bucket', key: str = 'uploads/object'):
    # swap in a real boto3 client in production
    client = DummyClient()
    data = generate_s3_presigned_post(client, bucket, key)
    return JSONResponse(content=data)
