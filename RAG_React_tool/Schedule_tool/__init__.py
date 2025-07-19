from .schedule_sql_tool import ScheduleSQLTool, get_schedule_sql_tool

# For backward compatibility
SQLTool = ScheduleSQLTool
get_sql_tool = get_schedule_sql_tool

__all__ = ['ScheduleSQLTool', 'SQLTool', 'get_schedule_sql_tool', 'get_sql_tool']
