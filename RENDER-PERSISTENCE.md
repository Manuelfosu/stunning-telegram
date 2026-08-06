# Render deployment and permanent data storage

SSGA HOLDINGS uses SQLite plus uploaded files. Environment variables point the app to storage, but **a Render persistent disk is required** to keep that storage across deployments.

## 1. Render service

Use these service settings:

- **Service type:** Web Service
- **Runtime:** Docker
- **Plan:** Starter or another paid plan that supports persistent disks
- **Dockerfile path:** `./Dockerfile`
- **Health check path:** `/api/health`

The free Render plan does not provide persistent disks and should not be used for this SQLite deployment.

## 2. Persistent disk

Attach this disk to the same web service:

| Setting | Value |
|---|---|
| Disk name | `ssga-persistent-data` |
| Mount path | `/var/data` |
| Size | `1 GB` or larger |

Do not change the mount path after the application has started storing live data.

## 3. Environment variables

Enter these values in Render → Service → Environment:

| Key | Value / information to enter |
|---|---|
| `DATABASE_URL` | `sqlite:////var/data/ssga.db` |
| `UPLOAD_DIR` | `/var/data/uploads` |
| `SECRET_KEY` | A permanent random secret of at least 32 characters. Generate it once and do not change it after deployment. Render Blueprint can generate this automatically. |
| `ADMIN_PHONE` | The phone number the administrator will use to log in, for example `0200000000` |
| `ADMIN_PASSWORD` | A strong administrator password. Do not use `admin123` in production. |
| `ALLOWED_ORIGINS` | Your deployed website origin, for example `https://ssga-holdings.onrender.com` (use the exact custom domain if you have one) |
| `ACCESS_TOKEN_MINUTES` | Optional. `10080` keeps sessions for seven days. |

## 4. Blueprint configuration

The included `render.yaml` already configures:

```yaml
plan: starter
disk:
  name: ssga-persistent-data
  mountPath: /var/data
  sizeGB: 1
envVars:
  - key: DATABASE_URL
    value: "sqlite:////var/data/ssga.db"
  - key: UPLOAD_DIR
    value: "/var/data/uploads"
```

When using the Blueprint, Render will ask you to provide `ADMIN_PASSWORD`. Confirm that the disk appears under **Service → Disks** before entering live data.

## 5. What remains after deployments

With the disk mounted correctly, these survive rebuilds and redeployments:

- Users and password records
- Wallet balances and transaction history
- Deposits and withdrawals
- Investments and daily-income credits
- Tasks, questions, advertisements and notifications
- Admin settings and activity logs
- Uploaded package, advertisement and broadcast images

## Important notes

- Environment variables alone do not preserve SQLite data; the persistent disk is mandatory.
- Data previously stored on Render's ephemeral filesystem cannot automatically move to the new disk. Export/import it before switching if it is still accessible.
- Do not delete the Render disk when redeploying.
- Do not change `DATABASE_URL` or `UPLOAD_DIR` after live data exists.
- Keep backups of `/var/data/ssga.db` before major releases.
