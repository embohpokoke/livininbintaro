# DEPLOYMENT GUIDE — LIVININBINTARO V2.0

**Version:** 1.0
**Date:** 2026-03-14
**Target:** VPS Hostinger (72.60.78.181)

---

## OVERVIEW

This guide covers deploying Livininbintaro V2.0 to production VPS with zero-downtime blue-green deployment strategy.

**Deployment Phases:**
1. Staging deployment and testing
2. Production cutover
3. Rollback procedure (if needed)
4. Post-deployment monitoring

**Estimated Time:** 4-6 hours (including testing)

---

## PRE-DEPLOYMENT CHECKLIST

Before starting deployment:

```bash
# Local verification
[ ] Frontend build completes without errors
[ ] Backend tests pass
[ ] .env.production configured
[ ] Database migrations ready (if any)
[ ] Rollback plan reviewed

# VPS verification
[ ] SSH access working
[ ] Disk space available (>10GB free)
[ ] PostgreSQL running
[ ] Nginx running
[ ] GOWA WhatsApp connected
[ ] Backup of V1 files created
```

---

## STEP 1: PREPARE PRODUCTION BUILD

### 1.1 Frontend Production Build

```bash
# On local Mac
cd ~/Desktop/project/livininbintaro/v2.0-pwa/frontend

# Update environment for production
cat > .env.production <<EOF
VITE_API_BASE_URL=https://livininbintaro.my.id/api
VITE_WA_NUMBER=6281288783088
EOF

# Build optimized production bundle
npm run build

# Verify build output
ls -lh dist/
# Expected: index.html, assets/, icons/, manifest.json

# Check bundle size
du -sh dist/
# Target: <500KB gzipped
```

**Build Optimization:**

Verify bundle size in `dist/assets/`:

```bash
cd dist/assets
ls -lh *.js *.css
# Expected:
# - index-[hash].js: ~150KB (gzipped ~50KB)
# - index-[hash].css: ~20KB (gzipped ~5KB)
# - vendor-[hash].js: ~80KB (Vue + dependencies)
```

If bundle too large:

```javascript
// vite.config.js - add code splitting
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'ui-vendor': ['@headlessui/vue']
        }
      }
    }
  }
})
```

### 1.2 Backend Preparation

```bash
cd ~/Desktop/project/livininbintaro/v2.0-pwa/backend

# Freeze dependencies
pip freeze > requirements.txt

# Create production .env template
cat > .env.production.template <<EOF
DATABASE_URL=postgresql://livin:PASSWORD@localhost:5432/livininbintaro
JWT_SECRET=GENERATE_WITH_OPENSSL
GOWA_URL=http://localhost:3003
GOWA_USERNAME=livinin
GOWA_PASSWORD=livininwa2026
OLLAMA_URL=http://localhost:11434
EOF
```

### 1.3 Create Deployment Package

```bash
cd ~/Desktop/project/livininbintaro/v2.0-pwa

# Create tarball
tar -czf livininbintaro-v2.0-$(date +%Y%m%d).tar.gz \
  frontend/dist/ \
  backend/ \
  --exclude=backend/venv \
  --exclude=backend/__pycache__ \
  --exclude=backend/.env

# Verify package
ls -lh livininbintaro-v2.0-*.tar.gz
# Expected: ~2-5MB
```

---

## STEP 2: STAGING DEPLOYMENT

### 2.1 Upload to VPS

```bash
# Upload deployment package
scp livininbintaro-v2.0-$(date +%Y%m%d).tar.gz vpshost:/tmp/

# SSH to VPS
ssh vpshost
```

### 2.2 Extract and Setup Staging

```bash
# Create staging directory
sudo mkdir -p /opt/livininbintaro-v2-staging
cd /opt/livininbintaro-v2-staging

# Extract package
sudo tar -xzf /tmp/livininbintaro-v2.0-*.tar.gz

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create production .env
cat > .env <<EOF
DATABASE_URL=postgresql://livin:$(cat /opt/livininbintaro/.db-password)@localhost:5432/livininbintaro
JWT_SECRET=$(openssl rand -hex 32)
GOWA_URL=http://localhost:3003
GOWA_USERNAME=livinin
GOWA_PASSWORD=livininwa2026
OLLAMA_URL=http://localhost:11434
EOF

chmod 600 .env
```

### 2.3 Create Systemd Service (Staging)

