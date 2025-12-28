"""Cleanup utilities - Temporary file management."""

import os
import tempfile
import time


def cleanup_temp_files(test_id: str):
    """Cleanup temporary files for a specific test.
    
    Args:
        test_id: Test ID to cleanup files for
    """
    tmp_dir = tempfile.gettempdir()
    patterns = [
        f"k6-summary-{test_id}.json",
        f"k6-script-{test_id}.js",
        f"k6-output-{test_id}.log"
    ]
    
    for pattern in patterns:
        filepath = os.path.join(tmp_dir, pattern)
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
        except Exception:
            pass


def cleanup_old_files(max_age_hours: int = 24):
    """Cleanup old K6 temporary files.
    
    Args:
        max_age_hours: Maximum age in hours before cleanup
    """
    tmp_dir = tempfile.gettempdir()
    max_age_seconds = max_age_hours * 60 * 60
    current_time = time.time()
    
    try:
        for filename in os.listdir(tmp_dir):
            if not filename.startswith("k6-"):
                continue
            
            filepath = os.path.join(tmp_dir, filename)
            try:
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    os.unlink(filepath)
            except Exception:
                pass
    except Exception:
        pass

