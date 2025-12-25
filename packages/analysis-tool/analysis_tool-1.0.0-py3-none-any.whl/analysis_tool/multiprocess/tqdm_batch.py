'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-02-23 02:00:12 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-02-23 02:37:30 +0100
FilePath     : tqdm_batch.py
Description  : 

Copyright (c) 2025 by everyone, All Rights Reserved. 
'''

from typing import List, Dict, Union, Callable
from math import ceil

from threading import Thread
from multiprocessing import Queue, Manager
from joblib import Parallel, delayed
from tqdm.auto import tqdm


def progress_bar(
    totals: Union[int, List[int]],
    queue: Queue,
) -> None:
    """
    Progress bar Thread

    A separate thread to manage the progress of all
    workers. When totals is a integer value a
    single progress bar is created and all updates
    in the queue update this single bar. To have
    a progress bar for each worker, totals should
    be a list with totals for each worker.

    Parameters:
    -----------
    totals : Union[int, List[int]]
      Totals for the single bar or for each worker,
      depending if it is a List of int or a single
      int.
    queue : multiprocessing.Queue
      Queue to receive progress updates. progress_bar
      expects an 'update' string to update a single
      bar or a string with the pid of the worker
      (i.e. f'update{pid}'). When finished, send a
      'done' to terminate the Thread.
    """
    if isinstance(totals, list):
        splitted = True
        pbars = [
            tqdm(
                desc=f'Worker {pid + 1}',
                total=total,
                position=pid,
            )
            for pid, total in enumerate(totals)
        ]
    else:
        splitted = False
        pbars = [tqdm(total=totals)]

    while True:
        try:
            message = queue.get()
            if message.startswith('update'):
                if splitted:
                    pid = int(message[6:])
                    pbars[pid].update(1)
                else:
                    pbars[0].update(1)
            elif message == 'done':
                break
        except:
            pass
    for pbar in pbars:
        pbar.close()


def task_wrapper(pid, function, batch, queue, *args, **kwargs):
    """
    Wrapper to add progress bar update
    """
    result = []
    for example in batch:
        result.append(function(example, *args, **kwargs))
        queue.put(f'update{pid}')
    return result


def batch_process(
    items: list,
    function: Callable,
    n_workers: int = 8,
    sep_progress: bool = False,
    *args,
    **kwargs,
) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Batch process a list of items

    The <items> will be divided into n_workers batches which process
    the list individually using joblib. When done, all results are
    collected and returned as a list.

    Parameters:
    -----------
    items : list
      List of items to batch process. This list will be divided in
      n_workers batches and processed by the function.
    function : Callable
      Function used to process each row. Format needs to be:
      callable(item, *args, **kwargs).
    n_workers : int (Default: 8)
      Number of processes to start (processes). Generally there is
      an optimum between 1 <= n_workeres <= total_cpus as there is
      an overhead for creating separate processes.
    sep_progress : bool (Default: False)
      Show a separate progress bar for each worker.
    *args, **kwargs : -
      (named) arguments to pass to batch process function.

    Returns:
    --------
    input_items : List [ Dict [ str, Union [ str, List [ str ]]]]
      List of processed input_items with collected id, words,
      tokens, and labels.
    """
    # Divide data in batches
    batch_size = ceil(len(items) / n_workers)
    batches = [items[ix : ix + batch_size] for ix in range(0, len(items), batch_size)]

    # Check single or multiple progress bars
    if sep_progress:
        totals = [len(batch) for batch in batches]
    else:
        totals = len(items)

    # Start progress bar in separate thread
    manager = Manager()
    queue = manager.Queue()
    try:
        progproc = Thread(target=progress_bar, args=(totals, queue))
        progproc.start()

        # Parallel process the batches
        result = Parallel(n_jobs=n_workers)(delayed(task_wrapper)(pid, function, batch, queue, *args, **kwargs) for pid, batch in enumerate(batches))

    finally:
        # Stop the progress bar thread
        queue.put('done')
        progproc.join()

    # Flatten result
    flattened = [item for sublist in result for item in sublist]

    return flattened


# Local test
if __name__ == '__main__':
    # from tqdm_batch import batch_process
    import random
    import time

    def batch_process_function(row, some_var):
        time.sleep(0.01)
        return row + some_var

    def _batch_process_function(row, some_var):
        _haha = batch_process_function(row, some_var)
        return {row: _haha}

    def _batch_process_function2(args: Dict[str, int]):
        _haha = batch_process_function(**args)
        return {args['row']: _haha}

    if 0:
        N = 2_0
        # items = range(N)
        items = [i for i in range(N)]

        result = batch_process(
            items,
            _batch_process_function,
            some_var=42,
            n_workers=6,
            sep_progress=True,
        )
    if 1:
        N = 2_0
        items = []
        for i in range(N):
            items.append(
                {
                    'row': i,
                    'some_var': i,
                }
            )

        result = batch_process(
            items,
            _batch_process_function2,
            n_workers=6,
            sep_progress=True,
        )

    print(result)
    combined_dict = {k: v for d in result for k, v in d.items()}
    print(combined_dict)
