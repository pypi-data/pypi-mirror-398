from ..pancakekit import Tag

class NavigationBar(Tag):
    def __init__(self, cake_name_list, menu_dict, restricted):
        super().__init__("div", {"id": "navigator", "class": "w3-bar w3-border w3-black w3-margin-bottom"})
        if not restricted:
            self.add(PancakeMenu(menu_dict))
        for cake_name in cake_name_list:
            nav_tab = self.add("a", {"onclick": f"go_to_cake('{cake_name}')", "class": "w3-bar-item w3-button w3-hover-none w3-text-grey w3-hover-text-white"})
            nav_tab.add_html(cake_name)
        if not restricted:
            right_group = self.add("div", {"class": "pk-nav-right"})
            script = right_group.add("a", {"class": "w3-bar-item w3-button w3-hover-none w3-text-grey w3-hover-text-white", "id": "script_indicator"})
            script.properties["onclick"] = "switch_card('script_card');"
            script.add_html("&starf;")
            waiting = right_group.add("b", {"class": "w3-bar-item w3-button w3-hover-none pc-animation-scale pc-animation-y", "id": "wait_indicator"}, style={"display":"none"})
            waiting.add_html("&#128293;")

class PancakeMenu(Tag):
    def __init__(self, menu_dict:dict):
        super().__init__("div", {"class": "w3-dropdown-hover pk-dropdown", "id": "pancake_menu"})
        button = self.add("button", {"class": "w3-button w3-black"})
        button.properties.update({"aria-haspopup": "menu", "aria-expanded": "false", "onclick": "toggle_dropdown('pancake_menu', event);"})
        button.add_html("&#129374;")
        tool_content = self.add("div", {"class": "w3-dropdown-content w3-bar-block w3-border w3-round-large", "role": "menu"})
        for title, func_str in menu_dict.items():
            tool_menu = tool_content.add("a", {"onclick": func_str, "class": "w3-bar-item w3-button w3-round-large", "role": "menuitem"})
            tool_menu.add_html(title)
