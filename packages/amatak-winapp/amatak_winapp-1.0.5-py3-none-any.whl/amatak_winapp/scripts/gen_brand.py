import os
import re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Configuration
TREE_FILE = "tree.txt"
DEFAULT_BRAND_PATH = "assets/brand"
CURRENT_YEAR = datetime.now().year
OWNER = "Amatak Holdings Pty Ltd"

def split_camel_case(name):
    """Split camelCase or PascalCase words"""
    # Using regex to split on uppercase letters followed by lowercase
    parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|[A-Z]+', name)
    return [part.lower() for part in parts]

def split_compound_word(word):
    """Try to split compound words like 'winbuilder' into ['win', 'builder']"""
    # Common word patterns to help splitting
    common_prefixes = ['win', 'web', 'app', 'soft', 'data', 'code', 'net', 'cloud', 'tech']
    common_suffixes = ['builder', 'maker', 'tool', 'manager', 'editor', 'viewer', 'analyzer']
    
    word_lower = word.lower()
    
    # Try to split by common patterns first
    for prefix in common_prefixes:
        if word_lower.startswith(prefix) and len(word_lower) > len(prefix):
            suffix = word_lower[len(prefix):]
            if suffix and len(suffix) >= 3:  # Ensure suffix is reasonable length
                return [prefix, suffix]
    
    for suffix in common_suffixes:
        if word_lower.endswith(suffix) and len(word_lower) > len(suffix):
            prefix = word_lower[:-len(suffix)]
            if prefix and len(prefix) >= 3:  # Ensure prefix is reasonable length
                return [prefix, suffix]
    
    # If no pattern matches, try to split by vowel-consonant transitions
    # This handles cases like "winbuilder" -> "win" + "builder"
    for i in range(1, len(word_lower) - 2):
        # Check if this is a good split point (consonant to vowel or vowel to consonant)
        if (word_lower[i] in 'aeiou' and word_lower[i-1] not in 'aeiou' and
            len(word_lower[:i]) >= 3 and len(word_lower[i:]) >= 3):
            return [word_lower[:i], word_lower[i:]]
    
    # If we can't split intelligently, return the whole word
    return [word_lower]

def get_brand_text(project_name):
    """Extracts brand initials from project name with intelligent word splitting"""
    
    # Clean the project name - remove special characters, keep alphanumeric and hyphens
    cleaned_name = re.sub(r'[^\w\s-]', '', project_name)
    
    # Split by common separators first
    words = []
    for part in re.split(r'[-_\s]+', cleaned_name):
        if not part:
            continue
            
        # Check if part contains camelCase or PascalCase
        if re.search(r'[a-z][A-Z]|[A-Z][a-z][a-z]', part):
            # Split camelCase/PascalCase
            camel_parts = split_camel_case(part)
            words.extend(camel_parts)
        elif part.isalpha() and len(part) >= 8:
            # Check if it's a long compound word like "winbuilder"
            # First check if it's actually an English word
            # For simplicity, we'll assume long words without separators are compound
            if re.search(r'[aeiou]{2,}', part.lower()) or len(part) >= 10:
                # Try to split compound words
                compound_parts = split_compound_word(part)
                words.extend(compound_parts)
            else:
                words.append(part.lower())
        else:
            # Regular word
            words.append(part.lower())
    
    # Debug: print extracted words
    print(f"Project: '{project_name}' -> Words: {words}")
    
    if not words:
        return "AI"
    
    # Generate initials based on words
    if len(words) == 1:
        # Single word: use first and last character
        word = words[0]
        if len(word) >= 2:
            return f"{word[0].upper()}{word[-1].upper()}"
        else:
            return word[0].upper()
    elif len(words) == 2:
        # Two words: use first letter of each
        return f"{words[0][0].upper()}{words[1][0].upper()}"
    else:
        # Multiple words: use first letter of first, middle, and last words
        first = words[0][0].upper()
        middle = "".join([w[0].upper() for w in words[1:-1]])
        last = words[-1][0].upper()  # Changed from last character to first character of last word
        return f"{first}{middle}{last}"

def generate_styled_assets(text, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    
    # --- 1. BRAND.PNG (512x512 Styled Logo) ---
    img = Image.new("RGBA", (512, 512), (33, 37, 41, 255)) # Dark Slate
    draw = ImageDraw.Draw(img)
    
    # Draw a subtle circular border
    draw.ellipse([40, 40, 472, 472], outline=(108, 117, 125, 255), width=8)
    
    try:
        font_main = ImageFont.truetype("arialbd.ttf", 220) # Bold
        font_copy = ImageFont.truetype("arial.ttf", 24)
    except:
        font_main = font_copy = ImageFont.load_default()

    # Main Brand Text
    draw.text((256, 240), text, fill="white", font=font_main, anchor="mm")
    
    # Copyright Symbol at the bottom
    copyright_text = f"© {CURRENT_YEAR} {OWNER}"
    draw.text((256, 420), copyright_text, fill=(173, 181, 189), font=font_copy, anchor="mm")
    
    img.save(os.path.join(target_dir, "brand.png"))

    # --- 2. BRAND.ICO (Windows Icon) ---
    img.save(os.path.join(target_dir, "brand.ico"), format="ICO", sizes=[(32,32), (64,64), (256,256)])

    # --- 3. BRAND_INSTALLER.BMP (150x57 Styled Banner) ---
    bmp_img = Image.new("RGB", (150, 57), (255, 255, 255))
    bmp_draw = ImageDraw.Draw(bmp_img)
    
    try:
        bmp_font = ImageFont.truetype("arialbd.ttf", 28)
        bmp_copy_font = ImageFont.truetype("arial.ttf", 8)
    except:
        bmp_font = bmp_copy_font = ImageFont.load_default()

    bmp_draw.text((75, 22), text, fill=(33, 37, 41), font=bmp_font, anchor="mm")
    bmp_draw.text((75, 45), f"© {OWNER}", fill=(108, 117, 125), font=bmp_copy_font, anchor="mm")
    
    bmp_img.save(os.path.join(target_dir, "brand_installer.bmp"), "BMP")
    print(f"[{CURRENT_YEAR}] Styled brand assets generated in {target_dir}")

# Test function to verify the logic
def test_brand_text():
    test_cases = [
        "win-builder",     # Should return "WB"
        "winbuilder",      # Should return "WB" (split into win+builder)
        "winbuild",        # Should return "WB" (split into win+build)
        "win-build",       # Should return "WB"
        "win_builder",     # Should return "WB"
        "WebApp",          # Should return "WA"
        "myProject",       # Should return "MP"
        "DataAnalyzer",    # Should return "DA"
        "code-generator",  # Should return "CG"
        "net-manager",     # Should return "NM"
        "simple",          # Should return "SE" (first and last of single word)
        "a",               # Should return "A"
        "WinBuildPro",     # Should return "WBP" (win+build+pro)
        "cloud-storage-manager",  # Should return "CSM"
    ]
    
    print("Testing brand text generation:")
    print("-" * 40)
    for test in test_cases:
        result = get_brand_text(test)
        print(f"{test:25} -> {result}")
    print("-" * 40)

if __name__ == "__main__":
    # Run tests
    test_brand_text()
    print()
    
    # Generate for current directory
    name = os.path.basename(os.getcwd())
    print(f"Generating for current directory: {name}")
    brand_text = get_brand_text(name)
    generate_styled_assets(brand_text, DEFAULT_BRAND_PATH)