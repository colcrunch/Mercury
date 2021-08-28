-- upgrade --
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "botadminrole" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "role_id" BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS "lastthera" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "last_thera" BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS "therachannel" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS "theraeveconstellation" (
    "constellation_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "theraeveregion" (
    "region_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "theraevesystem" (
    "system_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "welcomechannel" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS "welcomemessage" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "message" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "therachannel_theraevesystem" (
    "therachannel_id" BIGINT NOT NULL REFERENCES "therachannel" ("guild_id") ON DELETE CASCADE,
    "theraevesystem_id" BIGINT NOT NULL REFERENCES "theraevesystem" ("system_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "therachannel_theraeveregion" (
    "therachannel_id" BIGINT NOT NULL REFERENCES "therachannel" ("guild_id") ON DELETE CASCADE,
    "theraeveregion_id" BIGINT NOT NULL REFERENCES "theraeveregion" ("region_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "therachannel_theraeveconstellation" (
    "therachannel_id" BIGINT NOT NULL REFERENCES "therachannel" ("guild_id") ON DELETE CASCADE,
    "theraeveconstellation_id" BIGINT NOT NULL REFERENCES "theraeveconstellation" ("constellation_id") ON DELETE CASCADE
);
