from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.tree import Tree
from sayou.core.callbacks import BaseCallback


class RichConsoleTracer(BaseCallback):
    def __init__(self):
        self.root_tree = Tree("🚀 [bold white]Pipeline Started[/]")
        self.comp_branches = {}
        self.live = Live(self.render_panel(), refresh_per_second=4)
        self.record_console = Console(record=True)

    def render_panel(self):
        return Panel(
            self.root_tree, title="Sayou Fabric - Live Status", border_style="blue"
        )

    def on_start(self, component_name, input_data, **kwargs):
        if not self.live.is_started:
            self.live.start()

        if component_name not in self.comp_branches:
            if "ConnectorPipeline" in component_name:
                branch = self.root_tree
            else:
                icon = "💎" if "Generator" in component_name else "⚡"
                branch = self.root_tree.add(f"{icon} [bold cyan]{component_name}[/]")

            self.comp_branches[component_name] = branch

        branch = self.comp_branches[component_name]
        data_id = self._get_simple_id(input_data)

        if data_id:
            branch.add(f"[yellow]Processing:[/] {data_id}")
            self.live.refresh()

    def on_finish(self, component_name, result_data, success, **kwargs):
        # 완료 시점 처리 (여기서는 단순화를 위해 색상 변경 등은 생략하고 로그처럼 쌓이게 둠)
        # 고도화 시: Tree의 마지막 노드를 찾아서 아이콘을 ✅로 변경 가능
        pass

    def on_error(self, component_name, error, **kwargs):
        branch = self.comp_branches.get(component_name, self.root_tree)
        branch.add(f"❌ [bold red]Error:[/] {str(error)}")
        self.live.refresh()

    def stop(self):
        self.root_tree.add("✅ [bold green]Finished[/]")
        self.live.stop()

    def _get_simple_id(self, data):
        if isinstance(data, dict):
            return data.get("source")
        if hasattr(data, "uri"):
            return data.uri
        return None

    def save_html(self, filename="live_log.html"):
        self.record_console.print(self.render_panel())
        self.record_console.save_html(filename)
        self.record_console.save_svg(filename.replace(".html", ".svg"))
