#!/usr/bin/env python3
"""Create a simple icon from the green circle emoji."""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    # Complete set of macOS icon sizes with proper naming
    icon_configs = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]
    
    # Create iconset directory
    iconset_dir = "icon.iconset"
    os.makedirs(iconset_dir, exist_ok=True)
    
    for size, filename in icon_configs:
        # Create image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw a green circle with better quality
        margin = max(1, size // 10)  # Smaller margin for larger icons
        outline_width = max(1, size // 128)  # Proportional outline
        
        draw.ellipse([margin, margin, size - margin, size - margin], 
                    fill='#00CC00', outline='#008800', width=outline_width)
        
        # Save PNG files for iconset
        img.save(f"{iconset_dir}/{filename}")
    
    # Create ICNS file using macOS iconutil
    import subprocess
    subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', 'ping_app.icns'], check=True)
    
    print("✅ Icon created successfully: ping_app.icns")
    
    # Clean up iconset directory
    import shutil
    shutil.rmtree(iconset_dir)
    
except ImportError:
    print("❌ PIL (Pillow) not available. Creating a simple approach...")
    # Fallback: create a basic PNG using system tools
    import subprocess
    
    # Use macOS built-in tools to create a simple icon
    # This creates a 512x512 green circle
    script = '''
tell application "Image Events"
    launch
    set this_image to make new image with properties {dimensions:{512, 512}}
    tell this_image
        -- This is a simplified approach - would need more complex AppleScript
        save in POSIX file "''' + os.getcwd() + '''/ping_app.png"
    end tell
end tell
'''
    
    print("⚠️  Simple fallback: You'll need to manually create an icon.")
    print("📝 Suggested: Use any graphics app to create a 512x512 green circle PNG")
    print("💾 Save it as 'ping_app.png' or 'ping_app.icns' in this directory")
    
except Exception as e:
    print(f"❌ Error creating icon: {e}")
    print("📝 Manual option: Create a 512x512 green circle image as 'ping_app.png'")