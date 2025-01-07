-- Drop the existing table if it exists
DROP TABLE IF EXISTS token_usage;

-- Create the token usage tracking table
CREATE TABLE token_usage (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    timestamp TIMESTAMPTZ NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL
); 