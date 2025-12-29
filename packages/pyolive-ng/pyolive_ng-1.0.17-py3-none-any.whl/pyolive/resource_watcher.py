
import os
import threading
import importlib
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

class ResourceReloadHandler(FileSystemEventHandler):
    def __init__(self, module_map, tasks, logger):
        super().__init__()
        self.module_map = module_map
        self.tasks = tasks
        self.logger = logger

    def on_modified(self, event):
        if event.is_directory:
            return

        abs_path = os.path.abspath(event.src_path)
        self.logger.info(f"watcher, modified file = {abs_path}")
        module_name = self.module_map.get(abs_path)

        if module_name:
            try:
                mod = importlib.import_module(module_name)
                importlib.reload(mod)
                self.logger.info(f"watcher, reloaded module: {module_name}")

                for task in self.tasks:
                    if task["resource"].__module__ == module_name:
                        if isinstance(task["resource"], type):
                            cls_name = task["resource"].__name__
                        else:
                            cls_name = type(task["resource"]).__name__

                        if hasattr(mod, cls_name):
                            new_class = getattr(mod, cls_name)
                            task["resource"] = new_class() if not isinstance(task["resource"], type) else new_class
                            self.logger.info(f"watcher, resource replaced: {module_name}.{cls_name}")
                        else:
                            self.logger.warning(f"watcher, class '{cls_name}' not found in module '{module_name}'")

            except Exception as e:
                self.logger.exception(f"watcher, reload failed for {module_name}: {e}")

def start_resource_watcher(tasks, logger):
    seen_modules = set()
    module_map = {}
    for task in tasks:
        resource = task.get("resource")
        if not resource:
            continue
        modname = resource.__module__
        if modname in seen_modules:
            continue
        seen_modules.add(modname)

        spec = importlib.util.find_spec(modname)
        if spec and spec.origin:
            filepath = os.path.abspath(spec.origin)
            module_map[filepath] = modname
            logger.info("module = %s", modname)
        else:
            logger.warning("Watchdog, cannot find module path: %s", modname)

    if not module_map:
        logger.info("Watchdog, no resource modules to watch.")
        return None

    watch_dirs = set()
    for path in module_map.keys():
        watch_dirs.add(os.path.dirname(path))

    event_handler = ResourceReloadHandler(module_map, tasks, logger)
    observer = PollingObserver()

    for d in watch_dirs:
        observer.schedule(event_handler, path=d, recursive=False)
        logger.info("Watchdog, watching directory: %s", d)

    thread = threading.Thread(target=observer.start, daemon=True)
    thread.start()
    logger.info("Watchdog, resource module watcher started.")
    return observer
