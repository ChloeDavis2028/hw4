# Problem 4 evidence: users table after testing

Captured from `data/campus_customs.db` (salts and hashes are hidden in this public copy; every stored value is a salted PBKDF2 hash, never a password, and each row's salt is different).

| id | name | first | last | rank | email | created_at | password_hash |
|---|---|---|---|---|---|---|---|
| 1 | Test User | Test | User | Captain | test@campuscustoms.yale.edu | 2026-09-19 11:34:09 | pbkdf2_sha256$(salt hidden)$(hash hidden) |
| 2 | Ada Lovelace | Ada | Lovelace | Captain | ada.1789818990@yale.edu | 2026-09-19 11:56:30 | pbkdf2_sha256$(salt hidden)$(hash hidden) |
| 3 | Tauhid Zaman | Tauhid | Zaman | Captain | tauhid.zaman@yale.edu | 2026-09-19 11:57:56 | pbkdf2_sha256$(salt hidden)$(hash hidden) |
| 4 | Amelia Earhart | Amelia | Earhart | Captain | amelia.pilot@yale.edu | 2026-10-23 03:23:03 | pbkdf2_sha256$(salt hidden)$(hash hidden) |
| 5 | Chloe Yeager | Chloe | Yeager | Colonel | colonel.chloe@yale.edu | 2026-10-23 03:25:18 | pbkdf2_sha256$(salt hidden)$(hash hidden) |
| 6 | Ace Pilot | Ace | Pilot | Captain | ace.pilot@yale.edu | 2026-10-23 03:43:54 | pbkdf2_sha256$(salt hidden)$(hash hidden) |
