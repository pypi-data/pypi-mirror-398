# ShieldCommit 🔐 (Beta)

ShieldCommit is a lightweight security CLI tool that helps prevent accidental
secret leaks by scanning Git commits for sensitive information such as
cloud credentials, API keys, and tokens.

 ![logo.png](logo.png)

This project is currently in **beta** and actively evolving.

---

## 🚨 Why ShieldCommit Exists

This tool was born from a real-world mistake.

While working on an AWS EKS project, I accidentally used an **extended support Kubernetes version** in Terraform.
That small configuration oversight resulted in **unexpectedly high cloud costs**.

👉 I wrote about this incident here:  
📖 Medium: <https://medium.com/@krishnafattepurkar/how-i-accidentally-chose-an-extended-support-kubernetes-version-on-eks-and-paid-extra-because-i-6bbad34d2d4d>

That experience made me realize:
- Small mistakes in config or secrets can cause **huge impact**
- Most tools are powerful but sometimes **overkill for personal or small projects**

So I decided to build **my own simple, focused tool**.

---

### 🧰 Industry Tools & Motivation

There are many well-established tools in the ecosystem for detecting secrets and improving security workflows, such as:

- **Gitleaks**
- **TruffleHog**
- **GitGuardian**
- **Detect Secrets (Yelp)**

These tools are widely used across the industry.

While exploring security practices and learning from real production mistakes, I decided to build something **of my own** — a tool that helps me understand the problem deeply, experiment with ideas, and evolve it step by step.

ShieldCommit started as a **personal learning project**, focused on:
- Catching obvious secret leaks early
- Keeping the workflow simple
- Growing gradually with practical use

In upcoming versions, the tool will expand beyond secret scanning to include **version-related checks**, such as:
- Detecting unsupported or risky software versions
- Highlighting configuration choices that may lead to unexpected costs or security risks

This project is intentionally evolving, with features added based on real-world experience and lessons learned.

---

## 🎯 What ShieldCommit Does (Current)

✅ Scans Git commits for hardcoded secrets  
✅ Blocks commits if secrets are detected  
✅ Works as a Git pre-commit hook  
✅ Simple CLI — one command setup  
✅ No external services, no heavy dependencies  

---

## 🔍 Supported Secret Detection (v0.x)

- AWS Access Keys
- Google Cloud API Keys
- GitHub Tokens
- Generic API tokens
- Common secret patterns

> ⚠️ Note: This is **pattern-based detection**, not entropy-based (yet).

---

## 📦 Installation

```bash
pip install shieldcommit  
```
  
Verify installation:

```bash
shieldcommit --help
```

## 🔧 Getting Started (Quick Setup)

**2️⃣ Initialize a Git repository (if not already)**

```bash
git init
```

**3️⃣ Install ShieldCommit Git hook**

```bash
shieldcommit install
```

✅ This installs a **pre-commit hook** in your repository.

## 🔒 How It Works

Once installed:

- Every `git commit` automatically scans **staged files**
- If secrets are detected → **commit is blocked**
- You'll see the file, line number, and matched pattern
- Fix or remove the secret, then commit again

This ensures secrets never accidentally reach your Git history.