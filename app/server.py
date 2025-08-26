import uvicorn


def main():
    """
    Entry point per avviare il server FastAPI
    """
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
