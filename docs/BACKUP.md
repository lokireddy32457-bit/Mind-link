# Mind Link — Backup Strategy

This document describes the PostgreSQL backup strategy for the production VPS.

> [!IMPORTANT]
> These backups run on the **VPS** via cron. No cloud credentials are stored in this repository.

---

## Backup Architecture

```
PostgreSQL 16 (mindlink_db)
        ↓
    pg_dump (daily)
        ↓
  gzip compression
        ↓
  /var/backups/mindlink/  (local VPS storage)
        ↓
  (Optional) Remote copy via rsync/scp to separate location
```

---

## Backup Schedule

| Type | Frequency | Retention |
|---|---|---|
| Daily full dump | Every day at 02:00 AM | 30 days |
| Weekly archive | Every Sunday at 03:00 AM | 12 weeks |

---

## Setting Up Automated Backups

### 1. Create the Backup Directory

```bash
sudo mkdir -p /var/backups/mindlink
sudo chown deploy:deploy /var/backups/mindlink
sudo chmod 750 /var/backups/mindlink
```

### 2. Create the Backup Script

```bash
sudo nano /usr/local/bin/mindlink-backup.sh
```

Paste the following:

```bash
#!/bin/bash
# =========================================
# Mind Link — PostgreSQL Backup Script
# =========================================
set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────────
DB_NAME="mindlink_db"
DB_USER="mindlink_user"
DB_HOST="127.0.0.1"
BACKUP_DIR="/var/backups/mindlink"
RETENTION_DAYS=30
DATE=$(date +%Y-%m-%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/mindlink_${DATE}.sql.gz"

# ─── Create backup ────────────────────────────────────────────────────────────
echo "[$(date)] Starting backup: ${BACKUP_FILE}"

pg_dump \
    --username="${DB_USER}" \
    --host="${DB_HOST}" \
    --dbname="${DB_NAME}" \
    --no-owner \
    --no-acl \
    --format=plain \
    | gzip -9 > "${BACKUP_FILE}"

# Verify the file was created and has content
if [ ! -s "${BACKUP_FILE}" ]; then
    echo "[$(date)] ERROR: Backup file is empty or missing!" >&2
    exit 1
fi

FILE_SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
echo "[$(date)] Backup complete: ${BACKUP_FILE} (${FILE_SIZE})"

# ─── Rotate old backups ───────────────────────────────────────────────────────
echo "[$(date)] Removing backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "mindlink_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Rotation complete."

# ─── List current backups ─────────────────────────────────────────────────────
echo "[$(date)] Current backups:"
ls -lh "${BACKUP_DIR}"/mindlink_*.sql.gz 2>/dev/null | tail -10

echo "[$(date)] Backup job finished successfully."
```

Make it executable:

```bash
sudo chmod +x /usr/local/bin/mindlink-backup.sh
```

### 3. Configure PGPASSWORD (or .pgpass)

Create a `.pgpass` file so the script can connect without prompting for a password:

```bash
# Format: hostname:port:database:username:password
echo "127.0.0.1:5432:mindlink_db:mindlink_user:YOUR_DB_PASSWORD" > /home/deploy/.pgpass
chmod 600 /home/deploy/.pgpass
```

### 4. Set Up Cron Job

```bash
crontab -e -u deploy
```

Add these lines:

```cron
# Mind Link — Daily backup at 2:00 AM
0 2 * * * /usr/local/bin/mindlink-backup.sh >> /var/log/mindlink-backup.log 2>&1

# Mind Link — Weekly archive copy (Sunday 3:00 AM, keep 12 weeks)
0 3 * * 0 cp /var/backups/mindlink/$(ls -t /var/backups/mindlink/ | head -1) \
             /var/backups/mindlink/weekly_$(date +\%Y-W\%V).sql.gz
```

### 5. Test the Backup Script

Run it manually first to verify it works:

```bash
sudo -u deploy /usr/local/bin/mindlink-backup.sh
ls -lh /var/backups/mindlink/
```

---

## Backup Verification

Verify a backup is valid by testing a restore to a test database:

