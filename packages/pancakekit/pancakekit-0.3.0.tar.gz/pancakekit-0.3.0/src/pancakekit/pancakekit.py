import uuid
import os, sys, time
import traceback
import logging
import glob
import pickle
import html as html_module
from datetime import datetime
import queue
import inspect
import importlib
import re
import webbrowser
import functools

import uvicorn
# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer

from jinja2 import Template

from .utils import *
from .server import FastAPIServer

PANCAKE_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
PANCAKE_TEMP_DIR = os.path.join(os.path.dirname(__file__), "static", "temp")

def package_path(*path):
    return os.path.join(os.path.dirname(__file__), *path)

def static_path(*path):
    return os.path.join(PANCAKE_STATIC_DIR, *path)

def temp_path(*path):
    return os.path.join(PANCAKE_TEMP_DIR, *path)


# class PancakeChangeHandler(FileSystemEventHandler):
#     def __init__(self, file_path, callback_func):
#         self.file_path = file_path
#         self.callback_func = callback_func
#         super().__init__()
#     def on_modified(self, event):
#         if event.src_path == self.file_path:
#             self.callback_func()

class RecipeBook:
    def __init__(self, plate:object, recipes:list=None):
        self._plate = plate
        self._modules = {}
        self._toppings = {}
        self._tags = {}
        if recipes is None:
            recipes = self.get_recipe_list()
        self.load_recipes(recipes)
    
    def load_recipes(self, recipes):
        self._plate.logger.info("Loading recipes...")
        for recipe_name in recipes:
            self._plate.logger.info(f" - {recipe_name}")
            if not self.load_recipe(recipe_name):
                self._plate.logger.warning(f" --> failed")

    def load_recipe(self, recipe_name):
        loaded = True
        try:
            module_name = f"pancakekit.recipes.{recipe_name}"
            
            if module_name not in self._modules:
                self._modules[module_name] = importlib.import_module(module_name)
            else:
                self._modules[module_name] = importlib.reload(self._modules[module_name])
            for item_name in dir(self._modules[module_name]):
                item = getattr(self._modules[module_name], item_name)
                if item_name.startswith("_") or not inspect.isclass(item):
                    continue
                if issubclass(item, Topping):
                    self._toppings[item_name] = item
                elif issubclass(item, Tag):
                    self._toppings[item_name] = item
                    
        except Exception:
            self._plate.logger.exception(traceback.format_exc())
            loaded = False
        return loaded


    @classmethod
    def get_recipe_list(cls):
        recipe_list = skip_exception(glob.glob, package_path("recipes", "*/"), error_return_value=[])
        recipe_list = [os.path.basename(file_path[:-1]) for file_path in recipe_list]
        return recipe_list

    @classmethod
    def open_recipe_folder(cls):
        if skip_exception(os.makedirs, package_path("recipes"), exist_ok=True, return_value="ok") is None:
            return
        path = os.path.realpath(static_path("recipes"))
        webbrowser.open('file:///' + path)
    
    def __getattr__(self, key):
        if key in self._toppings:
            return self._toppings[key]
        if key in self._tags:
            return self._tags[key]

class NameManager:
    def __init__(self, parent=None):
        self.count_dict = {}

    def unique_name(self, candidate):
        no_index_if_possible = True
        if not isinstance(candidate, str):
            if hasattr(candidate, "arguments") and "name" in candidate.arguments:
                candidate = candidate.arguments["name"]
            else:
                candidate = candidate.__class__.__name__.lower()
                no_index_if_possible = False

        index_str = re.search(r"\d*$", candidate).group()
        sl = len(index_str)
        index = int(index_str) if sl else 0
        basename = candidate[:-sl if sl else None]
        if basename not in self.count_dict:
            self.count_dict[basename] = -1
            if no_index_if_possible:
                return candidate
        self.count_dict[basename] = max(self.count_dict[basename]+1, index)
        return basename + str(self.count_dict[basename])


class ToppingCollection:
    def __init__(self):
        self.toppings = {}
        self.topping_order = []
        self.name_manager = NameManager()

    def register(self, topping, name=None):
        name = self.name_manager.unique_name(topping if name is None else name)
        self.toppings[name] = topping
        if name not in self.topping_order:
            self.topping_order.append(name)
        return name

    def unregister(self, topping_name):
        topping = self.toppings.pop(topping_name, None)
        if topping_name in self.topping_order:
            self.topping_order.remove(topping_name)
        return topping

class Event:
    def __init__(self, sender_id, event_type, value, in_cake):
        self.sender_id = sender_id
        self.event_type = event_type
        self.value = value
        self.in_cake = in_cake
        self.origin = None
        self.topping = None

