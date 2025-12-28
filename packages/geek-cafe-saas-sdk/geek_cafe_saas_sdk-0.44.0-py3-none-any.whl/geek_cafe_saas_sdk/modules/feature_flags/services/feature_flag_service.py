"""
Feature Flag Service

- Evaluates feature flags by user/tenant/everyone precedence
- DynamoDB single-table model-backed using FeatureFlag model indexes
- In-memory TTL cache per Lambda container to minimize DDB reads
- Optional guarded header override for canary/testing

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""
from __future__ import annotations

import os
import time
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from aws_lambda_powertools import Logger

from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.modules.feature_flags.models import FeatureFlag


logger = Logger()

# Module-level cache shared across service instances within a warm Lambda container
# key -> (expires_at_epoch_seconds, FeatureDecision)
_CACHE: Dict[str, Tuple[float, "FeatureDecision"]] = {}


@dataclass
class FeatureDecision:
    enabled: bool
    source: str  # 'override' | 'user' | 'tenant' | 'everyone' | 'default'
    matched_rule_id: Optional[str] = None
    reason: Optional[str] = None


class FeatureFlagService(DatabaseService[FeatureFlag]):
    """
    Feature flag evaluation and CRUD.

    Precedence: header override > user > tenant > everyone > default(False)
    """

    def __init__(
        self,
        *,
        dynamodb=None,
        table_name: Optional[str] = None,
        request_context: RequestContext,
        cache_ttl_seconds: Optional[int] = None,
    ):
        super().__init__(dynamodb=dynamodb, table_name=table_name, request_context=request_context)
        self._cache_ttl_seconds = (
            int(cache_ttl_seconds)
            if cache_ttl_seconds is not None
            else int(os.getenv("FEATURE_FLAG_CACHE_TTL_SECONDS", "300"))
        )
        self._environment = os.getenv("ENVIRONMENT", "prod").lower()

    # =====================
    # Public API - Evaluate
    # =====================

    def is_enabled(
        self,
        feature_key: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        allow_header_in_prod: bool = False,
        override_permission: str = "features:allow_override",
        default: bool = False,
    ) -> FeatureDecision:
        """
        Evaluate whether a feature is enabled for the current request.

        Args:
            feature_key: The feature key (e.g., 'file_system_v2')
            headers: Optional HTTP headers to check for override
            allow_header_in_prod: If True, allow header override even in prod
            override_permission: Permission required to use header override in prod
            default: Default if no rules found
        """
        # 1) Header override (guarded)
        decision = self._evaluate_header_override(
            feature_key=feature_key,
            headers=headers or {},
            allow_header_in_prod=allow_header_in_prod,
            override_permission=override_permission,
        )
        if decision:
            return decision

        cache_key = self._build_cache_key(feature_key)
        # 2) Cache check
        if cache_key in _CACHE:
            expires_at, cached = _CACHE[cache_key]
            if time.time() < expires_at:
                return cached

        # 3) User-level rule (GSI2)
        rule = self._get_user_rule(feature_key)
        decision = self._evaluate_rule(rule, source="user")
        if decision:
            self._cache_set(cache_key, decision)
            return decision

        # 4) Tenant-level rule (GSI1)
        rule = self._get_tenant_rule(feature_key)
        decision = self._evaluate_rule(rule, source="tenant")
        if decision:
            self._cache_set(cache_key, decision)
            return decision

        # 5) Everyone-level rule (GSI3)
        rule = self._get_everyone_rule(feature_key)
        decision = self._evaluate_rule(rule, source="everyone")
        if decision:
            self._cache_set(cache_key, decision)
            return decision

        # 6) Default
        decision = FeatureDecision(enabled=bool(default), source="default", reason="no_rule")
        self._cache_set(cache_key, decision)
        return decision

    # =====================
    # CRUD (admin usage)
    # =====================

    @service_method("create")


    def create(self, **kwargs) -> ServiceResult[FeatureFlag]:
        try:
            model = FeatureFlag()
            model.tenant_id = tenant_id
            model.user_id = user_id
            model.feature_key = kwargs.get("feature_key")
            model.scope = kwargs.get("scope")
            model.scope_id = kwargs.get("scope_id")
            model.enabled = bool(kwargs.get("enabled", False))
            model.environments = kwargs.get("environments")
            model.permissions_required = kwargs.get("permissions_required")
            model.percentage = kwargs.get("percentage")
            model.start_ts = kwargs.get("start_ts")
            model.end_ts = kwargs.get("end_ts")
            model.metadata = kwargs.get("metadata")

            model.prep_for_save()
            return self._save_model(model)
        except Exception as e:
            return self._handle_service_exception(e, "feature_flag.create", tenant_id=tenant_id, user_id=user_id)

    @service_method("get_by_id")


    def get_by_id(self, flag_id: str) -> ServiceResult[FeatureFlag]:
        try:
            model = self._get_by_id(flag_id, FeatureFlag)
            if not model:
                return ServiceResult.error_result(
                    message="Feature flag not found",
                    error_code=ErrorCode.NOT_FOUND,
                    error_details={"id": flag_id},
                )
            return ServiceResult.success_result(model)
        except Exception as e:
            return self._handle_service_exception(e, "feature_flag.get_by_id", id=flag_id)

    @service_method("update")


    def update(
        self, flag_id: str, updates: Dict[str, Any]
    ) -> ServiceResult[FeatureFlag]:
        try:
            model = self._get_by_id(flag_id, FeatureFlag)
            if not model:
                return ServiceResult.error_result(
                    message="Feature flag not found",
                    error_code=ErrorCode.NOT_FOUND,
                    error_details={"id": flag_id},
                )

            # Apply updates (only known fields)
            for field in (
                "feature_key",
                "scope",
                "scope_id",
                "enabled",
                "environments",
                "permissions_required",
                "percentage",
                "start_ts",
                "end_ts",
                "metadata",
            ):
                if field in updates:
                    setattr(model, field, updates[field])

            model.prep_for_save()
            return self._save_model(model)
        except Exception as e:
            return self._handle_service_exception(e, "feature_flag.update", id=flag_id)

    @service_method("delete")


    def delete(self, flag_id: str) -> ServiceResult[bool]:
        try:
            model = self._get_by_id(flag_id, FeatureFlag)
            if not model:
                return ServiceResult.error_result(
                    message="Feature flag not found",
                    error_code=ErrorCode.NOT_FOUND,
                    error_details={"id": flag_id},
                )
            return self._delete_model(model)
        except Exception as e:
            return self._handle_service_exception(e, "feature_flag.delete", id=flag_id)

    def list(
        self,
        *,
        feature_key: str,
        scope: Optional[str] = None,
        scope_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> ServiceResult[List[FeatureFlag]]:
        try:
            if not feature_key:
                return ServiceResult.error_result(
                    message="feature_key is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                    error_details={"field": "feature_key"},
                )

            items: List[FeatureFlag] = []

            def q_tenant() -> List[FeatureFlag]:
                m = FeatureFlag()
                m.feature_key = feature_key
                m.scope = "tenant"
                # prefer explicit scope_id; fallback to authenticated tenant
                m.tenant_id = scope_id or self.request_context.target_tenant_id
                m.scope_id = m.tenant_id
                res = self._query_by_index(m, "gsi1", limit=limit)
                return res.data or [] if res.success else []

            def q_user() -> List[FeatureFlag]:
                m = FeatureFlag()
                m.feature_key = feature_key
                m.scope = "user"
                # prefer explicit scope_id; fallback to authenticated user
                m.scope_id = scope_id or self.request_context.target_user_id
                res = self._query_by_index(m, "gsi2", limit=limit)
                return res.data or [] if res.success else []

            def q_everyone() -> List[FeatureFlag]:
                m = FeatureFlag()
                m.feature_key = feature_key
                m.scope = "everyone"
                res = self._query_by_index(m, "gsi3", limit=limit)
                return res.data or [] if res.success else []

            if scope in ("tenant", "user", "everyone"):
                if scope == "tenant":
                    items = q_tenant()
                elif scope == "user":
                    items = q_user()
                else:
                    items = q_everyone()
            else:
                # Union of all applicable scopes
                items = q_tenant() + q_user() + q_everyone()
                if limit is not None and isinstance(limit, int):
                    items = items[: max(0, limit)]

            return ServiceResult.success_result(items)
        except Exception as e:
            return self._handle_service_exception(e, "feature_flag.list", feature_key=feature_key, scope=scope)

    # =====================
    # Internal helpers
    # =====================

    def _build_cache_key(self, feature_key: str) -> str:
        uid = self.request_context.target_user_id or "anonymous"
        tid = self.request_context.target_tenant_id or "unknown"
        return f"{self.table_name}:{self._environment}:{tid}:{uid}:{feature_key}"

    def _cache_set(self, key: str, decision: FeatureDecision) -> None:
        ttl = max(0, self._cache_ttl_seconds)
        _CACHE[key] = (time.time() + ttl, decision)

    def _evaluate_header_override(
        self,
        *,
        feature_key: str,
        headers: Dict[str, str],
        allow_header_in_prod: bool,
        override_permission: str,
    ) -> Optional[FeatureDecision]:
        if not headers:
            return None
        # Normalize headers to lowercase keys
        hdrs = {str(k).lower(): v for k, v in headers.items()}
        raw = hdrs.get("x-feature-override")
        if not raw:
            return None

        # Guard policy
        in_prod = self._environment == "prod"
        has_perm = self.request_context.has_permission(override_permission)
        if in_prod and not (allow_header_in_prod or has_perm):
            return None

        # Parse pairs like: "file_system_v2=on, other_feature=off"
        try:
            pairs = [p.strip() for p in str(raw).split(",") if p.strip()]
            mapping: Dict[str, str] = {}
            for p in pairs:
                if "=" in p:
                    k, v = p.split("=", 1)
                    mapping[k.strip()] = v.strip().lower()
            if feature_key in mapping:
                v = mapping[feature_key]
                if v in ("on", "true", "1"):
                    return FeatureDecision(enabled=True, source="override", reason="header")
                if v in ("off", "false", "0"):
                    return FeatureDecision(enabled=False, source="override", reason="header")
        except Exception as e:
            logger.warning(f"Invalid X-Feature-Override header: {e}")
        return None

    def _get_user_rule(self, feature_key: str) -> Optional[FeatureFlag]:
        try:
            model = FeatureFlag()
            model.feature_key = feature_key
            model.scope = "user"
            # scope_id is used in index build; prefer authenticated_user_id
            model.scope_id = self.request_context.target_user_id
            result = self._query_by_index(model, "gsi2", limit=1)
            if result.success and result.data:
                return result.data[0]
        except Exception as e:
            logger.error(f"_get_user_rule error: {e}")
        return None

    def _get_tenant_rule(self, feature_key: str) -> Optional[FeatureFlag]:
        try:
            model = FeatureFlag()
            model.feature_key = feature_key
            model.scope = "tenant"
            # GSI1 uses tenant_id or scope_id
            model.tenant_id = self.request_context.target_tenant_id
            model.scope_id = self.request_context.target_tenant_id
            result = self._query_by_index(model, "gsi1", limit=1)
            if result.success and result.data:
                return result.data[0]
        except Exception as e:
            logger.error(f"_get_tenant_rule error: {e}")
        return None

    def _get_everyone_rule(self, feature_key: str) -> Optional[FeatureFlag]:
        try:
            model = FeatureFlag()
            model.feature_key = feature_key
            model.scope = "everyone"
            result = self._query_by_index(model, "gsi3", limit=1)
            if result.success and result.data:
                return result.data[0]
        except Exception as e:
            logger.error(f"_get_everyone_rule error: {e}")
        return None

    def _evaluate_rule(self, rule: Optional[FeatureFlag], *, source: str) -> Optional[FeatureDecision]:
        """
        Return a decision if a rule applies; otherwise None to allow fallback.
        """
        if not rule:
            return None

        # Environment constraint
        if rule.environments:
            envs = [e.lower() for e in rule.environments]
            if self._environment not in envs:
                return None

        # Time window
        now = time.time()
        if rule.start_ts is not None and now < float(rule.start_ts):
            return None
        if rule.end_ts is not None and now > float(rule.end_ts):
            return None

        # Permissions required
        if rule.permissions_required:
            if not self.request_context.has_all_permissions(rule.permissions_required):
                return None

        # Percentage rollout (stable hash on user+tenant)
        if rule.percentage is not None:
            threshold = int(rule.percentage)
            uid = self.request_context.target_user_id or "anonymous"
            tid = self.request_context.target_tenant_id or "unknown"
            h_input = f"{uid}:{tid}:{rule.feature_key}".encode("utf-8")
            h_val = int(hashlib.sha1(h_input).hexdigest()[:6], 16) % 100  # 0..99
            if h_val >= threshold:
                return None

        # If we reached here, rule applies. Use its enabled value.
        return FeatureDecision(
            enabled=bool(rule.enabled),
            source=source,
            matched_rule_id=rule.id,
            reason="rule_match",
        )
