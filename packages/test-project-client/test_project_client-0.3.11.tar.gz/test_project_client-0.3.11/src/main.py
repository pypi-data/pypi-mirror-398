import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("src.api.server:create_app", factory=True, host="0.0.0.0", port=port, reload=True)
