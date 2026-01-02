# PyAutokit Examples

Complete working examples demonstrating all PyAutokit modules.

## 📁 File Organizer Examples

### Basic Organization

```bash
# Organize Downloads by category (Documents, Images, etc.)
python organize_downloads.py

# Test without moving files (dry-run)
python organize_downloads.py --dry-run

# Organize by file extension
python organize_downloads.py --method extension

# Show statistics only
python organize_downloads.py --stats
```

### Advanced: Auto-Watch Mode

```bash
# Continuously watch and organize new downloads
python organize_downloads.py --watch

# Watch with custom interval (60 seconds)
python organize_downloads.py --watch --interval 60
```

**Note**: Auto-watch requires `watchdog` package:
```bash
pip install watchdog
```

## 🌐 Web Scraper Examples

```bash
# Scrape Hacker News headlines
python scrape_news.py

# Output saved to: data/news_headlines.json
```

## 📧 Email Automation Examples

```bash
# Send bulk personalized emails
python send_bulk_emails.py
```

**Note**: Configure email settings in `.env` first:
```bash
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

## 💾 Backup Examples

```bash
# Backup current project
python backup_project.py

# Backups saved to: backups/
```

## 📊 Log Analyzer Examples

```bash
# Analyze log files
python analyze_logs.py

# Note: Run other pyautokit scripts first to generate logs
```

## ⛓️ Blockchain Monitor Examples

```bash
# Check current EGLD price and trending coins
python monitor_egld.py

# Output includes:
# - Current prices for EGLD, BTC, ETH, BNB
# - 24h price changes
# - Top trending cryptocurrencies
```

## 🔧 Customization

All examples can be customized by:

1. **Editing the script** - Modify parameters, add features
2. **Using command-line arguments** - Most scripts accept `--help`
3. **Configuring .env** - Set defaults for API keys, credentials

## 💡 Tips

- Start with `organize_downloads.py --dry-run` to test safely
- Use `--stats` flag to preview what will be organized
- Check logs in `logs/` directory for detailed information
- All examples create necessary directories automatically

## 🚀 Next Steps

1. Run examples to see PyAutokit in action
2. Modify examples for your specific needs
3. Combine multiple modules for complex workflows
4. Create your own automation scripts using PyAutokit

## 📚 Documentation

For full module documentation, see the main [README.md](../README.md)
