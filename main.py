from fastapi import FastAPI

app = FastAPI(title="Echo API", version="1.0.0")


@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Welcome to the Echo API", "endpoints": ["/echo"]}


@app.get("/echo")
async def echo(message: str):
    """
    Echo endpoint that takes a message parameter and returns it back.
    
    Args:
        message: The message to echo back
        
    Returns:
        The echoed message
    """
    return {"echoed_message": message}
