---
noteId: 129
---

What does the KDC return in an AS-REP?

---

1. A TGT — encrypted with the KDC's secret key
2. A Session Key (copy 1) — encrypted with the user's key (for client use)
3. A Session Key (copy 2) — embedded inside the TGT (for KDC/TGS use)