"""Route resolver utility for EchoIntel SDK."""

from __future__ import annotations

from echointel.endpoints import Endpoints


class RouteResolver:
    """Utility class for resolving route patterns to URIs.

    This class handles the resolution of dot-notation route patterns
    (e.g., 'forecasting.revenue') to actual API URIs.
    """

    # Categories excluded from wildcard (*) resolution.
    # These require admin credentials.
    ADMIN_CATEGORIES = frozenset({"admin"})

    @classmethod
    def resolve(cls, routes: list[str]) -> list[str]:
        """Resolve allowed routes from dot notation to URIs.

        Args:
            routes: List of route patterns (e.g., ['*'], ['forecasting'],
                   ['forecasting.revenue'])

        Returns:
            List of resolved URIs.
        """
        if "*" in routes:
            return cls._resolve_wildcard()

        resolved: list[str] = []

        for route in routes:
            resolved.extend(cls._resolve_route(route))

        return list(dict.fromkeys(resolved))

    @classmethod
    def _resolve_wildcard(cls) -> list[str]:
        """Resolve wildcard (*) to all non-admin routes.

        Returns:
            List of all non-admin endpoint URIs.
        """
        all_endpoints = Endpoints.all()
        resolved: list[str] = []

        for category, endpoints in all_endpoints.items():
            if category in cls.ADMIN_CATEGORIES:
                continue

            resolved.extend(endpoints.values())

        return resolved

    @classmethod
    def _resolve_route(cls, route: str) -> list[str]:
        """Resolve a single route pattern.

        Args:
            route: Route pattern (e.g., 'forecasting' or 'forecasting.revenue')

        Returns:
            List of resolved URIs.
        """
        all_endpoints = Endpoints.all()

        if "." not in route:
            return cls._resolve_category_routes(route, all_endpoints)

        return cls._resolve_specific_route(route, all_endpoints)

    @classmethod
    def _resolve_category_routes(
        cls, category: str, all_endpoints: dict[str, dict[str, str]]
    ) -> list[str]:
        """Resolve all routes for a category.

        Args:
            category: Category name (e.g., 'forecasting')
            all_endpoints: All endpoints grouped by category

        Returns:
            List of resolved URIs.
        """
        if category not in all_endpoints:
            return [category]

        return list(all_endpoints[category].values())

    @classmethod
    def _resolve_specific_route(
        cls, route: str, all_endpoints: dict[str, dict[str, str]]
    ) -> list[str]:
        """Resolve a specific endpoint route.

        Args:
            route: Route in dot notation (e.g., 'forecasting.revenue')
            all_endpoints: All endpoints grouped by category

        Returns:
            List with single resolved URI.
        """
        category, endpoint = route.split(".", 1)

        if category not in all_endpoints or endpoint not in all_endpoints[category]:
            return [route]

        return [all_endpoints[category][endpoint]]

    @classmethod
    def categories(cls) -> list[str]:
        """Get all available categories.

        Returns:
            List of category names.
        """
        return list(Endpoints.all().keys())

    @classmethod
    def endpoints(cls, category: str) -> list[str]:
        """Get all available endpoints for a category.

        Args:
            category: Category name

        Returns:
            List of endpoint names.
        """
        all_endpoints = Endpoints.all()

        if category not in all_endpoints:
            return []

        return list(all_endpoints[category].keys())
