# SIIT (Simple Image Interlacement Tool)

A simple python CLI tool used to interleave images by rows or columns, intended for use in the creation of structures and weave files for the TC2 Loom.

The goal for the program is to create an new method of constructing multi-weft structures for the TC2. I struggle to comprehend the existing methods of manual construction in Photoshop, and built a tool to construct these in the way my brain can conceptualize them. This is a tool that essentially allows you to add interlacement steps one by one. Examples provided (see wiki, in progress)

This is not intended to be an all in one design tool nor to replace Photoshop entirely! Simply to help with the creation of multi-weft structures (weft backed weaves, supplemental weft structures like overshot/summer & winter). It also has great applications for the creation of doubleweave structures.

## Installation

Best install method is via pip, standalone executables in releases do work, but function much slower!

<!-- ### Option 1: Standalone Executable (Easiest for Non-Technical Users)

**No Python installation required!**

1. Go to the [Latest Release](../../releases/latest) page
2. Download the executable for your operating system:
   - **macOS (Apple Silicon / M1/M2/M3)**: `image-interlacement` (arm64)
   - **macOS (Intel)**: `image-interlacement` (x86_64)
   - **Linux**: `image-interlacement` (x86_64)
   - **Windows**: `image-interlacement.exe`
3. On macOS/Linux, make it executable and run:
   ```bash
   chmod +x image-interlacement
   ./image-interlacement --help
   ```
4. On Windows, simply double-click or run from Command Prompt:
   ```cmd
   image-interlacement.exe --help
   ``` -->

### Python Package via pip

**Requires Python 3.8 or higher and pip**

Install from PyPI:
```bash
pip install image-interlacement
```

Then run from anywhere:
```bash
image-interlacement --help
```

Or clone and install from source:
```bash
git clone https://github.com/rooomba/image-interlacement
cd image-interlacement
pip install -e .
image-interlacement --help
```
### From standalone binary
Download executable from releases page, then run via CLI. Example
```bash
./[path to image-interlacement-binary] composite image1.png image2.png --output output.png --tile-mode lcm --mode rows
```

**NOTE FOR MACOS USERS:** Will trigger a security quarantine on first run, when initial error appears, do not move to trash, then navigate to System Settings > Privacy & Security > Security (scroll to bottom) and allow program to run.


<!-- ### Option 3: Run from Source (For Development)

If you're modifying the code:

