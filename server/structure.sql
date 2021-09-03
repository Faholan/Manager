CREATE TABLE sessions (
  id GENERATED ALWAYS AS IDENTITY,
  username VARCHAR(30) NOT NULL,
  password BYTEA NOT NULL,
  salt BYTEA NOT NULL,
  admin BOOLEAN NOT NULL
);

ALTER TABLE sessions ADD CONSTRAINT sessions_primary
  PRIMARY KEY (username);

CREATE TABLE identifiers (
  id integer FOREIGN KEY REFERENCES sessions.id,
  context TEXT NOT NULL,
  username TEXT NOT NULL,
  password BYTEA NOT NULL,
  nonce BYTEA NOT NULL
);

ALTER TABLE identifiers ADD CONSTRAINT identifiers_primary
  PRIMARY KEY (id, context, username);
