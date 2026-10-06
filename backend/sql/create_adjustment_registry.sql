-- Registre minimal des ajustements manuels.
-- La ligne reste présente après suppression afin de conserver l'historique.
CREATE TABLE IF NOT EXISTS public.adjustment_registry (
    adjustment_id UUID PRIMARY KEY,
    bi_id VARCHAR(36) NOT NULL UNIQUE,
    asofdate DATE NOT NULL,
    asofdateflow_version TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL DEFAULT 'local_user',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(100),

    CONSTRAINT adjustment_registry_status_check
        CHECK (status IN ('ACTIVE', 'DELETED'))
);

-- Une seule ligne ACTIVE est permise par contexte. Les anciennes lignes
-- DELETED ne bloquent donc pas la création d'un nouvel ajustement.
CREATE UNIQUE INDEX IF NOT EXISTS uq_adjustment_registry_active_context
    ON public.adjustment_registry (asofdate, asofdateflow_version)
    WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS ix_adjustment_registry_context
    ON public.adjustment_registry (asofdate, asofdateflow_version);
