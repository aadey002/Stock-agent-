\# 📱 Notification System Setup Guide

\# 📱 Notification System Setup Guide



\## Quick Start



The Stock Agent notification system supports multiple channels:

\- 📧 Email (SMTP)

\- 💬 Discord webhooks

\- 📱 Slack webhooks



---



\## 🔧 Configuration



\### Option 1: Discord (Recommended - Easiest!)



1\. \*\*Create Discord Server\*\* (if you don't have one)

&nbsp;  - Open Discord

&nbsp;  - Click "+" → "Create My Own" → "For me and my friends"

&nbsp;  - Name it "Trading Alerts"



2\. \*\*Create Webhook\*\*

&nbsp;  - Right-click your server → "Server Settings"

&nbsp;  - Click "Integrations" → "Webhooks"

&nbsp;  - Click "New Webhook"

&nbsp;  - Name it "Stock Agent"

&nbsp;  - Select channel (e.g., #alerts)

&nbsp;  - Click "Copy Webhook URL"



3\. \*\*Add to GitHub Secrets\*\*

&nbsp;  - Go to GitHub: Settings → Secrets → Actions

&nbsp;  - Click "New repository secret"

&nbsp;  - Name: `DISCORD\_WEBHOOK`

&nbsp;  - Value: Paste your webhook URL

&nbsp;  - Click "Add secret"

&nbsp;  

&nbsp;  - Add another secret:

&nbsp;  - Name: `DISCORD\_ENABLED`

&nbsp;  - Value: `true`



---



\### Option 2: Slack



1\. \*\*Create Slack Workspace\*\* (if needed)

&nbsp;  - Go to slack.com

&nbsp;  - Create workspace



2\. \*\*Create Incoming Webhook\*\*

&nbsp;  - Go to api.slack.com/apps

&nbsp;  - Click "Create New App" → "From scratch"

&nbsp;  - Name: "Stock Agent"

&nbsp;  - Select your workspace

&nbsp;  - Click "Incoming Webhooks"

&nbsp;  - Toggle "Activate Incoming Webhooks" to ON

&nbsp;  - Click "Add New Webhook to Workspace"

&nbsp;  - Select channel

&nbsp;  - Click "Allow"

&nbsp;  - Copy webhook URL



3\. \*\*Add to GitHub Secrets\*\*

&nbsp;  - Name: `SLACK\_WEBHOOK` → Value: Your webhook URL

&nbsp;  - Name: `SLACK\_ENABLED` → Value: `true`



---



\### Option 3: Email (Gmail)



1\. \*\*Enable App Password\*\* (for Gmail)

&nbsp;  - Go to myaccount.google.com

&nbsp;  - Security → 2-Step Verification (enable if not enabled)

&nbsp;  - App passwords

&nbsp;  - Select app: "Mail"

&nbsp;  - Select device: "Other" → "Stock Agent"

&nbsp;  - Click "Generate"

&nbsp;  - Copy the 16-character password



2\. \*\*Add to GitHub Secrets\*\*

&nbsp;  - `EMAIL\_ENABLED` → `true`

&nbsp;  - `EMAIL\_FROM` → your.email@gmail.com

&nbsp;  - `EMAIL\_PASSWORD` → app password from step 1

&nbsp;  - `EMAIL\_TO` → recipient@email.com

&nbsp;  - `SMTP\_SERVER` → `smtp.gmail.com`

&nbsp;  - `SMTP\_PORT` → `587`



---



\## 🧪 Test Notifications



\### Test Locally

```powershell

cd C:\\StockAgent\\Stock-agent-\\notifications

python notifier.py

```



You should see:

```

Testing basic alert...

Testing trading signal...

Testing health alert...

Testing daily summary...

```



\### Test on GitHub Actions



After setting up secrets, your workflows will automatically send notifications when:

\- ✅ Trading signals are generated

\- ⚠️ System health degrades

\- 🚨 Critical errors occur

\- 📊 Daily summary (optional)



---



\## 📊 Notification Types



\### 1. Trading Signals

Sent when new signals are generated:

```

🎯 New Trading Signal: CALL

Entry: $450.50

Stop: $445.00

Target: $460.00

```



\### 2. Health Alerts

Sent when system health degrades:

```

🚨 System Health Alert: DEGRADED

Failed Checks: Data Feed

Review system immediately

```



\### 3. Daily Summary

Sent at end of day with performance:

```

📊 Daily Trading Summary

Total Trades: 12

Win Rate: 58.3%

Total P\&L: $1,250.75

```



---



\## ⚙️ Customization



\### Change Notification Frequency



Edit workflow files to adjust when notifications are sent.



\### Add More Channels



The notifier.py supports easy extension. Add your own notification method in the `Notifier` class.



---



\## 🆘 Troubleshooting



\### Discord: "Webhook not found"

\- Verify webhook URL is correct

\- Check webhook wasn't deleted

\- Ensure webhook is for correct channel



\### Email: "Authentication failed"

\- Use app password, not account password

\- Enable 2-factor authentication first

\- Check SMTP settings are correct



\### Slack: "Invalid webhook URL"

\- Verify webhook URL copied completely

\- Check webhook is still active

\- Try recreating webhook



---



\## 📱 Mobile Setup



\### Discord Mobile

1\. Install Discord app

2\. Enable push notifications

3\. Get alerts on your phone!



\### Slack Mobile

1\. Install Slack app

2\. Enable notifications

3\. Receive instant alerts



---



\## 🎯 Best Practices



✅ \*\*Start with Discord\*\* - Easiest to set up  

✅ \*\*Test before trading\*\* - Verify notifications work  

✅ \*\*Set quiet hours\*\* - Avoid notification overload  

✅ \*\*Use different channels\*\* - Signals vs. alerts  

✅ \*\*Monitor regularly\*\* - Don't rely solely on notifications  



---



\*\*Now you'll never miss a trading signal!\*\* 🚀

\## Quick Start



The Stock Agent notification system supports multiple channels:

\- 📧 Email (SMTP)

\- 💬 Discord webhooks

\- 📱 Slack webhooks



---



\## 🔧 Configuration



\### Option 1: Discord (Recommended - Easiest!)



1\. \*\*Create Discord Server\*\* (if you don't have one)

&nbsp;  - Open Discord

&nbsp;  - Click "+" → "Create My Own" → "For me and my friends"

&nbsp;  - Name it "Trading Alerts"



2\. \*\*Create Webhook\*\*

&nbsp;  - Right-click your server → "Server Settings"

&nbsp;  - Click "Integrations" → "Webhooks"

&nbsp;  - Click "New Webhook"

&nbsp;  - Name it "Stock Agent"

&nbsp;  - Select channel (e.g., #alerts)

&nbsp;  - Click "Copy Webhook URL"



3\. \*\*Add to GitHub Secrets\*\*

&nbsp;  - Go to GitHub: Settings → Secrets → Actions

&nbsp;  - Click "New repository secret"

&nbsp;  - Name: `DISCORD\_WEBHOOK`

&nbsp;  - Value: Paste your webhook URL

&nbsp;  - Click "Add secret"

&nbsp;  

&nbsp;  - Add another secret:

&nbsp;  - Name: `DISCORD\_ENABLED`

&nbsp;  - Value: `true`



---



\### Option 2: Slack



1\. \*\*Create Slack Workspace\*\* (if needed)

&nbsp;  - Go to slack.com

&nbsp;  - Create workspace



2\. \*\*Create Incoming Webhook\*\*

&nbsp;  - Go to api.slack.com/apps

&nbsp;  - Click "Create New App" → "From scratch"

&nbsp;  - Name: "Stock Agent"

&nbsp;  - Select your workspace

&nbsp;  - Click "Incoming Webhooks"

&nbsp;  - Toggle "Activate Incoming Webhooks" to ON

&nbsp;  - Click "Add New Webhook to Workspace"

&nbsp;  - Select channel

&nbsp;  - Click "Allow"

&nbsp;  - Copy webhook URL



3\. \*\*Add to GitHub Secrets\*\*

&nbsp;  - Name: `SLACK\_WEBHOOK` → Value: Your webhook URL

&nbsp;  - Name: `SLACK\_ENABLED` → Value: `true`



---



\### Option 3: Email (Gmail)



1\. \*\*Enable App Password\*\* (for Gmail)

&nbsp;  - Go to myaccount.google.com

&nbsp;  - Security → 2-Step Verification (enable if not enabled)

&nbsp;  - App passwords

&nbsp;  - Select app: "Mail"

&nbsp;  - Select device: "Other" → "Stock Agent"

&nbsp;  - Click "Generate"

&nbsp;  - Copy the 16-character password



2\. \*\*Add to GitHub Secrets\*\*

&nbsp;  - `EMAIL\_ENABLED` → `true`

&nbsp;  - `EMAIL\_FROM` → your.email@gmail.com

&nbsp;  - `EMAIL\_PASSWORD` → app password from step 1

&nbsp;  - `EMAIL\_TO` → recipient@email.com

&nbsp;  - `SMTP\_SERVER` → `smtp.gmail.com`

&nbsp;  - `SMTP\_PORT` → `587`



---



\## 🧪 Test Notifications



\### Test Locally

```powershell

cd C:\\StockAgent\\Stock-agent-\\notifications

python notifier.py

```



You should see:

```

Testing basic alert...

Testing trading signal...

Testing health alert...

Testing daily summary...

```



\### Test on GitHub Actions



After setting up secrets, your workflows will automatically send notifications when:

\- ✅ Trading signals are generated

\- ⚠️ System health degrades

\- 🚨 Critical errors occur

\- 📊 Daily summary (optional)



---



\## 📊 Notification Types



\### 1. Trading Signals

Sent when new signals are generated:

```

🎯 New Trading Signal: CALL

Entry: $450.50

Stop: $445.00

Target: $460.00

```



\### 2. Health Alerts

Sent when system health degrades:

```

🚨 System Health Alert: DEGRADED

Failed Checks: Data Feed

Review system immediately

```



\### 3. Daily Summary

Sent at end of day with performance:

```

📊 Daily Trading Summary

Total Trades: 12

Win Rate: 58.3%

Total P\&L: $1,250.75

```



---



\## ⚙️ Customization



\### Change Notification Frequency



Edit workflow files to adjust when notifications are sent.



\### Add More Channels



The notifier.py supports easy extension. Add your own notification method in the `Notifier` class.



---



\## 🆘 Troubleshooting



\### Discord: "Webhook not found"

\- Verify webhook URL is correct

\- Check webhook wasn't deleted

\- Ensure webhook is for correct channel



\### Email: "Authentication failed"

\- Use app password, not account password

\- Enable 2-factor authentication first

\- Check SMTP settings are correct



\### Slack: "Invalid webhook URL"

\- Verify webhook URL copied completely

\- Check webhook is still active

\- Try recreating webhook



---



\## 📱 Mobile Setup



\### Discord Mobile

1\. Install Discord app

2\. Enable push notifications

3\. Get alerts on your phone!



\### Slack Mobile

1\. Install Slack app

2\. Enable notifications

3\. Receive instant alerts



---



\## 🎯 Best Practices



✅ \*\*Start with Discord\*\* - Easiest to set up  

✅ \*\*Test before trading\*\* - Verify notifications work  

✅ \*\*Set quiet hours\*\* - Avoid notification overload  

✅ \*\*Use different channels\*\* - Signals vs. alerts  

✅ \*\*Monitor regularly\*\* - Don't rely solely on notifications  



---



\*\*Now you'll never miss a trading signal!\*\* 🚀

