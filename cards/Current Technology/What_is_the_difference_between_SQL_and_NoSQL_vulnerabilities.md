---
noteId: 54
---

What is the difference between SQL and NoSQL vulnerabilities??

---

- SQL vulnerabilities usually target structured, relational databases through flaws like SQL injection

- NoSQL vulnerabilities abuse flexible query formats and weak access controls in document/key-value databases through issues like NoSQL injection and insecure API/query logic.

<!-- notes -->
NoSQL injection attacks may execute in different areas of an application than traditional SQL injection. Where SQL injection would execute within the database engine, NoSQL variants may execute during within the application layer or the database layer, depending on the NoSQL API used and data model. Typically NoSQL injection attacks will execute where the attack string is parsed, evaluated, or concatenated into a NoSQL API call.