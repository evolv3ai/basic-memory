CREATE TABLE IF NOT EXISTS "schema_migrations" (version varchar(128) primary key);
CREATE TABLE IF NOT EXISTS "observation" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    content TEXT NOT NULL,         -- the actual observation text
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    context TEXT,                  -- where this observation came from
    FOREIGN KEY (entity_id) REFERENCES "entity"(id)
);
CREATE TABLE IF NOT EXISTS "relation" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entity_id TEXT NOT NULL,
    to_entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,   -- the verb describing the relationship
    context TEXT,                  -- optional context about the relationship
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_entity_id) REFERENCES "entity"(id),
    FOREIGN KEY (to_entity_id) REFERENCES "entity"(id),
    -- Ensure we don't duplicate the exact same relationship
    UNIQUE(from_entity_id, to_entity_id, relation_type)
);
CREATE TABLE IF NOT EXISTS "entity" (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
      type TEXT NOT NULL,
    description TEXT NULL,
    "references" TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Dbmate schema migrations
INSERT INTO "schema_migrations" (version) VALUES
  ('20240101000000'),
  ('20240102000000'),
  ('20241210213454');
