import bpy
import random
import math

# Clear existing objects in the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a collection to store all curly hyphae
curly_hyphae_collection = bpy.data.collections.new("CurlyHyphaeGroup")
bpy.context.scene.collection.children.link(curly_hyphae_collection)

# Function to create a material with a specific color
def create_material(name, color, is_emission=False):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Remove default nodes
    for node in nodes:
        nodes.remove(node)
    
    # Create necessary shader nodes
    material_output = nodes.new(type='ShaderNodeOutputMaterial')
    principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    
    # Set base color
    principled_bsdf.inputs['Base Color'].default_value = (*color, 1)  # RGBA (R, G, B, Alpha)
    
    if is_emission:
        # Use emission for glowing green effect
        emission = nodes.new(type='ShaderNodeEmission')
        emission.inputs['Color'].default_value = (*color, 1)
        links.new(emission.outputs['Emission'], material_output.inputs['Surface'])
    else:
        # Link the Principled BSDF to the material output
        links.new(principled_bsdf.outputs['BSDF'], material_output.inputs['Surface'])
    
    return mat

# Create white-ish material for nodes and strings (hyphae)
white_material = create_material("WhiteMaterial", (1, 1, 1))  # White color
green_material = create_material("GreenMaterial", (0, 1, 0), is_emission=True)  # Green flowing effect

# Function to assign a material to an object
def assign_material(obj, material):
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)

# Function to create a node (fungal junction)
def create_node(location, scale=(0.1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=scale, location=location)
    node = bpy.context.object
    node.name = "Node"
    assign_material(node, white_material)
    # Add node to collection
    curly_hyphae_collection.objects.link(node)
    return node

# Function to create a curly hypha (Bézier curve) between nodes
def create_curly_hypha(start_loc, end_loc, control_strength=6, thickness=0.01):
    # Create a curve data block
    curve_data = bpy.data.curves.new(name="CurlyHypha", type='CURVE')
    curve_data.dimensions = '3D'
    
    # Create a Bézier spline
    spline = curve_data.splines.new(type='BEZIER')
    spline.bezier_points.add(1)  # Start and end points
    
    # Define start, control, and end points for curvature
    start_point = spline.bezier_points[0]
    end_point = spline.bezier_points[1]
    
    # Assign start and end positions
    start_point.co = start_loc
    end_point.co = end_loc

    # Define control points to create the curl
    mid_x = (start_loc[0] + end_loc[0])/2
    mid_y = (start_loc[1] + end_loc[1])/2
    mid_z = (start_loc[2] + end_loc[2])/2
    
    # Offset control points to make the curve
    start_point.handle_right_type = 'FREE'
    end_point.handle_left_type = 'FREE'
    
    start_point.handle_right = (mid_x + random.uniform(-control_strength, control_strength),
                                mid_y + random.uniform(-control_strength, control_strength),
                                mid_z + random.uniform(-control_strength, control_strength))
    
    end_point.handle_left = (mid_x + random.uniform(-control_strength, control_strength),
                             mid_y + random.uniform(-control_strength, control_strength),
                             mid_z + random.uniform(-control_strength, control_strength))

    # Create a node with the curve data and link it to the scene
    curve_obj = bpy.data.objects.new("CurlyHypha", curve_data)
    bpy.context.collection.objects.link(curve_obj)
    
    # Add curve to collection
    curly_hyphae_collection.objects.link(curve_obj)

    # Add some thickness to the curve to make it visible
    curve_obj.data.bevel_depth = 0.01
    curve_obj.data.bevel_resolution = 0  # Simplified resolution

    # Assign white material for the hyphae
    assign_material(curve_obj, white_material)

    # Duplicate the curve for the green flowing signal
    curve_obj.select_set(True)
    bpy.ops.object.duplicate()
    green_curve_obj = bpy.context.object
    green_curve_obj.scale = (0.8, 0.8, 0.8)  # Slightly smaller to fit inside
    
    # Assign the green glowing material
    assign_material(green_curve_obj, green_material)
    
    # Add the duplicated green curve to the collection
    curly_hyphae_collection.objects.link(green_curve_obj)

    # Animate the green signal (flowing effect)
    animate_green_flow(green_curve_obj)

    return curve_obj

# Function to animate the green flowing effect inside the strings
def animate_green_flow(curve_obj):
    # Create texture coordinate and mapping nodes to animate the flow
    mat = curve_obj.data.materials[0]
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    gradient = nodes.new('ShaderNodeGradientTexture')

    # Add nodes for the green flowing effect
    gradient.location = (0, 0)
    mapping.location = (-300, 0)
    tex_coord.location = (-600, 0)
    
    # Link the nodes
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], gradient.inputs['Vector'])
    links.new(gradient.outputs['Color'], nodes['Emission'].inputs['Color'])

    # Animate the green flow (moving texture coordinates)
    mapping.inputs['Location'].default_value[0] = 0  # Start animation
    mapping.keyframe_insert(data_path="inputs[1].default_value", frame=1)

    mapping.inputs['Location'].default_value[0] = -10  # End of animation (flowing effect)
    mapping.keyframe_insert(data_path="inputs[1].default_value", frame=250)

# Recursive function to generate a branching network of curly hyphae with nodes
def generate_network(start_loc, depth=3, branching_factor=2, spread=2, control_strength=2):
    if depth == 0:
        return
    
    # Create a node at the start location
    create_node(start_loc, scale=0.1)

    # Generate branches from the start location
    branch_locations = []
    for _ in range(branching_factor):
        # Random direction and distance for each branch
        angle_h = random.uniform(0, 2 * math.pi)
        angle_v = random.uniform(-math.pi / 5, math.pi / 5)
        distance = random.uniform(1.5, spread)
        
        # Calculate end location for the hypha
        x_offset = distance * math.cos(angle_h) * math.cos(angle_v)
        y_offset = distance * math.sin(angle_h) * math.cos(angle_v)
        z_offset = distance * math.sin(angle_v)
        end_loc = (start_loc[0] + x_offset, start_loc[1] + y_offset, start_loc[2] + z_offset)
        
        # Create a curly connection (hypha) between the start location and the end location
        create_curly_hypha(start_loc, end_loc, control_strength=control_strength, thickness=0.01)
        
        # Store the end location to use as a new node
        branch_locations.append(end_loc)

    # Recursively generate more branches and nodes
    for branch_loc in branch_locations:
        generate_network(branch_loc, depth=depth-1, branching_factor=branching_factor, spread=spread, control_strength=control_strength)

# Start generating the mycorrhizal network with curly hyphae
root_location = (0, 0, 0)
generate_network(root_location, depth=3, branching_factor=2, spread=2, control_strength=2)

bpy.context.view_layer.update()
