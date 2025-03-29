import bpy
import json
import os
import sys
from math import pi
from mathutils import Euler
from typing import Type

# ---------------------------
# Literals
# ---------------------------
settings_file = "settings.json"

# ---------------------------
# Data
# ---------------------------
class Settings:
    input_path: str = "./src"
    input_file: str = ""
    export_path: str = "./dst"
    output_file_suffix: str = "_baked"
    bake_image_width: int = 1024
    bake_image_height: int = 1024
    light_type: str = "POINT"
    light_energy: float = 1000
    debug: bool = False

    @classmethod
    def load_from_json(cls: Type["Settings"], filepath: str) -> "Settings":
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Settings file '{filepath}' not found!")
        with open(filepath, "r") as f:
            data = json.load(f)
        settings = cls()
        settings.input_path = data.get("input_path", settings.input_path)
        settings.input_file = data.get("input_file", settings.input_file)
        settings.export_path = data.get("export_path", settings.export_path)
        settings.output_file_suffix = data.get("output_file_suffix", settings.output_file_suffix)
        settings.bake_image_width = data.get("bake_image_width", settings.bake_image_width)
        settings.bake_image_height = data.get("bake_image_height", settings.bake_image_height)
        settings.light_type = data.get("light_type", settings.light_type).upper()
        settings.light_energy = data.get("light_energy", settings.light_energy)
        settings.debug = data.get("debug", settings.debug)
        return settings

# ---------------------------
# Main
# ---------------------------
def cleanup():
    # Remove all elements
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    bpy.context.scene.cursor.location = (0, 0, 0)

def read_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
        if len(argv) == 1:
            settings_file = argv[0]
            return settings_file
    return None

def init_from_settings(file_path):
    try:
        settings = Settings.load_from_json(file_path)
        print("Using settings:", settings.__dict__)
        return settings
    except Exception as e:
        print("Error loading settings:", e)
        return None

def import_mesh(settings: Settings):
    file_name = settings.input_path;
    if file_name.endswith("/"):
        file_name = file_name[:-1]
    file_name = os.path.join(file_name, settings.input_file)

    input_filepath = os.path.abspath(file_name)
    print("Importing:", input_filepath)

    before_import = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=input_filepath)
    imported_objects = set(bpy.data.objects) - before_import

    mesh_objects = [obj for obj in imported_objects if obj.type == 'MESH']

    if mesh_objects:
        print(f"Successfully imported {len(mesh_objects)} mesh object(s)")
        #TODO: implementation for one mesh object
        return mesh_objects[0]
    else:
        print("Failed to find imported mesh objects")
        return None

def export_mesh(mesh: bpy.types.Object, settings: Settings):
    output_filename = settings.input_file.replace(".glb", settings.output_file_suffix + ".glb")
    os.makedirs(settings.export_path, exist_ok=True)
    export_filepath = os.path.join(settings.export_path, output_filename)

    # Exports entire scene
    # bpy.ops.export_scene.gltf(filepath=export_filepath, export_format='GLB')

    # Exports only the selected mesh
    # Deselect everything
    bpy.ops.object.select_all(action='DESELECT')

    if not mesh or mesh.type != 'MESH':
        print("Error: Provided object is not a valid mesh.")
        return

    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.export_scene.gltf(filepath=export_filepath, export_format='GLB', use_selection=True)

    print(f"Exported mesh to {export_filepath}")

def setup_light(settings: Settings):
    # refer to https://docs.blender.org/api/current/bpy_types_enum_items/light_type_items.html
    light_data = bpy.data.lights.new(name="Light", type=settings.light_type)
    light_data.energy = settings.light_energy
    light_object = bpy.data.objects.new(name="Light", object_data=light_data)
    bpy.context.collection.objects.link(light_object)
    light_object.location = (5, 5, 5)

# ---------------------------
# Main
# ---------------------------
def debug():
    # Create camera
    bpy.ops.object.add(type='CAMERA', location=(-5, -5.0, 5))
    camera = bpy.context.object
    camera.data.lens = 35
    camera.rotation_euler = Euler((pi*55/180, 0, -pi*45/180), 'XYZ')

    # Make this the current camera
    bpy.context.scene.camera = camera
    # Render image
    scene = bpy.context.scene
    scene.render.resolution_x = 256
    scene.render.resolution_y = 256
    scene.render.resolution_percentage = 100
    scene.render.engine = 'CYCLES'
    scene.render.filepath = 'debug/out.png'
    bpy.ops.render.render(write_still=True)

if __name__ == '__main__':
    cleanup()
    argv = read_args()
    settings = init_from_settings(settings_file)
    if settings:
        mesh = import_mesh(settings)
        setup_light(settings)
        export_mesh(mesh, settings)

    if settings.debug:
        debug();
