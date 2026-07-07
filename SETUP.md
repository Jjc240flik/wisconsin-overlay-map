# Wisconsin Overlay Map – VPS Setup Guide (PRD v2.0)

This guide walks you through running the full **PRD v2.0 Spatial Pipeline** on your VPS.

## 1. Prerequisites

Make sure your VPS has the following installed:

- Docker
- Docker Compose
- Git

### Install Docker & Docker Compose (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## 2. Clone the Repository

```bash
git clone https://github.com/Jjc240flik/wisconsin-overlay-map.git
cd wisconsin-overlay-map
```

## 3. Start the Database

```bash
docker-compose up -d
```

This will start a PostGIS container with the database `wisconsin_spatial`.

Verify it's running:

```bash
docker ps
```

## 4. Run the Pipeline

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python main.py --county "Brown" --phase 1
```

## 5. Output Files

After a successful run, you will find the following in the `/output` folder:

| File                  | Description                              |
|-----------------------|------------------------------------------|
| `map.html`            | Interactive Folium map with targets      |
| `mailing_list.csv`    | Sorted list of target parcels (by acres) |

## 6. Important Notes

### Updating GIS Data Sources

The current `agents/harvester.py` contains **placeholder endpoints**. You will need to replace them with real Brown County open data URLs before running in production.

Edit this file:
```bash
nano agents/harvester.py
```

Look for the `self.endpoints` dictionary and update the URLs.

### Re-running the Pipeline

If you want to reset and run again:

```bash
docker-compose down -v          # Removes database volume
docker-compose up -d
python main.py --county "Brown" --phase 1
```

## 7. Troubleshooting

| Problem                        | Solution |
|--------------------------------|----------|
| `database does not exist`      | Already handled by `db/db_setup.py` |
| Port 5432 already in use       | Change the port in `docker-compose.yml` |
| Permission errors              | Run commands with `sudo` if needed |
| Missing Python packages        | Make sure you're inside the virtual environment |

---

**You are now ready to deploy and run the full spatial targeting pipeline on your VPS.**