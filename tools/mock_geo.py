from fastapi import FastAPI, HTTPException

app = FastAPI()
down = {"a": False, "b": False}

@app.get("/a/json/{ip}")
def provider_a(ip: str):
    if down["a"]:
        raise HTTPException(status_code=503)
    return {"status": "success", "country": "MockLand-A", "city": "Alpha City"}

@app.get("/b/{ip}/json/")
def provider_b(ip: str):
    if down["b"]:
        raise HTTPException(status_code=503)
    return {"country_name": "MockLand-B", "city": "Beta City"}

@app.post("/toggle/{name}/{state}")
def toggle(name: str, state: str):
    down[name] = (state == "down")
    return down