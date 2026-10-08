-- Historique des ajustements LCR.
--
-- Une ligne représente un bloc complet validé par l'utilisateur.
-- Les lignes métier restent dans public.completude_table et sont retrouvées
-- grâce au tableau bi_ids tant que le bloc est ACTIVE.
-- Après suppression, bi_ids est vidé : seules les métadonnées d'audit restent.

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
        CHECK (status IN ('ACTIVE', 'DELETED')),
    CONSTRAINT adjustment_registry_deletion_check
        CHECK (
            (status = 'ACTIVE' AND deleted_at IS NULL AND deleted_by IS NULL)
            OR
            (status = 'DELETED' AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL)
        )
);

-- Accélère les filtres Date d'arrêté / Version du registre.
CREATE INDEX IF NOT EXISTS ix_adjustment_registry_context
    ON public.adjustment_registry (asofdate, asofdateflow_version);

-- Accélère la séparation des blocs actifs et supprimés et leur ordre d'affichage.
CREATE INDEX IF NOT EXISTS ix_adjustment_registry_status_event
    ON public.adjustment_registry (
        status,
        (COALESCE(deleted_at, created_at)) DESC
    );

-- Exemple de suppression utilisée par l'API après le DELETE de completude_table :
-- UPDATE public.adjustment_registry
-- SET status = 'DELETED',
--     deleted_at = CURRENT_TIMESTAMP,
--     deleted_by = 'local_user',
--     bi_ids = ARRAY[]::VARCHAR(36)[]
-- WHERE adjustment_id = '00000000-0000-0000-0000-000000000000';
