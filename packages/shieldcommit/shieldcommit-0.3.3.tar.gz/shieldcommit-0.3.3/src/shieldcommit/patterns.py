# Patterns dictionary (industry-grade; many patterns).
# Tune and expand as needed.

PATTERNS = {
    # AWS
    "AWS Access Key ID": r"AKIA[0-9A-Z]{16}",
    "AWS Secret Access Key": r"(?i)aws(.{0,20})?(secret|access)?.{0,20}?['\"][0-9a-zA-Z/+]{40}['\"]",
    "AWS Session Token": r"(?i)x-amz-security-token",

    # Google
    "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Google OAuth Client Secret": r"(?i)google(.{0,20})?(client_secret)['\"][0-9A-Za-z-_]{24}",
    "Firebase Server Key": r"AAAA[A-Za-z0-9_-]{7}:[A-Za-z0-9_-]{140}",

    # OpenAI
    "OpenAI API Key": r"sk-[A-Za-z0-9]{20,}",
    "OpenAI Org Key": r"org-[A-Za-z0-9]{20,}",

    # GitHub / GitLab / Bitbucket
    "GitHub Token": r"gh[pousr]_[A-Za-z0-9]{30,}",
    "GitLab Personal Token": r"glpat-[0-9a-zA-Z\-]{20,}",
    "Bitbucket App Password": r"bbp_[A-Za-z0-9]{32}",

    # Stripe
    "Stripe Secret Key": r"sk_live_[0-9a-zA-Z]{24}",
    "Stripe Publishable Key": r"pk_live_[0-9a-zA-Z]{24}",

    # Slack
    "Slack Token": r"xox[baprs]-[0-9A-Za-z]{10,48}",
    "Slack Webhook URL": r"https://hooks.slack.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+",

    # Twilio
    "Twilio API Key": r"SK[0-9a-fA-F]{32}",
    "Twilio Account SID": r"AC[a-fA-F0-9]{32}",

    # Telegram
    "Telegram Bot Token": r"[0-9]{9}:[A-Za-z0-9_-]{35}",

    # Discord
    "Discord Bot Token": r"[MN][A-Za-z0-9\-_]{23}\.[A-Za-z0-9\-_]{6}\.[A-Za-z0-9\-_]{27}",

    # Dropbox
    "Dropbox Access Token": r"sl\.[A-Za-z0-9\-_]{60}",

    # Facebook
    "Facebook Access Token": r"EAACEdEose0cBA[0-9A-Za-z]+",

    # PayPal
    "PayPal Client ID": r"AdV[0-9A-Za-z\-]{80,}",
    "PayPal Secret": r"E[0-9A-Za-z]{80,}",

    # Azure
    "Azure Storage Key": r"(?i)(azure).{0,20}(account|key)['\"][A-Za-z0-9+/=]{40,}",
    "Azure DevOps Token": r"(?i)azd[o0]ps_pat_[A-Za-z0-9]{50,}",

    # JWT
    "JWT Token": r"eyJ[A-Za-z0-9_-]+?\.[A-Za-z0-9_-]+?\.[A-Za-z0-9_-]+",

    # SSH Keys
    "RSA Private Key": r"-----BEGIN RSA PRIVATE KEY-----",
    "DSA Private Key": r"-----BEGIN DSA PRIVATE KEY-----",
    "EC Private Key": r"-----BEGIN EC PRIVATE KEY-----",
    "OpenSSH Private Key": r"-----BEGIN OPENSSH PRIVATE KEY-----",

    # Databases
    "MongoDB URI": r"mongodb(\+srv)?:\/\/[^\"'\s]+",
    "PostgreSQL URI": r"postgres:\/\/[^\"'\s]+",
    "MySQL URI": r"mysql:\/\/[^\"'\s]+",

    # Cloudflare
    "Cloudflare API Key": r"(?i)(cloudflare).{0,20}(api|key)['\"][A-Za-z0-9]{37}",

    # Heroku
    "Heroku API Key": r"(?i)heroku(.{0,20})?(api|key)['\"][A-Za-z0-9]{32}",

    # Mailgun / SendGrid
    "Mailgun API Key": r"key-[0-9a-zA-Z]{32}",
    "SendGrid API Key": r"SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}",

    # Bearer / OAuth
    "Bearer Token": r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
    "OAuth Token (Google)": r"ya29\.[0-9A-Za-z\-_]+",

    # Generic
    "Generic Password": r"(?i)(password|passwd|pwd)['\"][^\"']{4,50}",
    "Generic Token": r"(?i)(token)['\"][A-Za-z0-9\-_]{10,}",
    "Generic Secret": r"(?i)(secret)['\"][A-Za-z0-9\-_]{10,}",

    # High-Entropy
    "High Entropy String": r"[A-Za-z0-9_\-]{32,}",

    # ENV patterns
    "ENV API Key": r"(?i)(api_key|apikey|api-key)['\"][A-Za-z0-9\-_]{12,}",
    "ENV Secret Key": r"(?i)(secret|secret_key)['\"][A-Za-z0-9\-_]{12,}",

    # Webhook
    "Generic Webhook": r"https:\/\/[^\s\"']+\/webhook[^\s\"']*",

    # Authorization header
    "Authorization Header": r"(?i)authorization:\s*[A-Za-z0-9_\-\.=]+",
}
