"""
In your terminal make sure you're in the `backend` folder and run:
uvicorn main:app --reload

http://127.0.0.1:8000/docs for FastAPi auto-generated documentaiton
"""


"""
cd backend
source venv/bin/activate
"""


# 127.0.0.1 is localhost IP address
# we are listening on port 8000





from fastapi import FastAPI
from database import engine
import models

# tells SQLAlcehmy to look at all models (python classes) and create the corresponding tables in Postgres if they dont exist yet
# just a sfety net to keep models and DB in sync in case one is changed and forget to update the other (so Python and SQL schema always matching)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Earnings analayzer API is running"}