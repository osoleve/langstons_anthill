#!/usr/bin/env python3
"""Watch for interesting events in the game."""

import time
import sys

sys.path.insert(0, '/home/user/langstons_anthill')
from engine.state import load_state

def main():
    prev_tick = 0
    prev_ant_count = 0
    prev_influence = 0
    prev_visitor_count = 0

    print("Watching game state... (Ctrl+C to stop)")
    print()

    while True:
        try:
            state = load_state()
            tick = state['tick']
            fungus = state['resources']['fungus']
            influence = state['resources']['influence']
            ant_count = len([e for e in state['entities'] if e.get('type') == 'ant'])
            visitor_count = len([e for e in state['entities'] if e.get('type') == 'visitor'])

            # Only print updates every 10 ticks
            if tick - prev_tick >= 10:
                print(f"[{tick}] Fungus: {fungus:.2f}/15  Influence: {influence:.3f}/2.0  Ants: {ant_count}  Visitors: {visitor_count}")
                prev_tick = tick

            # Alert on queen spawn
            if ant_count > prev_ant_count:
                print(f"\n🐜 QUEEN SPAWNED at tick {tick}! Colony now has {ant_count} ants\n")
                prev_ant_count = ant_count

            # Alert on summoning threshold
            if influence >= 2.0 and prev_influence < 2.0:
                print(f"\n📡 SUMMONING THRESHOLD at tick {tick}! Influence: {influence:.3f}\n")
                prev_influence = influence

            # Alert on visitor arrival
            if visitor_count > prev_visitor_count:
                visitors = [e for e in state['entities'] if e.get('type') == 'visitor']
                for v in visitors:
                    print(f"\n👽 VISITOR ARRIVED at tick {tick}! Type: {v.get('subtype', 'unknown')}\n")
                prev_visitor_count = visitor_count

            # Alert on visitor departure
            if visitor_count < prev_visitor_count:
                print(f"\n👋 VISITOR DEPARTED at tick {tick}\n")
                prev_visitor_count = visitor_count

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n\nWatcher stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
