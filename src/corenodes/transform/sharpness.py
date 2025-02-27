from dearpygui import dearpygui as dpg
from PIL import Image, ImageEnhance

from src.utils import find_available_pos, theme
from src.utils.nodes import NodeParent


class SharpnessModule(NodeParent):
    name = "Sharpness"
    tooltip = "Adjust sharpness"

    def __init__(self, update_output: callable):
        super().__init__(update_output)

    def new(self, history=True):
        with dpg.node(
            parent="MainNodeEditor",
            tag="sharpness_" + str(self.counter),
            label="Sharpness",
            pos=find_available_pos(),
            user_data=self,
        ):
            dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Input)
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_slider_int(
                    tag="sharpness_percentage_" + str(self.counter),
                    width=150,
                    max_value=100,
                    min_value=1,
                    default_value=1,
                    clamped=True,
                    format="%0.0f%%",
                    callback=self.update_output,
                )

        tag = "sharpness_" + str(self.counter)
        dpg.bind_item_theme(tag, theme.blue)
        self.settings[tag] = {"sharpness_percentage_" + str(self.counter): 1}
        if history:
            self.update_history(tag)
        self.counter += 1

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        tag = tag.split("_")[-1]
        percent = self.settings["sharpness_" + tag]["sharpness_percentage_" + tag]
        return ImageEnhance.Sharpness(image).enhance(percent / 25)
