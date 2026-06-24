# Event Management System

This repository contains a small web-based event management system. The application uses **Flask** with **SQLite** and provides a simple interface for managing customers, events, tickets and reservations.

## Features
- Add, view and delete customers
- Create events with different ticket types and prices
- Issue tickets and link them to events
- Book and cancel reservations
- Cancel entire events and refund reservations
- View statistics such as total revenue, active reservations and most popular event

## Project Structure
- **code/** – Flask application with HTML/CSS/JavaScript front‑end
  - `app.py` – main server application. When run for the first time it creates `EventManagement.db` automatically.
  - `templates/` – contains `index.html` which serves the user interface.
  - `static/` – JavaScript and CSS files used by the front‑end.
- **report/** – LaTeX sources and PDF report (in Greek) describing the database design.
- **Guidlines.pdf** – project specification.

## Requirements
- Python 3.8+
- Flask
- Flask-Cors

Install the dependencies with:

```bash
pip install Flask Flask-Cors
```

## Running the Application

### Local development

From the repository root run:

```bash
pip install -r code/requirements.txt
python code/app.py
```

The server starts on `http://localhost:5000/` and serves the web interface at the root URL. On first run a new SQLite database file `EventManagement.db` will be created.

### Docker (production)

```bash
cp .env.example .env   # optional; see comments in file
docker compose --profile prod up --build -d
```

| Service | URL |
|---------|-----|
| **Web app** | http://localhost/ |

Stop the stack with `docker compose --profile prod down`.

## Notes
The application was created as part of a university course (HY360). For further details on the database schema and queries see `report/report.pdf`.
