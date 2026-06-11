Stop the Flask newsletter app running on port 5678.

1. Find the PID using the port:
   ```
   netstat -ano | findstr :5678
   ```

2. Extract the PID from the last column of the LISTENING row.

3. Kill that process:
   ```
   taskkill /PID <pid> /F
   ```

4. Confirm the process is gone and tell the user the app has been stopped.
   If no process was found on port 5678, tell the user the app was not running.
