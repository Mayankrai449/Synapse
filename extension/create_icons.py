"""
Simple script to create placeholder icons for the Chrome extension
Run: python create_icons.py
"""

from PIL import Image, ImageDraw, ImageFont

def create_icon(size, filename):
    # Create a blue square
    img = Image.new('RGB', (size, size), color='#4285f4')
    draw = ImageDraw.Draw(img)

    # Add white text
    try:
        # Try to use a default font
        font_size = size // 3
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    text = "A"

    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(position, text, fill='white', font=font)

    # Save the image
    img.save(filename)
    print(f"Created {filename}")

if __name__ == "__main__":
    create_icon(16, "icon16.png")
    create_icon(48, "icon48.png")
    create_icon(128, "icon128.png")
    print("\nAll icons created successfully!")
