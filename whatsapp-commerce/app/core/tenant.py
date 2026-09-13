from sqlalchemy.orm import Query

class TenantQuery(Query):
    """Warns or raises if a tenant-scoped model is queried without business_id."""

    def _check_tenant(self):
        if not self.column_descriptions:
            return
        model = self.column_descriptions[0].get('entity')
        if model is None or not hasattr(model, 'business_id'):
            return
        sql = str(self.statement)
        if 'business_id' not in sql:
            from flask import current_app
            if current_app and current_app.config.get('TENANT_STRICT'):
                raise RuntimeError(
                    f"Tenant query on {model.__name__} without business_id filter!"
                )

    def all(self, *a, **kw):
        self._check_tenant(); return super().all(*a, **kw)

    def first(self, *a, **kw):
        self._check_tenant(); return super().first(*a, **kw)

    def first_or_404(self, *a, **kw):
        self._check_tenant(); return super().first_or_404(*a, **kw)