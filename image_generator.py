import os
import logging
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from datetime import datetime
import random

def create_result_image(score, total, message):
    """
    Create an image displaying the quiz result
    Returns the base64 encoded image data for embedding in HTML
    """
    try:
        # Create a drawing surface
        width, height = 800, 600
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Draw border
        draw.rectangle(
            ((0, 0), (width-1, height-1)),
            outline=(255, 140, 0),
            width=10
        )
        
        # Add a background color
        draw.rectangle(
            ((10, 10), (width-10, height-10)),
            fill=(255, 245, 235),
            outline=None
        )
        
        # Use default font since we might not have specific fonts installed
        title_font = ImageFont.load_default()
        score_font = ImageFont.load_default()
        message_font = ImageFont.load_default()
        
        # Add title
        title_text = "India's Hardest Brain Challenge"
        # For PIL older versions that don't have textlength
        try:
            title_width = draw.textlength(title_text, font=title_font)
        except AttributeError:
            title_width = title_font.getmask(title_text).getbbox()[2]
        
        draw.text(
            ((width - title_width) / 2, 50),
            title_text,
            font=title_font,
            fill=(255, 69, 0)
        )
        
        # Add score circle
        circle_center_x = width // 2
        circle_center_y = height // 2 - 50
        circle_radius = 100
        
        # Draw circle
        draw.ellipse(
            [(circle_center_x - circle_radius, circle_center_y - circle_radius),
             (circle_center_x + circle_radius, circle_center_y + circle_radius)],
            fill=(255, 140, 0),
            outline=None
        )
        
        # Add score text inside circle
        score_text = f"{score}/{total}"
        # For PIL older versions that don't have textlength
        try:
            score_width = draw.textlength(score_text, font=score_font)
        except AttributeError:
            score_width = score_font.getmask(score_text).getbbox()[2]
            
        draw.text(
            ((width - score_width) / 2, circle_center_y - score_font.getbbox("0")[3] // 2),
            score_text,
            font=score_font,
            fill=(255, 255, 255)
        )
        
        # Add message below circle
        # For PIL older versions that don't have textlength
        try:
            message_width = draw.textlength(message, font=message_font)
        except AttributeError:
            message_width = message_font.getmask(message).getbbox()[2]
            
        draw.text(
            ((width - message_width) / 2, circle_center_y + circle_radius + 30),
            message,
            font=message_font,
            fill=(0, 0, 0)
        )
        
        # Add footer
        footer_text = "Share this result to challenge your friends!"
        # For PIL older versions that don't have textlength
        try:
            footer_width = draw.textlength(footer_text, font=message_font)
        except AttributeError:
            footer_width = message_font.getmask(footer_text).getbbox()[2]
            
        draw.text(
            ((width - footer_width) / 2, height - 80),
            footer_text,
            font=message_font,
            fill=(255, 69, 0)
        )
        
        # Add decorative elements based on score
        if score >= 8:  # High score
            # Add stars or trophies
            for _ in range(5):
                star_x = random.randint(50, width-50)
                star_y = random.randint(50, height-50)
                star_size = random.randint(10, 20)
                
                # Draw a simple star (actually a small circle)
                draw.ellipse(
                    [(star_x - star_size, star_y - star_size),
                     (star_x + star_size, star_y + star_size)],
                    fill=(255, 215, 0),  # Gold color
                    outline=None
                )
        
        # Generate a unique filename for the image and save it to static folder
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_id = random.randint(1000, 9999)
        filename = f"result_{timestamp}_{random_id}.png"
        
        # Ensure directory exists
        os.makedirs("static/images", exist_ok=True)
        filepath = f"static/images/{filename}"
        
        # Save the image file
        image.save(filepath)
        
        # Return the URL path to the image
        return f"/static/images/{filename}"
    
    except Exception as e:
        logging.error(f"Error creating result image: {e}")
        # Return fallback default image URL
        return "/static/images/default_result.png"

def create_fallback_image(score, total):
    """Create a very simple fallback image when the main function fails"""
    try:
        # Create a simple image
        width, height = 400, 300
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Add a border
        draw.rectangle(((0, 0), (width-1, height-1)), outline=(255, 140, 0), width=5)
        
        # Use default font
        font = ImageFont.load_default()
        
        # Add text
        title_text = "Quiz Result"
        score_text = f"Score: {score}/{total}"
        
        draw.text((20, 50), title_text, font=font, fill=(0, 0, 0))
        draw.text((20, 100), score_text, font=font, fill=(0, 0, 0))
        
        # Save the image
        os.makedirs("static/images", exist_ok=True)
        filepath = "static/images/default_result.png"
        image.save(filepath)
        
        return "/static/images/default_result.png"
    except Exception as e:
        logging.error(f"Error creating fallback image: {e}")
        return None
