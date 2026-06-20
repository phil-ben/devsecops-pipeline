# DevSecOps Pipeline — Security-Integrated CI/CD Demo

<img alt="gitleaks badge" src="https://img.shields.io/badge/protected%20by-gitleaks-blue">

A complete **shift-left DevSecOps pipeline** built with GitHub Actions, demonstrated against a
**deliberately vulnerable Flask application**. The app ships with intentional, CWE-mapped
security flaws so the pipeline's SAST, SCA, and DAST stages have real vulnerabilities to detect —
showing security scanning embedded across the full software development lifecycle.

> ⚠️ **WARNING — INTENTIONALLY VULNERABLE.**
> `app.py` contains deliberate security vulnerabilities and hardcoded secrets **for demonstration
> only**. This application must **never** be deployed to a production, internet-facing, or shared
> environment. It exists solely as a scanning target to prove the pipeline works.

---

## What this demonstrates

- Embedding **SAST, SCA, DAST, and secret scanning** as automated stages in a CI/CD pipeline
- **Shift-left security** — catching vulnerabilities at build time, not in production
- Mapping findings to **OWASP / CWE** vulnerability classes
- Multi-stage **GitHub Actions** orchestration with job dependencies and a self-hosted runner
- Test automation with **coverage reporting** feeding into static analysis

---

## Pipeline architecture

```
push / pull_request -> main
        |
        v
+---------------------+
| 1. TEST (ubuntu)    |  pytest + pytest-cov -> coverage (XML/HTML)
|                     |  -> upload artifacts -> Codecov
+----------+----------+
           | needs: test
           v
+----------------------+
| 2. SAST (self-hosted)|  SonarQube scan (consumes coverage XML)
+----------+-----------+
           |
+----------v----------+      +----------------------+
| 3. SCA (ubuntu)     |      | SECRET-SCAN (ubuntu) |  Gitleaks (full history)
|     Trivy fs scan   |      +----------------------+
+----------+----------+
           | needs: [sast, sca]
           v
+---------------------+
| 4. DAST (ubuntu)    |  start Flask app -> OWASP ZAP full scan
+---------------------+
```

| Stage | Job | Tool(s) | Purpose |
|-------|-----|---------|---------|
| Test + Coverage | `test` (ubuntu) | pytest, pytest-cov, Codecov | Run unit tests, generate coverage, publish to Codecov |
| **SAST** | `sast` (self-hosted) | SonarQube | Static analysis of source for code-level vulnerabilities |
| **SCA** | `sca` (ubuntu) | Trivy | Scan dependencies/filesystem for known CVEs |
| **Secret scan** | `secret-scan` (ubuntu) | Gitleaks | Detect hardcoded secrets across full git history |
| **DAST** | `dast` (ubuntu) | OWASP ZAP | Dynamic scan against the running app for runtime vulnerabilities |

**Triggers:** push and pull request to `main`.

---

## The deliberately planted vulnerabilities

The Flask app exposes endpoints that each demonstrate a common vulnerability class — the targets the
pipeline is designed to catch:

| Endpoint | Vulnerability | CWE |
|----------|---------------|-----|
| `/login` | SQL Injection (unparameterized query) | CWE-89 |
| `/search` | Reflected Cross-Site Scripting (XSS) | CWE-79 |
| `/ping` | OS Command Injection (`shell=True`) | CWE-78 |
| `/file` | Path Traversal | CWE-22 |
| `app.py` (module) | Hardcoded credentials / secrets | CWE-798 |
| `app.run(debug=True)` | Active debug in production config | CWE-489 |

This CWE mapping is the point: it gives SAST/SCA/DAST/secret-scanning concrete, verifiable findings
and demonstrates fluency with the OWASP Top Ten / CWE vulnerability taxonomy.

---

## Running locally

> Run only on an isolated local machine. Never expose this app to a network.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app (binds to port 5000)
python app.py

# 3. Run tests with coverage
pip install pytest pytest-cov
pytest --cov=. --cov-report=term --cov-report=html
```

App available at `http://127.0.0.1:5000` — endpoints: `/`, `/login`, `/search`, `/ping`, `/file`.

---

## Screenshots

See the `screens/` directory for pipeline runs and scan outputs (SAST/SCA/DAST findings, coverage reports).

---

## Tech stack

`Python` · `Flask` · `GitHub Actions` · `SonarQube (SAST)` · `Trivy (SCA)` · `Gitleaks (secret scanning)` ·
`OWASP ZAP (DAST)` · `pytest` / `pytest-cov` · `Codecov` · self-hosted runner

---

## Repository structure

```
devsecops-pipeline/
├── .github/workflows/devsecops.yml   # pipeline: test -> SAST -> SCA / secret-scan -> DAST
├── app.py                            # deliberately vulnerable Flask app (scan target)
├── requirements.txt                  # Python dependencies
├── tests/                            # unit tests
├── .coveragerc                       # coverage configuration
├── sonar-project.properties          # SonarQube scan configuration
├── screens/                          # pipeline & scan-result screenshots
├── .gitignore
└── README.md
```

---

