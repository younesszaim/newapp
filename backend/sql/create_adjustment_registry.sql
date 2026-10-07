-- Un enregistrement représente un bloc saisi et validé en une seule fois.
CREATE TABLE IF NOT EXISTS public.adjustment_registry (
    adjustment_id UUID PRIMARY KEY,
    bi_ids VARCHAR(36)[] NOT NULL DEFAULT ARRAY[]::VARCHAR(36)[],
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

-- Migration des anciennes lignes du registre vers un tableau contenant leur BI ID.
ALTER TABLE public.adjustment_registry
    ADD COLUMN IF NOT EXISTS bi_ids VARCHAR(36)[]
        DEFAULT ARRAY[]::VARCHAR(36)[];

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'adjustment_registry'
          AND column_name = 'bi_id'
    ) THEN
        EXECUTE $migration$
            UPDATE public.adjustment_registry
            SET bi_ids = ARRAY[bi_id]::VARCHAR(36)[]
            WHERE COALESCE(cardinality(bi_ids), 0) = 0
              AND bi_id IS NOT NULL
              AND status = 'ACTIVE'
        $migration$;
    END IF;
END $$;

ALTER TABLE public.adjustment_registry
    ALTER COLUMN bi_ids SET NOT NULL,
    DROP COLUMN IF EXISTS bi_id,
    DROP COLUMN IF EXISTS tradeno,
    DROP COLUMN IF EXISTS ldp_impact_lcr_reglementaire,
    DROP COLUMN IF EXISTS ldp_impact_lcr_gestion,
    DROP COLUMN IF EXISTS impact_lcr_inflow,
    DROP COLUMN IF EXISTS impact_lcr_outflow,
    DROP COLUMN IF EXISTS impact_lcr_asset,
    DROP COLUMN IF EXISTS impact_lcr_asset_cash;

DROP INDEX IF EXISTS public.uq_adjustment_registry_active_context;

CREATE INDEX IF NOT EXISTS ix_adjustment_registry_context
    ON public.adjustment_registry (asofdate, asofdateflow_version);