```bash
# Create a test database
sudo -u postgres psql -c "CREATE DATABASE mindlink_test;"
sudo -u postgres psql -c "GRANT ALL ON DATABASE mindlink_test TO mindlink_user;"

# Restore the latest backup
LATEST=$(ls -t /var/backups/mindlink/mindlink_*.sql.gz | head -1)
gunzip -c "${LATEST}" | psql -U mindlink_user -h 127.0.0.1 -d mindlink_test

# Verify row counts
psql -U mindlink_user -h 127.0.0.1 -d mindlink_test -c "
    SELECT 'appointments' AS tbl, COUNT(*) FROM appointments
    UNION ALL SELECT 'inquiries', COUNT(*) FROM inquiries
    UNION ALL SELECT 'admin_users', COUNT(*) FROM admin_users;
"

# Drop the test database
sudo -u postgres psql -c "DROP DATABASE mindlink_test;"
```

Run this verification test **monthly** or after any major database change.

---

## Restore Procedure

### Step 1 — Stop the Application

```bash
sudo systemctl stop mindlink
```

### Step 2 — Drop and Recreate the Database

```bash
sudo -u postgres psql -c "DROP DATABASE mindlink_db;"
sudo -u postgres psql -c "CREATE DATABASE mindlink_db OWNER mindlink_user;"
sudo -u postgres psql -c "GRANT ALL ON DATABASE mindlink_db TO mindlink_user;"
sudo -u postgres psql -c "\c mindlink_db; GRANT ALL ON SCHEMA public TO mindlink_user;"
```

### Step 3 — Restore from Backup

```bash
# List available backups
ls -lh /var/backups/mindlink/

# Restore a specific backup (replace FILENAME with the actual file):
gunzip -c /var/backups/mindlink/FILENAME.sql.gz | \
    psql -U mindlink_user -h 127.0.0.1 -d mindlink_db
```

### Step 4 — Verify the Restore

```bash
psql -U mindlink_user -h 127.0.0.1 -d mindlink_db -c "
    SELECT 'appointments' AS tbl, COUNT(*) FROM appointments
    UNION ALL SELECT 'inquiries', COUNT(*) FROM inquiries
    UNION ALL SELECT 'admin_users', COUNT(*) FROM admin_users;
"
```

### Step 5 — Restart the Application

```bash
sudo systemctl start mindlink
sudo systemctl status mindlink
journalctl -u mindlink -n 30 --no-pager
```

---

## Off-Site Backup (Optional)

For additional protection, copy backups to a separate location. Options:

### Option A — Rsync to Another Server

```bash
rsync -avz --delete \
    /var/backups/mindlink/ \
    user@backup-server:/backups/mindlink/
```

Add to cron (run after the daily backup):

```cron
30 2 * * * rsync -avz --delete /var/backups/mindlink/ user@backup-server:/backups/mindlink/
```

### Option B — rclone to Object Storage (Cloudflare R2, Backblaze B2, etc.)

```bash
# Install rclone (https://rclone.org/install/)
curl https://rclone.org/install.sh | sudo bash

# Configure your storage provider
rclone config

# Daily sync (add to cron after backup)
rclone sync /var/backups/mindlink/ remote:mindlink-backups/
```

> [!IMPORTANT]
> Do not store rclone credentials or cloud API keys in the Git repository.
> Store them in the rclone config file (`~/.config/rclone/rclone.conf`) on the VPS only.

---

## Disaster Recovery

| Scenario | Recovery Time | Data Loss Risk | Action |
|---|---|---|---|
| App crash (Gunicorn) | < 1 min | None | systemd auto-restarts |
| VPS reboot | 1-2 min | None | systemd starts on boot |
| Database corruption | 5-15 min | Up to 24 hours | Restore from last daily backup |
| VPS total failure | 30-60 min | Up to 24 hours | Provision new VPS, restore from off-site backup |
| Accidental data deletion | 5-15 min | Up to 24 hours | Restore from last daily backup |

### Minimum Viable Recovery

1. New VPS with Ubuntu 24.04
2. Follow `docs/DEPLOYMENT.md` from scratch
3. Restore database from most recent off-site backup
4. Update DNS to new server IP
5. Reissue SSL certificate

---

## Backup Log Monitoring

```bash
# View backup log
cat /var/log/mindlink-backup.log

# Check last backup result
tail -20 /var/log/mindlink-backup.log

# List all current backups and sizes
ls -lh /var/backups/mindlink/ | sort -k9

# Total backup storage used
du -sh /var/backups/mindlink/
```
