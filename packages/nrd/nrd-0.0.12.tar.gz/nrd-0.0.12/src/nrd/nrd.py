#!/usr/bin/env python

from .sites import secured_sites
import subprocess
import time
from icecream import ic


def main():
    """Main entry point for NRD."""
    processes = {}
    
    # Start all Vite dev servers
    for site in secured_sites:
        site_name = site["site"]
        ic(f"Starting {site_name}")
        proc = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=site["path"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        processes[site_name] = {
            'process': proc,
            'path': site["path"],
            'restarts': 0
        }
    
    # Monitor and restart crashed processes
    try:
        while True:
            for site_name, site_info in processes.items():
                proc = site_info['process']
                
                # Check if process has died
                if proc.poll() is not None:
                    site_info['restarts'] += 1
                    ic(f"⚠️  {site_name} crashed! Restarting... (restart #{site_info['restarts']})")
                    
                    # Restart the process
                    new_proc = subprocess.Popen(
                        ['npm', 'run', 'dev'],
                        cwd=site_info['path'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    site_info['process'] = new_proc
                    
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print("\nShutting down NRD...")
        # Terminate all processes
        for site_name, site_info in processes.items():
            proc = site_info['process']
            if proc.poll() is None:
                ic(f"Stopping {site_name}")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()


if __name__ == '__main__':
    main()
