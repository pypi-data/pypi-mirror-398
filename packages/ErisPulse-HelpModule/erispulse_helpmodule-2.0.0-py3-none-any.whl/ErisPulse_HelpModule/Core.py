from ErisPulse import sdk
from ErisPulse.Core.Event import command
from ErisPulse.Core import config
from ErisPulse.Core.Bases import BaseModule
from typing import Dict, List

class HelpModule(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("HelpModule")
        self.command_list = []
        
    @staticmethod
    def should_eager_load():
        return True
    
    async def on_load(self, event):
        self._register_commands()
        self.logger.info("HelpModule 已加载")
        return True
        
    async def on_unload(self, event):
        self._unregister_commands()
        self.logger.info("HelpModule 已卸载")
        return True

    def _get_config(self):
        module_config = config.getConfig("HelpModule")
        if not module_config:
            default_config = {
                "show_hidden_commands": False,
                "group_commands": True
            }
            config.setConfig("HelpModule", default_config)
            self.logger.warning("未找到HelpModule配置，已创建默认配置")
            return default_config
        return module_config
    
    def _get_command_prefix(self) -> str:
        event_config = config.getConfig("ErisPulse.event", {})
        command_config = event_config.get("command", {})
        return command_config.get("prefix", "/")
        
    def _register_commands(self):
        self.help_command_func = self._create_help_command()
        command(
            "help", 
            aliases=["h", "帮助"], 
            help="显示帮助信息",
            usage="help [序号] - 显示命令列表或查看指定序号的命令详情"
        )(self.help_command_func)

    def _unregister_commands(self):
        if hasattr(self, 'help_command_func'):
            command.unregister(self.help_command_func)
    
    def _create_help_command(self):
        async def help_command(event):
            await self._handle_help_command(event)
        return help_command

    def _build_command_list(self) -> List[Dict]:
        self.command_list = []
        module_config = self._get_config()
        show_hidden = module_config.get("show_hidden_commands", False)
        
        if show_hidden:
            all_commands = command.get_commands()
            for cmd_name in all_commands:
                cmd_info = command.get_command(cmd_name)
                if cmd_info and cmd_name == cmd_info.get("main_name"):
                    self.command_list.append({
                        "name": cmd_name,
                        "info": cmd_info
                    })
        else:
            visible_commands = command.get_visible_commands()
            for cmd_name in visible_commands:
                cmd_info = command.get_command(cmd_name)
                if cmd_info and cmd_name == cmd_info.get("main_name"):
                    self.command_list.append({
                        "name": cmd_name,
                        "info": cmd_info
                    })
        
        return self.command_list

    def _group_commands_by_category(self, commands: List[Dict]) -> Dict[str, List]:
        grouped = {}
        for cmd in commands:
            group = cmd["info"].get("group") or "default"
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(cmd)
        return grouped

    async def _handle_help_command(self, event: Dict) -> None:
        try:
            platform = event["platform"]
            if event.get("detail_type") == "group":
                target_type = "group"
                target_id = event["group_id"]
            else:
                target_type = "user"
                target_id = event["user_id"]
                
            args = event.get("command", {}).get("args", [])
            adapter = getattr(sdk.adapter, platform)
            
            commands = self._build_command_list()
            
            if args:
                try:
                    index = int(args[0]) - 1
                    if 0 <= index < len(commands):
                        help_text = self._format_command_detail(commands[index])
                    else:
                        help_text = f"错误: 序号超出范围，请输入 1-{len(commands)} 之间的序号"
                except ValueError:
                    help_text = "错误: 请输入有效的序号"
            else:
                help_text = self._format_command_list(commands)
            
            await adapter.Send.To(target_type, target_id).Text(help_text)
        except Exception as e:
            self.logger.error(f"处理帮助命令时出错: {e}")

    def _format_command_list(self, commands: List[Dict]) -> str:
        prefix = self._get_command_prefix()
        module_config = self._get_config()
        
        lines = [
            "命令帮助",
            "-" * 10,
            f"使用 '{prefix}help <序号>' 查看命令详情",
            ""
        ]
        
        if module_config.get("group_commands", True):
            grouped = self._group_commands_by_category(commands)
            
            # 默认组
            if "default" in grouped:
                lines.append("[通用命令]")
                for idx, cmd in enumerate(grouped["default"], 1):
                    name = cmd["name"]
                    help_text = cmd["info"].get("help", "暂无描述")
                    lines.append(f"{idx}. {prefix}{name} - {help_text}")
                lines.append("")
            
            # 其他组
            for group, cmds in grouped.items():
                if group == "default":
                    continue
                group_name = str(group) if group else "其他"
                lines.append(f"[{group_name}命令]")
                for idx, cmd in enumerate(cmds, 1):
                    name = cmd["name"]
                    help_text = cmd["info"].get("help", "暂无描述")
                    lines.append(f"{idx}. {prefix}{name} - {help_text}")
                lines.append("")
        else:
            lines.append("[所有命令]")
            for idx, cmd in enumerate(commands, 1):
                name = cmd["name"]
                help_text = cmd["info"].get("help", "暂无描述")
                lines.append(f"{idx}. {prefix}{name} - {help_text}")
            lines.append("")
        
        lines.append("-" * 10)
        lines.append(f"共 {len(commands)} 个可用命令")
        
        return "\n".join(lines)
    
    def _format_command_detail(self, cmd: Dict) -> str:
        prefix = self._get_command_prefix()
        name = cmd["name"]
        info = cmd["info"]
        
        lines = [
            f"命令详情: {prefix}{name}",
            "-" * 10,
            f"描述: {info.get('help', '暂无描述')}"
        ]
        
        # 别名
        aliases = []
        for alias, main_name in command.aliases.items():
            if main_name == info['main_name'] and alias != info['main_name']:
                aliases.append(alias)
        
        if aliases:
            lines.append(f"别名: {', '.join(f'{prefix}{a}' for a in aliases)}")
        
        # 用法
        if info.get("usage"):
            lines.append(f"用法: {info['usage'].replace('/', prefix)}")
        
        # 权限
        if info.get("permission"):
            lines.append("权限: 需要特殊权限")
        
        # 隐藏状态
        if info.get("hidden"):
            lines.append("状态: 隐藏命令")
        
        # 分组
        if info.get("group"):
            lines.append(f"分组: {info['group']}")
        
        lines.append("-" * 10)
        
        return "\n".join(lines)