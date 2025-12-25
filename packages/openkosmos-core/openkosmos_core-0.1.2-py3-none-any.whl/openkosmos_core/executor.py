import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from openkosmos_core.setting import Setting

log = Setting.logger("executor")


class TaskExecutor:

    def __init__(self, fn, completed_callback=None, delay=0, meta={}, exception_callback=None):
        self.fn = fn
        self.completed_callback = completed_callback
        if exception_callback is None:
            self.exception_callback = lambda exception: True
        else:
            self.exception_callback = exception_callback
        self.delay = delay
        self.meta = meta

    def start(self, feed, max_worker=1, wait=True, show_progress=True):
        if wait:
            start = time.time()
            with ThreadPoolExecutor(max_workers=max_worker) as executor:
                futures = {executor.submit(self.execute, param): param for param in feed}
                results = []
                if show_progress:
                    with tqdm(total=len(feed), desc="progress") as progress_bar:
                        for future in as_completed(futures):
                            param = futures[future]
                            try:
                                result = future.result()
                                results.append(result)
                                progress_bar.update(1)
                            except Exception as e:
                                log.exception(e)
                                log.error("an exception when execute : {}, {}".format(param, e))
                                if self.exception_callback(e):
                                    progress_bar.close()
                                    executor.shutdown()
                                    return results
                else:
                    for future in as_completed(futures):
                        param = futures[future]
                        try:
                            result = future.result()
                            results.append(result)
                        except Exception as e:
                            log.exception(e)
                            log.error("an exception when execute : {}, {}".format(param, e))
                            if self.exception_callback(e):
                                executor.shutdown()
                                return results

                log.info("all completed...")
                if self.completed_callback is not None:
                    self.completed_callback(results, self.meta)
                else:
                    log.info("all done[{:.3f}] with results : {}, {}".format(time.time() - start, results,
                                                                             self.meta))
                return results
        else:
            executor = ThreadPoolExecutor(max_workers=max_worker)
            futures = {executor.submit(self.execute, param): param for param in feed}
            return futures

    def execute(self, param):
        # log.debug("start : {}".format(param))
        if self.delay > 0:
            time.sleep(self.delay)
        result = self.fn(param, self.meta)
        # log.debug("stop : {}".format(param))
        return result
