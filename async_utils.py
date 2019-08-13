import asyncio
import concurrent.futures
import threading

import click

def safe_run_async(async_fn, *argv):
    loop = asyncio.get_event_loop()

    try:
        ret = loop.run_until_complete(async_fn(*argv))
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        loop.close()

    return ret

class AsyncProgressBar:
    '''
    An implementation of an async version of click's CLI progress bar,
    with atomic-based progress reporting.
    '''
    def __init__(self, max_workers):
        self.max_workers = max_workers
        # used to atomically update the progress bar
        self._lock = threading.Lock()

    def process(self, lst, map_fn, label):
        async def run_progressive_task(lst):
            def run_map_fn(item, bar):
                result = map_fn(item)

                # we lock the bar's access to prevent overwriting of
                # the progress from multiple workers
                with self._lock:
                    bar.update(1)

                return result

            with click.progressbar(length=len(lst), label=label) as bar:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    loop = asyncio.get_event_loop()
                    # generate the required tasks needed to be executed
                    futures = [loop.run_in_executor(executor, run_map_fn, item, bar) for item in lst]
                    # gather all the returned results and return the array
                    results_list = await asyncio.gather(*futures)
                    return results_list

        return safe_run_async(run_progressive_task, lst)