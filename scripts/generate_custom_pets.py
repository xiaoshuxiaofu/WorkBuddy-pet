"""
Generate custom pet sprite atlases for 坤坤 and 奶蛙.
"""
from PIL import Image, ImageDraw
import json, math, os

FRAME_WIDTH = 192
FRAME_HEIGHT = 208
COLUMNS = 8
ROWS = 9
STATE_NAMES = ['idle', 'running-right', 'running-left', 'waving', 'jumping', 'failed', 'waiting', 'running', 'review']

def draw_creature(draw, cx, cy, size, body_color, eye_color=(40,40,60), accent_color=None, 
                  eye_offset_x=0, eye_offset_y=0, mouth_type='smile', arm_left=0, arm_right=0, 
                  squash=1.0, stretch=1.0, creature_type='slime'):
    r, g, b = body_color
    if accent_color is None:
        accent_color = (min(r+40,255), min(g+40,255), min(b+40,255))
    
    # Shadow
    shadow_w = int(size * 0.8 * squash)
    shadow_h = int(size * 0.15)
    draw.ellipse([cx - shadow_w, cy + size * 0.7, cx + shadow_w, cy + size * 0.7 + shadow_h], fill=(0,0,0,40))
    
    body_w = int(size * squash)
    body_h = int(size * stretch)
    
    if creature_type == 'frog':
        # Wider flatter body
        draw.ellipse([cx - int(body_w*1.3), cy - int(body_h*0.7), cx + int(body_w*1.3), cy + int(body_h*0.7)], fill=(r,g,b,230))
        # Belly
        belly_color = (min(r+60,255), min(g+60,255), min(b+60,255), 200)
        draw.ellipse([cx - int(body_w*0.8), cy - int(body_h*0.2), cx + int(body_w*0.8), cy + int(body_h*0.5)], fill=belly_color)
        # Eye bumps on top
        eye_bump_r = int(size * 0.25)
        for side in [-1, 1]:
            bump_cx = cx + side * int(size*0.4)
            draw.ellipse([bump_cx - eye_bump_r, cy - int(size*0.6) - eye_bump_r, 
                          bump_cx + eye_bump_r, cy - int(size*0.6) + eye_bump_r], fill=(r,g,b,230))
    else:
        # Standard slime body
        draw.ellipse([cx - body_w, cy - body_h, cx + body_w, cy + body_h], fill=(r,g,b,230))
        hl_r = int(size * 0.6 * squash)
        hl_h = int(size * 0.6 * stretch)
        draw.ellipse([cx - hl_r, cy - hl_h, cx + hl_r, cy + hl_h], fill=(*accent_color, 100))
    
    # Shine
    shine_x = cx - int(size * 0.3 * squash)
    shine_y = cy - int(size * 0.3 * stretch)
    shine_r = int(size * 0.2)
    draw.ellipse([shine_x - shine_r, shine_y - shine_r, shine_x + shine_r, shine_y + shine_r], fill=(255,255,255,120))
    
    # Eyes
    eye_spacing = int(size * 0.3)
    eye_size = int(size * 0.12)
    eye_y = cy - int(size * 0.15 * stretch) + eye_offset_y
    if creature_type == 'frog':
        eye_y = cy - int(size * 0.4)
        eye_size = int(size * 0.15)
    
    for base_ex in [cx - eye_spacing, cx + eye_spacing]:
        lx = base_ex + eye_offset_x
        draw.ellipse([lx - eye_size - 2, eye_y - eye_size - 2, lx + eye_size + 2, eye_y + eye_size + 2], fill=(255,255,255,240))
        draw.ellipse([lx - eye_size, eye_y - eye_size, lx + eye_size, eye_y + eye_size], fill=(*eye_color, 250))
        draw.ellipse([lx - 1, eye_y - eye_size + 1, lx + 3, eye_y - eye_size + 5], fill=(255,255,255,200))
    
    # Mouth
    mouth_y = cy + int(size * 0.2 * stretch) + eye_offset_y
    mouth_x = cx + eye_offset_x
    if creature_type == 'frog':
        mouth_y = cy + int(size * 0.05)
    
    if mouth_type == 'smile':
        draw.arc([mouth_x - 10, mouth_y - 6, mouth_x + 10, mouth_y + 10], start=0, end=180, fill=(*eye_color, 220), width=2)
    elif mouth_type == 'sad':
        draw.arc([mouth_x - 10, mouth_y, mouth_x + 10, mouth_y + 14], start=180, end=360, fill=(*eye_color, 220), width=2)
    elif mouth_type == 'open':
        draw.ellipse([mouth_x - 6, mouth_y - 2, mouth_x + 6, mouth_y + 8], fill=(*eye_color, 200))
    elif mouth_type == 'neutral':
        draw.line([mouth_x - 8, mouth_y + 3, mouth_x + 8, mouth_y + 3], fill=(*eye_color, 220), width=2)
    
    # Arms
    arm_y = cy + int(size * 0.05 * stretch)
    arm_len = int(size * 0.4)
    if creature_type == 'frog':
        arm_y = cy - int(size * 0.1)
        arm_len = int(size * 0.5)
    
    for side, base_x, a_angle in [('left', cx - body_w, -60), ('right', cx + body_w, -120)]:
        if side == 'left':
            a_angle += arm_left
            ax = base_x + int(math.cos(math.radians(a_angle)) * 5)
        else:
            a_angle += arm_right
            ax = base_x - int(math.cos(math.pi - math.radians(a_angle)) * 5)
        a_rad = math.radians(a_angle)
        a_end_x = ax + int(math.cos(a_rad) * arm_len)
        a_end_y = arm_y + int(math.sin(a_rad) * arm_len)
        draw.line([ax, arm_y, a_end_x, a_end_y], fill=(r,g,b,200), width=5 if creature_type == 'frog' else 4)
        hand_r = 6 if creature_type == 'frog' else 5
        draw.ellipse([a_end_x - hand_r, a_end_y - hand_r, a_end_x + hand_r, a_end_y + hand_r], fill=(*accent_color, 220))


