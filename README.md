# Orbit Health Console

Orbit Health Console is a NASA Space Apps prototype for astronaut health
decision support. It combines a local, low-data assessment workflow with a
personal 1G baseline, 0G trend comparison, explainable drift alerts, and an
optional Meteomatics environmental context service.

This project is a **prototype**. It is not a medical device, a diagnostic
system, a NASA-certified application, or a substitute for an onboard medical
officer or flight surgeon.

## Contents

- [Features](#features)
- [Project structure](#project-structure)
- [Requirements](#requirements)
- [Run locally](#run-locally)
- [Environment variables](#environment-variables)
- [Using the dashboard](#using-the-dashboard)
- [Backend API](#backend-api)
- [Data flow](#data-flow)
- [Deployment on Render](#deployment-on-render)
- [Connecting a custom domain](#connecting-a-custom-domain)
- [Security and privacy](#security-and-privacy)
- [Limitations and prototype status](#limitations-and-prototype-status)
- [Troubleshooting](#troubleshooting)
- [Development and validation](#development-and-validation)

## Features

### Assessment workflow

The Assessment tab accepts measurements that could be available through common
crew equipment or self-report:

- Resting heart rate
- Systolic and diastolic blood pressure
- Blood oxygen saturation (SpO2)
- Blood glucose
- Core temperature
- Sleep duration and sleep efficiency
- Reaction time
- Single-leg balance
- Fatigue, mood, and pain scores
- Symptoms such as dizziness, nausea, headache, vision changes, congestion,
  back pain, rash, and shortness of breath

The assessment:

1. Ignores blank optional fields rather than treating them as zero.
2. Classifies each supplied reading as `ok`, `watch`, or `alert`.
3. Produces a health index from 0 to 100 when at least one value or symptom is
   supplied.
4. Links findings to a body region, explanatory note, source context, and
   recommended action.
5. Escalates alert-level findings in the results dialog.

The thresholds are illustrative placeholders and must be replaced with
approved mission criteria before operational use.

### 1G to 0G monitor

The monitor compares a personal Earth/1G baseline with available
spaceflight/0G telemetry. It displays:

- Sleep efficiency
- Reaction time
- Resting heart rate
- Sensorimotor balance when compatible data is available
- Fluid-shift index when compatible data is available
- Environmental radiation proxy after a successful Meteomatics request
- Immune dysregulation status when compatible data is available

After **Run Assessment**, compatible submitted values update the monitor's
current telemetry values. The current implementation connects:

- `sleepEfficiency` to `sleep_efficiency_pct`
- `reaction` to `reaction_time_ms`
- `hr` to `heart_rate_bpm`

The historical sleep chart contains demonstration history. The latest 0G
sleep-efficiency point is replaced by the submitted sleep-efficiency value
after a successful assessment.

### Environmental context

The dashboard sends latitude and longitude to the FastAPI backend. The backend
requests Meteomatics `global_rad:W`, then returns the value to the browser.
Credentials never need to be sent to or embedded in the browser.

The returned value is an environmental radiation proxy in `W/m2`. It is not
spacecraft dosimeter data, absorbed astronaut dose, or a substitute for
mission radiation instrumentation.

### Reference and method views

The dashboard includes:

- NASA/OSDR and PSI source context
- A body-region knowledge base
- An explanation of the personal-baseline method
- Explicit prototype limitations
- A downloadable sample telemetry JSON document

## Project structure

```text
orbit-health/
|-- app.py                              FastAPI backend and API relay
|-- astronaut-health-console-nasa.html  Dashboard UI and browser logic
|-- requirements.txt                    Python dependencies
|-- README.md                           Project documentation
|-- .git/                               Git metadata
```

The dashboard is intentionally a single HTML file. The browser-side
assessment, monitor, chart, body map, and UI interactions are implemented in
that file. `app.py` serves the HTML and provides the server-side Meteomatics
relay.

## Requirements

- Windows PowerShell, macOS Terminal, or Linux shell
- Python 3.10 or newer recommended
- A Meteomatics account if live environmental radiation is required
- Git for source control and deployment

The Python dependencies are defined in [requirements.txt](requirements.txt):

- FastAPI
- HTTPX
- Uvicorn

## Run locally

Open PowerShell and change to the repository directory:

```powershell
cd C:\Users\rizza\Downloads\orbit\orbit-health
```

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, either allow local scripts for your user or
run the Uvicorn command using the environment's executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

Set Meteomatics credentials for the current PowerShell session:

```powershell
$env:METEOMATICS_USERNAME = "your-meteomatics-username"
$env:METEOMATICS_PASSWORD = "your-meteomatics-password"
```

Start the development server:

```powershell
py -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open the dashboard at <http://127.0.0.1:8000/>.

To stop the server, press `Ctrl+C`.

### Local preview without Meteomatics

The dashboard and local assessment still load without Meteomatics credentials.
The environmental request will show an explicit backend error, while the
local assessment and other offline-ready UI remain available.

### Local health check

With the server running, open:

<http://127.0.0.1:8000/api/health>

Expected response:

```json
{
  "status": "ok",
  "service": "astronaut-health-environment"
}
```

## Environment variables

| Variable | Required | Default | Description |
|---|---:|---|---|
| `METEOMATICS_USERNAME` | For live radiation | Empty | Meteomatics API username |
| `METEOMATICS_PASSWORD` | For live radiation | Empty | Meteomatics API password |
| `METEO_CACHE_SECONDS` | No | `600` | Successful response cache lifetime in seconds |

Never commit credentials to Git, place them in HTML, or include them in
screenshots. Use local environment variables for development and the hosting
provider's secret/environment-variable store for deployment.

## Using the dashboard

### Run an assessment

1. Open the **Assessment** tab.
2. Enter only measurements that were actually collected.
3. Leave unavailable fields blank; do not guess values.
4. Select applicable symptoms.
5. Click **Run Assessment**.
6. Review the result dialog, score, findings, sources, and recommended actions.
7. Open **1G <-> 0G Monitor** to review compatible submitted values against
   the personal baseline.

The **Load Sample Data** button is for demonstrations only. It fills the form
with illustrative values and immediately runs the assessment.

The **Clear** button removes Assessment form values and closes the result
dialog. It does not represent a clinical record deletion workflow.

### Refresh environmental radiation

1. Open **1G <-> 0G Monitor**.
2. Confirm or change the latitude and longitude.
3. Click **Refresh global radiation**.
4. Wait for the status message.
5. On success, the value is added to the environmental monitor card and drift
   comparison.

The page also attempts an automatic refresh every ten minutes. A successful
value is cached by the backend. If Meteomatics temporarily fails after a
successful request, the backend can return the last successful value with a
stale indicator.

## Backend API

### `GET /`

Returns the dashboard HTML file.

Example:

```text
http://127.0.0.1:8000/
```

### `GET /api/health`

Returns a simple service health response:

```json
{
  "status": "ok",
  "service": "astronaut-health-environment"
}
```

### `GET /api/environment/radiation`

Requests global radiation context for a coordinate.

Parameters:

| Parameter | Type | Constraints |
|---|---|---|
| `lat` | number | -90 through 90 |
| `lon` | number | -180 through 180 |

Example:

```text
GET /api/environment/radiation?lat=28.5729&lon=-80.6490
```

Successful response shape:

```json
{
  "source": "Meteomatics",
  "parameter": "global_rad:W",
  "latitude": 28.5729,
  "longitude": -80.649,
  "value": 410.0,
  "unit": "W/m2",
  "observed_at": "2026-11-15T00:00:00Z",
  "fetched_at": "2026-11-15T00:00:00Z",
  "cached": false,
  "stale": false
}
```

Possible errors:

- `422`: invalid or missing latitude/longitude
- `502`: Meteomatics returned an HTTP error, malformed data, or is unavailable
- `503`: backend credentials are not configured

## Data flow

```text
Assessment form
    |
    +--> browser-side evaluate()
    |       +--> findings, score, body status, actions
    |       +--> compatible values copied into current 0G monitor telemetry
    |
    +--> monitor comparison
            +--> personal 1G baseline
            +--> available 0G telemetry
            +--> OK/watch/alert drift classification

Latitude/longitude
    |
    +--> browser fetch()
            +--> FastAPI /api/environment/radiation
                    +--> Meteomatics API
                    +--> cached response
                    +--> environmental monitor card and alert row
```

The browser does not send Meteomatics credentials. The backend owns the
credentialed request and exposes only the dashboard-safe result.

## Deployment on Render

Create a **Web Service**, not a Static Site. The backend must run because it
serves the dashboard and relays the credentialed Meteomatics request.

Connect the GitHub repository and use:

| Render setting | Value |
|---|---|
| Language | Python 3 |
| Root directory | Leave blank |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app:app --host 0.0.0.0 --port $PORT` |

Add these Render environment variables:

```text
METEOMATICS_USERNAME=your-meteomatics-username
METEOMATICS_PASSWORD=your-meteomatics-password
```

Optional:

```text
METEO_CACHE_SECONDS=600
```

After the first deploy:

1. Open the Render service URL.
2. Check `/api/health`.
3. Open the Monitor tab.
4. Confirm the environmental request succeeds.
5. Confirm the radiation value appears in the monitor cards and drift alerts.
6. Check the Render logs if the request fails.

## Connecting a custom domain

The domain registrar and the hosting provider are separate concerns:

1. Deploy and test the Render service URL first.
2. Add the custom domain in Render.
3. Copy the exact DNS records Render provides.
4. Add those records at the provider controlling the domain's DNS.
5. Remove conflicting records for the same host.
6. Wait for DNS propagation and HTTPS certificate issuance.

Do not configure the same hostname with conflicting records at both Porkbun
and GoDaddy. Use the provider that currently controls the domain's
nameservers/DNS zone.

## Security and privacy

- Meteomatics credentials are read from server environment variables.
- Credentials are not included in the browser bundle.
- The uploaded image preview uses a local object URL and is not sent by the
  current application.
- The backend validates latitude and longitude ranges.
- HTTPX uses a request timeout for the external API call.
- Cached environmental values are held in process memory, not a persistent
  database.
- Do not enter real personally identifiable or sensitive medical information
  into a public demo deployment.
- Use HTTPS in production and protect any future patient/crew data store with
  appropriate authentication, authorization, auditing, retention, and
  encryption controls.

## Limitations and prototype status

This project intentionally has important limitations:

- Health thresholds are illustrative and are not approved flight-medicine
  criteria.
- OSDR is used as research context and mapping guidance; the dashboard does
  not currently query OSDR for live physiological records.
- The local 1G/0G fixture contains demonstration values.
- Only compatible Assessment fields update the current monitor telemetry.
- Single-leg balance is collected in seconds while the monitor's balance score
  is percentage-based, so it is not automatically converted.
- Fluid-shift and immune-dysregulation monitor values require compatible
  telemetry that the Assessment form does not currently collect.
- Meteomatics global radiation is environmental context, not dosimeter data or
  absorbed dose.
- The in-memory cache is lost when the process restarts and is not shared
  across multiple application instances.
- No user authentication, persistence, audit trail, role model, or clinical
  record integration is implemented.
- This repository does not claim NASA certification or clinical readiness.

Before any operational use, a qualified flight-medicine and engineering team
must validate datasets, units, thresholds, devices, alert policy, privacy
controls, failure modes, and clinical escalation procedures.

## Troubleshooting

### `fatal: not a git repository`

Run commands from the repository root:

```powershell
cd C:\Users\rizza\Downloads\orbit\orbit-health
```

### `Meteomatics credentials are not configured on the backend`

Set both environment variables in the same terminal session that starts
Uvicorn, or add them to the Render service's Environment settings.

### The website loads but the radiation card is absent

Check:

1. `/api/health` responds successfully.
2. The credentials are present in the running backend environment.
3. Latitude and longitude are valid.
4. The backend logs do not show a Meteomatics HTTP or response-format error.
5. The browser is loading the latest deployed commit rather than a cached page.

### Changes are not visible after deployment

Confirm that the changed file was committed and pushed:

```powershell
git status
git log -1 --oneline
git push origin main
```

Then trigger a new deploy if automatic deploys are disabled. Hard-refresh the
browser after deployment.

### Port or import errors locally

Confirm that dependencies are installed in the active environment:

```powershell
py -m pip install -r requirements.txt
py -m uvicorn app:app --host 127.0.0.1 --port 8000
```

## Development and validation

Check the working tree:

```powershell
git status
```

Check Python syntax:

```powershell
py -m py_compile app.py
```

Check the backend health endpoint while the server is running:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/health
```

Check formatting errors in the Git diff:

```powershell
git diff --check
```

Run the application locally before pushing UI or backend changes. Test both
credential-present and credential-missing behavior, and verify that the UI
shows explicit errors rather than silently presenting a successful-looking
environmental value.

## License and attribution

This repository is a NASA Space Apps prototype. NASA, OSDR, PSI, and
Meteomatics names and references identify the relevant source or context; they
do not imply NASA endorsement, certification, or ownership of this project.
