# DermaAI · Dermatology Workspace

Responsive clinician workspace with dermoscopy intake, CHI medication search, cryotherapy, electrosurgery, laser, filler, botulinum toxin, and UVB case forms. The bundled CHI Edition 59 reference has 26,134 entries.

## Docker on macOS

Install and open Docker Desktop, then run these commands from this directory:

```sh
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). Docker Compose builds the React frontend and Django API into one container, migrates the database, imports the formulary on first startup, and serves the interface. The seed is included, so no manual database or spreadsheet setup is required.

To stop the containers, press `Ctrl+C` and run:

```sh
docker compose down
```

The named `dermaai-data` volume preserves the database and uploads when containers stop or rebuild. **To permanently delete that local data**, run `docker compose down --volumes` from this directory.

Optional local configuration: copy `.env.example` to `.env`, then set a unique `DJANGO_SECRET_KEY` and, if needed, change `DERMAAI_PORT`. The default key is only suitable for local evaluation. To use another port without an env file, run `DERMAAI_PORT=8081 docker compose up --build`.

## Included features

- CHI search by indication, medicine name, pharmacological class, or ICD-10 code.
- Authenticated dermoscopy uploads, clinician notes, reviewed diagnosis, and explicit training-consent tracking. Images are only served through an authenticated endpoint.
- Electrosurgery intake for age, sex, diagnosis, site, lesion type/count, and device.
- Case forms for cryotherapy, laser, fillers, botulinum toxin, and UVB.
- Persistent SQLite database and private image storage in a Docker-managed volume.

The API is served on the same origin at `/api/v1/`. Health: `/api/v1/health/`; formulary: `/api/v1/formulary/`; clinician login: `/api/v1/auth/login/`; admin: `/admin/`.

To create an administrator for the Django admin, run:

```sh
docker compose exec app python manage.py createsuperuser
```

Superusers can sign in to the clinician workspace. To approve another clinician, open **Users** in Django admin and enable **Is verified clinician** for that account.

## Development

Frontend development server:

```sh
cd frontend
npm ci
npm run dev
```

The Vite server proxies `/api` to `localhost:8000`. For direct backend development, use Python 3.12+, install `backend/requirements.txt`, then run migrations and `python manage.py seed_formulary` from `backend/`.

## Model and procedure limitations

The archive and workspace contain no HAM10000 dataset, trained weights, model architecture, preprocessing specification, or class-label mapping. Dermoscopy intake and clinician review work, but automated diagnosis, confidence, and descriptive analysis are unavailable. Images submitted with a confirmed diagnosis and explicit consent are stored; no training pipeline is included.

All procedure endpoints return `501 Not Implemented` after validating clinician access and electrosurgery inputs. Freeze/thaw timing, electrosurgery power or anesthesia, laser settings, filler/Botox products or quantities, UVB dose, and Arabic pre/post instructions are intentionally not invented. Add device-specific, clinically approved sources before enabling those outputs.

The included SQLite seed contains the CHI formulary only. This is a local software demonstration, not a validated clinical decision-support system. Confirm reference data against current authoritative sources; do not expose it to the internet or store real patient information in it.