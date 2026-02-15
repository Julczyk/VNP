import arcade
import json
import os
import sys
from PIL import Image

# Constants matching visual.py
TILE_SIZE = 10
SCREEN_MARGIN = 20
LAND_COLOR = arcade.color.DARK_SPRING_GREEN

# Simplified colors map
RESOURCE_COLORS = {
    "RAW_ORE": arcade.color.BROWN,
    "COAL": arcade.color.DARK_BROWN,
    "IRON": arcade.color.GRAY,
    "GOLD": arcade.color.GOLD,
    "URANIUM": arcade.color.LIME_GREEN,
    "GOLD_INGOT": arcade.color.AMBER,
    "PROCESSED_METAL": arcade.color.SILVER,
    "ENERGY": arcade.color.YELLOW,
}

class ReplayView(arcade.Window):
    def __init__(self, log_path):
        self.log_data = self.load_log(log_path)
        
        self.width_tiles = self.log_data["width"]
        self.height_tiles = self.log_data["height"]
        
        # Calculate full map size
        self.map_width_px = self.width_tiles * TILE_SIZE + SCREEN_MARGIN * 2
        self.map_height_px = self.height_tiles * TILE_SIZE + SCREEN_MARGIN * 2
        
        # Window size
        window_width = min(1280, self.map_width_px)
        window_height = min(720, self.map_height_px)
        
        super().__init__(window_width, window_height, f"Replay: {os.path.basename(log_path)}", resizable=True)
        arcade.set_background_color(arcade.color.BLACK)
        
        # Cameras
        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()
        
        # Simulation State
        self.current_step_idx = 0
        self.total_steps = len(self.log_data["steps"])
        self.paused = False
        self.playback_speed = 1
        self.frame_counter = 0

        # Map Data - USING SPRITELIST FOR PERFORMANCE
        self.map_sprites = arcade.SpriteList(use_spatial_hash=False)
        self.prepare_map_sprites()
        
        # HUD
        self.hud_text = arcade.Text(
            text=f"Tick: 0 / {self.total_steps}",
            x=10,
            y=10,
            color=arcade.color.WHITE,
            font_size=14
        )
        
        self.center_camera()

    def load_log(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def prepare_map_sprites(self):
        print("Generating map sprites...")
        # Helper to get LB pixel coords
        def get_rect_center(x, y):
            draw_x = SCREEN_MARGIN + x * TILE_SIZE + TILE_SIZE / 2
            draw_y = SCREEN_MARGIN + y * TILE_SIZE + TILE_SIZE / 2
            return draw_x, draw_y

        res_map = {}
        for r in self.log_data.get("map_resources", []):
            res_map[(r[0], r[1])] = r[2]

        water_map = {}
        for w in self.log_data.get("water_tiles", []):
            water_map[(w[0], w[1])] = w[2]

        # Texture Cache
        texture_cache = {}

        def get_solid_texture(color):
            # Ensure color is tuple with alpha
            if len(color) == 3:
                color = color + (255,)
            
            key = color
            if key not in texture_cache:
                # Create image
                image = Image.new('RGBA', (TILE_SIZE, TILE_SIZE), color)
                texture = arcade.Texture(image)
                texture_cache[key] = texture
            return texture_cache[key]

        for y in range(self.height_tiles):
            for x in range(self.width_tiles):
                cx, cy = get_rect_center(x, y)
                
                if (x, y) in water_map:
                    depth = min(water_map[(x,y)], 1.0)
                    blue = int(120 + 100 * depth)
                    color = (0, 0, blue)
                else:
                    color = LAND_COLOR
                    if (x, y) in res_map:
                        res_name = res_map[(x,y)]
                        color = RESOURCE_COLORS.get(res_name, LAND_COLOR)
                
                texture = get_solid_texture(color)
                sprite = arcade.Sprite(texture)
                sprite.center_x = cx
                sprite.center_y = cy
                self.map_sprites.append(sprite)
        
        print(f"Map generated: {len(self.map_sprites)} sprites. Unique textures: {len(texture_cache)}")

    def center_camera(self):
        screen_center_x = self.map_width_px / 2
        screen_center_y = self.map_height_px / 2
        self.camera.position = (screen_center_x, screen_center_y)

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.camera.match_window()
        self.gui_camera.match_window()

    def on_draw(self):
        self.clear()
        
        # --- World View ---
        self.camera.use()
        
        # Draw Map (Batched!)
        self.map_sprites.draw()
        
        # Draw Dynamic Content
        if self.current_step_idx < self.total_steps:
            step = self.log_data["steps"][self.current_step_idx]
            
            # Wrecks
            for w in step.get("wrecks", []):
                tile_lb_x = SCREEN_MARGIN + w['x'] * TILE_SIZE
                tile_lb_y = SCREEN_MARGIN + w['y'] * TILE_SIZE
                wreck_lb_x = tile_lb_x + TILE_SIZE / 4
                wreck_lb_y = tile_lb_y + TILE_SIZE / 4
                arcade.draw_lbwh_rectangle_filled(wreck_lb_x, wreck_lb_y, TILE_SIZE/2, TILE_SIZE/2, arcade.color.BROWN)

            # Automata
            for a in step["automata"]:
                draw_x = SCREEN_MARGIN + a['x'] * TILE_SIZE + TILE_SIZE / 2
                draw_y = SCREEN_MARGIN + a['y'] * TILE_SIZE + TILE_SIZE / 2
                color = arcade.color.CYAN
                if a.get('gold', 0) > 0:
                    color = arcade.color.GOLD
                arcade.draw_circle_filled(draw_x, draw_y, TILE_SIZE/2, color)

        # --- GUI View ---
        self.gui_camera.use()
        self.hud_text.text = f"Tick: {self.current_step_idx} / {self.total_steps} | Speed: {self.playback_speed}x | Space: Pause, Arrows: Step/Speed, Scroll: Zoom"
        self.hud_text.draw()

    def on_update(self, delta_time):
        if not self.paused:
            # Advance multiple steps per frame if speed > 1
            steps_to_advance = self.playback_speed
            
            for _ in range(steps_to_advance):
                if self.current_step_idx < self.total_steps - 1:
                    self.current_step_idx += 1
                else:
                    self.paused = True
                    break

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.SPACE:
            self.paused = not self.paused
        elif symbol == arcade.key.RIGHT:
            if self.current_step_idx < self.total_steps - 1:
                self.current_step_idx += 1
        elif symbol == arcade.key.LEFT:
            if self.current_step_idx > 0:
                self.current_step_idx -= 1
        elif symbol == arcade.key.UP:
            self.playback_speed += 1
        elif symbol == arcade.key.DOWN:
            self.playback_speed = max(1, self.playback_speed - 1)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        zoom_factor = 1.1
        if scroll_y > 0:
            self.camera.zoom *= zoom_factor
        elif scroll_y < 0:
            self.camera.zoom /= zoom_factor

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons == arcade.MOUSE_BUTTON_LEFT or buttons == arcade.MOUSE_BUTTON_RIGHT:
            self.camera.position = (
                self.camera.position.x - dx / self.camera.zoom,
                self.camera.position.y - dy / self.camera.zoom
            )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python replay_viewer.py <log_file.json>")
        sys.exit(1)
        
    log_file = sys.argv[1]
    window = ReplayView(log_file)
    arcade.run()
