import configparser
import os
import sys
import webbrowser

import dearpygui.dearpygui as dpg

from src.editor import node_editor
from src.utils import AlignmentType, auto_align, fd, history_manager, resource, toaster
from src.utils import ImageController as dpg_img
from src.utils.paths import general_path

config = configparser.ConfigParser()
config.read(general_path("pyproject.toml"))
try:
    VERSION = config["tool.poetry"]["version"][1:-1]
except KeyError:
    VERSION = "0.0.0"

dpg.create_context()
if node_editor.debug:
    dpg.configure_app(manual_callback_management=True)
dpg.create_viewport(title="Cresliant", small_icon=resource("icon.ico"), large_icon=resource("icon.ico"))

dpg_img.set_texture_registry(dpg.add_texture_registry())
with dpg.font_registry():
    dpg.add_font(resource("Roboto-Regular.ttf"), 17, tag="font")
    dpg.bind_font("font")


with dpg.texture_registry():
    dpg.add_static_texture(1, 1, [0] * 1 * 1 * 4, tag="output_0")


def export(info):
    try:
        filename = info[0]
        extension = info[1]
        location = info[2]
    except IndexError:
        toaster.show("Export Output", "Invalid location specified.")
        return

    if not extension or extension == ".*":
        extension = ".png"
    if not filename.endswith(extension):
        filename += extension

    location = os.path.join(location, filename)
    image = dpg.get_item_user_data("Output").pillow_image

    try:
        image.save(location)
    except ValueError:
        toaster.show("Export Output", "Invalid location specified.")
        return
    if sys.platform == "win32":
        webbrowser.open(location)
    else:
        image.show()


with dpg.window(
    tag="popup_window",
    no_move=True,
    no_close=True,
    no_resize=True,
    no_collapse=True,
    show=False,
    label="Add Node",
    max_size=[200, 250],
):
    for module in node_editor.modules[1:-1]:
        dpg.add_button(label=module.name, tag=module.name + "_popup", callback=module.new, indent=3, width=180)

with dpg.window(
    tag="node_popup_window", no_move=True, no_close=True, no_resize=True, no_collapse=True, show=False, label="Settings"
):
    dpg.add_button(label="Delete node", callback=node_editor.delete_nodes)
    dpg.add_button(label="Duplicate node", callback=node_editor.duplicate_nodes)

