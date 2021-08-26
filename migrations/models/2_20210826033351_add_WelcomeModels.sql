-- upgrade --
CREATE TABLE IF NOT EXISTS "welcomechannel" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL
);;
CREATE TABLE IF NOT EXISTS "welcomemessage" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "message" TEXT NOT NULL
);;
-- downgrade --
DROP TABLE IF EXISTS "welcomechannel";
DROP TABLE IF EXISTS "welcomemessage";
