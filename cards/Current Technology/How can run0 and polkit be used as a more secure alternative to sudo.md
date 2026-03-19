---
noteId: 1772627304589
---

How can run0 and polkit be used as a more secure alternative to sudo?

---

run0 executes commands through systemd while polkit handles the authorization decision, allowing fine grained policy based privilege escalation instead of relying on a setuid sudo binary.
