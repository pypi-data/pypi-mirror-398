"""
Session statistics.
"""

import time
import uuid
import sys
import platform
import os
import requests
from .theme import Colors, Borders, Icons
from . import config
from . import __version__

# Telemetry Configuration
# This is used to have an idea of how many people are using the project.
# It is completely anonymous and can be disabled with `/telemetry false`.
# It has a vercel-side rate limit of 1 request per 10 minutes.
TELEMETRY_URL = "https://grucli.gru0.dev/api/stats"
LAST_PING_FILE = os.path.join(config.get_config_dir(), ".last_ping")

class SessionStats:
    """Track session statistics."""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.start_time = time.time()
        self.tool_calls_total = 0
        self.tool_calls_success = 0
        self.tool_calls_failed = 0
        self.model_usage = {}
        self.api_time_total = 0
    
    def record_tool_call(self, success=True):
        self.tool_calls_total += 1
        if success:
            self.tool_calls_success += 1
        else:
            self.tool_calls_failed += 1
            
    def record_request(self, model_name, api_duration=0):
        if model_name not in self.model_usage:
            self.model_usage[model_name] = {'reqs': 0, 'input_tokens': 0, 'cache_reads': 0, 'output_tokens': 0}
        self.model_usage[model_name]['reqs'] += 1
        self.api_time_total += api_duration
        
    def record_tokens(self, model_name, input_tokens=0, output_tokens=0, cache_reads=0):
        if model_name not in self.model_usage:
            self.model_usage[model_name] = {'reqs': 0, 'input_tokens': 0, 'cache_reads': 0, 'output_tokens': 0}
        self.model_usage[model_name]['input_tokens'] += input_tokens
        self.model_usage[model_name]['output_tokens'] += output_tokens
        self.model_usage[model_name]['cache_reads'] += cache_reads

    def get_formatted_summary(self):
        """Generate session summary."""
        end_time = time.time()
        wall_time = end_time - self.start_time
        
        minutes = int(wall_time // 60)
        seconds = int(wall_time % 60)
        wall_time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        
        tool_success_rate = 0.0
        if self.tool_calls_total > 0:
            tool_success_rate = (self.tool_calls_success / self.tool_calls_total) * 100
            
        api_time_pct = 0.0
        if wall_time > 0:
            api_time_pct = (self.api_time_total / wall_time) * 100

        summary = []
        
        summary.append("")
        summary.append(f"{Colors.MUTED}{Borders.HORIZONTAL * 40}{Colors.RESET}")
        summary.append(f"{Colors.BOLD}Session{Colors.RESET}  {Colors.MUTED}#{self.session_id}{Colors.RESET}")
        
        summary.append(f"  {Colors.MUTED}Duration:{Colors.RESET}  {Colors.WHITE}{wall_time_str}{Colors.RESET}")
        summary.append(f"  {Colors.MUTED}API time:{Colors.RESET}  {Colors.WHITE}{self.api_time_total:.1f}s{Colors.RESET} {Colors.MUTED}({api_time_pct:.0f}%){Colors.RESET}")
        
        if self.tool_calls_total > 0:
            summary.append(f"  {Colors.MUTED}Tools:{Colors.RESET}     {Colors.WHITE}{self.tool_calls_total}{Colors.RESET} {Colors.MUTED}({Colors.SUCCESS}{Icons.CHECK}{self.tool_calls_success}{Colors.MUTED} {Colors.ERROR}{Icons.CROSS}{self.tool_calls_failed}{Colors.MUTED}){Colors.RESET}")
        
        if self.model_usage:
            for model, usage in self.model_usage.items():
                display_model = model if len(model) < 25 else model[:22] + "..."
                summary.append(f"  {Colors.MUTED}Model:{Colors.RESET}     {Colors.SECONDARY}{display_model}{Colors.RESET} {Colors.MUTED}({usage['reqs']}){Colors.RESET}")

        summary.append(f"{Colors.MUTED}{Borders.HORIZONTAL * 40}{Colors.RESET}")
        summary.append("")
        
        return "\n".join(summary)

    def print_summary(self):
        print(self.get_formatted_summary())


def send_telemetry_ping():
    """
    Sends an anonymous ping to the developer to track usage.
    This is non-invasive and can be disabled via `/telemetry false`.
    """
    if not config.get_telemetry_enabled():
        return


    # Prepare anonymous payload
    payload = {
        "os": platform.system().lower(),
        "version": __version__
    }

    # Send ping in the background (roughly) by using a small timeout
    try:
        # We don't want to wait for the response, but we can't easily do a true 
        # async call without extra dependencies or threading.
        # A very short timeout ensures we don't hang if the server is slow.
        requests.post(TELEMETRY_URL, json=payload, timeout=1.5)
    except Exception:
        # Silently fail, telemetry should never break the user experience
        pass


# Global instance
STATS = SessionStats()