class Plate():
    SCRIPT_DIR = "js"
    def __init__(self, storage:bool=True, auto_reload:bool=True, recipes:list=None, logger:logging.Logger=None, **kwargs):
        self.running = False
        self.set_logger(logger)
        self.server = FastAPIServer(self, static_dir=PANCAKE_STATIC_DIR)
        self.app = self.server.app
        # expose Event for server without circular import
        self.Event = Event

        main_file = skip_exception(getattr, sys.modules['__main__'], "__file__", error_msg="file cannot be saved.")
        self.main_file_path = os.path.abspath(main_file) if main_file is not None else None

        self.restricted = False
        self.storage_dir = None
        if storage and self.main_file_path is not None:
            name = os.path.splitext(os.path.basename(self.main_file_path))[0]
            dir_name = f"pancake_storage_{name}"
            storage_dir = os.path.join(os.path.dirname(self.main_file_path), dir_name)
            self.storage_dir = skip_exception(os.makedirs, storage_dir, exist_ok=True, return_value=storage_dir)
        self.arguments = kwargs.copy()
        self.gv = Variables(file_path=join_path_or_none(self.storage_dir, "global_variables"))
        self.cakes = {}
        self.pancakes = {}
        self.default_cake = ""
        self.current_cake_name = None
        
        self.update_interval = 0.05 # (s)
        self.long_polling_interval = 10.0 # (s)
        self.uid = uuid.uuid4().hex
        self.update_needed_queue = queue.Queue(maxsize=1)
        self.commands = []
        self.name_manager = NameManager()
        # self.recipes = RecipeBook(self, recipes)

        if "card_script" not in self.arguments:
            self.arguments["card_script"] = ["from pancakekit import *", "from math import *"]

        self._observer = None
        if auto_reload and self.main_file_path is not None:
            self.observe_main_recipe()
        
        self.cake = Cake(self, "_plate_", hidden=True)

    
    def serve(self, wait_done=True, debug=False, host:str="127.0.0.1", port:int=8000, interactive=False):
        self.host = host
        self.port = port
        self.url = f"http://{self.host}:{self.port}"
        self.restricted = host not in ["127.0.0.1"]
        if is_mode_interactive():
            wait_done = False

        if not debug:
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
        self.run_server()
        time.sleep(1)
        self.logger.info(f"Go to: http://{self.host}:{self.port}/")
        if wait_done and not interactive:
            self.wait_done()

        if is_mode_interactive() or interactive:
            webbrowser.open(f"http://{self.host}:{self.port}/")

        if interactive:
            import code
            code.interact(local=globals())
    
    @new_thread
    def run_server(self):
        if not self.running:
            self.running = True
            uvicorn.run(self.app, port=self.port, host=self.host, log_level="info")

    def wait_done(self):
        while True:
            try:
                user_input = input("Input q to finish: \n")
                if user_input == "q":
                    break
            except KeyboardInterrupt:
                break
        self.done()

    def make_response(self, cake_name):
        updates = self.cake.revisions()
        for k, v in self.cakes[cake_name].revisions().items():
            updates[k] = v
        self.organize_commands()
        response_dict = {"status": "ok", "updates": updates, "commands": self.commands}
        self.commands = []
        return response_dict
    
    def __getitem__(self, name):
        return self.pancakes[name] if name in self.pancakes else None
        
    def __setitem__(self, name, pancake):
        if name in self.pancakes:
            self.logger.error(f"Pancake {name} already exists.")
            return
        self.pancakes[name] = pancake
        
    def new_cake(self, cake_name, hidden=False, **kwargs):
        cake_name = self.name_manager.unique_name(cake_name)
        cake = Cake(self, cake_name, hidden=hidden)
        if len(self.cakes) == 0 and not hidden:
            self.default_cake = cake_name
            self.current_cake_name = cake_name
        self.cakes[cake_name] = cake
        return cake
    
    def render(self):
        self.prepare_hidden_contents()
        root_html = self.make_root_html()
        return "<!DOCTYPE html>\n" + root_html.render()

    def make_root_html(self):
        root_html = Tag("html")
        head = root_html.add("head")
        meta = head.add("meta", {"name": "apple-mobile-web-app-capable", "content": "yes"})
        title = head.add("title")
        title.add_html("Pancake")
        # Web Awesome (Free) + legacy class compatibility layer.
        # Use a local, bundled 2-file build (CSS + JS) to avoid CDN dependency.
        head.add("link", {"rel": "stylesheet", "href": "/static/vendor/webawesome/webawesome.min.css"})
        head.add("script", {"type": "module", "src": "/static/vendor/webawesome/webawesome.min.js"})
        head.add("link", {"rel": "stylesheet", "href": "/static/css/webawesome-compat.css"})
        head.add("link", {"rel":"stylesheet", "href":"/static/css/pancake.css"})
        head.add("link", {"rel":"stylesheet", "href":"/static/css/card.css"})
        head.add("link", {"rel":"stylesheet", "href":"/static/css/honeycomb.css"})
        javascript = head.add("script")
        js = ""
        file_list = glob.glob(static_path("js", "*.js"))
        update_interval_ms = self.update_interval * 1000
        variables = locals()
        variables["SELF"] = {key: value for key, value in self.__dict__.items()}
        file_list = [file_path for file_path in file_list if file_path.endswith(f"{os.sep}main.js")] + [file_path for file_path in file_list if not file_path.endswith(f"{os.sep}main.js")]
        for file_path in file_list:
            try:
                with open(file_path, "r") as f:
                    source = f.read()
                    template = Template(source)
                    js += template.render(variables) + "\n"
            except Exception:
                self.logger.exception(traceback.format_exc())
        javascript.add_html(js)
        
        from .basecomponent.navigation import NavigationBar
        menu_dict = {"Kitchen": "go_to_cake('_Kitchen');"}
        body = root_html.add("body")
        cakes_on_nav = [k for k, v in self.cakes.items() if not v.hidden]
        body.add(NavigationBar(cake_name_list=cakes_on_nav, menu_dict=menu_dict, restricted=self.restricted))
        
        self.container = body.add("div", {"id": "container", "class": "w3-container"})
        self.floating_container = body.add("div", {"id": "floating_container"}, style={"position":"absolute", "top":"0px", "left":"0px", "z-index":"100"})
        self.msg_box = body.add("div", {"id": "msg_box", "class": "pancake-toast"})
        return root_html
    
    def update_needed(self, state=True):
        try:
            self.update_needed_queue.put_nowait(state)
        except queue.Full:
            pass
        # Notify WebSocket clients if available
        if hasattr(self, "server"):
            try:
                self.server.notify_update()
            except Exception:
                pass
    
    def show_message(self, *args, **kwargs):
        msg = ""
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    msg += f"{k}: {v}<br>"
            else:
                msg += f"{arg}"
                msg += " "
        self.send_command("show_message", {"msg": str(msg)})
    
    def send_command(self, command, parameters:dict=None):
        self.commands.append({"command": command, "parameters": parameters if parameters is not None else {}})
    
    def organize_commands(self, remove_refresh=False):
        commands = []
        refresh_flag = False
        for command in self.commands:
            if command["command"] == "refresh":
                refresh_flag = True
            else:
                commands.append(command)
        if refresh_flag and not remove_refresh:
            commands.append({"command": "refresh"})
        self.commands = commands
    
    def go_to(self, cake_name, request=None):
        if request is None:
            request = {}
        self.send_command("go_to", {"cake": cake_name, "request": request})

    def refresh(self):
        self.send_command("refresh")

    def reload(self):
        self.send_command("reload")
    
    def observe_main_recipe(self):
        if False:
            self._observer = Observer()
            self._observer.schedule(PancakeChangeHandler(self.main_file_path, self._restart), path=os.path.dirname(self.main_file_path), recursive=False)
            self._observer.start()
    
    def _restart(self):
        for _ in range(5):
            try:
                os.execl(sys.executable, self.main_file_path, os.path.basename(self.main_file_path))
            except PermissionError:
                time.sleep(0.2)
                pass
        
    def done(self):
        self.gv.save()
        for cake in self.cakes.values():
            cake.goodbye()
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()

    def retained_file(self, file_path, none_if_not_exist=True):
        file_path = os.path.join(self.storage_dir, *file_path.split("/"))
        if none_if_not_exist and not os.path.exists(file_path):
            return
        return file_path

    def file_list(self, file_path):
        file_path = os.path.join(self.storage_dir, *file_path.split("/"))
        if file_path is None:
            return
        
        file_list = [os.path.basename(x) for x in glob.glob(file_path)]
        file_list = sorted(file_list, reverse=True)
        return file_list
    
    def write_to(self, file_path, content):
        if not self.is_storage_enabled:
            return
        file_path = self.retained_file(file_path, none_if_not_exist=False)
        file_path = skip_exception(os.makedirs, os.path.dirname(file_path), exist_ok=True, return_value=file_path)
        if file_path is None:
            return
        with open(file_path, "w") as f:
            f.write(content)

    def read_from(self, file_path):
        if not self.is_storage_enabled:
            return
        file_path = self.retained_file(file_path)
        if file_path is None:
            return
        with open(file_path, "r") as f:
            content = skip_exception(f.read)
        return content

    def prepare_hidden_contents(self):
        if "_Kitchen" not in self.cakes:
            Kitchen(self, name="_Kitchen", hidden=True)
        
    def set_logger(self, logger):
        self.logger = logging.getLogger("pancakekit") if logger is None else logger
        self.logger.setLevel(logging.INFO)
        stream_handler = logging.StreamHandler()
        handler_format = logging.Formatter("Pancake %(levelname)s: %(message)s")
        stream_handler.setFormatter(handler_format)
        self.logger.addHandler(stream_handler)
    
    @property
    def is_storage_enabled(self):
        return self.storage_dir is not None


