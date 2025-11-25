\# 🧪 Testing Guide



\## Running Tests



\### Run All Tests

```powershell

cd C:\\StockAgent\\Stock-agent-\\tests

python run\_all\_tests.py

```



\### Run Individual Test Suites

```powershell

\# Health monitor tests

python test\_health\_monitor.py



\# Notifier tests

python test\_notifier.py

```



---



\## Test Coverage



\### 1. Health Monitor Tests

\- ✅ Initialization

\- ✅ API connection check

\- ✅ Data feed validation

\- ✅ Portfolio health

\- ✅ Performance metrics

\- ✅ Overall status logic

\- ✅ Report generation

\- ✅ Edge cases \& error handling



\### 2. Notifier Tests

\- ✅ Initialization

\- ✅ Basic alerts

\- ✅ Trading signal notifications

\- ✅ Health alerts

\- ✅ Daily summaries

\- ✅ Multiple severity levels

\- ✅ Configuration handling



---



\## Continuous Integration



Tests run automatically on:

\- ✅ Every push to main branch

\- ✅ Every pull request

\- ✅ Daily at 6 AM UTC

\- ✅ Manual trigger via Actions tab



---



\## Test Results



Check test results in:

1\. GitHub Actions → "Run Tests" workflow

2\. Download test artifacts for detailed logs

3\. View console output for quick summary



---



\## Adding New Tests



1\. Create `test\_\[module].py` in tests/ directory

2\. Follow unittest framework pattern

3\. Import in `run\_all\_tests.py`

4\. Tests run automatically on next push



---



\## Best Practices



✅ Test before committing code  

✅ Fix failing tests immediately  

✅ Add tests for new features  

✅ Keep tests fast and focused  

✅ Use descriptive test names  



---



\*\*Happy Testing!\*\* 🧪

