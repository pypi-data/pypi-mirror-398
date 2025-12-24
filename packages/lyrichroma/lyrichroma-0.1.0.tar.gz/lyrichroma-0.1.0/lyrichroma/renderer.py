import numpy as np
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip, ColorClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import platform
import os


class SubtitleRenderer:
    def __init__(self, width=1280, height=720, font_path=None, font_size=40):
        self.width = width
        self.height = height
        self.font_size = font_size
        self.font_path = font_path

        # Try to load a font, fallback to default if fails
        self._load_font()

    def _load_font(self):
        """Load appropriate font with Chinese support"""
        # First try the provided font path
        if self.font_path:
            try:
                self.font = ImageFont.truetype(self.font_path, self.font_size)
                self.highlight_font = ImageFont.truetype(
                    self.font_path, int(self.font_size * 1.1)
                )
                return
            except IOError:
                print(
                    f"Warning: Could not load font {self.font_path}. Trying system fonts."
                )

        # Detect system and use appropriate Chinese fonts
        system = platform.system()
        chinese_fonts = []

        if system == "Darwin":  # macOS
            chinese_fonts = [
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
        elif system == "Windows":
            windows_fonts = os.environ.get("WINDIR", r"C:\Windows") + r"\Fonts"
            chinese_fonts = [
                os.path.join(windows_fonts, "msyh.ttc"),
                os.path.join(windows_fonts, "simsun.ttc"),
                os.path.join(windows_fonts, "simhei.ttf"),
            ]
        else:  # Linux and others
            chinese_fonts = [
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]

        # Try to load Chinese fonts
        for font_path in chinese_fonts:
            try:
                if os.path.exists(font_path):
                    self.font = ImageFont.truetype(font_path, self.font_size)
                    self.highlight_font = ImageFont.truetype(
                        font_path, int(self.font_size * 1.1)
                    )
                    print(f"Successfully loaded font: {font_path}")
                    return
            except (IOError, OSError):
                continue

        # Final fallback to default font
        print(
            "Warning: Could not load any system font. Using default font (limited character support)."
        )
        self.font = ImageFont.load_default()
        self.highlight_font = self.font

    def _get_current_segment(self, t, segments):
        """Find the text segment active at time t."""
        for seg in segments:
            if seg.start <= t <= seg.end:
                return seg
        return None

    def create_subtitle_clip(
        self,
        segments,
        duration,
        font_color="white",
        highlight_color="yellow",
        text_y_ratio=0.8,
    ):
        """
        Create a VideoClip that renders the subtitles.
        """

        def make_frame(t):
            # Create transparent image
            img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            current_seg = self._get_current_segment(t, segments)

            if current_seg:
                # We have a segment to display
                text = current_seg.text.strip()
                words = (
                    current_seg.words
                    if hasattr(current_seg, "words") and current_seg.words
                    else []
                )

                # Calculate text position
                text_y = self.height * text_y_ratio

                if not words:
                    # Fallback if no word timestamps: just show text
                    # For Chinese, we need smaller width per line
                    # Wrap text considering Chinese characters
                    lines = []
                    current_line = ""

                    for char in text:
                        # Check if adding this character would exceed the line limit
                        test_line = current_line + char
                        bbox = draw.textbbox((0, 0), test_line, font=self.font)
                        line_width = bbox[2] - bbox[0]

                        if (
                            line_width > self.width * 0.9
                        ):  # 90% of width as safety margin
                            if current_line:
                                lines.append(current_line)
                                current_line = char
                            else:
                                # If even one character is too wide, force break
                                lines.append(test_line)
                                current_line = ""
                        else:
                            current_line = test_line

                    # Add the last line if it exists
                    if current_line:
                        lines.append(current_line)

                    y_offset = text_y
                    for line in lines:
                        # Center text
                        bbox = draw.textbbox((0, 0), line, font=self.font)
                        text_w = bbox[2] - bbox[0]
                        text_x = (self.width - text_w) // 2

                        # Draw outline for better visibility
                        shadow_color = (0, 0, 0, 255)

                        # Thick stroke
                        draw.text(
                            (text_x, y_offset),
                            line,
                            font=self.font,
                            fill=shadow_color,
                            stroke_width=2,
                            stroke_fill=shadow_color,
                        )
                        draw.text(
                            (text_x, y_offset), line, font=self.font, fill=font_color
                        )

                        y_offset += self.font_size + 5
                else:
                    # Flatten words into lines
                    lines_of_words = []
                    current_line = []
                    current_line_len = 0
                    max_chars = 50

                    for word in words:
                        w_text = word.word.strip()
                        if current_line_len + len(w_text) + 1 > max_chars:
                            lines_of_words.append(current_line)
                            current_line = [word]
                            current_line_len = len(w_text)
                        else:
                            current_line.append(word)
                            current_line_len += len(w_text) + 1
                    if current_line:
                        lines_of_words.append(current_line)

                    # Now draw
                    y_offset = text_y - (
                        len(lines_of_words) * self.font_size
                    )  # Move up

                    for line_words in lines_of_words:
                        # Calculate total width of line to center it
                        full_line_text = "".join([w.word.strip() for w in line_words])
                        bbox = draw.textbbox((0, 0), full_line_text, font=self.font)
                        line_w = bbox[2] - bbox[0]
                        start_x = (self.width - line_w) // 2

                        curr_x = start_x
                        for word in line_words:
                            w_text = word.word.strip()

                            color = font_color
                            is_active = word.start <= t <= word.end

                            if is_active:
                                color = highlight_color
                                this_font = self.highlight_font
                            else:
                                this_font = self.font

                            # Draw
                            draw.text(
                                (curr_x, y_offset),
                                w_text,
                                font=this_font,
                                fill=(0, 0, 0, 255),
                                stroke_width=2,
                                stroke_fill=(0, 0, 0, 255),
                            )
                            draw.text(
                                (curr_x, y_offset), w_text, font=this_font, fill=color
                            )

                            # Advance x
                            w_bbox = draw.textbbox((0, 0), w_text, font=this_font)
                            w_width = w_bbox[2] - w_bbox[0]
                            curr_x += w_width + (self.font_size // 4)  # Space

                        y_offset += self.font_size + 10

            return np.array(img)

        return VideoClip(make_frame, duration=duration)

    # Pre-defined palettes
    PALETTES = {
        "aurora": [
            [44, 0, 62],  # Deep Purple
            [0, 80, 100],  # Dark Cyan
            [120, 20, 80],  # Magenta-ish
        ],
        "sunset": [
            [45, 10, 60],  # Dark Purple
            [180, 60, 20],  # Deep Orange
            [220, 140, 40],  # Golden Yellow
        ],
        "ocean": [
            [0, 20, 40],  # Deep Blue
            [0, 80, 100],  # Teal
            [0, 120, 140],  # Light Cyan
        ],
        "cyberpunk": [
            [20, 0, 40],  # Dark Violet
            [0, 255, 255],  # Neon Cyan
            [255, 0, 128],  # Neon Pink
        ],
        "forest": [
            [10, 30, 10],  # Dark Green
            [40, 80, 20],  # Moss Green
            [100, 140, 40],  # Lime Green
        ],
    }

    def _create_dynamic_bg_clip(self, duration, palette_name="aurora"):
        """Create a background clip with a moving plasma/gradient effect."""

        # Select palette
        palette_name = palette_name.lower()
        if palette_name not in self.PALETTES:
            print(f"Warning: Palette '{palette_name}' not found. Using 'aurora'.")
            palette_name = "aurora"

        colors = self.PALETTES[palette_name]
        c1 = np.array(colors[0])
        c2 = np.array(colors[1])
        c3 = np.array(colors[2])

        # Optimization: Render at low resolution and resize up.
        res_w, res_h = 160, 90  # 1/8th of 720p

        # Pre-compute coordinate grids
        x = np.linspace(0, 4 * np.pi, res_w)
        y = np.linspace(0, 4 * np.pi, res_h)
        X, Y = np.meshgrid(x, y)

        def make_frame(t):
            # Plasma effect using sine waves
            v1 = np.sin(X + t * 0.5)
            v2 = np.sin(np.sqrt((X - res_w / 2) ** 2 + (Y - res_h / 2) ** 2) * 0.2 + t)
            v3 = np.sin(X * 0.5 + Y * 0.5 + t)

            # Combine to get -1 to 1 range
            final = (v1 + v2 + v3) / 3.0

            # Map [-1, 1] to [0, 1]
            val = (final + 1) / 2.0

            # Expand dimensions to (H, W, 1) for easy broadcasting with colors
            val_expanded = val[:, :, np.newaxis]

            # Create output array
            img = np.zeros((res_h, res_w, 3), dtype=np.float32)

            # Calculate mix factors across the whole image
            # We mix c1->c2 where val < 0.5, and c2->c3 where val >= 0.5

            # Factor for first transition (0.0 to 0.5 maps to 0.0 to 1.0)
            t1 = np.clip(val_expanded * 2, 0, 1)

            # Factor for second transition (0.5 to 1.0 maps to 0.0 to 1.0)
            t2 = np.clip((val_expanded - 0.5) * 2, 0, 1)

            # Calculate both possible color values everywhere (simplifies vectorized logic)
            # This avoids masking headaches with broadcasting:
            color_low = (1 - t1) * c1 + t1 * c2
            color_high = (1 - t2) * c2 + t2 * c3

            # Select based on threshold
            mask = val_expanded < 0.5
            img = np.where(mask, color_low, color_high)

            return img.astype(np.uint8)

        # Create low-res clip and resize
        clip = VideoClip(make_frame, duration=duration)
        return clip.resized(new_size=(self.width, self.height))

    def generate_video(
        self,
        audio_path,
        segments,
        output_path,
        bg_type="color",
        bg_value="#000000",
        font_color="white",
        highlight_color="yellow",
        text_y_ratio=0.8,
    ):
        print(f"Generating video to {output_path}...")

        # Load audio
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        # Create background
        if bg_type == "image":
            # Load image and resize/crop to fit
            bg_clip = ImageClip(bg_value).with_duration(duration)
            bg_clip = bg_clip.resized(height=self.height)
            # Center crop if needed (simplified: just resize to cover or fit?)
            # MoviePy resize is handy.
            # If width is still too small, resize by width.
            if bg_clip.w < self.width:
                bg_clip = bg_clip.resized(width=self.width)
            # Center crop
            bg_clip = bg_clip.cropped(
                x1=bg_clip.w / 2 - self.width / 2,
                width=self.width,
                y1=bg_clip.h / 2 - self.height / 2,
                height=self.height,
            )
        elif bg_type == "dynamic":
            # Treat bg_value as palette name if valid, otherwise properly defaults inside the method
            palette = (
                bg_value if bg_value and not bg_value.startswith("#") else "aurora"
            )
            bg_clip = self._create_dynamic_bg_clip(duration, palette_name=palette)
        else:
            # Solid color
            if bg_value.startswith("#"):
                h = bg_value.lstrip("#")
                rgb = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
            else:
                rgb = (0, 0, 0)  # Default black
            bg_clip = ColorClip(
                size=(self.width, self.height), color=rgb, duration=duration
            )

        clips_to_composite = [bg_clip]

        # Create subtitles
        subtitle_clip = self.create_subtitle_clip(
            segments,
            duration,
            font_color=font_color,
            highlight_color=highlight_color,
            text_y_ratio=text_y_ratio,
        )
        clips_to_composite.append(subtitle_clip)

        # Composite
        final_video = CompositeVideoClip(clips_to_composite)
        final_video = final_video.with_audio(audio_clip)

        # Write
        final_video.write_videofile(
            output_path, fps=24, codec="libx264", audio_codec="aac"
        )
        print("Video generation successful.")


if __name__ == "__main__":
    pass