def generate_atlas(output_dir, pet_name, body_color, eye_color, accent_color, creature_type='slime'):
    os.makedirs(output_dir, exist_ok=True)
    atlas = Image.new('RGBA', (FRAME_WIDTH * COLUMNS, FRAME_HEIGHT * ROWS), (0,0,0,0))
    base_size = 50
    cx = FRAME_WIDTH // 2
    cy = FRAME_HEIGHT // 2 + 20
    
    states_config = []
    for row, state_name in enumerate(STATE_NAMES):
        for col in range(COLUMNS):
            frame = Image.new('RGBA', (FRAME_WIDTH, FRAME_HEIGHT), (0,0,0,0))
            draw = ImageDraw.Draw(frame)
            t = col / max(COLUMNS - 1, 1)
            
            if state_name == 'idle':
                offset_y = math.sin(t * 2 * math.pi) * 5
                squash = 1.0 + math.sin(t * 2 * math.pi) * 0.03
                stretch = 1.0 - math.sin(t * 2 * math.pi) * 0.03
                draw_creature(draw, cx, cy + offset_y, base_size, body_color, eye_color, accent_color,
                            squash=squash, stretch=stretch, creature_type=creature_type)
            elif state_name == 'running-right':
                offset_x = math.sin(t * 2 * math.pi) * 3
                offset_y = -abs(math.sin(t * 2 * math.pi)) * 8
                squash = 1.0 - abs(math.sin(t * 2 * math.pi)) * 0.05
                stretch = 1.0 + abs(math.sin(t * 2 * math.pi)) * 0.05
                draw_creature(draw, cx + offset_x, cy + offset_y, base_size, body_color, eye_color, accent_color,
                            eye_offset_x=3, squash=squash, stretch=stretch, creature_type=creature_type,
                            arm_left=-10 + math.sin(t * 2 * math.pi) * 20,
                            arm_right=-10 - math.sin(t * 2 * math.pi) * 20)
            elif state_name == 'running-left':
                offset_x = -math.sin(t * 2 * math.pi) * 3
                offset_y = -abs(math.sin(t * 2 * math.pi)) * 8
                squash = 1.0 - abs(math.sin(t * 2 * math.pi)) * 0.05
                stretch = 1.0 + abs(math.sin(t * 2 * math.pi)) * 0.05
                draw_creature(draw, cx + offset_x, cy + offset_y, base_size, body_color, eye_color, accent_color,
                            eye_offset_x=-3, squash=squash, stretch=stretch, creature_type=creature_type,
                            arm_left=-10 - math.sin(t * 2 * math.pi) * 20,
                            arm_right=-10 + math.sin(t * 2 * math.pi) * 20)
            elif state_name == 'waving':
                wave_angle = math.sin(t * 2 * math.pi) * 40
                offset_y = math.sin(t * 2 * math.pi) * 2
                draw_creature(draw, cx, cy + offset_y, base_size, body_color, eye_color, accent_color,
                            mouth_type='smile', creature_type=creature_type, arm_right=-80 + wave_angle)
            elif state_name == 'jumping':
                offset_y = -abs(math.sin(t * math.pi)) * 30
                squash = 1.0 + (1 - abs(math.sin(t * math.pi))) * 0.1
                stretch = 1.0 + abs(math.sin(t * math.pi)) * 0.1
                if abs(math.sin(t * math.pi)) < 0.1:
                    squash, stretch = 1.15, 0.85
                draw_creature(draw, cx, cy + offset_y, base_size, body_color, eye_color, accent_color,
                            mouth_type='open', squash=squash, stretch=stretch, creature_type=creature_type,
                            arm_left=-30, arm_right=-30)
            elif state_name == 'failed':
                wobble = math.sin(t * 3 * math.pi) * 3
                draw_creature(draw, cx + wobble, cy + 5, base_size, body_color, eye_color, accent_color,
                            eye_offset_y=3, mouth_type='sad', squash=1.05, stretch=0.95,
                            creature_type=creature_type, arm_left=20, arm_right=20)
            elif state_name == 'waiting':
                look_x = math.sin(t * 2 * math.pi) * 5
                offset_y = math.sin(t * 4 * math.pi) * 2
                draw_creature(draw, cx, cy + offset_y, base_size, body_color, eye_color, accent_color,
                            eye_offset_x=int(look_x), mouth_type='neutral', creature_type=creature_type)
            elif state_name == 'running':
                offset_y = -abs(math.sin(t * 2 * math.pi)) * 10
                squash = 1.0 - abs(math.sin(t * 2 * math.pi)) * 0.08
                stretch = 1.0 + abs(math.sin(t * 2 * math.pi)) * 0.08
                draw_creature(draw, cx, cy + offset_y, base_size, body_color, eye_color, accent_color,
                            mouth_type='open', squash=squash, stretch=stretch, creature_type=creature_type,
                            arm_left=-10 + math.sin(t * 2 * math.pi) * 25,
                            arm_right=-10 - math.sin(t * 2 * math.pi) * 25)
            elif state_name == 'review':
                look_x = math.sin(t * 2 * math.pi) * 3
                draw_creature(draw, cx, cy, base_size, body_color, eye_color, accent_color,
                            eye_offset_x=int(look_x), eye_offset_y=-2, mouth_type='neutral',
                            creature_type=creature_type, arm_right=-60 + math.sin(t * math.pi) * 10)
            
            x = col * FRAME_WIDTH
            y = row * FRAME_HEIGHT
            atlas.paste(frame, (x, y), frame)
        
        fps = 10
        if state_name in ('idle', 'waiting', 'review'): fps = 8
        elif state_name == 'failed': fps = 6
        states_config.append({'name': state_name, 'row': row, 'frames': COLUMNS, 'fps': fps})
    
    atlas_path = os.path.join(output_dir, f'{pet_name}_atlas.png')
    atlas.save(atlas_path, 'PNG')
    manifest_path = os.path.join(output_dir, 'pet.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump({'name': pet_name, 'version': '1.0', 'frame_width': FRAME_WIDTH, 'frame_height': FRAME_HEIGHT,
                    'columns': COLUMNS, 'states': states_config}, f, indent=2, ensure_ascii=False)
    print(f'Generated: {atlas_path} ({os.path.getsize(atlas_path)} bytes)')
    print(f'Manifest: {manifest_path}')
    return atlas_path, manifest_path


if __name__ == '__main__':
    print('=== 坤坤 (Dark Teal Slime) ===')
    generate_atlas(r'C:\Users\Admin\Desktop\宠物\坤坤\generated', 'kunkun',
                   body_color=(30, 30, 40), eye_color=(200, 230, 240),
                   accent_color=(100, 180, 200), creature_type='slime')
    
    print('\n=== 奶蛙 (Orange Frog) ===')
    generate_atlas(r'C:\Users\Admin\Desktop\宠物\奶蛙\generated', 'milk-frog',
                   body_color=(230, 160, 50), eye_color=(40, 60, 40),
                   accent_color=(255, 200, 80), creature_type='frog')
    
    print('\nDone!')
