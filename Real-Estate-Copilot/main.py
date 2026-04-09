import sys
sys.path.insert(0, ".")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.routes:app", host="0.0.0.0", port=8000, reload=True)