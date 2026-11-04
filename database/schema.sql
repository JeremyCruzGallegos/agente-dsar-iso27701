-- Esquema de conocimiento del agente de derechos. PostgreSQL 13+.
-- Las demás tablas operativas son creadas por Flask-SQLAlchemy con `flask init-db`.
CREATE TABLE IF NOT EXISTS legal_sources (
    id SERIAL PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    title VARCHAR(300) NOT NULL,
    source_type VARCHAR(30) NOT NULL CHECK (source_type IN
        ('law','regulation','iso','institutional','jurisprudence','guidance')),
    issuing_body VARCHAR(200) NOT NULL,
    jurisdiction VARCHAR(100) NOT NULL DEFAULT 'Perú',
    publication_date DATE,
    effective_from DATE,
    effective_to DATE,
    official_url VARCHAR(1000),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN
        ('draft','active','repealed','superseded')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS legal_provisions (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES legal_sources(id) ON DELETE CASCADE,
    provision_code VARCHAR(100) NOT NULL,
    heading VARCHAR(500),
    content TEXT NOT NULL,
    topic VARCHAR(100),
    right_type VARCHAR(40),
    applies_to VARCHAR(300),
    keywords TEXT,
    parent_id INTEGER REFERENCES legal_provisions(id) ON DELETE SET NULL,
    sort_order INTEGER NOT NULL DEFAULT 0 CHECK (sort_order >= 0),
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_source_provision_code UNIQUE (source_id, provision_code)
);

CREATE TABLE IF NOT EXISTS legal_relations (
    id SERIAL PRIMARY KEY,
    from_provision_id INTEGER NOT NULL REFERENCES legal_provisions(id) ON DELETE CASCADE,
    to_provision_id INTEGER NOT NULL REFERENCES legal_provisions(id) ON DELETE CASCADE,
    relation_type VARCHAR(30) NOT NULL,
    explanation TEXT,
    CONSTRAINT uq_legal_relation UNIQUE (from_provision_id, to_provision_id, relation_type)
);

CREATE INDEX IF NOT EXISTS ix_legal_sources_status ON legal_sources(status);
CREATE INDEX IF NOT EXISTS ix_legal_provisions_verified ON legal_provisions(verified);
CREATE INDEX IF NOT EXISTS ix_legal_provisions_topic ON legal_provisions(topic);
CREATE INDEX IF NOT EXISTS ix_legal_provisions_right_type ON legal_provisions(right_type);
