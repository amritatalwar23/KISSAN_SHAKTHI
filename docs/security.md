# Kisan Shakti — Security & Privacy Architecture

## 1. Secrets and Credential Management
- No API keys, credentials, or secrets are hardcoded in the codebase.
- Configuration is loaded via environment variables from `.env` (template provided in `.env.example`).
- `.env`, SQLite databases (`*.db`), model weights (`*.pth`), and raw image caches are excluded in `.gitignore`.

---

## 2. File Upload Safeguards
- **MIME Type Validation**: Rejects non-image files (`image/jpeg`, `image/png`, `image/webp` allowed).
- **Payload Size Limits**: Strict 10 MB maximum upload size enforced (`MAX_UPLOAD_SIZE_MB = 10`).
- **Integrity Verification**: Images are decompressed and verified with Pillow before being passed to PyTorch tensors to prevent image bomb exploits.
- **Out-of-Distribution Checks**: Images with near-zero pixel variance are caught and rejected.

---

## 3. Privacy & Farmer Data Protection
- Queries and predictions logged for analytics are stripped of personally identifiable information (PII).
- Phone numbers, Aadhaar numbers, and bank details are never requested or stored.
- Severe crisis messages are not permanently linked to user IP addresses.

---

## 4. Production Deployment Checklist
Before public deployment beyond the local prototype:
1. Enable HTTPS / SSL termination at a reverse proxy (e.g. Nginx or Cloudflare).
2. Configure rate limiting on `/predict/disease` and `/query` (e.g. `slowapi` or Redis token bucket).
3. Set restrictive CORS origins instead of wildcards.
4. Establish regular backup policies for the SQLite analytics database.
