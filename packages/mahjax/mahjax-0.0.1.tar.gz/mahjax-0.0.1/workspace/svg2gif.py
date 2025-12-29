"""
Most SVG to Gif online generators are using magick's command
this was not sufficent for my use case due to the outputs not formatting correctly 
and scalability
"""


import glob
import contextlib
import re
import os 
import shutil
import sys
import warnings
import time

from PIL import Image
from bs4 import BeautifulSoup, FeatureNotFound, XMLParsedAsHTMLWarning
from math import ceil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


########################################################
# Constants
########################################################
if len(sys.argv) == 2:
	FILE_NAME = sys.argv[1]
	ABSOLUTE_FILE_PATH = os.getcwd()
elif len(sys.argv) == 1:
	ABSOLUTE_FILE_PATH = os.getcwd()
	FILE_NAME = "examples/test.svg"
else:
	raise Exception("Usage: python svg2gif.py <SVG_file>")
DEFAULT_SCREENSHOTS_PER_SECOND = 11  # Minimum capture rate fallback

########################################################
# Helper functions
########################################################

def _clean_time_element(time):
	"""
	takes time paramter in an svg and converts it to seconds

	Args:
		time (str): time format from SVG i.e. 10s = 10 seconds
	Returns:
		(float): cleaned time
	"""
	if not isinstance(time, str):
		raise TypeError("Expected time format as string")

	match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?\s*", time)
	if not match:
		raise ValueError(f"Time '{time}' was not in a supported format")

	value = float(match.group(1))
	unit = (match.group(2) or "s").lower()

	if unit in {"s", "sec", "secs", "second", "seconds"}:
		return value
	if unit in {"ms", "millisecond", "milliseconds"}:
		return value / 1000
	if unit in {"m", "min", "mins", "minute", "minutes"}:
		return value * 60
	raise ValueError(f"Time unit '{unit}' was not recognized")


_ANIMATION_TAGS = ("animate", "animateMotion", "animateTransform", "animateColor")
_ANIMATION_DECLARATION_RE = re.compile(r"animation\s*:\s*([^;{}]+)(?:;|$)", re.IGNORECASE)
_ANIMATION_DURATION_RE = re.compile(r"animation-duration\s*:\s*([^;{}]+)(?:;|$)", re.IGNORECASE)
_ANIMATION_DELAY_RE = re.compile(r"animation-delay\s*:\s*([^;{}]+)(?:;|$)", re.IGNORECASE)
_TIME_VALUE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(ms|s|m)\b", re.IGNORECASE)
BLANK_FRAME_TOLERANCE = 2


def _parse_animation_value_list(value_list):
	values = []
	for token in value_list.split(","):
		token = token.strip()
		if not token:
			continue
		values.append(_clean_time_element(token))
	return values


def _parse_animation_shorthand(value):
	durations = []
	for chunk in value.split(","):
		time_values = _TIME_VALUE_RE.findall(chunk)
		if not time_values:
			continue

		duration = _clean_time_element(f"{time_values[0][0]}{time_values[0][1]}")
		delay = 0
		if len(time_values) > 1:
			delay = _clean_time_element(f"{time_values[1][0]}{time_values[1][1]}")
		durations.append(duration + delay)
	return durations


def _extract_css_animation_durations(css_text):
	durations = []
	duration_only_values = []
	delay_values = []

	for match in _ANIMATION_DECLARATION_RE.finditer(css_text):
		durations.extend(_parse_animation_shorthand(match.group(1)))

	for match in _ANIMATION_DURATION_RE.finditer(css_text):
		duration_only_values.extend(_parse_animation_value_list(match.group(1)))

	for match in _ANIMATION_DELAY_RE.finditer(css_text):
		delay_values.extend(_parse_animation_value_list(match.group(1)))

	if duration_only_values:
		durations.extend(duration_only_values)
		if delay_values:
			durations.append(max(duration_only_values) + max(delay_values))
	elif delay_values and not durations:
		durations.extend(delay_values)

	return durations


def _build_svg_soup(svg_text):
	for parser in ("xml", "html.parser"):
		try:
			return BeautifulSoup(svg_text, features=parser)
		except FeatureNotFound:
			continue
	raise RuntimeError("BeautifulSoup could not find a working parser. Install lxml to enable XML parsing.")


def _collect_animation_durations(soup):
	durations = []
	for tag_name in _ANIMATION_TAGS:
		for element in soup.find_all(tag_name):
			dur = element.get("dur")
			if not dur:
				continue
			try:
				duration_seconds = _clean_time_element(dur)
			except ValueError:
				continue

			repeat_count = element.get("repeatcount")
			if repeat_count and repeat_count.lower() != "indefinite":
				try:
					duration_seconds *= float(repeat_count)
				except ValueError:
					pass
			durations.append(duration_seconds)

	style_text = []
	for style_tag in soup.find_all("style"):
		text = style_tag.get_text()
		if text:
			style_text.append(text)

	for element in soup.find_all(style=True):
		style_text.append(element["style"])

	for text in style_text:
		durations.extend(_extract_css_animation_durations(text))

	return durations


def _count_declared_frames(soup):
	"""
	Counts how many SVG nodes use the 'frame' class (typical frame-by-frame export).

	Args:
		soup (BeautifulSoup): parsed SVG.
	Returns:
		(int): number of discrete frames declared in the SVG.
	"""
	return len(soup.select(".frame"))


