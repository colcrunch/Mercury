-- upgrade --
CREATE TABLE IF NOT EXISTS "botadminrole" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "role_id" BIGINT NOT NULL
);
-- downgrade --
DROP TABLE IF EXISTS "botadminrole";
