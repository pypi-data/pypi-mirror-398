import os
import random
import string
from typing import Optional
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont


# -----------------------------
# Config
# -----------------------------
@dataclass
class CaptchaConfig:
    """
    Configuration class for CAPTCHA generation.

    Attributes:
        width (int): Width of the CAPTCHA image in pixels.
        height (int): Height of the CAPTCHA image in pixels.
        min_len (int): Minimum number of characters in the CAPTCHA text.
        max_len (int): Maximum number of characters in the CAPTCHA text.
        rotate (bool): If True, randomly rotate individual characters.
        noise (bool): If True, add random noise (dots and lines).
        random_color (bool): If True, characters will have random colors.
        dot_count (int): Number of dot noise elements to add.
        line_count (int): Number of line noise elements to add.
        text_mode (str): Type of text content. Options: 'digits', 'lower', 'upper', 
                         'letters', 'alnum', 'custom'.
        custom_charset (Optional[str]): Custom character set used if text_mode='custom'.
    """
    width: int = 200
    height: int = 80
    min_len: int = 4
    max_len: int = 6
    rotate: bool = False
    noise: bool = False
    random_color: bool = False
    dot_count: int = 200
    line_count: int = 8
    text_mode: str = "alnum"
    custom_charset: Optional[str] = None


# -----------------------------
# CAPTCHA Generator
# -----------------------------
class CaptchaGenerator:
    """
    A CAPTCHA generator class that produces images with configurable text, fonts, 
    rotation, colors, and noise.
    """
    def __init__(self, fonts_dir: str, config: CaptchaConfig):
        """
        Initialize the CAPTCHA generator.

        Args:
            fonts_dir (str): Directory containing .ttf font files.
            config (CaptchaConfig): Configuration object for CAPTCHA generation.
        """
        self.fonts = self._load_fonts(fonts_dir)
        self.config = config

    def _load_fonts(self, font_dir: str):
        """
        Load all TTF fonts from the specified directory.

        Args:
            font_dir (str): Path to fonts directory.

        Returns:
            List[str]: List of full paths to TTF font files.

        Raises:
            RuntimeError: If no TTF fonts are found.
        """
        fonts = [
            os.path.join(font_dir, f)
            for f in os.listdir(font_dir)
            if f.lower().endswith(".ttf")
        ]
        if not fonts:
            raise RuntimeError(f"No .ttf fonts found in '{font_dir}'")
        return fonts

    def _random_text(self) -> str:
        """
        Generate a random text string based on the config's text_mode.

        Returns:
            str: Randomly generated CAPTCHA text.

        Raises:
            ValueError: If text_mode is 'custom' and custom_charset is not provided,
                        or if text_mode is unknown.
        """
        length = random.randint(self.config.min_len, self.config.max_len)

        if self.config.text_mode == "digits":
            chars = string.digits
        elif self.config.text_mode == "lower":
            chars = string.ascii_lowercase
        elif self.config.text_mode == "upper":
            chars = string.ascii_uppercase
        elif self.config.text_mode == "letters":
            chars = string.ascii_letters
        elif self.config.text_mode == "alnum":
            chars = string.ascii_letters + string.digits
        elif self.config.text_mode == "custom":
            if not self.config.custom_charset:
                raise ValueError("custom_charset must be set when text_mode='custom'")
            chars = self.config.custom_charset
        else:
            raise ValueError(f"Unknown text_mode: {self.config.text_mode}")

        return "".join(random.choice(chars) for _ in range(length))

    def _random_color(self) -> tuple[int, int, int]:
        """
        Generate a random RGB color with low intensity (0-150).

        Returns:
            tuple[int, int, int]: Random color in RGB.
        """
        return tuple(random.randint(0, 150) for _ in range(3))

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """
        Select a random font from the loaded fonts and return a font object.

        Args:
            size (int): Font size.

        Returns:
            ImageFont.FreeTypeFont: PIL font object.
        """
        return ImageFont.truetype(random.choice(self.fonts), size)

    def _add_dot_noise(self, draw: ImageDraw.ImageDraw):
        """
        Add random dot noise to the image.

        Args:
            draw (ImageDraw.ImageDraw): PIL ImageDraw object to draw on.
        """
        for _ in range(self.config.dot_count):
            r = random.randint(1, 3)  # Dot radius
            x = random.randint(0, self.config.width - r)
            y = random.randint(0, self.config.height - r)
            draw.ellipse((x, y, x + r, y + r), fill=self._random_color())

    def _add_line_noise(self, draw: ImageDraw.ImageDraw):
        """
        Add random line noise to the image.

        Args:
            draw (ImageDraw.ImageDraw): PIL ImageDraw object to draw on.
        """
        for _ in range(self.config.line_count):
            w = random.randint(1, 2)  # Line width
            x1, y1 = random.randint(0, self.config.width), random.randint(0, self.config.height)
            x2, y2 = random.randint(0, self.config.width), random.randint(0, self.config.height)
            draw.line((x1, y1, x2, y2), fill=self._random_color(), width=w)

    def generate(self) -> tuple[Image.Image, str]:
        """
        Generate a CAPTCHA image with the current configuration.

        Returns:
            tuple[Image.Image, str]: Generated PIL image and the corresponding text.
        """
        cfg = self.config
        text = self._random_text()

        # Create blank image with white background
        image = Image.new("RGB", (cfg.width, cfg.height), "white")
        draw = ImageDraw.Draw(image)

        font_size = int(cfg.height * 0.7)
        spacing = random.randint(5, 12)  # Random spacing between characters

        char_images = []

        # Render each character individually
        for ch in text:
            font = self._get_font(font_size)
            temp = Image.new("RGBA", (font_size * 2, cfg.height * 2), (0, 0, 0, 0))
            temp_draw = ImageDraw.Draw(temp)

            color = self._random_color() if cfg.random_color else (0, 0, 0)
            temp_draw.text((font_size // 2, cfg.height // 2), ch, font=font, fill=color)

            # Apply rotation if enabled
            if cfg.rotate:
                temp = temp.rotate(random.uniform(-25, 25), expand=1, resample=Image.BICUBIC)

            # Crop to the character bounding box
            bbox = temp.getbbox()
            char_images.append(temp.crop(bbox))

        # Compute total width and scale if too large
        total_width = sum(c.width for c in char_images) + spacing * (len(char_images) - 1)
        if total_width > cfg.width:
            scale = cfg.width / total_width
            char_images = [
                c.resize((int(c.width * scale), int(c.height * scale)), Image.BICUBIC)
                for c in char_images
            ]
            total_width = sum(c.width for c in char_images) + spacing * (len(char_images) - 1)

        # Paste characters centered
        x = (cfg.width - total_width) // 2
        for c in char_images:
            y = (cfg.height - c.height) // 2
            image.paste(c, (x, y), c)
            x += c.width + spacing

        # Add noise if enabled
        if cfg.noise:
            self._add_dot_noise(draw)
            self._add_line_noise(draw)

        return image, text