class Cake():
    def __init__(self, plate, name, hidden=False):
        assert "/" not in name, "'/' cannot be used in a cake name."
        self.plate = plate
        self.name = name
        self.hidden = hidden
        
        self.is_storage_enabled = self.plate.is_storage_enabled
        if self.is_storage_enabled:
            self.is_storage_enabled = skip_exception(os.makedirs, join_path_or_none(self.plate.storage_dir, self.name), exist_ok=True, return_value=True, error_return_value=False)
        
        self.request = None #  request with latest load event
        
        self.clear_all()

        self.variables = Variables()
        if self.is_storage_enabled:
            self.load_toppings()

    def clear_all(self):
        self._collection = ToppingCollection()
        self.name_manager = self._collection.name_manager
        self.topping_order = self._collection.topping_order
        self.toppings = self._collection.toppings
        self.storaged_toppings = {}
        self.render_callback_func = None
        self._topping_events = {}
        self._topping_revisions = {}
        self.cake_events = {}
        self.mutable_tags = {}
        self.values_to_be_updated = {}
        self.styles_to_be_updated = {}
        self.attrs_to_be_updated = {}
        self.htmls_to_be_updated = {}
        self.functions_to_call = {}
        
        # for topping in self.toppings.values():
        #     topping.goodbye()
        self.plate.refresh()


    def refresh(self):
        self.plate.refresh()


    def render(self, request=None):
        content = ""
        floating_content = ""
        self.request = request if request is not None else {}
        if self.render_callback_func is not None:
            func_params = inspect.signature(self.render_callback_func).parameters.keys()
            if len(func_params) == 0:
                self.render_callback_func()
            else:   
                self.render_callback_func(self.request)
        
        for name in self.topping_order:
            topping = self.toppings[name]
            is_floating = getattr(topping, "floating", False)
            if is_floating:
                floating_content += topping.render()
            else:
                content += topping.render()
        return {"content": content, "floating_content": floating_content, "function_call": list(self.functions_to_call.values()), "revisions": self.revisions(cake_revision_only=True), 'cake_name': self.name}

    def revised_rendering(self, request):
        response = {}
        for topping_id in request:
            if topping_id in self._topping_revisions:
                response[topping_id] = {"revision":self._topping_revisions[topping_id]["revision"], "content":self._topping_revisions[topping_id]["topping"].html(), "function_call": list(self.functions_to_call.values())}
        return response
    
    def register_topping(self, topping, name=None, skip_rendering=False):
        name = self._collection.register(topping, name=name)
        if skip_rendering:
            self.topping_order.remove(name)
        return name
    
    def add(self, topping, name=None, storaged=False):
        assert topping is not None
        topping = input_topping_converter(topping, self.plate.logger)
        if topping is None:
            return
        name = self.register_topping(topping, name=name)
        topping.set_cake(self, uid=f"{self.name}.{name}", name=name)
        self.plate.refresh()
        return topping

    def remove(self, topping_name):
        topping = self._collection.unregister(topping_name)
        if topping is not None:
            topping.goodbye()
        self.plate.refresh()
    
    def swap(self, topping0, topping1):
        if topping0 not in self.topping_order or topping1 not in self.topping_order:
            return
        index0 = self.topping_order.index(topping0)
        index1 = self.topping_order.index(topping1)
        self.topping_order[index1] = topping0
        self.topping_order[index0] = topping1
        self.plate.refresh()

    def revisions(self, cake_revision_only=False):
        revisions = {k: v["revision"] for k, v in self._topping_revisions.items()}
        if not cake_revision_only:
            revisions["_root_"] = self.plate.uid
            revisions["_value_"] = self.values_to_be_updated
            revisions["_style_"] = self.styles_to_be_updated
            revisions["_attr_"] = self.attrs_to_be_updated
            revisions["_inner_html_"] = self.htmls_to_be_updated
            self.values_to_be_updated = {}
            self.styles_to_be_updated = {}
            self.attrs_to_be_updated = {}
            self.htmls_to_be_updated = {}
        return revisions
    
    def register_events(self, topping, event_types):
        if topping.uid not in self._topping_events:
            self._topping_events[topping.uid] = {"topping": topping, "events": set()}
        self._topping_events[topping.uid]["events"].update(set(event_types))
        self.plate.refresh()
    
    def register_revision(self, topping, revision):
        if topping.uid not in self._topping_revisions:
            self._topping_revisions[topping.uid] = {"topping": topping, "revision": revision}
        self._topping_revisions[topping.uid]["revision"] = revision
        self.plate.update_needed()
    
    def register_mutable_tag(self, tag):
        self.mutable_tags[tag.element_id] = tag.topping
    
    def register_function_call(self, topping_id, name, argv):
        self.functions_to_call[topping_id] = (name, argv)
    
    def value_changed(self, topping):
        for element_id, tag in topping._tags.items():
            if not tag.is_mutable:
                continue
            if tag.is_value_in_html:
                self.htmls_to_be_updated[element_id] = tag.value
            else:
                self.values_to_be_updated[element_id] = tag.value
        self.plate.update_needed()
    
    def state_changed(self, topping):
        self.styles_to_be_updated[topping.uid] = topping.style
        for element_id, tag in topping._tags.items():
            self.styles_to_be_updated[element_id] = tag.style
            self.attrs_to_be_updated[element_id] = tag.attr
        self.plate.update_needed()
        
    def reflect_change_value(self, request, cake):
        for element_id, value in request.items():
            if element_id not in self.mutable_tags:
                continue
            self.mutable_tags[element_id].set_value_from_web(element_id, value, cake)
    
    def process_event(self, event:Event):
        if event.sender_id == self.name:
            return self.process_card_event(event)
        if event.sender_id in self._topping_events and event.event_type in self._topping_events[event.sender_id]["events"]:
            return self._topping_events[event.sender_id]["topping"].process_event(event)
        
    def goodbye(self):
        self.variables.save()
        for topping in self.toppings.values():
            topping.goodbye()
    
    def run_script(self, script):
        if self.plate.restricted:
            return
        if script is None or len(script) == 0:
            return
        scope = self.variables._as_dict()
        current_pancake = self.plate[self.name]
        gscope = {"g": self.plate.gv, "cake": current_pancake if current_pancake is not None else self}
        scope.update(gscope)
        try:
            exec(script, scope)
            del scope["g"]
            del scope["cake"]
        except:
            self.plate.logger.exception(traceback.format_exc())
            return traceback.format_exc()
        return None

    def write_to(self, file_path, content):
        file_path = self.name+"/"+file_path
        self.plate.write_to(file_path, content)

    def read_from(self, file_path):
        file_path = self.name+"/"+file_path
        return self.plate.read_from(file_path)

    def file_list(self, file_path):
        file_path = self.name+"/"+file_path
        return self.plate.file_list(file_path)
    
    def load_toppings(self):
        topping_list = self.read_from("toppings/topping_list.txt")
        if topping_list is None:
            return
        topping_list = topping_list.split(",")
        for topping_name in topping_list:
            script = self.read_from(f"toppings/{topping_name}.py")
            if script is not None:
                self.run_script(script)
    
    def register_cake_event(self, event_type, func, key="_default_"):
        if event_type not in self.cake_events:
            self.cake_events[event_type] = {}
        self.cake_events[event_type][key] = func
        
    def process_card_event(self, event):
        if event.event_type in self.cake_events:
            for func in self.cake_events[event.event_type].values():
                func(event)
        
    def __getitem__(self, name):
        if name in self.toppings:
            return self.toppings[name]
        raise KeyError(f"{name} does not exist in cake {self.name}.")

    def __setitem__(self, name, value):
        if name not in self.toppings:
            raise KeyError(f"{name} does not exist in cake {self.name}.")
        topping = self.toppings[name]
        topping.value = value
        return topping

    def show_message(self, *args, **kwargs):
        self.plate.show_message(*args, **kwargs)

        
