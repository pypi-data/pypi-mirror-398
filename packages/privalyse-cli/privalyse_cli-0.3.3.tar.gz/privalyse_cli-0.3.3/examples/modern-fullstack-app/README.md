# Modern Fullstack App Example (TypeScript)

This example demonstrates a modern full-stack application with privacy vulnerabilities that Privalyse can detect.

## Structure

- **Frontend**: React/TypeScript application with forms and API calls.
- **Backend**: Node.js/Express/TypeScript application with API endpoints.

## Vulnerabilities to Detect

### Frontend (`frontend/`)
1. **PII in Forms**: `RegistrationForm.tsx` collects Name, Email, Password, Phone, DOB.
2. **Insecure Storage**: Storing passwords and tokens in `localStorage`/`sessionStorage`.
3. **Data Leaks**: `console.log` of form data.
4. **Insecure API**: Calls to `http://` endpoints.

### Backend (`backend/`)
1. **Taint Tracking**:
   - Variables like `userPassword`, `creditCard` are detected as sources.
   - Assignments like `const pwdDebug = userPassword` propagate the taint.
   - Sinks like `console.log(pwdDebug)` are flagged as data leaks.
2. **Logging PII**: Explicit logging of email, password, and credit card numbers.

## Running the Scan

To scan this example project:

```bash
# From the root of the repo
python3 privalyse_v2.py --root privalyse-cli/examples/modern-fullstack-app --out fullstack_scan.json
```
