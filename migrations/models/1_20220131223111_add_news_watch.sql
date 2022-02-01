-- upgrade --
CREATE TABLE IF NOT EXISTS "newschannel" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL,
    "news" BOOL NOT NULL  DEFAULT False,
    "devblogs" BOOL NOT NULL  DEFAULT False,
    "patchnotes" BOOL NOT NULL  DEFAULT False
);;
CREATE TABLE IF NOT EXISTS "postedarticles" (
    "article_id" VARCHAR(255) NOT NULL  PRIMARY KEY
);-- downgrade --
DROP TABLE IF EXISTS "newschannel";
DROP TABLE IF EXISTS "postedarticles";
