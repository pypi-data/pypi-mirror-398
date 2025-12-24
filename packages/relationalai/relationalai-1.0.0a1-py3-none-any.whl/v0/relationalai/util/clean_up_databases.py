import v0.relationalai as rai
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
import re
import logscope
import argparse

from datetime import datetime, timedelta
from relationalai_test_util.fixtures import make_config

log = logscope.logger()

def contains_hash_like_substring(s):
    """
    Checks whether the input string contains a hash-like substring.
    A hash-like substring is defined as a string of 8 or more hexadecimal characters.

    Args:
        s (str): The input string to check.

    Returns:
        bool: True if a hash-like substring is found, False otherwise.
    """
    hex_pattern = re.compile(r'[a-fA-F0-9]{8,}')
    return bool(hex_pattern.search(s))

def should_delete(m, users, days):
    cutoff = (datetime.now() + timedelta(days=-days)).strftime('%Y-%m-%dT%H:%M')

    # Always preserve pyrel_root_db
    if m['name'] == 'pyrel_root_db':
        return False

    return (
        m['created_by'] in users
        and contains_hash_like_substring(m['name'])
        and str(m['created_on']) < cutoff
    )

def delete_model(provider, model_name):
    try:
        provider.delete_model(model_name)
        log(model_name, "deleted")
        return True, model_name
    except Exception as e:
        return False, f"Error for model {model_name}: {e}"

def delete_more_concurrently(users, days, max_workers=10, timeout=15):
    config = make_config()
    # Disable graph index since we are directly collecting and deleting rai databases for passed users
    config.set("use_graph_index", False)
    provider = rai.Provider(config=config)
    models = [m for m in provider.list_models() if should_delete(m, users, days)]

    log(f"Deleting {len(models)} models...")

    deleted_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(delete_model, provider, m['name']): m['name']
            for m in models
        }

        for future in as_completed(futures):
            model_name = futures[future]
            try:
                success, result = future.result(timeout=timeout)
                if success:
                    deleted_count += 1
                else:
                    log(result)
            except TimeoutError:
                log(f"Timeout reached for model: {model_name}. Moving on.")
            except Exception as e:
                log(f"Unexpected error for model {model_name}: {e}")

    return deleted_count

def main():
    parser = argparse.ArgumentParser(description='Clean up databases')
    parser.add_argument('--users', nargs='+', required=True,
                        help='List of users whose databases to clean up')
    parser.add_argument('--days', type=int, required=True,
                        help='Delete databases older than this many days')

    args = parser.parse_args()

    log(f"Starting cleanup for users: {args.users}")
    log(f"Deleting databases older than {args.days} days")

    while d := delete_more_concurrently(args.users, args.days):
        log(f"Deleted {d} more models...")

if __name__ == '__main__':
    main()