def _compute_effective_screenshots(total_duration, use_tmp_path, frame_count):
	"""
	Determine how many screenshots to capture to cover the full animation.

	Args:
		total_duration (int): ceil'd animation duration in seconds.
		use_tmp_path (bool): whether the svg durations were doubled.
		frame_count (int): number of explicit frames found in the SVG.
	Returns:
		(int): screenshot count.
	"""
	effective_duration = total_duration * 2 if use_tmp_path else total_duration
	if effective_duration <= 0:
		effective_duration = 1

	minimum_frames = ceil(DEFAULT_SCREENSHOTS_PER_SECOND * effective_duration)

	if frame_count:
		minimum_frames = max(minimum_frames, frame_count)

	return minimum_frames, effective_duration


def _is_blank_frame(image_path):
	"""
	Detects nearly uniform screenshots that are effectively blank pages.

	Args:
		image_path (str): path to screenshot.
	Returns:
		(bool): True if the frame should be discarded.
	"""
	with Image.open(image_path) as image:
		extrema = image.convert("RGB").getextrema()

	return all((high - low) <= BLANK_FRAME_TOLERANCE for low, high in extrema)


def _filter_blank_frames(file_paths):
	"""
	Removes empty frames while preserving order.

	Args:
		file_paths (List[str]): ordered screenshot paths.
	Returns:
		(List[str]): filtered screenshot paths.
	"""
	filtered_files = []
	for path in file_paths:
		if _is_blank_frame(path):
			continue
		filtered_files.append(path)
	return filtered_files


########################################################
# Beautiful soup parse to find total duration of SVG
########################################################

with open(FILE_NAME, "r", encoding="utf-8") as svg_source:
	svg_text = svg_source.read()

soup = _build_svg_soup(svg_text)
animation_timers = _collect_animation_durations(soup)
frame_count = _count_declared_frames(soup)

if not animation_timers:
	raise ValueError(
		f"Could not find any animation durations in '{FILE_NAME}'. "
		"Ensure the SVG contains <animate> tags or CSS animations."
	)

total_time_animated = ceil(max(animation_timers)) 


########################################################
#                Create Temporary File
# Useful to provide more files to smooth the gif
########################################################
USE_TMP_PATH = False

if total_time_animated < 20:
	USE_TMP_PATH = True 

	file_text = svg_text
	for animation_timer in animation_timers:
		if animation_timer % 1 == 0:
			file_text = file_text.replace(f"{int(animation_timer)}s",f"{int(animation_timer * 2)}s")
		else:
			file_text = file_text.replace(f"{animation_timer}s",f"{animation_timer * 2}s")

	with open(f"TMP_{FILE_NAME}", "w") as text_file:
		print(file_text, file=text_file)


########################################################
# Use Selenium to play the SVG file to play the file
# and capture screenshots of the SVG

## currently Magick doesn't support this conversion:
## https://github.com/ImageMagick/ImageMagick/discussions/2391
########################################################
if not os.path.exists("_screenshots"):
	os.makedirs("_screenshots")


driver = webdriver.Firefox()

# In Selenium you need the prefix file:/// to open a local file
if USE_TMP_PATH:
	driver.get(f"file:///{ABSOLUTE_FILE_PATH}/TMP_{FILE_NAME}")
else:
	driver.get(f"file:///{ABSOLUTE_FILE_PATH}/{FILE_NAME}")

total_screenshots, effective_duration = _compute_effective_screenshots(total_time_animated, USE_TMP_PATH, frame_count)
capture_interval = effective_duration / total_screenshots if total_screenshots else 0
start_time = time.perf_counter()
for i in range(total_screenshots):
	screenshot_path = f"_screenshots/{i}.png"
	try:
		driver.find_element(By.TAG_NAME, "svg").screenshot(screenshot_path)
	except (NoSuchElementException, StaleElementReferenceException):
		driver.get_screenshot_as_file(screenshot_path)
	if capture_interval <= 0 or i == total_screenshots - 1:
		continue
	target_elapsed = (i + 1) * capture_interval
	elapsed = time.perf_counter() - start_time
	sleep_time = target_elapsed - elapsed
	if sleep_time > 0:
		time.sleep(sleep_time)

driver.close()
driver.quit()


########################################################
# use PIL to combine the save PNG's to a GIF
########################################################


# filepaths
fp_in = "_screenshots/*.png"
fp_out = f'{FILE_NAME.replace(".svg",".gif")}'

# use exit stack to automatically close opened images
with contextlib.ExitStack() as stack:

    files = glob.glob(fp_in)
    files.sort(key=lambda f: int(re.sub('\D', '', f))) 
    files = _filter_blank_frames(files)

    if not files:
        raise RuntimeError("All captured frames were blank. Try increasing the animation duration or check the SVG playback.")

    # lazily load images
    imgs = (stack.enter_context(Image.open(f))
            for f in files)

    img = next(imgs)


    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
    img.save(fp=fp_out, format='GIF', append_images=imgs,
             save_all=True,
             duration=(total_time_animated * 1000)/len(files) - 20, # the math here feels off because the resulting gif is too slow thus -10 is implemented
              loop=0)


########################################################
# Remove temporary directories
########################################################
if USE_TMP_PATH:
	os.remove(f"TMP_{FILE_NAME}")
shutil.rmtree("_screenshots")

# Optional delete of selenium logs if present
if os.path.exists("geckodriver.log"):
	os.remove("geckodriver.log")
