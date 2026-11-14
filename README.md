# Astronaut Health Python backend

This FastAPI service keeps Meteomatics credentials on the server and exposes a
small dashboard-safe endpoint:

```text
GET /api/environment/radiation?lat=28.5729&lon=-80.6490
```

## Run locally

From `C:\Users\rizza\Downloads`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:METEOMATICS_USERNAME = "your-username"
$env:METEOMATICS_PASSWORD = "your-password"
py -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. The service caches successful values for ten
minutes by default and can return a stale cached value when Meteomatics is
temporarily unavailable. This weather value is environmental context, not
spacecraft dosimeter data or absorbed astronaut dose.
