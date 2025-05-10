from datetime import datetime, timedelta
from typing import List
from ..core.models import PythonInstallation

class OptimizationRecommender:
    def __init__(self, max_inactive_days=90):
        self.max_inactive = max_inactive_days

    def generate_recommendations(self, installations: List[PythonInstallation]):
        recommendations = []
        for install in installations:
            if self._is_unused(install):
                recommendations.append({
                    'type': 'UNUSED_INSTALLATION',
                    'target': install.path,
                    'reason': f'Non utilisée depuis {self.max_inactive} jours'
                })
        return recommendations

    def _is_unused(self, install):
        if not install.last_used:
            return True
        return (datetime.now() - install.last_used) > timedelta(days=self.max_inactive)
