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

-- Plusieurs deals fictifs peuvent désormais être créés pour le même contexte.
-- DROP est idempotent : le script reste rejouable sur une ancienne base.
DROP INDEX IF EXISTS public.uq_adjustment_registry_active_context;

CREATE INDEX IF NOT EXISTS ix_adjustment_registry_context
    ON public.adjustment_registry (asofdate, asofdateflow_version);

-- Snapshot minimal conservé même lorsque le trade est ensuite supprimé.
ALTER TABLE public.adjustment_registry
    ADD COLUMN IF NOT EXISTS tradeno BIGINT,
    ADD COLUMN IF NOT EXISTS ldp_impact_lcr_reglementaire NUMERIC(20,2),
    ADD COLUMN IF NOT EXISTS ldp_impact_lcr_gestion NUMERIC(20,2),
    ADD COLUMN IF NOT EXISTS impact_lcr_inflow NUMERIC(20,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS impact_lcr_outflow NUMERIC(20,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS impact_lcr_asset NUMERIC(20,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS impact_lcr_asset_cash NUMERIC(20,2) DEFAULT 0;
