'''
Author: yasin l1y0l20@qq.com
Date: 2025-01-16 16:39:21
LastEditors: yasin l1y0l20@qq.com
LastEditTime: 2025-01-16 16:47:33
FilePath: /applet-video-python-handle/src/utils/timing_instrumentation.py
Description: 

Copyright (c) 2021-2025 by yasin, All Rights Reserved. 
'''
import json
import logging
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class TimingInstrumentation:
    def __init__(self, threshold: Optional[int] = None):
        self.timings: Dict[str, Dict[str, Any]] = {}
        self.start_times: Dict[str, float] = {}
        self.threshold = 50 if threshold  is None else threshold
        
    def start_timer(self, name: str):
        """Start timing a named section"""
        if name in self.start_times:
            logger.warn("Cannot start new timer while another is running")
            return
        self.start_times[name] = time.time()
        
    def stop_timer(self, name: str):
        """Stop timing a named section and record the duration"""
        if name not in self.start_times:
            return
            
        duration = time.time() - self.start_times[name]
        if name not in self.timings:
            self.timings[name] = {'durations': [], 'total': 0.0}
        durations = self.timings[name]['durations']
        durations.append(duration)
        excess = len(durations) - self.threshold
        if excess > 0:
            self.timings[name]['durations'] = durations[excess:]
        self.timings[name]['total'] = sum(self.timings[name]['durations'])
        del self.start_times[name]
        
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all timings"""
        """Return timing summary with performance analysis"""
        summary = {}
        for name, data in self.timings.items():
            durations = data['durations']
            summary[name] = {
                'duration': data['total'],
                'durations': durations,
                'count': len(durations),
                'avg': sum(durations) / len(durations) if durations else 0,
                'max': max(durations) if durations else 0,
                'min': min(durations) if durations else 0
            }
        return summary
    
    def log_summary(self):
        """Return timing summary with performance analysis"""
        summary = self.get_summary()
        logger.info(f"Timing summary is {json.dumps(summary)}")