```bash
# Create service file
sudo cat > /etc/systemd/system/livininbintaro-v2-staging.service <<EOF
[Unit]
Description=Livininbintaro V2.0 API (Staging)
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/livininbintaro-v2-staging/backend
Environment="PATH=/opt/livininbintaro-v2-staging/backend/venv/bin"
ExecStart=/opt/livininbintaro-v2-staging/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8100 --workers 2
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable livininbintaro-v2-staging
sudo systemctl start livininbintaro-v2-staging

# Check status
sudo systemctl status livininbintaro-v2-staging
# Expected: Active (running)

# Verify API
curl http://localhost:8100/health
# Expected: {"status":"healthy","version":"2.0.0"}
```

### 2.4 Configure Nginx (Staging Subdomain)

```bash
# Backup existing nginx config
sudo cp /etc/nginx/conf.d/livininbintaro.conf \
       /etc/nginx/conf.d/livininbintaro.conf.backup-$(date +%Y%m%d)

# Create staging subdomain config
sudo cat > /etc/nginx/conf.d/livininbintaro-staging.conf <<EOF
server {
    listen 443 ssl;
    http2 on;
    server_name staging.livininbintaro.my.id;

    # SSL certificates (reuse main domain cert)
    ssl_certificate /etc/letsencrypt/live/livininbintaro.my.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/livininbintaro.my.id/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend SPA
    location / {
        root /var/www/livininbintaro-v2-staging;
        try_files \$uri \$uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Access log
    access_log /var/log/nginx/livininbintaro-staging.access.log;
    error_log /var/log/nginx/livininbintaro-staging.error.log;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name staging.livininbintaro.my.id;
    return 301 https://\$host\$request_uri;
}
EOF

# Copy frontend files to staging web root
sudo mkdir -p /var/www/livininbintaro-v2-staging
sudo cp -r /opt/livininbintaro-v2-staging/frontend/dist/* \
           /var/www/livininbintaro-v2-staging/

# Set permissions
sudo chown -R www-data:www-data /var/www/livininbintaro-v2-staging

# Test nginx config
sudo nginx -t
# Expected: syntax is okay, test is successful

# Reload nginx
sudo systemctl reload nginx
```

### 2.5 DNS Configuration (if needed)

```bash
# Add staging subdomain to DNS (if not already)
# Point staging.livininbintaro.my.id → 72.60.78.181

# Verify DNS propagation
dig staging.livininbintaro.my.id +short
# Expected: 72.60.78.181
```

### 2.6 SSL Certificate (if separate cert needed)

```bash
# If using separate cert for staging (optional)
sudo certbot certonly --nginx -d staging.livininbintaro.my.id

# Or reuse main domain cert (current config)
# No action needed
```

---

## STEP 3: STAGING TESTING

### 3.1 Automated Tests

```bash
# API health check
curl https://staging.livininbintaro.my.id/api/health
# Expected: {"status":"healthy","version":"2.0.0"}

# Test public endpoints
curl "https://staging.livininbintaro.my.id/api/public/listings?limit=5" | jq .total
# Expected: 17930

# Test authentication
curl -X POST https://staging.livininbintaro.my.id/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ocha@livininbintaro.my.id",
    "password": "PASSWORD"
  }' | jq .token
# Expected: JWT token string

# Test protected endpoint
TOKEN="eyJhbGci..."
curl https://staging.livininbintaro.my.id/api/leads \
  -H "Authorization: Bearer $TOKEN" | jq .total
# Expected: 110
```

### 3.2 Frontend Testing

Open browser and test:

```
https://staging.livininbintaro.my.id
```

**Public Pages:**
- [ ] Home page loads (<2s)
- [ ] Hero section displays
- [ ] Featured listings show (3 cards)
- [ ] Search page loads
- [ ] Filters work (property type, price range)
- [ ] Property detail page loads
- [ ] Images display
- [ ] Mobile responsive (test on phone)

**Agent Dashboard:**
- [ ] Login page loads
- [ ] Login works (email + password)
- [ ] Dashboard redirects after login
- [ ] Stats cards display
- [ ] Leads Kanban shows 5 columns
- [ ] Lead cards display in correct columns
- [ ] Drag-drop works (move lead between columns)
- [ ] Lead detail page loads
- [ ] Tabs work (WA, Notes, Activities, AI)
- [ ] WhatsApp conversation displays (if data exists)
- [ ] AI score badge shows

**PWA Features:**
- [ ] Service worker registers (DevTools → Application)
- [ ] Manifest loads (DevTools → Application → Manifest)
- [ ] Install prompt appears (wait ~30 seconds)
- [ ] Offline mode works (DevTools → Network → Offline, reload)
- [ ] Cache shows listings (DevTools → Application → Cache Storage)

