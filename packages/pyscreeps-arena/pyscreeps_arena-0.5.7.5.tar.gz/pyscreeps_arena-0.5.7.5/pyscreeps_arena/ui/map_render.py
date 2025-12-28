import json
import os
import math
import importlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps


class MapRender:
    def __init__(self, map_path, cell_size=32):
        self._map_path = map_path
        self._cell_size = cell_size
        self._map_data = None
        
        # Updated terrain colors
        self._terrain_colors = {
            'X': (139, 126, 102),  # terrain-wall #8B7E66
            '2': (144, 238, 144),    # plain #90EE90
            'A': (205, 190, 112),    # swamp #CDBE70
        }
        
        # Object rendering configurations with custom scale ratios
        self._object_styles = {
            'StructureSpawn': {
                'shape': 'circle',
                'fill': (255, 255, 0),  # yellow
                'outline': (200, 200, 0),
                'size': 1.1  # 1.1x scale as requested
            },
            'StructureWall': {
                'shape': 'rounded_square',
                'fill': (128, 128, 128),  # gray
                'outline': (100, 100, 100),
                'size': 0.8,
                'radius': 0.2
            },
            'StructureContainer': {
                'shape': 'square',
                'fill': (254, 238, 0),  # #FEEE00
                'outline': (255, 255, 255),  # white border
                'outline_width': 2,
                'size': 0.8
            },
            'StructureTower': {
                'shape': 'tower',  # circle + triangle
                'circle_fill': (100, 100, 100),
                'triangle_fill': (200, 200, 200),
                'size': 1.1  # 1.1x scale as requested
            },
            'StructureRampart': {
                'shape': 'ring',
                'fill': None,
                'outline': (150, 150, 150),
                'outline_width': 3,
                'size': 0.85
            },
            'StructureExtension': {
                'shape': 'circle',
                'fill': (200, 200, 200),
                'outline': (150, 150, 150),
                'size': 0.6
            },
            'StructureRoad': {
                'shape': 'line',
                'fill': (100, 100, 100),
                'width': 3,
                'size': 0.8
            },
            'Flag': {
                'shape': 'flag',  # pole + flag shape
                'pole_color': (139, 69, 19),  # brown
                'flag_color': (255, 0, 0),    # red
                'size': 0.9
            },
            'Source': {
                'shape': 'circle',
                'fill': (255, 215, 0),  # gold
                'outline': (200, 170, 0),
                'size': 0.7
            },
            'Creep': {
                'shape': 'circle',
                'fill': (0, 255, 255),  # cyan
                'outline': (0, 200, 200),
                'size': 0.6
            },
            'Resource': {
                'shape': 'diamond',
                'fill': (255, 165, 0),  # orange
                'outline': (200, 130, 0),
                'size': 0.5
            },
            'ConstructionSite': {
                'shape': 'square',
                'fill': (255, 165, 0),  # orange
                'outline': (200, 130, 0),
                'size': 0.7
            },
            'Portal': {
                'shape': 'ring',
                'fill': None,
                'outline': (128, 0, 128),  # purple
                'outline_width': 4,
                'size': 0.8
            }
        }
        
        # Resource management: Load local images
        self._resources = {}
        self._load_resources()
        
    def _load_resources(self):
        """Load local resources from resources directory."""
        # Define resources directory path
        resources_dir = Path(__file__).parent.parent / 'resources'
        
        if not resources_dir.exists():
            print(f"[DEBUG] Resources directory not found: {resources_dir}")
            return
        
        # Scan all Python files in resources directory
        for resource_file in resources_dir.glob('*.py'):
            if resource_file.name.startswith('_'):
                continue  # Skip __init__.py and other hidden files
            
            # Get resource name from filename (remove .py extension)
            resource_name = resource_file.stem
            
            try:
                # Import the module dynamically
                module_name = f"pyscreeps_arena.resources.{resource_name}"
                module = importlib.import_module(module_name)
                
                # Check if toImage method exists
                if hasattr(module, 'toImage'):
                    # Load the toImage method
                    self._resources[resource_name] = module.toImage
                    print(f"[DEBUG] Loaded resource: {resource_name}")
            except Exception as e:
                print(f"[DEBUG] Failed to load resource {resource_name}: {e}")
        
    def _load_map(self):
        """Load map data from JSON file."""
        try:
            with open(self._map_path, 'r', encoding='utf-8') as f:
                self._map_data = json.load(f)
            print(f"[DEBUG] Loaded map data with {len(self._map_data['map'])} rows")  # 调试输出：查看地图行数
        except FileNotFoundError:
            raise FileNotFoundError(f"Map file not found: {self._map_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in map file: {e}")
    
    def _get_map_dimensions(self):
        """Get map width and height."""
        if not self._map_data:
            return 0, 0
        
        height = len(self._map_data['map'])
        width = len(self._map_data['map'][0]) if height > 0 else 0
        print(f"[DEBUG] Map dimensions: {width}x{height}")  # 调试输出：查看地图尺寸
        return width, height
    
    def _draw_terrain(self, draw, img_width, img_height):
        """Draw terrain tiles with inner borders for continuous regions."""
        map_rows = self._map_data['map']
        height = len(map_rows)
        width = len(map_rows[0]) if height > 0 else 0
        
        # First draw all terrain tiles
        for y, row in enumerate(map_rows):
            for x, char in enumerate(row):
                if char in self._terrain_colors:
                    color = self._terrain_colors[char]
                    left = x * self._cell_size
                    top = y * self._cell_size
                    right = left + self._cell_size
                    bottom = top + self._cell_size
                    
                    draw.rectangle([left, top, right, bottom], fill=color)
        
        # Then draw inner borders for continuous terrain regions
        self._draw_terrain_inner_borders(draw, map_rows, width, height)
    
    def _draw_terrain_inner_borders(self, draw, map_rows, width, height):
        """Draw inner borders for continuous terrain regions."""
        # Mark visited cells to avoid redundant processing
        visited = [[False for _ in range(width)] for _ in range(height)]
        
        # Iterate through all cells
        for y in range(height):
            for x in range(width):
                if not visited[y][x]:
                    # Find continuous region
                    region = self._find_continuous_region(map_rows, x, y, visited)
                    if len(region) > 1:  # Only draw borders for regions larger than 1 cell
                        self._draw_region_inner_borders(draw, region, map_rows[y][x])
    
    def _find_continuous_region(self, map_rows, start_x, start_y, visited):
        """Find continuous terrain region starting from (start_x, start_y)."""
        terrain_type = map_rows[start_y][start_x]
        region = []
        queue = [(start_x, start_y)]
        visited[start_y][start_x] = True
        
        # Directions: up, down, left, right (no diagonals)
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        while queue:
            x, y = queue.pop(0)
            region.append((x, y))
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                # Check boundaries and if cell is same terrain type and not visited
                if 0 <= nx < len(map_rows[0]) and 0 <= ny < len(map_rows):
                    if not visited[ny][nx] and map_rows[ny][nx] == terrain_type:
                        visited[ny][nx] = True
                        queue.append((nx, ny))
        
        return region
    
    def _draw_region_inner_borders(self, draw, region, terrain_type):
        """Draw inner borders for a continuous region."""
        if terrain_type not in self._terrain_colors:
            return
        
        # Calculate border color (50% opacity, 70% self color + 30% black)
        base_color = self._terrain_colors[terrain_type]
        # Mix 70% self color with 30% black
        r = max(0, int(base_color[0] * 0.7))
        g = max(0, int(base_color[1] * 0.7))
        b = max(0, int(base_color[2] * 0.7))
        border_color = (r, g, b, 128)  # 128 = 50% opacity
        
        # Fixed border width of 1 as requested
        border_width = 1
        
        # Create a set for quick lookup
        region_set = set(region)
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        # Iterate through each cell in region and check adjacent cells
        for x, y in region:
            # Check all four directions
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                # If neighbor is not in region, draw border on that side
                if (nx, ny) not in region_set:
                    # Calculate border coordinates
                    left = x * self._cell_size
                    top = y * self._cell_size
                    right = left + self._cell_size
                    bottom = top + self._cell_size
                    
                    # Draw border based on direction
                    if dx == 0 and dy == -1:  # Top border
                        draw.rectangle([left, top, right, top + border_width], fill=border_color)
                    elif dx == 0 and dy == 1:  # Bottom border
                        draw.rectangle([left, bottom - border_width, right, bottom], fill=border_color)
                    elif dx == -1 and dy == 0:  # Left border
                        draw.rectangle([left, top, left + border_width, bottom], fill=border_color)
                    elif dx == 1 and dy == 0:  # Right border
                        draw.rectangle([right - border_width, top, right, bottom], fill=border_color)
    
    def _draw_shape(self, draw, x, y, style, overlay_color=None):
        """Draw a specific shape based on style configuration."""
        center_x = x * self._cell_size + self._cell_size // 2
        center_y = y * self._cell_size + self._cell_size // 2
        size = int(self._cell_size * style.get('size', 0.7))
        
        shape = style.get('shape', 'circle')
        
        if shape == 'circle':
            radius = size // 2
            fill_color = style.get('fill')
            outline_color = style.get('outline')
            
            # Draw main circle
            draw.ellipse([
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius
            ], fill=fill_color, outline=outline_color)
            
            # Add highlight and shadow for质感效果
            if fill_color:
                # Top-left highlight
                highlight_radius = radius // 2
                highlight_offset = radius // 3
                highlight_color = tuple(min(255, c + 60) for c in fill_color)
                draw.ellipse([
                    center_x - radius + highlight_offset, center_y - radius + highlight_offset,
                    center_x - radius + highlight_offset + highlight_radius,
                    center_y - radius + highlight_offset + highlight_radius
                ], fill=highlight_color)
                
                # Bottom-right shadow
                shadow_radius = radius // 2
                shadow_offset = radius // 3
                shadow_color = tuple(max(0, c - 40) for c in fill_color)
                draw.ellipse([
                    center_x + radius - shadow_offset - shadow_radius,
                    center_y + radius - shadow_offset - shadow_radius,
                    center_x + radius - shadow_offset,
                    center_y + radius - shadow_offset
                ], fill=shadow_color)
            
        elif shape == 'ring':
            radius = size // 2
            draw.ellipse([
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius
            ], outline=style.get('outline'), width=style.get('outline_width', 2))
            
        elif shape == 'square':
            half_size = size // 2
            left = center_x - half_size
            top = center_y - half_size
            right = center_x + half_size
            bottom = center_y + half_size
            
            fill_color = style.get('fill')
            outline_color = style.get('outline')
            outline_width = style.get('outline_width', 1)
            
            # Create gradient fill for质感效果
            if fill_color:
                # Create a small gradient image
                gradient_img = Image.new('RGBA', (size, size))
                gradient_draw = ImageDraw.Draw(gradient_img)
                
                # Linear gradient from top-left to bottom-right
                for i in range(size):
                    for j in range(size):
                        # Calculate gradient factor (0.0 to 1.0)
                        factor = (i + j) / (2 * size)
                        # Interpolate color between highlight and shadow
                        highlight = tuple(min(255, c + 40) for c in fill_color)
                        shadow = tuple(max(0, c - 30) for c in fill_color)
                        # Calculate interpolated color
                        r = int(highlight[0] * (1 - factor) + shadow[0] * factor)
                        g = int(highlight[1] * (1 - factor) + shadow[1] * factor)
                        b = int(highlight[2] * (1 - factor) + shadow[2] * factor)
                        gradient_draw.point((i, j), fill=(r, g, b, 255))
                
                # Paste gradient onto main image
                main_img = draw._image
                main_img.paste(gradient_img, (left, top), gradient_img)
                
                # Draw outline if needed
                if outline_color:
                    draw.rectangle([left, top, right, bottom], 
                                  outline=outline_color, width=outline_width)
            else:
                # Fallback to basic square if no fill color
                draw.rectangle([left, top, right, bottom], 
                              fill=fill_color, 
                              outline=outline_color,
                              width=outline_width)
            
        elif shape == 'rounded_square':
            half_size = size // 2
            left = center_x - half_size
            top = center_y - half_size
            right = center_x + half_size
            bottom = center_y + half_size
            radius = int(size * style.get('radius', 0.2))
            
            fill_color = style.get('fill')
            outline_color = style.get('outline')
            outline_width = style.get('outline_width', 1)
            
            # Create gradient fill for质感效果
            if fill_color:
                # Create a small gradient image
                gradient_img = Image.new('RGBA', (size, size))
                gradient_draw = ImageDraw.Draw(gradient_img)
                
                # Linear gradient from top-left to bottom-right
                for i in range(size):
                    for j in range(size):
                        # Calculate gradient factor (0.0 to 1.0)
                        factor = (i + j) / (2 * size)
                        # Interpolate color between highlight and shadow
                        highlight = tuple(min(255, c + 40) for c in fill_color)
                        shadow = tuple(max(0, c - 30) for c in fill_color)
                        # Calculate interpolated color
                        r = int(highlight[0] * (1 - factor) + shadow[0] * factor)
                        g = int(highlight[1] * (1 - factor) + shadow[1] * factor)
                        b = int(highlight[2] * (1 - factor) + shadow[2] * factor)
                        gradient_draw.point((i, j), fill=(r, g, b, 255))
                
                # Paste gradient onto main image
                main_img = draw._image
                main_img.paste(gradient_img, (left, top), gradient_img)
                
                # Draw rounded rectangle outline
                if outline_color:
                    draw.rounded_rectangle([left, top, right, bottom], radius,
                                          outline=outline_color,
                                          width=outline_width)
            else:
                # Fallback to basic rounded square if no fill color
                draw.rounded_rectangle([left, top, right, bottom], radius,
                                      fill=fill_color, 
                                      outline=outline_color,
                                      width=outline_width)
            
        elif shape == 'diamond':
            radius = size // 2
            points = [
                (center_x, center_y - radius),      # top
                (center_x + radius, center_y),      # right
                (center_x, center_y + radius),      # bottom
                (center_x - radius, center_y)       # left
            ]
            draw.polygon(points, fill=style.get('fill'), outline=style.get('outline'))
            
        elif shape == 'tower':
            # Circle background
            radius = size // 2
            circle_fill = style.get('circle_fill')
            triangle_fill = style.get('triangle_fill')
            
            # Draw main circle
            draw.ellipse([
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius
            ], fill=circle_fill)
            
            # Add metal reflection to circle
            if circle_fill:
                reflection_width = radius // 3
                reflection_color = tuple(min(255, c + 80) for c in circle_fill)
                draw.rectangle([
                    center_x - reflection_width,
                    center_y - radius,
                    center_x + reflection_width,
                    center_y + radius
                ], fill=reflection_color)
            
            # Triangle foreground with metal texture
            tri_size = size // 3
            triangle_points = [
                (center_x, center_y - tri_size),           # top
                (center_x - tri_size, center_y + tri_size), # bottom left
                (center_x + tri_size, center_y + tri_size)  # bottom right
            ]
            
            # Draw main triangle
            draw.polygon(triangle_points, fill=triangle_fill)
            
            # Add metal reflection to triangle
            if triangle_fill:
                # Vertical reflection line
                reflection_color = tuple(min(255, c + 60) for c in triangle_fill)
                draw.line([
                    center_x, center_y - tri_size,
                    center_x, center_y + tri_size
                ], fill=reflection_color, width=2)
                
                # Horizontal reflection line
                draw.line([
                    center_x - tri_size, center_y,
                    center_x + tri_size, center_y
                ], fill=reflection_color, width=2)
            
        elif shape == 'flag':
            # Pole
            pole_x = center_x - size // 4
            pole_top = center_y - size // 2
            pole_bottom = center_y + size // 2
            draw.line([pole_x, pole_top, pole_x, pole_bottom], 
                     fill=style.get('pole_color'), width=2)
            
            # Flag shape
            flag_left = pole_x
            flag_top = pole_top
            flag_right = center_x + size // 2
            flag_bottom = center_y - size // 4
            flag_middle = center_x
            
            flag_points = [
                (flag_left, flag_top),
                (flag_right, flag_top + (flag_bottom - flag_top) // 3),
                (flag_middle, center_y),
                (flag_right, flag_bottom - (flag_bottom - flag_top) // 3),
                (flag_left, flag_bottom)
            ]
            draw.polygon(flag_points, fill=style.get('flag_color'))
            
            # Add flag texture
            flag_color = style.get('flag_color')
            if flag_color:
                # Add diagonal stripes for texture
                stripe_color = tuple(max(0, c - 30) for c in flag_color)
                for i in range(5):
                    offset = i * 5
                    draw.line([
                        flag_left + offset, flag_top,
                        flag_right, flag_bottom - offset
                    ], fill=stripe_color, width=1)
            
        elif shape == 'line':
            # For roads, we'll draw a simple line, but in a real implementation
            # you might want to connect adjacent road pieces
            left = center_x - size // 2
            right = center_x + size // 2
            top = center_y - style.get('width', 3) // 2
            bottom = center_y + style.get('width', 3) // 2
            draw.rectangle([left, top, right, bottom], fill=style.get('fill'))
        
        # Apply overlay color if provided
        if overlay_color:
            # Calculate bounding box for overlay application
            half_size = size // 2
            bbox = [center_x - half_size, center_y - half_size, center_x + half_size, center_y + half_size]
            
            # Get main image reference
            main_img = draw._image
            
            # Extract the region containing the shape
            shape_region = main_img.crop(bbox)
            
            # Convert to RGBA if not already
            if shape_region.mode != 'RGBA':
                shape_region = shape_region.convert('RGBA')
            
            # Apply overlay using the provided blend method
            r, g, b, a = shape_region.split()
            rgb_img = Image.merge('RGB', (r, g, b))
            color_overlay = Image.new('RGB', shape_region.size, overlay_color)
            
            # Blend RGB parts (50% transparency)
            blended_rgb = Image.blend(rgb_img, color_overlay, alpha=0.5)
            
            # Recombine with original alpha channel
            new_r, new_g, new_b = blended_rgb.split()
            blended_region = Image.merge('RGBA', (new_r, new_g, new_b, a))
            
            # Paste blended region back to main image
            main_img.paste(blended_region, bbox, blended_region)
    
    def _draw_objects(self, draw):
        """Draw game objects."""
        objects = self._map_data.get('objects', {})
        
        for obj_type, obj_list in objects.items():
            if obj_type in self._object_styles and obj_list:
                style = self._object_styles[obj_type]
                
                for obj in obj_list:
                    x, y = obj['x'], obj['y']
                    
                    # Check for 'my' attribute and determine overlay color
                    overlay_color = None
                    if 'my' in obj:
                        if obj['my']:
                            overlay_color = '#76EE00'  # Green for friendly
                        else:
                            overlay_color = '#EE6363'  # Red for enemy
                    
                    # Try to use local resource image first
                    resource_name = obj_type
                    if resource_name in self._resources:
                        # Use local image
                        try:
                            self._draw_resource_image(draw, x, y, resource_name, style, overlay_color)
                            continue
                        except Exception as e:
                            print(f"[DEBUG] Failed to draw resource image for {obj_type}: {e}")
                    
                    # Fall back to质感绘图
                    self._draw_shape(draw, x, y, style, overlay_color)
    
    def _draw_resource_image(self, draw, x, y, resource_name, style, overlay_color=None):
        """Draw local resource image."""
        # Get the image from resource
        img = self._resources[resource_name]()
        
        # Calculate size based on style
        size = int(self._cell_size * style.get('size', 0.7))
        
        # Resize the image to fit the cell
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Apply overlay color if needed
        if overlay_color:
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Apply color overlay as per the provided blend method
            r, g, b, a = img.split()
            rgb_img = Image.merge('RGB', (r, g, b))
            color_overlay = Image.new('RGB', img.size, overlay_color)
            blended_rgb = Image.blend(rgb_img, color_overlay, alpha=0.5)
            new_r, new_g, new_b = blended_rgb.split()
            img = Image.merge('RGBA', (new_r, new_g, new_b, a))
        
        # Calculate position to center the image
        cell_x = x * self._cell_size
        cell_y = y * self._cell_size
        offset_x = (self._cell_size - size) // 2
        offset_y = (self._cell_size - size) // 2
        
        # Paste the image onto the main image
        # Note: draw is a ImageDraw object, but we need to access the underlying image
        # So we'll use the img attribute from the draw object
        main_img = draw._image
        main_img.paste(img, (cell_x + offset_x, cell_y + offset_y), img)
    
    def _draw_grid(self, draw, img_width, img_height):
        """Draw grid lines with transparency."""
        # Create a semi-transparent overlay for grid
        grid_img = Image.new('RGBA', (img_width, img_height), (255, 248, 220, 0))  # #FFF8DC with 0 alpha
        grid_draw = ImageDraw.Draw(grid_img)
        
        # Vertical lines
        for x in range(0, img_width + 1, self._cell_size):
            grid_draw.line([x, 0, x, img_height], fill=(255, 248, 220, 128), width=1)  # 50% transparent
        
        # Horizontal lines
        for y in range(0, img_height + 1, self._cell_size):
            grid_draw.line([0, y, img_width, y], fill=(255, 248, 220, 128), width=1)  # 50% transparent
        
        # Composite the grid onto the main image
        return grid_img
    
    def render(self, output_path=None, show_grid=True):
        """
        Render map to image file.
        
        :param output_path: Output image path (default: map_render.png in same directory as map)
        :param show_grid: Whether to show grid lines
        
        :raises: FileNotFoundError: If map file doesn't exist
        :raises: ValueError: If map data is invalid
        
        :usage:
            # 示例用法
            renderer = MapRender('map1.json')
            renderer.render('output.png')
        """
        self._load_map()
        
        # Get map dimensions
        width, height = self._get_map_dimensions()
        img_width = width * self._cell_size
        img_height = height * self._cell_size
        
        print(f"[DEBUG] Creating image {img_width}x{img_height}")  # 调试输出：查看图像尺寸
        
        # Create image with alpha channel for transparency support
        img = Image.new('RGBA', (img_width, img_height), color=(255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw terrain
        self._draw_terrain(draw, img_width, img_height)
        
        # Draw grid if requested (returns overlay image)
        if show_grid:
            grid_overlay = self._draw_grid(draw, img_width, img_height)
            img = Image.alpha_composite(img, grid_overlay)
            draw = ImageDraw.Draw(img)
        
        # Draw objects
        self._draw_objects(draw)
        
        # Save image
        if output_path is None:
            map_dir = os.path.dirname(self._map_path)
            output_path = os.path.join(map_dir, 'map_render.png')
        
        # Convert to RGB if saving as JPEG, keep RGBA for PNG
        if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
            img = img.convert('RGB')
        
        img.save(output_path)
        print(f"[DEBUG] Map rendered to {output_path}")  # 调试输出：查看输出路径
        
        return output_path


def main():
    """Main function for command line usage."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python map_render.py <map1.json> [output.png]")
        sys.exit(1)
    
    map_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        renderer = MapRender(map_path)
        result_path = renderer.render(output_path)
        print(f"Map rendered successfully to {result_path}")
    except Exception as e:
        print(f"Error rendering map: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
