# data/ — Session Storage Directory

This directory stores NeuroSpeak-AI runtime artefacts:

| Path | Contents |
|------|----------|
| `sessions.db` | SQLite database of all inference sessions |
| `embeddings/` | Optional: cached Wav2Vec2 embedding `.npy` files |

## Notes

- **`sessions.db`** is auto-created on first `app.py` launch.
- Database URL is configured via `DATABASE_URL` in `.env`.
- To switch to PostgreSQL, set `DATABASE_URL=postgresql+psycopg2://...`.

## Git Ignored

The contents of this directory (`.db`, `.sqlite`, audio files, embeddings)
are excluded from version control via `.gitignore`.
Only this `README.md` and directory structure are tracked.