### 3.3 Performance Testing

```bash
# Lighthouse CLI (on local Mac)
npm install -g lighthouse

lighthouse https://staging.livininbintaro.my.id \
  --output html \
  --output-path ./lighthouse-staging.html \
  --view

# Expected scores:
# Performance: >90
# Accessibility: >90
# Best Practices: >90
# SEO: >90
# PWA: Installable
```

### 3.4 Load Testing (Optional)

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test API endpoint
ab -n 1000 -c 10 https://staging.livininbintaro.my.id/api/public/listings

# Expected:
# Requests per second: >100
# Mean response time: <200ms
# Failed requests: 0
```

---

## STEP 4: PRODUCTION CUTOVER

**Prerequisites:**
- [ ] Staging testing passed (all checkboxes above)
- [ ] Erik approval received
- [ ] Backup plan ready
- [ ] Rollback tested
- [ ] Ocha notified (downtime window if any)

### 4.1 Backup V1

```bash
# Backup V1 files
sudo cp -r /var/www/livininbintaro \
           /var/www/livininbintaro-v1-backup-$(date +%Y%m%d)

sudo cp /etc/nginx/conf.d/livininbintaro.conf \
        /etc/nginx/conf.d/livininbintaro.conf.v1-backup-$(date +%Y%m%d)

# Backup database (optional, already in production)
pg_dump -U livin livininbintaro | gzip > \
  /opt/backups/livininbintaro-$(date +%Y%m%d).sql.gz

# Verify backups
ls -lh /var/www/livininbintaro-v1-backup-*/
ls -lh /opt/backups/livininbintaro-*.sql.gz
```

### 4.2 Deploy V2 to Production

```bash
# Copy staging to production directory
sudo cp -r /opt/livininbintaro-v2-staging /opt/livininbintaro-v2

