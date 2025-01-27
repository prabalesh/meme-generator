import os
import json
import random
import string
from moviepy import VideoFileClip, AudioFileClip, concatenate_audioclips, concatenate_videoclips, ImageClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy import ColorClip


class VideoMemeGenerator:
    def __init__(self, output_dir="generated_vid_memes"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _generate_random_filename(self):
        """Generate a random filename for the output video."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + ".mp4"

    def _create_blank_video(self, duration):
        """Create a blank video in portrait orientation (vertical)."""
        return ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=duration)

    def _add_text(self, text, video_duration, font_path, font_size, text_color, shadow_offset, shadow_color):
        """Create a list of text clips with shadows."""
        text_clips = []
        y_offset = 100  # Start near the top

        for line in text.split("\n"):
            shadow = TextClip(
                text=line,
                font=font_path,
                font_size=font_size,
                color=shadow_color,
                duration=video_duration,
            ).with_position(("center", y_offset + shadow_offset[1]))

            main_text = TextClip(
                text=line,
                font=font_path,
                font_size=font_size,
                color=text_color,
                duration=video_duration,
            ).with_position(("center", y_offset))

            text_clips.extend([shadow, main_text])
            y_offset += font_size + 10  # Adjust for line spacing

        return text_clips

    def _add_audio(self, final_clip, audio_path, video_duration):
        """Add audio to the final video clip."""
        if audio_path and os.path.exists(audio_path):
            audio_files = [f for f in os.listdir(audio_path) if f.endswith(('.mp3', '.wav'))]
            if audio_files:
                selected_audio = os.path.join(audio_path, random.choice(audio_files))
                audio = AudioFileClip(selected_audio).with_duration(video_duration)
                if audio.duration < video_duration:
                    loops = int(video_duration // audio.duration + 1)
                    audio = concatenate_audioclips([audio] * loops).with_duration(video_duration)

                return final_clip.with_audio(audio)

        return final_clip

    def generate_template0(self, meme_config):
        """Generate a video using Template 0."""
        video = VideoFileClip(meme_config["video_path0"])
        blank_video = self._create_blank_video(video.duration).with_fps(video.fps)
        video_resized = video.resized(width=blank_video.w).with_position("center")

        for text_content in meme_config["texts"]:
            text_clips = self._add_text(
                text=text_content,
                video_duration=video.duration,
                font_path=meme_config["font_path"],
                font_size=meme_config["font_size"],
                text_color=meme_config["text_color"],
                shadow_offset=tuple(meme_config["shadow_offset"]),
                shadow_color=meme_config["shadow_color"],
            )
            final_clip = CompositeVideoClip([blank_video, video_resized] + text_clips)

            audio_path = meme_config.get("audio_path0")
            final_clip = self._add_audio(final_clip, audio_path, video.duration)

            final_clip = self._add_audio(final_clip=final_clip, audio_path=meme_config["audio_path0"], video_duration=final_clip.duration)

            output_path = os.path.join(self.output_dir, self._generate_random_filename())
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    def generate_template1(self, meme_config):
        text_height_ratio = 0.1 
        video_height_ratio = 0.4
        resolution = (1080, 1920)

        total_height = resolution[1]
        text_height = int(total_height * text_height_ratio)
        video_height = int(total_height * video_height_ratio)

        # Load the video clips
        video1 = VideoFileClip(meme_config["video_path0"])
        video2 = VideoFileClip(meme_config["video_path1"])

        # Determine the max duration between the two video clips
        max_duration = max(video1.duration, video2.duration)

        # Loop the shorter video clip if necessary
        if video1.duration < max_duration:
            loops = int(max_duration // video1.duration) + 1  # Ensure at least enough loops
            video1 = concatenate_videoclips([video1] * loops).subclipped(0, max_duration)

        if video2.duration < max_duration:
            loops = int(max_duration // video2.duration) + 1
            video2 = concatenate_videoclips([video2] * loops).subclipped(0, max_duration)

        # Create a blank background
        background = self._create_blank_video(max_duration)
        
        for i in range(len(meme_config["texts"])):
            # Top text
            top_text = TextClip(text=meme_config["texts"][i],
                                font=meme_config["font_path"], 
                                font_size=meme_config["font_size"], 
                                color=meme_config["text_color"], 
                                size=(resolution[0], text_height))
            top_text = top_text.with_position(("center", 0)).with_duration(background.duration)

            # Stretch the first video
            video1_stretched = video1.resized(height=video_height)  # Stretch to 40% height of the background
            video1_stretched = video1_stretched.with_position(("center", text_height)).with_duration(background.duration)

            # Bottom text
            bottom_text = TextClip(text=meme_config["texts0"][i], 
                                font=meme_config["font_path"], 
                                font_size=meme_config["font_size"], 
                                color=meme_config["text_color"], 
                                size=(resolution[0], text_height))
            bottom_text = bottom_text.with_position(("center", text_height + video_height)).with_duration(background.duration)

            # Stretch the second video
            video2_stretched = video2.resized(height=video_height)  # Stretch to 40% height of the background
            video2_stretched = video2_stretched.with_position(("center", text_height + video_height + text_height)).with_duration(background.duration)

            # Combine everything into the final video
            final_video = CompositeVideoClip([background, top_text, video1_stretched, bottom_text, video2_stretched])
            
            # Add audio to the final video
            audio_path = meme_config.get("audio_path0")
            final_video = self._add_audio(final_video, audio_path, final_video.duration)

            # Output the video
            output_path = os.path.join(self.output_dir, self._generate_random_filename())
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")


    def process_batch(self, memes_config):
        """Process a batch of memes from a configuration."""
        for meme_config in memes_config:
            template_method_name = f"generate_template{meme_config.get('template')}"
            if hasattr(self, template_method_name):
                getattr(self, template_method_name)(meme_config)
            else:
                raise ValueError(f"Template {meme_config.get('template')} is not implemented.")


def load_config(config_path):
    """Load configuration from a JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} does not exist.")
    with open(config_path, "r") as file:
        return json.load(file)


if __name__ == "__main__":
    # Load the meme configuration
    config_path = "memes_config.json"
    memes_config = load_config(config_path)

    # Initialize the meme generator and process the batch
    meme_generator = VideoMemeGenerator(output_dir="generated_vid_memes")
    meme_generator.process_batch(memes_config)
