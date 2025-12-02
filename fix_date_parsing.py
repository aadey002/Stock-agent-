# -*- coding: utf-8 -*-

with open('C:/Users/adeto/Documents/Stock-agent-/web/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# Fix 1: Playbook Comparison date parsing
old_playbook = '''        tbody.innerHTML = allSignals.map(row => {
            // Parse CSV date format: "YYYY-MM-DD HH:MM:SS-TZ" - extract just the date part
            const dateStr = row.Date ? row.Date.split(' ')[0] : '';
            const date = dateStr || 'N/A';
            const signal = row.majority || 'NEUTRAL';'''

new_playbook = '''        tbody.innerHTML = allSignals.map(row => {
            // Parse CSV date format: "2023-05-01T00:00:00.000Z" - ISO format
            // Column name is lowercase 'date' not 'Date'
            const rawDate = row.date || row.Date || '';
            const dateStr = rawDate.split('T')[0]; // Split on T for ISO format
            const date = dateStr || 'N/A';
            const signal = row.majority || 'NEUTRAL';'''

if old_playbook in content:
    content = content.replace(old_playbook, new_playbook)
    changes += 1
    print("1. Fixed Playbook Comparison date parsing")
else:
    print("1. Could not find Playbook date parsing location")

# Fix 2: Ultra Confluence date parsing
old_ultra = '''        tbody.innerHTML = allSignals.map(row => {
            // Parse CSV date format: "YYYY-MM-DD HH:MM:SS-TZ" - extract just the date part
            const dateStr = row.Date ? row.Date.split(' ')[0] : '';
            const date = dateStr || 'N/A';
            const signal = row.majority || 'NEUTRAL';
            const signalClass = signal === 'CALL' ? 'badge-success' : signal === 'PUT' ? 'badge-danger' : 'badge-warning';
            const agents = `${row.call_votes || 0}C/${row.put_votes || 0}P/${row.hold_votes || 0}H`;'''

new_ultra = '''        tbody.innerHTML = allSignals.map(row => {
            // Parse CSV date format: "2023-05-01T00:00:00.000Z" - ISO format
            // Column name is lowercase 'date' not 'Date'
            const rawDate = row.date || row.Date || '';
            const dateStr = rawDate.split('T')[0]; // Split on T for ISO format
            const date = dateStr || 'N/A';
            const signal = row.majority || 'NEUTRAL';
            const signalClass = signal === 'CALL' ? 'badge-success' : signal === 'PUT' ? 'badge-danger' : 'badge-warning';
            const agents = `${row.call_votes || 0}C/${row.put_votes || 0}P/${row.hold_votes || 0}H`;'''

if old_ultra in content:
    content = content.replace(old_ultra, new_ultra)
    changes += 1
    print("2. Fixed Ultra Confluence date parsing")
else:
    print("2. Could not find Ultra Confluence date parsing location")

with open('C:/Users/adeto/Documents/Stock-agent-/web/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\\nTotal changes: {changes}")
