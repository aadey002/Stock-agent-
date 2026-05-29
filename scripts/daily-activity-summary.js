// Daily Activity Summary
import { execSync } from 'child_process';
import fs from 'fs';

const timestamp = new Date().toLocaleString('en-US', { timeZone: 'America/New_York' });
const dateStr = new Date().toISOString().split('T')[0];

function run(cmd) {
  try {
    return execSync(cmd, { timeout: 30000, encoding: 'utf8' }).trim();
  } catch (err) {
    return err.stdout?.toString().trim() || '';
  }
}

function categorizeCommit(msg) {
  if (msg.startsWith('feat:')) return 'New Features';
  if (msg.startsWith('fix:')) return 'Bug Fixes';
  if (msg.startsWith('refactor:')) return 'Refactoring';
  if (msg.startsWith('docs:')) return 'Documentation';
  if (msg.startsWith('test:')) return 'Testing';
  if (msg.startsWith('chore:') || msg.startsWith('ci:')) return 'Infrastructure';
  return 'Other';
}

function main() {
  const since = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const commitLog = run('git log --since="' + since + '" --pretty=format:"%h|%s|%an|%ai" --no-merges');

  if (!commitLog) {
    const report = '# Daily Activity Summary\n**Date:** ' + dateStr + '\n**Generated:** ' + timestamp + ' ET\n\n---\n\nNo development activity in the last 24 hours.\n';
    fs.mkdirSync('reports', { recursive: true });
    fs.writeFileSync('reports/activity-summary-' + dateStr + '.md', report);
    console.log('No activity. Minimal report saved.');
    return;
  }

  const commits = commitLog.split('\n').map(line => {
    const [hash, message, author, date] = line.split('|');
    return { hash, message, author, date };
  });

  const filesChanged = run('git log --since="' + since + '" --pretty=format: --name-only --no-merges');
  const uniqueFiles = [...new Set(filesChanged.split('\n').filter(f => f.trim()))];
  const diffStat = run('git log --since="' + since + '" --stat --no-merges --pretty=format:""');
  const insertions = (diffStat.match(/(\d+) insertions?/g) || []).reduce((sum, m) => sum + parseInt(m), 0);
  const deletions = (diffStat.match(/(\d+) deletions?/g) || []).reduce((sum, m) => sum + parseInt(m), 0);

  const categories = {};
  for (const c of commits) {
    const cat = categorizeCommit(c.message);
    if (!categories[cat]) categories[cat] = [];
    categories[cat].push(c);
  }

  let report = '# Daily Activity Summary\n';
  report += '**Date:** ' + dateStr + '  \n';
  report += '**Generated:** ' + timestamp + ' ET  \n\n---\n\n';
  report += '## Overview\n\n';
  report += '- **' + commits.length + ' commits** by ' + [...new Set(commits.map(c => c.author))].join(', ') + '\n';
  report += '- **' + uniqueFiles.length + ' files changed** (+' + insertions + ' / -' + deletions + ' lines)\n\n---\n\n';
  report += '## Changes\n\n';

  for (const cat of ['New Features', 'Bug Fixes', 'Refactoring', 'Documentation', 'Testing', 'Infrastructure', 'Other']) {
    if (!categories[cat]) continue;
    report += '### ' + cat + '\n\n';
    for (const c of categories[cat]) {
      report += '- `' + c.hash + '` ' + c.message + '\n';
    }
    report += '\n';
  }

  report += '## Key Files Changed\n\n';
  for (const f of uniqueFiles.slice(0, 30)) {
    report += '- ' + f + '\n';
  }
  if (uniqueFiles.length > 30) report += '- ... and ' + (uniqueFiles.length - 30) + ' more\n';
  report += '\n---\n*Automated daily activity summary*\n';

  fs.mkdirSync('reports', { recursive: true });
  fs.writeFileSync('reports/activity-summary-' + dateStr + '.md', report);
  console.log('Report saved: reports/activity-summary-' + dateStr + '.md');
}

main();