class Pancake():
    def __init__(self, plate=None, name=None, auto_serve_in_interactive_mode: bool = True, **kwargs):
        name = type(self).__name__ if name is None else name
        if plate is None:
            plate = Plate(storage=False)
        self.plate = plate
        self.auto_serve_in_interactive_mode = auto_serve_in_interactive_mode
        self._cake = plate.new_cake(name, **kwargs)
        if self._cake is None:
            return
        name = self._cake.name

        self.honeycomb = self.add(Honeycomb(hidden=True), name="honeycomb")
        plate[name] = self
        
        try:
            func_params = inspect.signature(self.decorate).parameters.keys()
            param_dict = {}
            for k, v in kwargs.items():
                if k in func_params:
                    param_dict[k] = v
            self.decorate(**param_dict)
                
            self._cake.render_callback_func = self.show_up
            
            if "card_script" in plate.arguments:
                script = plate.arguments["card_script"]
                if isinstance(script, list):
                    script = "\n".join(script)
                self._cake.run_script(script)
                    
            script = self._cake.read_from("scripts/_prepare.py")
            self._cake.run_script(script)

        except Exception as e:
            self.plate.logger.exception(traceback.format_exc())

        if self.auto_serve_in_interactive_mode and is_mode_interactive() and not getattr(self.plate, "running", False):
            # Automatically start the server in interactive environments unless explicitly disabled.
            self.serve(wait_done=False, interactive=True)
    
    def add(self, topping, name=None, storaged=False, **kwargs):
        if self._cake is None:
            return
        return self._cake.add(topping, name=name, storaged=storaged, **kwargs)
    
    def remove(self, topping_name):
        if self._cake is None:
            return
        return self._cake.remove(topping_name=topping_name)
    
    def swap(self, topping0, topping1):
        if self._cake is None:
            return
        return self._cake.swap(topping0, topping1)

    def clear_all(self):
        if self._cake is None:
            return
        self._cake.clear_all()
    
    def serve(self, wait_done: bool=True, port: int=8000, interactive=False):
        if self.plate is not None:
            self.plate.serve(wait_done=wait_done, port=port, interactive=interactive)
    
    def __getitem__(self, name):
        if self._cake is None:
            raise KeyError(f"{name} does not exist because the cake is not initialized.")
        return self._cake[name]

    def __setitem__(self, name, value):
        if self._cake is None:
            raise KeyError(f"{name} does not exist because the cake is not initialized.")
        return self._cake.__setitem__(name, value)

    def topping(self, func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        from .toppings.automatic import FromFunction
        self.add(FromFunction(func), name=func.__name__)
        return wrapper

    @property
    def toppings(self):
        toppings = self._cake.toppings.copy()
        try:
            toppings.pop("honeycomb")
        except:
            pass
        return toppings

    def __call__(self, *args, **kwargs):
        self.show_message(*args, **kwargs)

    def show_message(self, msg):
        self.plate.show_message(msg)

    def decorate(self, **kwargs):
        pass

    def show_up(self, request=None):
        pass

class Tag():
    NON_CLOSING = ("link", "img", "meta")   
    VALUE_IN_HTML = ("div", "label", "p", "b", "i", "button", "wa-button")
    INITIAL_VALUE_IN_HTML = ("textarea")
    
    def __init__(self, tag_name, properties=None, style=None, parent=None, element_id=None, name=None, value_ref=None):
        self.tag = tag_name
        self.properties = properties if properties is not None else {}
        self.topping = value_ref
        self.name = name
        self._parent = parent
        self.inner_items = []
        self.element_id = uuid.uuid4().hex if element_id is None else element_id
        self._changes = {"style": False, "attrs": False}
        self._style = {} if style is None else style.copy()
        if self.is_mutable:
            self.properties["id"] = self.element_id
            self.properties["onchange"] = f"value_changed('{self.element_id}');"
            self.topping.register_tag(self)
        
    def add(self, item, properties=None, style=None):
        if isinstance(item, Tag):
            item.parent = self
            self.inner_items.append(item)
        elif isinstance(item, Topping):
            self.inner_items.append(item)
        elif isinstance(item, str):
            item = Tag(item, properties=properties if properties is not None else {}, style=style if style is not None else {}, parent=self)
            self.inner_items.append(item)
        return item
    
    def add_html(self, item):
        self.inner_items.append(str(item))
    
    def render(self):
        if self.is_mutable:
            is_value_in_html = self.is_value_in_html or self.tag in self.INITIAL_VALUE_IN_HTML
            myvalue = self.value
            if myvalue is None:
                myvalue = ""
        if self.is_mutable and not is_value_in_html:
            self.properties["value"] = myvalue
        
        self._changes["style"] = True
        self.properties["style"] = style_dict_to_style_str(self.style)

        
        html = f"<{self.tag}"
        for key, value in self.properties.items():
            if value is None:
                html += f" {key}"
            else:
                if key == "style" and len(value) == 0:
                    continue
                escaped_value = html_module.escape(str(value), quote=True)
                html += f" {key}=\"{escaped_value}\""
        html += ">"
        
        if self.is_mutable and is_value_in_html:
            html += str(myvalue)
        for item in self.inner_items:
            if isinstance(item, Tag):
                html += item.render()
            elif isinstance(item, Topping):
                html += item.render()
            elif isinstance(item, str):
                html += item
        if self.tag not in self.NON_CLOSING:
            html += f"</{self.tag}>"
        return html
    
    def render_from_root(self):
        if self.parent is not None:
            return self.parent.render_from_root()
        return self.render()
    
    def __repr__(self):
        return f"<{self.tag}>"
    
    @property
    def parent(self):
        return self._parent
        
    @parent.setter
    def parent(self, p):
        self._parent = p

    @property
    def value(self):
        if not self.is_mutable:
            return None
        if hasattr(self.topping, "html_value"):
            value = getattr(self.topping, "html_value")(self.name)
        else:
            value = self.topping.value
        return value
        
    @value.setter
    def value(self, value):
        if not self.is_mutable:
            return 
        self.topping.value = value
    
    @property
    def is_mutable(self):
        return self.topping is not None
    
    @property 
    def is_value_in_html(self):
        return self.tag in self.VALUE_IN_HTML
    
    @property
    def style(self):
        if not self._changes["style"]:
            return {}
        self._changes["style"] = False
        style_dict = self._style.copy()
        return style_dict

    @style.setter
    def style(self, style_dict):
        self._changes["style"] = True
        self._style = style_dict.copy()

    @property
    def attr(self):
        if not self._changes["attrs"]:
            return {}
        self._changes["attrs"] = False
        attr_dict = {"disabled": "-"}
        return attr_dict
    
    def set_click_response(self, response_dict:dict=None, *, pressable: bool = False, initial_event: str = "onclick"):
        response_str = f",{response_dict}" if response_dict is not None else ""
        topping = self.topping if self.topping is not None else get_caller(target_class=Topping)
        if topping is None:
            return
        if pressable:
            initial_event = "onclick" if initial_event is None else str(initial_event)
            # Delegate click + long-press repeat behavior to the frontend to
            #  - fire "onclick" immediately on pointerdown
            #  - fire "pressed" repeatedly after a delay while the pointer is held
            #  - preserve keyboard-triggered clicks via the click event
            self.properties["onclick"] = f"pk_onclick(this, '{topping.uid}', '{initial_event}'{response_str});return false;"
            self.properties["onpointerdown"] = f"pk_pressable_down(event, this, '{topping.uid}', '{initial_event}'{response_str});"
            self.properties["onpointerup"] = f"pk_pressable_up(event, this, '{topping.uid}');"
            self.properties["onpointercancel"] = f"pk_pressable_up(event, this, '{topping.uid}');"
            self.properties["onpointerleave"] = f"pk_pressable_up(event, this, '{topping.uid}');"
            return
        self.properties["onclick"] = f"defocus();setTimeout(send_event.bind(this, '{topping.uid}', 'onclick'{response_str}), 50)"


class Topping():
    def __init__(self, *args, attributes=None, style=None, **kwargs):
        self.uid = None
        self.name = None
        self.attributes = {} if attributes is None else attributes
        self._events = {}
        self._parent = None
        self.cake = None
        self.revision = 0
        self._collection = ToppingCollection()
        self.topping_order = self._collection.topping_order
        self.toppings = self._collection.toppings
        self.function_to_call = None
        self._value = None
        self._args = args
        self.arguments = kwargs.copy()
        self._hidden = True if "hidden" in self.arguments and self.arguments["hidden"] else False
        self._changes = {"style": False}
        self._style = {} if style is None else style.copy()
        self.name_manager = self._collection.name_manager
        self.user_data = {} # Only for temporaly user storage.
        self._tags = {}
    
    def register_event(self, event_type, func):
        self._events[event_type] = func
        if self.cake is not None:
            self.cake.register_events(self, [event_type])

    def _callback_pancake(self, event: "Event"):
        in_cake = getattr(event, "in_cake", None)
        if in_cake is None:
            return None
        plate = getattr(in_cake, "plate", None)
        cake_name = getattr(in_cake, "name", None)
        if plate is not None and cake_name is not None:
            pancake = plate[cake_name]
            if pancake is not None:
                return pancake
        return in_cake

    def _inject_reserved_globals(self, func, reserved: dict[str, object]):
        target = func
        while isinstance(target, functools.partial):
            target = target.func
        if inspect.ismethod(target):
            target = target.__func__
        globals_dict = getattr(target, "__globals__", None)
        if not isinstance(globals_dict, dict):
            return None
        sentinel = object()
        previous = {}
        for key, value in reserved.items():
            previous[key] = globals_dict.get(key, sentinel)
            globals_dict[key] = value
        return globals_dict, previous, sentinel

    def _restore_reserved_globals(self, injected):
        if injected is None:
            return
        globals_dict, previous, sentinel = injected
        for key, prev_value in previous.items():
            if prev_value is sentinel:
                globals_dict.pop(key, None)
            else:
                globals_dict[key] = prev_value
    
    def process_event(self, event):
        response = None
        event.topping = self
        try:
            value_from_event = self.event_preprocessor(event)
            
            if event.event_type in self._events:
                func = self._events[event.event_type]
                cake_context = self._callback_pancake(event)
                injected = self._inject_reserved_globals(func, {"cake": cake_context})
                args_candidate = [value_from_event, event, cake_context]
                func_args = inspect.signature(func).parameters
                arg_count = len(func_args.keys())
                try:
                    response = func(*args_candidate[:arg_count])
                finally:
                    self._restore_reserved_globals(injected)

            elif self._parent is not None:
                event.origin = self if event.origin is None else event.origin
                response = self._parent.process_event(event)
            
        except Exception as e:
            if self.cake is not None:
                self.cake.plate.logger.exception(traceback.format_exc())
        return response
    
    def register_tag(self, tag):
        self._tags[tag.element_id] = tag
        if tag.is_mutable:
            self.register_event("onchange", self.set_value_from_web)
    
    def register_function_call(self, name, argv):
        self.function_to_call = (name, argv)
        if self.cake is not None:
            self.cake.register_function_call(self.uid, self.function_to_call[0], self.function_to_call[1])
    
    def set_cake(self, cake, uid, name):
        if cake is None:
            return
        self.cake = cake
        self.uid = uid
        self.name = name
        for cname, topping in self.toppings.items():
            topping.set_cake(self.cake, uid=f"{self.uid}.{cname}", name=cname)
            self.cake.register_topping(topping, name=cname, skip_rendering=True)
    
        keys = inspect.signature(self.prepare).parameters.keys()
        kwargs = {k: v for k, v in self.arguments.items() if k in keys}
        self.prepare(*self._args, **kwargs)

        cake.register_events(self, self._events.keys())
        cake.register_revision(self, self.revision)
        if self.function_to_call is not None:
            cake.register_function_call(self.uid, self.function_to_call[0], self.function_to_call[1])
        for tag in self._tags.values():
            if tag.is_mutable:
                cake.register_mutable_tag(tag)
        
    
    def render(self):
        attributes = self.attributes.copy()
        attributes["id"] = self.uid
        self._changes["style"] = True

        classes = ["topping"]
        if "class" in attributes and attributes["class"]:
            classes.append(attributes["class"])
        if hasattr(self, "ROOT_DIV_CLASS"):
            root_class = getattr(self, "ROOT_DIV_CLASS")
            if root_class:
                classes.append(root_class)
        attributes["class"] = " ".join(classes)
        div = Tag("div", attributes, style=self.style)
        div.add_html(self.html())
        return div.render()
    
    def updated(self):
        if self.cake is None:
            return
        self.revision += 1
        self.cake.register_revision(self, self.revision)
    
    def html(self):
        return "<p>[topping]</p>"
    
    def add(self, topping, name:str=None): # At this point self.cake can be None.
        topping = input_topping_converter(topping)
        name = self._collection.register(topping, name=name)
        topping.set_cake(self.cake, uid=f"{self.uid}.{name}", name=name)
        if self.cake is not None:
            self.cake.register_topping(topping, name=name, skip_rendering=True)

        topping.parent = self
        return topping

    def remove(self, topping_name):
        topping = self._collection.unregister(topping_name)
        if topping is not None:
            topping.goodbye()
        self.updated()
        
    def set_value_from_web(self, element_id, value, cake):
        tag = self._tags[element_id]
        try:
            prev_value = self._value
            value = self.web_value_proprocessor(tag, value)
            if value is None: 
                if prev_value != self._value:
                    event = Event(self.uid, "value_changed", self.value, cake)
                    event.topping = self
                    self.process_event(event)
                return           
        except Exception:
            if self.cake is not None:
                self.cake.plate.logger.exception(traceback.format_exc())
            self.cake.value_changed(self)
            return
        self.set_value(value, skip_update=True)
        event = Event(self.uid, "value_changed", self.value, cake)
        event.topping = self
        self.process_event(event)

    def set_value(self, value, skip_update=False, force_update=False):
        try:
            value = self.value_preprocessor(value)
        except Exception:
            if self.cake is not None:
                self.cake.plate.logger.exception(traceback.format_exc())
            return
        if self._value == value and not force_update:
            return
        self._value = value
        if (not skip_update or force_update) and self.cake is not None:
            self.cake.value_changed(self)
    
    def goodbye(self):
        pass
        
    @property
    def value(self):
        return self.value_getter()
    
    @value.setter
    def value(self, v):
        self.set_value(v)
        
        
    @property
    def child_htmls(self):
        htmls = []
        for name in self.topping_order:
            htmls.append(self.toppings[name].render())
        return htmls
        
    @property
    def children_html(self):
        return "".join(self.child_htmls)
        
    @property
    def hidden(self):
        return self._hidden
    
    @hidden.setter
    def hidden(self, s):
        if self._hidden != s:
            self.style_changed = True
        self._hidden = s

    @property
    def parent(self):
        return self._parent
        
    @parent.setter
    def parent(self, p):
        self._parent = p
        
    @property
    def clicked(self):
        return "onclick" in self._events
        
    @clicked.setter
    def clicked(self, func):
        self.register_event("onclick", func)

    @property
    def pressed(self):
        return "pressed" in self._events

    @pressed.setter
    def pressed(self, func):
        self.register_event("pressed", func)

    @property
    def value_changed(self):
        return "value_changed" in self._events
        
    @value_changed.setter
    def value_changed(self, func):
        self.register_event("value_changed", func)
    
    @property
    def style(self):
        if not self._changes["style"]:
            return {}
        self._changes["style"] = False
        style_dict = self._style.copy()
        style_dict.update({"display" : "none" if self.hidden else "initial"})
        return style_dict

    @style.setter
    def style(self, style_dict):
        self._changes["style"] = True
        self._style = style_dict.copy()
        self.cake.state_changed(self)
    
    @property
    def generation_script(self):
        script = self.__class__.__name__
        args = ""
        for arg in self._args:
            if isinstance(arg, str):
                args += f"'{arg}'"
            else:
                args += str(arg)
            args += ","
        args += f"attributes={self.attributes}"
        args += f",style={self.style}"
        for k, v in self.arguments.items():
            args += f",{k}={v}"
        script += "("+args+")"
        return script    
    
    def prepare(self, request: dict):
        return

    def event_preprocessor(self, event: Event): # Method to be overrode for a custom topping
        return event.value

    def value_preprocessor(self, value): # Method to be overrode for a custom topping
        return value
    
    def web_value_proprocessor(self, tag: Tag, value): 
        return value # Return None if the change cannot be accepted or value has been be set inside web_value_preprocessor.
    
    def value_getter(self): # Method to be overrode for a custom topping
        return self._value

class Arrangement(Topping):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def value_getter(self):
        return pk_wrapped_dict(lambda: self.cake.plate.logger.error("Cannot set values."), self.toppings)


class GroupContainer(Arrangement):
    ROOT_DIV_CLASS = ""

    def __init__(self, toppings=None, *, title: str = None, padding: bool | None = None, styles: dict | None = None, draggable: bool = False, classes: dict | str | None = None, **kwargs):
        toppings = [] if toppings is None else toppings
        self.group_title = title
        self._draggable = bool(draggable)
        self.display = {"styles": {}, "classes": {"group": [], "body": []}}
        kwargs = kwargs.copy()
        if padding is not None or styles is not None or classes is not None:
            kwargs["display"] = {"padding": padding, "styles": styles, "classes": classes}
        super().__init__(toppings, **kwargs)
        self.update_display(padding=padding, styles=styles, classes=classes)

    def prepare(self, toppings, display=None):
        if isinstance(display, dict):
            self.update_display(**display)
        for topping in toppings:
            self.add(topping)
        self._sync_draggable_registration()

    def _sync_draggable_registration(self):
        if self.cake is None:
            return
        if self._draggable:
            self.register_function_call("make_draggable", {"element_id": self.uid})
        else:
            self.cake.functions_to_call.pop(self.uid, None)

    def update_display(self, *, padding: bool | None = None, styles: dict | None = None, classes: dict | str | None = None):
        previous_styles = self.display.get("styles") if isinstance(self.display, dict) else None
        previous_classes = self.display.get("classes") if isinstance(self.display, dict) else None
        self.styles = self._resolve_styles(padding, styles, previous_styles)
        self.classes = self._normalize_classes(classes, base=previous_classes)
        self.display = {"styles": self.styles, "classes": self.classes}
        if self.cake is not None:
            self.cake.refresh()

    def __getitem__(self, name):
        if name in self.toppings:
            return self.toppings[name]
        raise KeyError(f"{name} does not exist in group {self.name}.")

    def __setitem__(self, name, value):
        if name not in self.toppings:
            raise KeyError(f"{name} does not exist in group {self.name}.")
        topping = self.toppings[name]
        topping.value = value
        return topping

    def html(self):
        classes = ["pancake-group", *self.classes.get("group", [])]
        group_style = self.styles.get("group", {}) if isinstance(self.styles, dict) else {}
        body_style = self.styles.get("body", {}) if isinstance(self.styles, dict) else {}
        fieldset = Tag("fieldset", style=group_style, properties={"class": " ".join(classes)})
        legend_text = self.group_title if self.group_title is not None else self.name
        if legend_text:
            legend_style = {"padding": "0 6px", "font-weight": "bold", "font-size": "0.95em"}
            legend_props = {}
            if self._draggable:
                legend_props["id"] = self.uid + "_handle"
                legend_style["cursor"] = "move"
            legend = fieldset.add("legend", legend_props, legend_style)
            legend.add_html(legend_text)

        body_classes = self.classes.get("body", [])
        body_props = {"class": " ".join(body_classes)} if body_classes else {}
        body = fieldset.add("div", properties=body_props, style=body_style)
        body.add_html(self.children_html)
        return fieldset.render()

    def add(self, topping, name: str = None):
        topping = input_topping_converter(topping, self.cake.plate.logger if self.cake is not None else None)
        if topping is None:
            return
        if not self._accepts_child(topping):
            if self.cake is not None:
                self.cake.plate.logger.warning("Cannot add this topping inside the current container due to nesting rules.")
            return
        return super().add(topping, name=name)

    def _accepts_child(self, topping) -> bool:
        if self._contains_card(topping):
            return False
        return True

    def _contains_card(self, topping) -> bool:
        if isinstance(topping, Card):
            return True
        if not isinstance(topping, Topping):
            return False
        for child in getattr(topping, "toppings", {}).values():
            if self._contains_card(child):
                return True
        return False

    def _resolve_styles(self, padding: bool | None, overrides: dict | None, previous_styles: dict | None = None):
        styles = {
            "group": {
                "border": "1px solid #ccc",
                "border-radius": "8px",
                "padding": "0.75em 0.75em 0.25em 0.75em",
                "margin": "0.25em 0",
            },
            "body": {"display": "flex", "flex-direction": "column", "gap": "0.5em"},
        }

        if padding is False:
            styles["group"]["padding"] = "0.25em"
        elif padding is True:
            styles["group"]["padding"] = "0.75em 0.75em 0.25em 0.75em"
        elif isinstance(previous_styles, dict):
            previous_group = previous_styles.get("group", {})
            styles["group"]["padding"] = previous_group.get("padding", styles["group"].get("padding"))

        if overrides:
            group_overrides = overrides.get("group") if isinstance(overrides, dict) else None
            body_overrides = overrides.get("body") if isinstance(overrides, dict) else None
            if isinstance(group_overrides, dict):
                styles["group"].update(group_overrides)
            if isinstance(body_overrides, dict):
                styles["body"].update(body_overrides)
        return styles

    def _normalize_classes(self, classes: dict | str | None, base: dict | None = None) -> dict:
        base = {"group": [], "body": []} if base is None else {key: list(value) for key, value in base.items() if key in ("group", "body")}
        if classes is None:
            return base
        if isinstance(classes, str):
            base["group"].append(classes)
            return base
        if isinstance(classes, dict):
            for key in base.keys():
                value = classes.get(key)
                if value is None:
                    continue
                if isinstance(value, str):
                    base[key].append(value)
                elif isinstance(value, (list, tuple)):
                    base[key].extend([v for v in value if isinstance(v, str)])
        return base


class Card(GroupContainer):
    ROOT_DIV_CLASS = "draggable"
    floating = True
    USE_WA_CARD = True

    def __init__(self, *args, **kwargs):
        kwargs.pop("floating", None)
        kwargs.pop("draggable", None)
        card_classes = kwargs.pop("classes", None)
        merged_classes = self._normalize_classes(card_classes)
        super().__init__(*args, draggable=True, classes=merged_classes, **kwargs)
        self._draggable = True
        if self.USE_WA_CARD:
            existing_classes = self.attributes.get("class", "")
            if "pk-wa-card" not in existing_classes.split():
                self.attributes["class"] = (existing_classes + " pk-wa-card").strip()
        self._sync_draggable_registration()

    def _resolve_styles(self, padding: bool | None, overrides: dict | None, previous_styles: dict | None = None):
        styles = super()._resolve_styles(padding, overrides, previous_styles)
        styles["group"].update({
            # Defer appearance (border/shadow/padding) to Web Awesome's <wa-card>.
            "width": "fit-content",
            "max-width": "calc(100vw - 2rem)",
        })
        styles["body"].update({
            # Keep body layout neutral; <wa-card> provides padding by default.
        })
        styles["title_bar"] = {
            "display": "flex",
            "align-items": "center",
            "width": "100%",
            "box-sizing": "border-box",
            "padding": "0 6px",
            "height": "16px",
            "min-height": "16px",
            "line-height": "16px",
            "font-size": "12px",
            "user-select": "none",
            "cursor": "move" if self._draggable else "default",
        }
        styles["title"] = {
            "flex": "1 1 auto",
            "min-width": "0",
            "overflow": "hidden",
            "text-overflow": "ellipsis",
            "white-space": "nowrap",
        }
        return styles

    def html(self):
        classes = ["pancake-card", *self.classes.get("group", [])]
        group_style = self.styles.get("group", {}) if isinstance(self.styles, dict) else {}
        body_style = self.styles.get("body", {}) if isinstance(self.styles, dict) else {}
        title_bar_style = self.styles.get("title_bar", {}) if isinstance(self.styles, dict) else {}
        title_style = self.styles.get("title", {}) if isinstance(self.styles, dict) else {}

        wa_card = Tag("wa-card", properties={"class": " ".join(classes)}, style=group_style)

        title_text = self.group_title if self.group_title is not None else self.name
        if title_text:
            wa_card.properties["with-header"] = None
            header_props = {"slot": "header", "class": "pk-card-handle"}
            if self._draggable:
                header_props["id"] = self.uid + "_handle"
            header = wa_card.add("div", properties=header_props, style=title_bar_style)
            header.add("span", style=title_style).add_html(title_text)

        body_classes = self.classes.get("body", [])
        body_props = {"class": "pk-card-body-inner"}
        if body_classes:
            body_props["class"] += " " + " ".join(body_classes)
        padded_body_style = {"padding": "4px"}
        if body_style:
            padded_body_style.update(body_style)
        body = wa_card.add("div", properties=body_props, style=padded_body_style)
        body.add_html(self.children_html)
        return wa_card.render()


class FloatingCard(Card):
    def __init__(self, *args, **kwargs):
        kwargs.pop("floating", None)
        super().__init__(*args, **kwargs)


class Honeycomb(Card):
    USE_WA_CARD = False

    def __init__(self, *args, **kwargs):
        kwargs.pop("floating", None)
        super().__init__(*args, **kwargs)

    def prepare(self, *args, **kwargs):
        super().prepare(*args, **kwargs)
        existing_classes = self.attributes.get("class", "")
        if "pk-honeycomb" not in existing_classes.split():
            self.attributes["class"] = (existing_classes + " pk-honeycomb").strip()
        self.register_event("run_script", self.run)
        element_id = "script_"+self.uid
        # Use Web Awesome's default textarea appearance.
        self.textarea = Tag("wa-textarea", element_id=element_id, value_ref=self)
        # Let the Honeycomb container handle resizing; keep the editor stretched to the available space.
        self.textarea.properties.update({"rows": 10, "resize": "none"})
        self.textarea.style = {"width": "100%", "height": "100%"}
        self.textarea.properties.update({"spellcheck":"false", "autocapitalize": "off", "autocomplete": "off", "autocorrect": "off"})
        script = self.cake.read_from("scripts/honeycomb.py")
        script = "" if script is None else script 
        self.prev_script = script
        self.initial_script = script
        self.value = script
        self.honeypod_index = -1
        self.register_event("recall_honeypod", self.recall_honeypod)

    def value_getter(self):
        return self._value
        
    def html(self):
        handle = Tag("div", {"id": self.uid + "_handle", "class": "draggable-handle pancake-title"})
        handle.add("div", {"class": "pancake-left-flatter"})
        handle.add("div", {"class": "pancake-right-flatter"})
        close_box = handle.add("div", {"class": "pancake-closebox"})
        close_box.properties["onclick"] = f"switch_card('{self.uid}', 'close')";
        content = Tag("div", {"class": "pk-honeycomb__body"})
        content.add(self.textarea)
#         front_most_div = content.add("div", {"class": "pancake-div-floating-fill"})
#         front_most_div.add(self.save_button)

        return handle.render() + content.render()
    
    def run(self):
        reply = self.cake.run_script(self.value)
        if reply is None and self.value != self.prev_script:
            self.save_script()
            self.prev_script = self.value
    
    def save_script(self, name = None):
        script = self.value
        if script is None:
            return
        if not self.cake.is_storage_enabled:
            return
        if name is None:
            name = datetime.now().strftime("honeypod-%y-%m-%d-%H-%M-%S")
        self.cake.write_to(f"scripts/{name}.py", script)
        self.honeypod_index = -1
    
    
    def recall_honeypod(self, increment):
        if not self.cake.is_storage_enabled:
            return
        self.honeypod_index += increment
        honeypod = self.get_honeypod(self.honeypod_index)
        if honeypod is None:
            return
        self.honeypod_index = honeypod["index"]
        self.value = honeypod["script"] # Textarea generate shadow user-agent after user input
        self.prev_script = self.value
        
    def get_honeypod(self, index):
        honeypod_list = self.cake.file_list("scripts/honeypod-*.py")
        if len(honeypod_list) == 0:
            return
        if index >= len(honeypod_list):
            index = len(honeypod_list)-1
        if index < 0:
            index = 0
        script = self.cake.read_from("scripts/"+honeypod_list[index])
        if script is None:
            return ""
        return {"index": index, "script": script}

    def event_preprocessor(self, event):
        if event.event_type == "run_script" and isinstance(event.value, dict):
            script = event.value.get("script")
            if script is not None:
                self.value = script
        if event.event_type == "recall_honeypod":
            return int(event.value["increment"])

    def goodbye(self):
        script = self.value
        if script != self.initial_script:
            self.save_script("honeycomb")
    

        
        
class Variables():
    RESERVED = ("_VARIABLES", "_SAVE_NEEDED", "_LAST_SAVE", "_FILE_PATH")
    def __init__(self, file_path=None):
        if file_path is not None:
            if not file_path.endswith(".pickle"):
                file_path += ".pickle"
            self._FILE_PATH = skip_exception(os.makedirs, os.path.dirname(file_path), exist_ok=True, return_value=file_path)
        else:
            self._FILE_PATH = None
        self._VARIABLES = {}
        self.load(warning_if_not_exist=False)
        self._TIME_INTERVAL = 20
        self._SAVE_NEEDED = False
        self._start_save_regular_timer()

    def load(self, file_path=None, warning_if_not_exist=True):
        file_path = self._FILE_PATH if file_path is None else file_path
        if file_path is None:
            return
        if not os.path.exists(file_path):
            if warning_if_not_exist:
                if self.cake is not None:
                    self.cake.plate.logger.error(f"Error: Pickled variable file {file_path} not found.")
            return
        try:
            with open(file_path, "rb") as f:
                self._VARIABLES.update(pickle.load(f))
        except Exception:
            if self.cake is not None:
                self.cake.plate.logger.exception(traceback.format_exc())
        # self._SAVE_NEEDED = False
        

    def save(self, file_path=None):
        if not self._SAVE_NEEDED:
            return
        file_path = self._FILE_PATH if file_path is None else file_path
        if file_path is None:
            return
        try:
            with open(file_path, "wb") as f:
                pickle.dump(self._VARIABLES, f)
            # self._SAVE_NEEDED = False
        except Exception:
            if self.cake is not None:
                self.cake.plate.logger.exception(traceback.format_exc())

    def _need_save(self):
        self._SAVE_NEEDED = True
        
    
    def _start_save_regular_timer(self):
        pass
        # skip_exception(self.save)
        # t = threading.Timer(self._TIME_INTERVAL, self._start_save_regular_timer)
        # t.daemon = True
        # t.start()

    def _as_dict(self):
        return self._VARIABLES
        
    def __getattr__(self, name):
        return self._VARIABLES[name] if name in self._VARIABLES else None
    
    def __setattr__(self, name, value):
        if name in self.RESERVED:
            super().__setattr__(name, value)
            return
        self._SAVE_NEEDED = True
        self._VARIABLES[name] = value
    
class Kitchen(Pancake):
    def decorate(self):
        from .toppings.basic import Button, Input
        from .toppings.table import Table
        self.cakes = self.add(Table())
        self.cake_name = self.add(Input("Cake name"))
        btn = self.add(Button("New cake"))
        btn.clicked = self.new_cake
    
    def show_up(self, request):
        cakes = list(self.plate.pancakes.keys())
        cakes.remove("_Kitchen")
        self.cakes.set({"cake": cakes})
    
    def new_cake(self):
        Pancake(self.plate, name=self.cake_name.value)
        self.plate.reload()

def input_topping_converter(topping, logger=None):
    if not isinstance(topping, Topping):
        from .toppings.automatic import topping_from_object
        topping = topping_from_object(topping)
        if topping is None:
            if logger is not None:
                logger.error("Incompatible object.")
            return None
        return topping
    return topping
