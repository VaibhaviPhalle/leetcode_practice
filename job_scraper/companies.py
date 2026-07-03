"""
Company → ATS mapping.
Each entry: { "name", "tier", "ats", "slug", "careers_url" }

ats values:
  "greenhouse" → https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
  "lever"      → https://api.lever.co/v0/postings/{slug}?mode=json
  "ashby"      → https://jobs.ashbyhq.com/api/non-user-graphql (POST with orgName)
  "custom"     → direct career page URL, basic HTML scrape
"""

COMPANIES = [
    # ── FAANG ──────────────────────────────────────────────────────────────────
    {"name": "Google",          "tier": "FAANG",        "ats": "custom",      "slug": "google",          "careers_url": "https://careers.google.com/api/jobs/list/?page_size=20&q=engineer&location=california"},
    {"name": "Meta",            "tier": "FAANG",        "ats": "custom",      "slug": "meta",            "careers_url": "https://www.metacareers.com/graphql"},
    {"name": "Apple",           "tier": "FAANG",        "ats": "custom",      "slug": "apple",           "careers_url": "https://jobs.apple.com/api/role/search"},
    {"name": "Amazon",          "tier": "FAANG",        "ats": "custom",      "slug": "amazon",          "careers_url": "https://www.amazon.jobs/en/search.json"},
    {"name": "Netflix",         "tier": "FAANG",        "ats": "lever",       "slug": "netflix",         "careers_url": ""},
    {"name": "Microsoft",       "tier": "FAANG",        "ats": "custom",      "slug": "microsoft",       "careers_url": "https://gcsservices.careers.microsoft.com/search/api/v1/search"},

    # ── AI-First ───────────────────────────────────────────────────────────────
    {"name": "OpenAI",          "tier": "AI-First",     "ats": "ashby",       "slug": "openai",          "careers_url": ""},
    {"name": "Anthropic",       "tier": "AI-First",     "ats": "greenhouse",  "slug": "anthropic",       "careers_url": ""},
    {"name": "xAI",             "tier": "AI-First",     "ats": "greenhouse",  "slug": "x-ai",            "careers_url": ""},
    {"name": "Perplexity AI",   "tier": "AI-First",     "ats": "ashby",       "slug": "perplexity",      "careers_url": ""},
    {"name": "Scale AI",        "tier": "AI-First",     "ats": "greenhouse",  "slug": "scaleai",         "careers_url": ""},
    {"name": "Databricks",      "tier": "AI-First",     "ats": "greenhouse",  "slug": "databricks",      "careers_url": ""},
    {"name": "Weights & Biases","tier": "AI-First",     "ats": "lever",       "slug": "wandb",           "careers_url": ""},
    {"name": "Anyscale",        "tier": "AI-First",     "ats": "lever",       "slug": "anyscale",        "careers_url": ""},
    {"name": "Together AI",     "tier": "AI-First",     "ats": "ashby",       "slug": "togetherai",      "careers_url": ""},
    {"name": "Character AI",    "tier": "AI-First",     "ats": "ashby",       "slug": "character",       "careers_url": ""},
    {"name": "Harvey AI",       "tier": "AI-First",     "ats": "ashby",       "slug": "harvey",          "careers_url": ""},
    {"name": "Sierra",          "tier": "AI-First",     "ats": "ashby",       "slug": "sierra",          "careers_url": ""},
    {"name": "Physical Intelligence", "tier": "AI-First", "ats": "ashby",    "slug": "physicalintelligence", "careers_url": ""},
    {"name": "Contextual AI",   "tier": "AI-First",     "ats": "greenhouse",  "slug": "contextualai",    "careers_url": ""},
    {"name": "Cohere",          "tier": "AI-First",     "ats": "ashby",       "slug": "cohere",          "careers_url": ""},
    {"name": "Twelve Labs",     "tier": "AI-First",     "ats": "ashby",       "slug": "twelve-labs",     "careers_url": ""},
    {"name": "Moveworks",       "tier": "AI-First",     "ats": "greenhouse",  "slug": "moveworks",       "careers_url": ""},
    {"name": "Groq",            "tier": "AI-First",     "ats": "custom",      "slug": "groq",            "careers_url": "https://groq.com/careers/"},
    {"name": "Cerebras",        "tier": "AI-First",     "ats": "ashby",       "slug": "cerebras",        "careers_url": ""},
    {"name": "SambaNova",       "tier": "AI-First",     "ats": "greenhouse",  "slug": "sambanova-systems","careers_url": ""},
    {"name": "Glean",           "tier": "AI-First",     "ats": "custom",      "slug": "glean",           "careers_url": "https://glean.com/careers"},
    {"name": "Hugging Face",    "tier": "AI-First",     "ats": "lever",       "slug": "huggingface",     "careers_url": ""},
    {"name": "Pinecone",        "tier": "AI-First",     "ats": "ashby",       "slug": "pinecone",        "careers_url": ""},
    {"name": "Deepgram",        "tier": "AI-First",     "ats": "ashby",       "slug": "deepgram",        "careers_url": ""},
    {"name": "Writer",          "tier": "AI-First",     "ats": "ashby",       "slug": "writer",          "careers_url": ""},
    {"name": "Snorkel AI",      "tier": "AI-First",     "ats": "lever",       "slug": "snorkelai",       "careers_url": ""},
    {"name": "Arize AI",        "tier": "AI-First",     "ats": "lever",       "slug": "arizeai",         "careers_url": ""},
    {"name": "Fiddler AI",      "tier": "AI-First",     "ats": "greenhouse",  "slug": "fiddler",         "careers_url": ""},
    {"name": "Cleanlab",        "tier": "AI-First",     "ats": "ashby",       "slug": "cleanlab",        "careers_url": ""},
    {"name": "Labelbox",        "tier": "AI-First",     "ats": "greenhouse",  "slug": "labelbox",        "careers_url": ""},
    {"name": "Vectara",         "tier": "AI-First",     "ats": "greenhouse",  "slug": "vectara",         "careers_url": ""},
    {"name": "Lambda Labs",     "tier": "AI-First",     "ats": "lever",       "slug": "lambdalabs",      "careers_url": ""},
    {"name": "CoreWeave",       "tier": "AI-First",     "ats": "greenhouse",  "slug": "coreweave",       "careers_url": ""},
    {"name": "Luma AI",         "tier": "AI-First",     "ats": "ashby",       "slug": "lumalabs",        "careers_url": ""},
    {"name": "Midjourney",      "tier": "AI-First",     "ats": "ashby",       "slug": "midjourney",      "careers_url": ""},

    # ── Large Tech ─────────────────────────────────────────────────────────────
    {"name": "Nvidia",          "tier": "Large Tech",   "ats": "custom",      "slug": "nvidia",          "careers_url": "https://careers.nvidia.com/api/jobs"},
    {"name": "Salesforce",      "tier": "Large Tech",   "ats": "custom",      "slug": "salesforce",      "careers_url": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site"},
    {"name": "Adobe",           "tier": "Large Tech",   "ats": "custom",      "slug": "adobe",           "careers_url": "https://adobe.wd5.myworkdayjobs.com/external_experienced"},
    {"name": "Uber",            "tier": "Large Tech",   "ats": "greenhouse",  "slug": "uber-2",          "careers_url": ""},
    {"name": "Airbnb",          "tier": "Large Tech",   "ats": "greenhouse",  "slug": "airbnb",          "careers_url": ""},
    {"name": "Zoom",            "tier": "Large Tech",   "ats": "greenhouse",  "slug": "zoom",            "careers_url": ""},
    {"name": "Stripe",          "tier": "Large Tech",   "ats": "greenhouse",  "slug": "stripe",          "careers_url": ""},
    {"name": "Rippling",        "tier": "Large Tech",   "ats": "greenhouse",  "slug": "rippling",        "careers_url": ""},
    {"name": "Figma",           "tier": "Large Tech",   "ats": "greenhouse",  "slug": "figma",           "careers_url": ""},
    {"name": "Notion",          "tier": "Large Tech",   "ats": "ashby",       "slug": "notion",          "careers_url": ""},
    {"name": "Cloudflare",      "tier": "Large Tech",   "ats": "greenhouse",  "slug": "cloudflare",      "careers_url": ""},
    {"name": "Okta",            "tier": "Large Tech",   "ats": "greenhouse",  "slug": "okta",            "careers_url": ""},
    {"name": "ServiceNow",      "tier": "Large Tech",   "ats": "custom",      "slug": "servicenow",      "careers_url": "https://jobs.smartrecruiters.com/ServiceNow"},
    {"name": "Palo Alto Networks","tier": "Large Tech", "ats": "greenhouse",  "slug": "paloaltonetworks","careers_url": ""},
    {"name": "Confluent",       "tier": "Large Tech",   "ats": "greenhouse",  "slug": "confluent",       "careers_url": ""},
    {"name": "Elastic",         "tier": "Large Tech",   "ats": "greenhouse",  "slug": "elastic",         "careers_url": ""},
    {"name": "Snowflake",       "tier": "Large Tech",   "ats": "greenhouse",  "slug": "snowflake",       "careers_url": ""},
    {"name": "Palantir",        "tier": "Large Tech",   "ats": "lever",       "slug": "palantir",        "careers_url": ""},
    {"name": "Twilio",          "tier": "Large Tech",   "ats": "greenhouse",  "slug": "twilio",          "careers_url": ""},
    {"name": "Box",             "tier": "Large Tech",   "ats": "greenhouse",  "slug": "box",             "careers_url": ""},
    {"name": "Pinterest",       "tier": "Large Tech",   "ats": "greenhouse",  "slug": "pinterest",       "careers_url": ""},
    {"name": "LinkedIn",        "tier": "Large Tech",   "ats": "custom",      "slug": "linkedin",        "careers_url": "https://careers.linkedin.com"},

    # ── Consumer & Growth ──────────────────────────────────────────────────────
    {"name": "Lyft",            "tier": "Consumer",     "ats": "greenhouse",  "slug": "lyft",            "careers_url": ""},
    {"name": "DoorDash",        "tier": "Consumer",     "ats": "custom",      "slug": "doordash",        "careers_url": "https://careers.doordash.com"},
    {"name": "Instacart",       "tier": "Consumer",     "ats": "greenhouse",  "slug": "instacart",       "careers_url": ""},
    {"name": "Reddit",          "tier": "Consumer",     "ats": "greenhouse",  "slug": "reddit",          "careers_url": ""},
    {"name": "Discord",         "tier": "Consumer",     "ats": "greenhouse",  "slug": "discord",         "careers_url": ""},
    {"name": "Dropbox",         "tier": "Consumer",     "ats": "greenhouse",  "slug": "dropbox",         "careers_url": ""},
    {"name": "Roblox",          "tier": "Consumer",     "ats": "greenhouse",  "slug": "roblox",          "careers_url": ""},

    # ── Enterprise SaaS ────────────────────────────────────────────────────────
    {"name": "Intuit",          "tier": "Enterprise",   "ats": "greenhouse",  "slug": "intuit",          "careers_url": ""},
    {"name": "Workday",         "tier": "Enterprise",   "ats": "custom",      "slug": "workday",         "careers_url": "https://workday.wd5.myworkdayjobs.com/Workday"},
    {"name": "Veeva Systems",   "tier": "Enterprise",   "ats": "greenhouse",  "slug": "veeva-systems",   "careers_url": ""},
    {"name": "Informatica",     "tier": "Enterprise",   "ats": "greenhouse",  "slug": "informatica",     "careers_url": ""},
    {"name": "DocuSign",        "tier": "Enterprise",   "ats": "greenhouse",  "slug": "docusign",        "careers_url": ""},
    {"name": "Zendesk",         "tier": "Enterprise",   "ats": "greenhouse",  "slug": "zendesk",         "careers_url": ""},
    {"name": "PagerDuty",       "tier": "Enterprise",   "ats": "greenhouse",  "slug": "pagerduty",       "careers_url": ""},
    {"name": "New Relic",       "tier": "Enterprise",   "ats": "greenhouse",  "slug": "new-relic",       "careers_url": ""},
    {"name": "Asana",           "tier": "Enterprise",   "ats": "greenhouse",  "slug": "asana",           "careers_url": ""},
    {"name": "Airtable",        "tier": "Enterprise",   "ats": "greenhouse",  "slug": "airtable",        "careers_url": ""},
    {"name": "Amplitude",       "tier": "Enterprise",   "ats": "greenhouse",  "slug": "amplitude",       "careers_url": ""},
    {"name": "Mixpanel",        "tier": "Enterprise",   "ats": "greenhouse",  "slug": "mixpanel",        "careers_url": ""},
    {"name": "Medallia",        "tier": "Enterprise",   "ats": "greenhouse",  "slug": "medallia",        "careers_url": ""},
    {"name": "Zuora",           "tier": "Enterprise",   "ats": "greenhouse",  "slug": "zuora",           "careers_url": ""},
    {"name": "Nutanix",         "tier": "Enterprise",   "ats": "greenhouse",  "slug": "nutanix",         "careers_url": ""},
    {"name": "Pure Storage",    "tier": "Enterprise",   "ats": "greenhouse",  "slug": "pure-storage",    "careers_url": ""},
    {"name": "NetApp",          "tier": "Enterprise",   "ats": "greenhouse",  "slug": "netapp",          "careers_url": ""},

    # ── Fintech ────────────────────────────────────────────────────────────────
    {"name": "Visa",            "tier": "Fintech",      "ats": "custom",      "slug": "visa",            "careers_url": "https://jobs.smartrecruiters.com/Visa"},
    {"name": "PayPal",          "tier": "Fintech",      "ats": "custom",      "slug": "paypal",          "careers_url": "https://paypal.eightfold.ai/careers"},
    {"name": "Block",           "tier": "Fintech",      "ats": "greenhouse",  "slug": "block",           "careers_url": ""},
    {"name": "Brex",            "tier": "Fintech",      "ats": "greenhouse",  "slug": "brex",            "careers_url": ""},
    {"name": "Affirm",          "tier": "Fintech",      "ats": "greenhouse",  "slug": "affirm",          "careers_url": ""},
    {"name": "Chime",           "tier": "Fintech",      "ats": "greenhouse",  "slug": "chime",           "careers_url": ""},
    {"name": "Robinhood",       "tier": "Fintech",      "ats": "greenhouse",  "slug": "robinhood",       "careers_url": ""},
    {"name": "Plaid",           "tier": "Fintech",      "ats": "greenhouse",  "slug": "plaid",           "careers_url": ""},
    {"name": "Coinbase",        "tier": "Fintech",      "ats": "greenhouse",  "slug": "coinbase",        "careers_url": ""},
    {"name": "Marqeta",         "tier": "Fintech",      "ats": "greenhouse",  "slug": "marqeta",         "careers_url": ""},
    {"name": "Nerdwallet",      "tier": "Fintech",      "ats": "greenhouse",  "slug": "nerdwallet",      "careers_url": ""},

    # ── Dev Tools & Infrastructure ─────────────────────────────────────────────
    {"name": "GitHub",          "tier": "Dev Tools",    "ats": "custom",      "slug": "github",          "careers_url": "https://github.careers/careers"},
    {"name": "Atlassian",       "tier": "Dev Tools",    "ats": "greenhouse",  "slug": "atlassian",       "careers_url": ""},
    {"name": "Datadog",         "tier": "Dev Tools",    "ats": "greenhouse",  "slug": "datadog",         "careers_url": ""},
    {"name": "JFrog",           "tier": "Dev Tools",    "ats": "greenhouse",  "slug": "jfrog",           "careers_url": ""},
    {"name": "HashiCorp",       "tier": "Dev Tools",    "ats": "custom",      "slug": "hashicorp",       "careers_url": "https://www.hashicorp.com/careers"},
    {"name": "Sumo Logic",      "tier": "Dev Tools",    "ats": "greenhouse",  "slug": "sumologic",       "careers_url": ""},

    # ── Unicorns ───────────────────────────────────────────────────────────────
    {"name": "Gusto",           "tier": "Unicorn",      "ats": "greenhouse",  "slug": "gusto",           "careers_url": ""},
    {"name": "Carta",           "tier": "Unicorn",      "ats": "greenhouse",  "slug": "carta",           "careers_url": ""},
    {"name": "Samsara",         "tier": "Unicorn",      "ats": "greenhouse",  "slug": "samsara",         "careers_url": ""},
    {"name": "Verkada",         "tier": "Unicorn",      "ats": "greenhouse",  "slug": "verkada",         "careers_url": ""},
    {"name": "Faire",           "tier": "Unicorn",      "ats": "greenhouse",  "slug": "faire",           "careers_url": ""},
    {"name": "Flexport",        "tier": "Unicorn",      "ats": "greenhouse",  "slug": "flexport",        "careers_url": ""},
    {"name": "Lattice",         "tier": "Unicorn",      "ats": "greenhouse",  "slug": "lattice",         "careers_url": ""},

    # ── Cybersecurity ──────────────────────────────────────────────────────────
    {"name": "Zscaler",         "tier": "Cybersecurity","ats": "greenhouse",  "slug": "zscaler",         "careers_url": ""},
    {"name": "CrowdStrike",     "tier": "Cybersecurity","ats": "custom",      "slug": "crowdstrike",     "careers_url": "https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers"},
    {"name": "Fortinet",        "tier": "Cybersecurity","ats": "custom",      "slug": "fortinet",        "careers_url": "https://www.fortinet.com/corporate/careers"},
    {"name": "SentinelOne",     "tier": "Cybersecurity","ats": "custom",      "slug": "sentinelone",     "careers_url": "https://www.sentinelone.com/careers/"},
    {"name": "Check Point",     "tier": "Cybersecurity","ats": "custom",      "slug": "checkpoint",      "careers_url": "https://www.checkpoint.com/careers/"},

    # ── Semiconductors ─────────────────────────────────────────────────────────
    {"name": "Qualcomm",        "tier": "Semiconductor","ats": "custom",      "slug": "qualcomm",        "careers_url": "https://careers.qualcomm.com/careers"},
    {"name": "Synopsys",        "tier": "Semiconductor","ats": "custom",      "slug": "synopsys",        "careers_url": "https://synopsys.wd1.myworkdayjobs.com/careers"},
    {"name": "Cadence",         "tier": "Semiconductor","ats": "custom",      "slug": "cadence",         "careers_url": "https://cadence.wd1.myworkdayjobs.com/External_Careers"},
    {"name": "Applied Materials","tier": "Semiconductor","ats": "custom",     "slug": "appliedmaterials","careers_url": "https://careers.appliedmaterials.com"},

    # ── Robotics & Autonomous ──────────────────────────────────────────────────
    {"name": "Waymo",           "tier": "Robotics",     "ats": "greenhouse",  "slug": "waymo",           "careers_url": ""},
    {"name": "Tesla",           "tier": "Robotics",     "ats": "custom",      "slug": "tesla",           "careers_url": "https://www.tesla.com/careers/search"},
    {"name": "Figure AI",       "tier": "Robotics",     "ats": "ashby",       "slug": "figure-ai",       "careers_url": ""},
    {"name": "Cruise",          "tier": "Robotics",     "ats": "custom",      "slug": "cruise",          "careers_url": "https://getcruise.com/careers"},
]
