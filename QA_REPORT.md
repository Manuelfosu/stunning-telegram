# SSGA HOLDINGS v3.1 — Recovery QA report

## Audit findings recovered

- Restored 15 explicit frontend page modules, including Login, Signup, both deposit steps, Withdrawal, Questions, Profile, Admin and NotFound.
- Added a root React error boundary.
- Added dedicated `/login`, `/signup` and authenticated 404 behavior.
- Added the missing `wallets`, `answers` and `referrals` tables.
- Aligned required table names to `ads` and `logs`.
- Added `income_credits` with a unique investment/date constraint to prevent repeat same-day income.
- Connected wallet records to every wallet movement.
- Connected answer records to each daily quiz response.
- Connected referral records during referred registration.
- Extended realtime updates to authenticated sessions while keeping payment creation payloads admin-only.
- Added package-range validation, two-decimal money normalization and negative-wallet protection.
- Enabled SQLite foreign keys, WAL and a 5-second busy timeout.

## Automated release checks

- Python AST parsing and bytecode compilation: passed.
- Required database table-name audit: passed.
- 59 unique backend HTTP method/path combinations: passed.
- 31 frontend literal API contracts matched to backend routes: passed.
- All 15 frontend page modules bundled with esbuild: passed.
- Main frontend application bundled with CSS: passed.
- Business invariant audit (wallets, deposits, withdrawals, quiz, income, referrals, tasks, realtime, error handling): passed.
- Responsive static audit for 320px, 375px and 430px breakpoint behavior: passed.
- Render Blueprint and Docker build-path audit: passed.
- ZIP integrity test: required before release.

## Core invariants

- Deposit credit is package-purchase credit and cannot be withdrawn.
- Earnings credit is withdrawable.
- A deposit request is created only after **I HAVE PAID**.
- Identical pending payment requests are blocked for ten minutes.
- Withdrawals require GHS 50 minimum and apply a 16% fee.
- Withdrawal transitions are pending → approved → completed; rejection refunds once.
- Five daily questions are required for income.
- Feedback and explanation are returned after each answer.
- The seeded bank contains 520 financial questions (104 days at five per day).
- Active investment income is credited automatically once per calendar day after quiz completion.
- Admin package, task, ad, notification and settings changes publish realtime events.

## Environment limitation

This sandbox has no network access, so third-party Python/npm dependencies could not be installed for a live HTTP/browser session. Offline Python compilation, route/schema audits and esbuild bundling were completed. Render installs the declared dependencies during the Docker build.
