#!/usr/bin/env python3
"""
watch_and_ingest.py

Watch `raw_data/` for new files and run the pipeline automatically. Uses
polling to keep dependency surface simple and cross-platform.
"""
import time
import os
import argparse
import subprocess


def find_unprocessed(raw_dir, processed_dir):
    os.makedirs(processed_dir, exist_ok=True)
    processed = set(os.listdir(processed_dir))
    all_files = [f for f in os.listdir(raw_dir) if os.path.isfile(os.path.join(raw_dir, f))]
    to_process = [os.path.join(raw_dir, f) for f in all_files if f not in processed]
    return to_process


def main():
    p = argparse.ArgumentParser(description='Watch raw_data and run pipeline on new files')
    p.add_argument('--raw', default='raw_data')
    p.add_argument('--processed', default='raw_data/processed')
    p.add_argument('--poll', type=int, default=5)
    p.add_argument('--db', default='data/leaks.db')
    p.add_argument('--hash-salt', default='')
    p.add_argument('--encrypt', action='store_true')
    args = p.parse_args()

    print('Watching', args.raw, '-> processed:', args.processed)
    while True:
        to_process = find_unprocessed(args.raw, args.processed)
        for path in to_process:
            print('Processing', path)
            try:
                subprocess.run(['python3', 'tools/ingest/pipeline.py', '--source', path, '--db', args.db, '--hash-salt', args.hash_salt] + (['--encrypt'] if args.encrypt else []), check=True)
            except subprocess.CalledProcessError as e:
                print('Pipeline failed for', path, e)
        time.sleep(args.poll)


if __name__ == '__main__':
    main()
