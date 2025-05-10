from dataclasses import dataclass
from typing import Dict, Set, Callable, List
import json
from pathlib import Path
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ..utils.storage import Storage

@dataclass
class Achievement:
    id: str
    name: str
    description: str
    icon: str
    condition: Callable[[Dict], bool]
    points: int = 10
    secret: bool = False
    category: str = "general"

class GamificationManager:
    def __init__(self):
        self.console = Console()
        self.storage = Storage(Path.home() / ".pyenvdoctor" / "stats.json")
        self.achievements: Dict[str, Achievement] = self._initialize_achievements()
        self.unlocked_achievements: Set[str] = self._load_unlocked()
        
    def _initialize_achievements(self) -> Dict[str, Achievement]:
        """Define all available achievements"""
        return {
            "first_scan": Achievement(
                id="first_scan",
                name="Environment Explorer",
                description="Perform your first environment scan",
                icon="🔍",
                condition=lambda stats: stats.get("scans_performed", 0) >= 1,
                points=5,
                category="basics"
            ),
            "clean_slate": Achievement(
                id="clean_slate",
                name="Clean Slate",
                description="Maintain zero issues for 7 days",
                icon="✨",
                condition=lambda stats: self._check_clean_streak(stats, 7),
                points=25,
                category="maintenance"
            ),
            "dependency_guru": Achievement(
                id="dependency_guru",
                name="Dependency Guru",
                description="Successfully resolve 50 dependency issues",
                icon="🧩",
                condition=lambda stats: stats.get("dependencies_fixed", 0) >= 50,
                points=30,
                category="expert"
            ),
        }
        
    def update_stats(self, **kwargs):
        """Update statistics and check for new achievements"""
        stats = self.storage.load() or {}
        
        # Update stats
        for key, value in kwargs.items():
            if key in stats:
                if isinstance(stats[key], int):
                    stats[key] += value
                elif isinstance(stats[key], list):
                    if isinstance(value, list):
                        stats[key].extend(value)
                    else:
                        stats[key].append(value)
            else:
                stats[key] = value
                
        # Always update last activity
        stats["last_activity"] = datetime.now().isoformat()
        
        # Save updated stats
        self.storage.save(stats)
        
        # Check for new achievements
        self.check_achievements(stats)
        
    def check_achievements(self, stats: Dict) -> List[Achievement]:
        """Check and unlock new achievements"""
        newly_unlocked = []
        
        for achievement_id, achievement in self.achievements.items():
            if achievement_id not in self.unlocked_achievements:
                if achievement.condition(stats):
                    self._unlock_achievement(achievement)
                    newly_unlocked.append(achievement)
                    
        return newly_unlocked
        
    def _unlock_achievement(self, achievement: Achievement):
        """Unlock an achievement with celebration"""
        self.unlocked_achievements.add(achievement.id)
        self._save_unlocked()
        
        # Celebration display
        self.console.print(Panel(
            f"\n[bold yellow]🎉 ACHIEVEMENT UNLOCKED! 🎉[/bold yellow]\n\n"
            f"[bold green]{achievement.icon} {achievement.name}[/bold green]\n"
            f"[italic]{achievement.description}[/italic]\n\n"
            f"Points earned: [bold cyan]{achievement.points}[/bold cyan]\n",
            title="[bold magenta]CONGRATULATIONS[/bold magenta]",
            border_style="gold1"
        ))
        
    def show_progress(self):
        """Display current progress and achievements"""
        stats = self.storage.load() or {}
        
        # Create progress display
        self.console.print("\n[bold blue]Your PyEnvDoctor Progress[/bold blue]\n")
        
        # Show unlocked achievements by category
        categories = {}
        for achievement in self.achievements.values():
            if achievement.category not in categories:
                categories[achievement.category] = []
            categories[achievement.category].append(achievement)
            
        for category, achievements in categories.items():
            table = Table(title=f"{category.title()} Achievements", show_header=True)
            table.add_column("Achievement", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Points", justify="right")
            
            for achievement in achievements:
                if achievement.secret and achievement.id not in self.unlocked_achievements:
                    continue
                    
                status = "✅" if achievement.id in self.unlocked_achievements else "⬜"
                name = f"{achievement.icon} {achievement.name}"
                
                table.add_row(name, status, str(achievement.points))
                
            self.console.print(table)
            self.console.print()
            
        # Show overall statistics
        self._show_statistics(stats)
        
    def _show_statistics(self, stats: Dict):
        """Display key statistics"""
        total_points = sum(
            achievement.points 
            for achievement in self.achievements.values() 
            if achievement.id in self.unlocked_achievements
        )
        
        stats_table = Table(title="Statistics", show_header=True)
        stats_table.add_column("Metric", style="green")
        stats_table.add_column("Value", justify="right", style="cyan")
        
        key_stats = [
            ("Total Achievement Points", str(total_points)),
            ("Scans Performed", str(stats.get("scans_performed", 0))),
            ("Issues Resolved", str(stats.get("issues_resolved", 0))),
            ("Dependencies Fixed", str(stats.get("dependencies_fixed", 0))),
            ("Python Versions Managed", str(len(stats.get("python_versions", [])))),
            ("Days Active", str(self._calculate_days_active(stats))),
        ]
        
        for metric, value in key_stats:
            stats_table.add_row(metric, value)
            
        self.console.print(stats_table)
        
    def _calculate_days_active(self, stats: Dict) -> int:
        """Calculate number of active days"""
        if "last_activity" not in stats:
            return 0
            
        last_activity = datetime.fromisoformat(stats["last_activity"])
        first_activity = datetime.fromisoformat(stats.get("first_activity", stats["last_activity"]))
        
        return (last_activity - first_activity).days + 1
        
    def _check_clean_streak(self, stats: Dict, days: int) -> bool:
        """Check if system has been clean for specified days"""
        clean_days = stats.get("consecutive_clean_days", 0)
        return clean_days >= days
        
    def _load_unlocked(self) -> Set[str]:
        """Load previously unlocked achievements"""
        achievements_file = Path.home() / ".pyenvdoctor" / "achievements.json"
        
        if achievements_file.exists():
            with open(achievements_file, "r") as f:
                return set(json.load(f))
        return set()
        
    def _save_unlocked(self):
        """Save unlocked achievements"""
        achievements_file = Path.home() / ".pyenvdoctor" / "achievements.json"
        achievements_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(achievements_file, "w") as f:
            json.dump(list(self.unlocked_achievements), f)
