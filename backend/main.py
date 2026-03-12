"""
In your terminal make sure you're in the `backend` folder and run:
uvicorn main:app --reload

http://127.0.0.1:8000/docs for FastAPi auto-generated documentaiton
"""

# 127.0.0.1 is localhost IP address
# we are listening on port 8000



from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Earnings analayzer API is running"}