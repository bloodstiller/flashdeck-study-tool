---
noteId: 137
---

Why does compromising the KDC compromise the entire domain?

---

The KDC holds all user and service secret keys.
Whoever controls the KDC can forge any ticket for any user or service.