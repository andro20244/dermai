# DermaAI

The supplied ZIP contained a Django API and CHI medicine formulary, but no working frontend or Docker setup. The completed application is in [`dermaAi_full_project_with_chi`](dermaAi_full_project_with_chi/).

## Run on macOS

1. Install and open [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. In Terminal, from the cloned repository, run:

   ```sh
   cd dermaAi_full_project_with_chi
   docker compose up --build
   ```

3. Open [http://localhost:8080](http://localhost:8080). The initial build downloads dependencies and the first startup imports the formulary; allow a little extra time on that first run.

To stop the app, press `Ctrl+C`, then run `docker compose down`. Your local database and uploads stay in a Docker volume between runs. To use a different port, run `DERMAAI_PORT=8081 docker compose up --build` and open `http://localhost:8081`.

See the [application guide](dermaAi_full_project_with_chi/README.md) for the API, admin setup, and data notes.

## Current limitations

The workspace contains no HAM10000 dataset, trained weights, or model architecture/preprocessing metadata, so dermoscopy image upload works but automated diagnosis does not. Procedure modules collect case details but withhold treatment settings and instructions until validated sources are supplied. This is a local reference app, not a clinical decision-support system. Do not expose it to the internet or store real patient information in it.