1. Clone the repository:
```bash
git clone <repository-url>
cd image-interlacement-program
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the program:
```bash
python src/main.py --help
``` -->

## Usage


### Basic Command format:
```bash
image-interlacement composite [image1] [image2] ([image3] [image4]...) --output [outputImage] --mode [rows/columns] --tile-mode [max/lcm] --stride [pattern]
```

**Image formats accepted:** `.jpg` `.png` `.bmp` (and more, but these are the only relevant ones to the usecase!)

### Basic Behavior:
The the program will interleave the two provided images (starting from the bottom left, but test, this directional function is a little iffy sometimes), alternating rows/columns from the source images (starting with `image1`). 

For example: if two images are being interlaced by rows, the program takes row 0 of `image1` for row 0 of `outputImage`, then takes row 0 of `image2` for row 1 of `outputImage`. Row 1 of `image1` becomes row 2 of `outputImage`, row 1 of `image2` becomes row 3, etc etc etc. This behavior is the same regardless of the number of images you use, the process will always proceed in order of the images provided in the command.

### `image1, image2 etc...`
Replace with paths to images you would like to interleave.

**Image formats accepted:** `.jpg` `.png` `.bmp` (and more, but these are the only relevant ones to the usecase!)

### A note on multiple (2+) image interleaveing:

Currently, the program allows the user to imput up to 6 images to be interleaeved at once. Support for more is theoretically possible, but memory usage is a concern. An in progress stride function will functionally allow for compositing of much larger numbers of images. You can test it out on the Stride branch of the project.

The usescases for it are likely limited, but you are able to use the same input image multiple times in the same command. It will treat them like separate files. If you were to run the command with `image1.png image2.png image2.png` the output image would consist of row one from `image1` and then row 1 from `image2` twice, then back to `image1` row 2 for the next row.

### `--output`
Replace `[outputImage]` with the file path where you'd like the program to output the image. Must include a file name and format. Example: `--output ./testimages/structure1.png`

### `--mode`
Fairly self explanatory, `columns` will interleave the images from left to right by columns, `rows` will interleave the images from top to bottom by rows. Required, will throw an error if left out.

### `--tile-mode`(optional)
the `--tile-mode` option currently has two sub-options, `max` and `lcm`. If the option is not used, the behavior defaults to `max`.

`max`: program detects largest image, automatically tiles all smaller images to match the size of the larger one. It does not pay any regard to the bounds of the smaller images. This is important to remember when you are attempting to create composites of structures with different repeat lengths! For instance: 5-end satin and a 7-end satin composited using `max` tiling mode will have unexpected results!

`lcm`: takes the images, and finds the LCM (least common multiple) of each dimension, then tiles all images to match. This allows you to composite structures with different repeat sizes and maintain those repeats. **Be cautious when using this feature** it may behave in unexpected ways, I have tested it and to the best of my knowledge it works as I intend, but, weave your own swatches to be sure!!

### `--stride` (optional)
This experimenal feature allows you to combine structures at different ratios, you can define a pattern that you'd like the program to follow when combining images. Simply list the number of rows/columns you'd like the program to take from each image in the same sequence you provided the first section of the command. For example

```bash
image-interlacement composite image1.png image2.png. image3.png --output out.png --mode columns --stride 1 2 2
```
Will output an image consisting of (left to right) row 1 from image1, row 1 from image2, row 2 from image2, row 1 from image3, row 2 from image3, and then row 2 from image1, etc. It's a bit hard to explain in words. Behavior with this function is tested with `--tile-mode lcm` and appears to work as expected. Swatch, test before committing to huge project, etc.

When not included, defaults to the standard behavior, 1 row from each image provided. 

### Additonal tools/options:

**Solid Color instead of image:**
The program by default includes the option to replace either one of the input images with a solid white or black. This is most useful when creating doubleweave structures. Simply replace *either*  of the input images with `white` or `black`, the command will output an error if you replace both.

Example:
```bash
image-interlacement composite image1.png white output.png --mode columns
```

<!-- #### Create a Row-based Composite

Alternate entire rows from two images:

```bash
python src/main.py composite image1.png image2.png output.png --mode rows
```

Pattern: Output rows are interleaved - Row 0 from image1, Row 1 from image2, Row 2 from image1, etc.
The output height will be **2x the input height**.

You can also use solid colors instead of image files:

```bash
python src/main.py composite image1.png white output.png --mode rows
python src/main.py composite image1.png black output.png --mode rows
```

#### Create a Column-based Composite

Alternate entire columns from two images:

```bash
python src/main.py composite image1.png image2.png output.png --mode columns
```

Pattern: Output columns are interleaved - Column 0 from image1, Column 1 from image2, Column 2 from image1, etc.
The output width will be **2x the input width**. -->

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Pillow | >=9.0.0 | Image processing and manipulation |
| NumPy | >=1.21.0 | Efficient array operations for pixel manipulation |


<!-- ### Running the Program

```bash
python src/main.py --help
```

View help for specific commands:

```bash
python src/main.py composite --help
```

## Quick Start

1. **Clone/navigate to repository**:
```bash
git clone https://github.com/rooomba/image-interlacement
cd image-interlacement-program
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Create a composite**:
```bash
python src/main.py composite photo1.jpg photo2.jpg output.jpg --mode rows
``` -->

## Troubleshooting

### Unsupported Image Format
- **Error**: "Cannot identify image file"
- **Solution**: Convert images to PNG, JPG, or BMP format. Use an image converter tool.

## Future additions
- Support for stride when it comes to the program, to interleave 2 rows from one image, 1 from another, etc.
- GUI functionality for those less comfortable with a CLI.

## Support

For issues or questions, please open an issue in the repository or shoot me a DM/email if you have my contact!

## AI Use

A large majority of this program was written with heavy reliance on GitHub's Copilot AI tool. I believe it is important to disclose AI use when it is present for transparency in my process.

---

**Last Updated**: December 21, 2025  
**Version**: 1.0.0
