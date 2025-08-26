from dotenv import load_dotenv
from fastapi import FastAPI

from .routes import generate_images, generate_text

load_dotenv()

app = FastAPI(
    title="MIR User Profiling API",
    description="API per generare descrizioni e immagini basate sui viaggi degli utenti",
    version="1.0.0",
)

app.include_router(generate_text.router)
app.include_router(generate_images.router)
