CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(64) PRIMARY KEY,
  email VARCHAR(255),
  display_name VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
  id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL REFERENCES users(id),
  workspace_path TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status VARCHAR(32) NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS messages (
  id VARCHAR(64) PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL REFERENCES sessions(id),
  user_id VARCHAR(64) NOT NULL REFERENCES users(id),
  role VARCHAR(32) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id VARCHAR(64) PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL REFERENCES sessions(id),
  user_id VARCHAR(64) NOT NULL REFERENCES users(id),
  model VARCHAR(255) NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  status VARCHAR(32) NOT NULL,
  success BOOLEAN NOT NULL DEFAULT FALSE,
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  tool_calls INTEGER NOT NULL DEFAULT 0,
  duration_ms INTEGER,
  error TEXT,
  metadata_json JSONB
);

CREATE TABLE IF NOT EXISTS tool_calls (
  id VARCHAR(64) PRIMARY KEY,
  agent_run_id VARCHAR(64) NOT NULL REFERENCES agent_runs(id),
  session_id VARCHAR(64) NOT NULL REFERENCES sessions(id),
  user_id VARCHAR(64) NOT NULL REFERENCES users(id),
  tool VARCHAR(64) NOT NULL,
  input_json JSONB,
  output_json JSONB,
  latency_ms INTEGER NOT NULL DEFAULT 0,
  success BOOLEAN NOT NULL DEFAULT TRUE,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usage (
  id VARCHAR(64) PRIMARY KEY,
  agent_run_id VARCHAR(64) NOT NULL REFERENCES agent_runs(id),
  session_id VARCHAR(64) NOT NULL REFERENCES sessions(id),
  user_id VARCHAR(64) NOT NULL REFERENCES users(id),
  model VARCHAR(255) NOT NULL,
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  latency_ms INTEGER NOT NULL DEFAULT 0,
  metadata_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
