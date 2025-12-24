import os, sys
from pathlib import Path

def main():
    for t in ['list', 'tuple']:
        os.system(sys.executable + f" {Path(__file__).parent}/test-{t}.py -o test-{t}.json")
    os.system(sys.executable + " -m pyperf compare_to test-tuple.json test-list.json")

if __name__ == "__main__":
    main()
