Start the Flask newsletter app on port 5678.

1. Check if something is already running on port 5678:
   ```
   netstat -ano | findstr :5678
   ```
   If a process is found, report it and stop — don't start a second instance.

2. If the port is free, start the app in the background:
   ```
   python app.py
   ```
   Run it with `run_in_background: true` so the server keeps running.

3. Tell the user the app is running at http://localhost:5678