with dpg.window(
    tag="manual_modal",
    modal=True,
    no_move=True,
    no_resize=True,
    no_collapse=True,
    show=False,
    label="Instruction Manual",
    pos=[dpg.get_viewport_width() // 2 - 100, dpg.get_viewport_height() // 2 - 100],
):
    dpg.add_text("To delete a node/link, select it and press the delete key.", bullet=True)
    dpg.add_text("To add a node, right click anywhere on the canvas or select it from the Nodes menu.", bullet=True)
    dpg.add_text("To add a link, drag from an output to an input.", bullet=True)
    dpg.add_text("To set an exact value on a slider, Ctrl+Click it.", bullet=True)
    dpg.add_text("To duplicate nodes, select them and press Ctrl+V.", bullet=True)
    dpg.add_text("To export the output, press Ctrl+E.", bullet=True)


def handle_popup(_sender, app_data):
    if app_data == 0 and not dpg.is_item_hovered("manual_modal"):
        dpg.hide_item("manual_modal")
    if app_data == 1 and dpg.is_item_hovered("MainNodeEditor"):
        if len(dpg.get_selected_nodes("MainNodeEditor")) != 0:
            dpg.focus_item("node_popup_window")
            dpg.show_item("node_popup_window")
            dpg.set_item_pos("node_popup_window", dpg.get_mouse_pos(local=False))
            return

        dpg.show_item("popup_window")
        dpg.set_item_pos("popup_window", dpg.get_mouse_pos(local=False))
    else:
        dpg.hide_item("popup_window")
        dpg.hide_item("node_popup_window")


actions = {
    dpg.mvKey_V: node_editor.duplicate_nodes,
    dpg.mvKey_N: node_editor.reset,
    dpg.mvKey_E: lambda: [fd.change(export, True), fd.show_file_dialog()],
    dpg.mvKey_S: node_editor.save,
    dpg.mvKey_O: node_editor.open,
    dpg.mvKey_Q: dpg.stop_dearpygui,
    dpg.mvKey_H: lambda: dpg.show_item("manual_modal"),
    dpg.mvKey_G: lambda: webbrowser.open("https://github.com/Cresliant/Cresliant"),
    dpg.mvKey_B: lambda: webbrowser.open("https://github.com/Cresliant/Cresliant/issues/new/choose"),
    dpg.mvKey_Z: history_manager.undo,
    dpg.mvKey_Y: history_manager.redo,
}


def handle_shortcuts(_sender, app_data):
    if not dpg.is_key_down(dpg.mvKey_Control):
        return

    action = actions.get(app_data)
    if action:
        action()


with dpg.handler_registry():
    dpg.add_mouse_click_handler(button=1, callback=handle_popup)
    dpg.add_mouse_release_handler(button=0, callback=handle_popup)

    dpg.add_key_press_handler(key=dpg.mvKey_Delete, callback=node_editor.delete_nodes)
    dpg.add_key_press_handler(key=dpg.mvKey_Delete, callback=node_editor.delete_links)

    for key in actions:
        dpg.add_key_release_handler(key=key, callback=handle_shortcuts)

    if node_editor.debug:
        dpg.add_key_release_handler(key=dpg.mvKey_F10, callback=dpg.show_item_registry)
        dpg.add_key_release_handler(key=dpg.mvKey_F11, callback=dpg.show_style_editor)
        dpg.add_key_release_handler(key=dpg.mvKey_F12, callback=dpg.show_metrics)


with dpg.window(
    tag="Cresliant",
    menubar=True,
    no_title_bar=True,
    no_move=True,
    no_resize=True,
    no_collapse=True,
    no_close=True,
):
    with dpg.menu_bar():
        with dpg.menu(tag="file", label="File"):
            dpg.add_menu_item(tag="new", label="New Project", shortcut="Ctrl+N", callback=node_editor.reset)
            dpg.add_menu_item(tag="open", label="Open Project...", shortcut="Ctrl+O", callback=node_editor.open)
            dpg.add_separator()
            dpg.add_menu_item(tag="save", label="Save Project...", shortcut="Ctrl+S", callback=node_editor.save)
            dpg.add_menu_item(tag="export", label="Export Output...     ", shortcut="Ctrl+E", callback=export)
            dpg.add_separator()
            dpg.add_menu_item(tag="close", label="Quit", shortcut="Ctrl+Q", callback=dpg.stop_dearpygui)

        with dpg.menu(tag="edit", label="Edit"):
            dpg.add_menu_item(label="Undo    ", tag="undo", shortcut="Ctrl+Z", callback=history_manager.undo)
            dpg.add_menu_item(label="Redo    ", tag="redo", shortcut="Ctrl+Y", callback=history_manager.redo)

        with dpg.menu(tag="nodes", label="Nodes"):
            for module in node_editor.modules[1:]:
                dpg.add_menu_item(tag=module.name, label=module.name, callback=module.new)

        with dpg.menu(tag="help", label="Help"):
            dpg.add_menu_item(
                tag="manual",
                label="View the manual     ",
                shortcut="Ctrl+H",
                callback=lambda: dpg.show_item("manual_modal"),
            )
            dpg.add_menu_item(
                tag="github",
                label="Visit Github",
                shortcut="Ctrl+G",
                callback=lambda: webbrowser.open("https://github.com/Cresliant/Cresliant"),
            )
            dpg.add_menu_item(
                tag="report",
                label="Report a bug",
                shortcut="Ctrl+B",
                callback=lambda: webbrowser.open("https://github.com/Cresliant/Cresliant/issues/new/choose"),
            )
            dpg.add_separator()
            dpg.add_menu_item(
                tag="version",
                label="Cresliant v" + (f"{VERSION} DEBUG" if node_editor.debug else VERSION),
                enabled=False,
            )

    dpg.add_text("For help with using Cresliant, press Ctrl+H.", bullet=True)
    node_editor.start()
    fd.init()
    fd.start()
    auto_align("manual_modal", AlignmentType.Both)


dpg.setup_dearpygui()
dpg.show_viewport()
dpg.maximize_viewport()
dpg.set_primary_window("Cresliant", True)

if node_editor.debug:
    # This makes debuggers actually work by stopping at breakpoints
    while dpg.is_dearpygui_running():
        jobs = dpg.get_callback_queue()
        dpg.run_callbacks(jobs)
        dpg.render_dearpygui_frame()

dpg.start_dearpygui()
dpg.destroy_context()
