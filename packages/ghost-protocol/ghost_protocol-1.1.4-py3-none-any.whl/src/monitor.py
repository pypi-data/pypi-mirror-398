import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.live import Live
from rich.text import Text
from .config import Config, VERSION
from .scanner import ProjectScanner
from .ai_reviewer import AIReviewer
from .analyzer import CodeAnalyzer

# Настройка таймзоны Ekaterinburg (+5)
EKB_TZ = timezone(timedelta(hours=5))

COST_PER_M_TOKENS = 3.0
SCAN_INTERVAL_SECONDS = 30

class Monitor:
    def __init__(self, root: Path):
        self.root = root
        self.scanner = ProjectScanner(root)
        self.cfg = Config.get()
        self.console = Console()
        
        # Инициализация новых модулей
        self.ai_reviewer = AIReviewer(root)
        self.analyzer = CodeAnalyzer(root)
        
        self.last_generated_prompt_status = "No prompt"
        self.command_queue = [] # Очередь команд на выполнение

    def _get_time_str(self):
        return datetime.now(EKB_TZ).strftime("%H:%M:%S")

    def _generate_layout(self) -> Layout:
        stats = self.scanner.get_stats()
        layout = Layout()
        
        # 3 колонки + Header
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1)
        )
        layout["body"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="top10", ratio=1),
            Layout(name="logs", ratio=1)
        )

        # Header
        layout["header"].update(
            Panel(f"👻 [bold]Ghost Protocol v{VERSION}[/bold] | Status: [bold green]GUARDIAN ACTIVE[/green][/bold]", style="black on #1e1e1e")
        )

        # Col 1: Stats
        table_stats = Table(box=None, expand=True, show_header=False)
        table_stats.add_column("Metric", style="cyan", width=15)
        table_stats.add_column("Value", style="bold green")
        
        tokens = stats.get('total_tokens', 0)
        files = stats.get('files_count', 0)
        table_stats.add_row("Total Tokens", f"{tokens:,}")
        table_stats.add_row("Files Tracked", str(files))
        table_stats.add_row("Est. Cost ($3/M)", f"${(tokens / 1_000_000) * COST_PER_M_TOKENS:.4f}")
        
        layout["stats"].update(Panel(table_stats, title="📊 Project Stats", style="#1e1e1e on #000000"))

        # Col 2: Top 10 Heavy Files (Здесь можно показать список тяжелых файлов)
        # Пока заглушка, в реальном сканере можно реализовать
        table_top = Table(box=None, expand=True, show_header=True)
        table_top.add_column("File", style="magenta")
        table_top.add_column("Tokens", style="yellow", justify="right")
        # Заглушка данных (реальный анализ будет медленным)
        table_top.add_row("scanner.py", "5.2K")
        table_top.add_row("config.py", "1.8K")
        
        layout["top10"].update(Panel(table_top, title="🔥 Top Heavy Files", style="#1e1e1e on #000000"))

        # Col 3: Logs (Динамический список)
        # В реальном приложении здесь будет `self.logs` (deque)
        log_text = (
            f"[{self._get_time_str()}] System ready.\n"
            f"[{self._get_time_str()}] Waiting for commands...\n"
            f"[dim]Last AI Status: {self.ai_reviewer.get_status()}[/dim]"
        )
        layout["logs"].update(Panel(log_text, title="🧠 Activity Log (+5)", style="#1e1e1e on #000000"))

        # Footer (выводим через print, т.к. это часть UI, а не Layout)
        # В Rich Live сложнее делать динамический footer, поэтому мы рисуем его в логах или просто оставляем как есть.
        
        return layout

    def _handle_input(self):
        """Обработка ввода (Windows only для msvcrt)"""
        if sys.platform != "win32":
            return # Не поддерживаем kbhit на Linux/Mac (там select нужен)
        
        import msvcrt
        
        if msvcrt.kbhit():
            key = msvcrt.getch()
            char = key.decode('utf-8')
            
            if char == '1':
                # Команда 1: AI Review
                self.console.print("\n[bold yellow]Running AI Review...[/bold yellow]")
                self.ai_reviewer.run_review()
            elif char == '2':
                # Команда 2: Copy Prompt
                success, msg = self.ai_reviewer.copy_prompt_to_clipboard()
                self.console.print(f"\n[{'green' if success else 'red'}]{msg}[/]")
            elif char == '3':
                # Команда 3: Full Check
                self.console.print("\n[bold yellow]Running Full Project Check...[/bold yellow]")
                report = self.analyzer.full_check()
                self.console.print(report)

    def start(self):
        # Initial scan
        self.scanner.scan_full_project()
        
        with Live(self._generate_layout(), console=self.console, refresh_per_second=1) as live:
            last_scan = time.time()
            
            self.console.print("\n[bold cyan]CONTROLS:[/bold cyan] [1] AI Review  [2] Copy Prompt  [3] Full Check")
            
            try:
                while True:
                    # Обновление данных
                    now = time.time()
                    if now - last_scan > SCAN_INTERVAL_SECONDS:
                        self.scanner.scan_full_project()
                        last_scan = now
                    
                    live.update(self._generate_layout())
                    
                    # Неблокирующая проверка ввода
                    self._handle_input()
                    
                    time.sleep(0.1) # Уменьшил с 1 до 0.1 для отзывчивости кнопок
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Ghost stopped.[/yellow]")