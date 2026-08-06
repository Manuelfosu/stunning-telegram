# SSGA HOLDINGS admin guide

## Daily operations

- **Overview:** monitor users, pending payments, active investments, question count and task availability.
- **Deposits:** compare the member's amount, MoMo number, network and account name before approving. Approval credits deposit purchasing balance.
- **Withdrawals:** approve only after validating the payout identity; mark paid only after sending the net amount. Rejection refunds held earnings.
- **Packages:** create, edit, lock or hide packages. A package with investment history is archived instead of destructively deleted.
- **Questions:** maintain text, four options, correct answer and explanation. The platform ships with 520 arithmetic questions (104 days at five per day).
- **Tasks:** optional activities only. Archive unavailable tasks so members see a clean empty state.
- **Ads:** approve valid campaigns or reject and automatically refund the campaign charge.
- **Broadcasts:** publish dashboard, banner, popup or uncropped image notifications.
- **Users:** disable/re-enable accounts or permanently block a phone number.
- **Logs:** review sensitive admin activity and timestamps.
- **Settings:** merchant details, minimums, fee percentages and referral rates publish immediately.

## Live alerts

Click **Enable browser alerts** in the admin console and allow notifications. While the console is open, the authenticated WebSocket reports new deposits, withdrawals and live configuration changes.

## Security

- Change the bootstrap password immediately.
- Never approve a payment using only a screenshot; verify merchant records.
- Do not share admin credentials.
- Keep `SECRET_KEY` private and persistent.
- Use a Render disk or PostgreSQL before accepting production payments.