# Copy frontend files to production web root
sudo mkdir -p /var/www/livininbintaro-v2
sudo cp -r /opt/livininbintaro-v2/frontend/dist/* \
           /var/www/livininbintaro-v2/

# Set permissions
sudo chown -R www-data:www-data /var/www/livininbintaro-v2
```

### 4.3 Create Production Systemd Service

```bash
# Create production service
sudo cat > /etc/systemd/system/livininbintaro-v2.service <<EOF
[Unit]
Description=Livininbintaro V2.0 API (Production)
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/livininbintaro-v2/backend
Environment="PATH=/opt/livininbintaro-v2/backend/venv/bin"
ExecStart=/opt/livininbintaro-v2/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8200 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=livininbintaro-v2

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable livininbintaro-v2
sudo systemctl start livininbintaro-v2

# Verify
sudo systemctl status livininbintaro-v2
curl http://localhost:8200/health
```

### 4.4 Update Nginx (Production Cutover)

```bash
# Update production nginx config
sudo cat > /etc/nginx/conf.d/livininbintaro.conf <<EOF
server {
    listen 443 ssl;
    http2 on;
    server_name livininbintaro.my.id www.livininbintaro.my.id;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/livininbintaro.my.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/livininbintaro.my.id/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend SPA (V2)
    location / {
        root /var/www/livininbintaro-v2;
        try_files \$uri \$uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Service worker (no cache)
        location = /sw.js {
            expires off;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }

        # Manifest (no cache)
        location = /manifest.json {
            expires off;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }
    }

    # API proxy (V2 on port 8200)
    location /api/ {
        proxy_pass http://127.0.0.1:8200;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # CORS (handled by FastAPI, but backup here)
        add_header Access-Control-Allow-Origin "https://livininbintaro.my.id" always;
    }

    # Legacy V1 API fallback (read-only, port 8000)
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # Images (shared with V1, no change)
    location /images/ {
        root /var/www/livininbintaro;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Access logs
    access_log /var/log/nginx/livininbintaro.access.log combined;
    error_log /var/log/nginx/livininbintaro.error.log warn;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name livininbintaro.my.id www.livininbintaro.my.id;
    return 301 https://livininbintaro.my.id\$request_uri;
}

# Redirect www to non-www
server {
    listen 443 ssl;
    http2 on;
    server_name www.livininbintaro.my.id;

    ssl_certificate /etc/letsencrypt/live/livininbintaro.my.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/livininbintaro.my.id/privkey.pem;

    return 301 https://livininbintaro.my.id\$request_uri;
}
EOF

# Test config
sudo nginx -t
# Expected: syntax is okay, test is successful

# Reload nginx (CUTOVER HAPPENS HERE)
sudo systemctl reload nginx
```

### 4.5 Verify Production

```bash
# Test from VPS
curl https://livininbintaro.my.id/api/health
# Expected: {"status":"healthy","version":"2.0.0"}

# Test from local Mac
curl https://livininbintaro.my.id
# Expected: V2 HTML

# Test in browser
# Open: https://livininbintaro.my.id
# Expected: V2 frontend loads
```

### 4.6 Stop V1 Services (Optional)

```bash
# Keep V1 services running for 24 hours as fallback
# After 24 hours of stable V2:

sudo systemctl stop livininbintaro-main
sudo systemctl stop livininbintaro-crm
sudo systemctl disable livininbintaro-main
sudo systemctl disable livininbintaro-crm

# Archive V1 files after 1 week:
# sudo tar -czf /opt/backups/livininbintaro-v1-archive-$(date +%Y%m%d).tar.gz \
#   /var/www/livininbintaro-v1-backup-* \
#   /root/livininbintaro.my.id \
#   /opt/livininbintaro
```

---

## STEP 5: ROLLBACK PROCEDURE

**If critical issues found in V2, rollback to V1:**

### 5.1 Quick Rollback (Nginx Only)

```bash
# Restore V1 nginx config
sudo cp /etc/nginx/conf.d/livininbintaro.conf.v1-backup-$(date +%Y%m%d) \
        /etc/nginx/conf.d/livininbintaro.conf

# Test and reload
sudo nginx -t && sudo systemctl reload nginx

# Verify
curl https://livininbintaro.my.id
# Expected: V1 frontend loads
```

### 5.2 Full Rollback (Services + Files)

```bash
# Stop V2 service
sudo systemctl stop livininbintaro-v2
sudo systemctl disable livininbintaro-v2

# Restart V1 services
sudo systemctl start livininbintaro-main
sudo systemctl start livininbintaro-crm

# Restore V1 nginx config (if not already done)
sudo cp /etc/nginx/conf.d/livininbintaro.conf.v1-backup-$(date +%Y%m%d) \
        /etc/nginx/conf.d/livininbintaro.conf

# Reload nginx
sudo nginx -t && sudo systemctl reload nginx

# Verify
curl https://livininbintaro.my.id/api/health
systemctl status livininbintaro-main
systemctl status livininbintaro-crm
```

---

## STEP 6: POST-DEPLOYMENT MONITORING

### 6.1 Monitor Logs

```bash
# Backend logs
sudo journalctl -u livininbintaro-v2 -f

# Nginx access logs
sudo tail -f /var/log/nginx/livininbintaro.access.log

# Nginx error logs
sudo tail -f /var/log/nginx/livininbintaro.error.log

# PostgreSQL logs (if issues)
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### 6.2 Monitor Metrics

```bash
# Check service status
sudo systemctl status livininbintaro-v2

# Check API response time
time curl https://livininbintaro.my.id/api/health
# Target: <100ms

# Check memory usage
free -h
ps aux | grep uvicorn

# Check disk usage
df -h

# Check database connections
psql -U livin -d livininbintaro -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='livininbintaro';"
# Target: <20 connections
```

### 6.3 Automated Monitoring (Optional)

Create monitoring script:

```bash
# /opt/scripts/monitor-v2.sh
#!/bin/bash

# Check API health
if ! curl -s https://livininbintaro.my.id/api/health | grep -q "healthy"; then
  echo "API health check failed!" | mail -s "ALERT: V2 API Down" erik@example.com
fi

# Check response time
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' https://livininbintaro.my.id)
if (( $(echo "$RESPONSE_TIME > 2" | bc -l) )); then
  echo "Response time: ${RESPONSE_TIME}s (threshold: 2s)" | \
    mail -s "ALERT: V2 Slow Response" erik@example.com
fi

# Check service status
if ! systemctl is-active --quiet livininbintaro-v2; then
  echo "V2 service is not running!" | mail -s "ALERT: V2 Service Down" erik@example.com
fi
```

```bash
# Make executable
chmod +x /opt/scripts/monitor-v2.sh

# Add to crontab (check every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/scripts/monitor-v2.sh") | crontab -
```

---

## MAINTENANCE TASKS

### Update SSL Certificate (Auto-renewal)

```bash
# Certbot auto-renews, verify cron job exists
sudo crontab -l | grep certbot

# Manual renewal (if needed)
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

### Restart Backend Service

```bash
# Graceful restart
sudo systemctl reload livininbintaro-v2

# Hard restart (if reload fails)
sudo systemctl restart livininbintaro-v2

# Check status
sudo systemctl status livininbintaro-v2
```

### Update Frontend

```bash
# On local Mac: rebuild
cd ~/Desktop/project/livininbintaro/v2.0-pwa/frontend
npm run build

# Upload to VPS
scp -r dist/* vpshost:/var/www/livininbintaro-v2/

# On VPS: set permissions
sudo chown -R www-data:www-data /var/www/livininbintaro-v2

# No nginx reload needed (static files)
```

### Update Backend

```bash
# On local Mac: create new package
cd ~/Desktop/project/livininbintaro/v2.0-pwa
tar -czf livininbintaro-v2-update-$(date +%Y%m%d).tar.gz backend/

# Upload to VPS
scp livininbintaro-v2-update-*.tar.gz vpshost:/tmp/

# On VPS: extract and restart
cd /opt/livininbintaro-v2
sudo tar -xzf /tmp/livininbintaro-v2-update-*.tar.gz
sudo systemctl restart livininbintaro-v2
```

### Database Maintenance

```bash
# Vacuum database
psql -U livin -d livininbintaro -c "VACUUM ANALYZE;"

# Check database size
psql -U livin -d livininbintaro -c \
  "SELECT pg_size_pretty(pg_database_size('livininbintaro'));"

# Check largest tables
psql -U livin -d livininbintaro -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
   LIMIT 10;"
```

---

## TROUBLESHOOTING

### Issue: 502 Bad Gateway

**Symptoms:**
- Nginx shows 502 error
- "upstream sent invalid header" in logs

**Solution:**

```bash
# Check backend service
sudo systemctl status livininbintaro-v2
sudo journalctl -u livininbintaro-v2 -n 50

# Restart backend
sudo systemctl restart livininbintaro-v2

# Check if backend is listening
sudo netstat -tlnp | grep 8200

# If backend won't start, check logs
sudo journalctl -u livininbintaro-v2 --since "5 minutes ago"
```

### Issue: Database Connection Error

**Symptoms:**
- "could not connect to server" in logs
- 500 errors on API calls

**Solution:**

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l | grep livininbintaro

# Check credentials
psql -U livin -d livininbintaro -c "SELECT 1;"

# Check .env file
cat /opt/livininbintaro-v2/backend/.env | grep DATABASE_URL
```

### Issue: Service Worker Not Updating

**Symptoms:**
- Old version cached
- Changes not visible

**Solution:**

```bash
# Update service worker version in code
# frontend/src/main.js or vite.config.js

# Force unregister (browser console)
navigator.serviceWorker.getRegistrations().then(function(registrations) {
  for(let registration of registrations) {
    registration.unregister()
  }
})

# Clear cache (browser console)
caches.keys().then(function(names) {
  for (let name of names) caches.delete(name);
});
```

### Issue: High Memory Usage

**Symptoms:**
- Uvicorn workers consuming >1GB RAM each
- VPS running out of memory

**Solution:**

```bash
# Reduce number of workers
# Edit /etc/systemd/system/livininbintaro-v2.service
# Change: --workers 4 → --workers 2

sudo systemctl daemon-reload
sudo systemctl restart livininbintaro-v2

# Check memory usage
ps aux | grep uvicorn
free -h
```

---

## SECURITY CHECKLIST

Post-deployment security verification:

```bash
# Check file permissions
ls -la /opt/livininbintaro-v2/backend/.env
# Expected: -rw------- (600)

ls -la /var/www/livininbintaro-v2
# Expected: drwxr-xr-x (755)

# Check open ports
sudo netstat -tlnp
# Expected: Only 80, 443, 22, 5432 (localhost only)

# Check firewall
sudo ufw status
# Expected: 80/tcp, 443/tcp, 22/tcp ALLOW

# Check SSL certificate
openssl s_client -connect livininbintaro.my.id:443 -servername livininbintaro.my.id < /dev/null | \
  openssl x509 -noout -dates
# Verify expiry date

# Test HTTPS redirect
curl -I http://livininbintaro.my.id
# Expected: 301 redirect to https

# Test security headers
curl -I https://livininbintaro.my.id
# Expected headers:
# - X-Frame-Options: SAMEORIGIN
# - X-Content-Type-Options: nosniff
# - X-XSS-Protection: 1; mode=block
# - Strict-Transport-Security: max-age=31536000
```

---

**Document Version:** 1.0
**Last Updated:** 2026-03-14
**Next Review:** After first production deployment
