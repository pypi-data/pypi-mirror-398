# videolab

A CLI for video processing.

## Installation

You can install videolab from source.

1.  Clone the repository:

    ```bash
    git clone https://github.com/kianmeng/videolab.git
    cd videolab
    ```

2.  Create a virtual environment and install the package:
    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -e .
    ```

## Usage

Once installed, you can use the `videolab` command.

To see the help message:

```bash
videolab --help
```

<!--help !-->

```console
usage: videolab [-h] [-V] [-v] {env,scrub,watermark} ...

A console program to manipulate videos.

website: https://github.com/kianmeng/videolab
changelog: https://github.com/kianmeng/videolab/blob/master/CHANGELOG.md
issues: https://github.com/kianmeng/videolab/issues

positional arguments:
  {env,scrub,watermark}
                        sub-command help
    env                 Show environment information
    scrub               Remove all metadata
    watermark           Add a watermark to a video.

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -v, --verbose         Enable verbose logging
```

<!--help !-->

### videolab env

```console
videolab env -h
```

<!--help-env !-->

```console
usage: videolab env [-h]

options:
  -h, --help  show this help message and exit
```

<!--help-env !-->

### videolab scrub

```console
videolab scrub -h
```

<!--help-scrub !-->

```console
usage: videolab scrub [-h] [--no-audio] input_file [output_file]

Removes all container-level and stream-level metadata from a video file by
remuxing it

positional arguments:
  input_file   Path to the input video file
  output_file  Path to save the scrubbed video file, defaults:
               '<input_file>_scrubbed.<ext>'

options:
  -h, --help   show this help message and exit
  --no-audio   Remove the audio from the video file
```

<!--help-scrub !-->

### videolab watermark

```console
videolab watermark -h
```

<!--help-watermark !-->

```console
usage: videolab watermark [-h] --text TEXT [--font-size FONT_SIZE]
                          [--font-color FONT_COLOR]
                          [--position {top-left,top-right,bottom-left,bottom-right,center}]
                          [--margin MARGIN]
                          input_file [output_file]

Adds a watermark to a video file.

positional arguments:
  input_file            Path to the input video file
  output_file           Path to save the watermarked video file, defaults:
                        '<input_file>_watermarked.<ext>'

options:
  -h, --help            show this help message and exit
  --text TEXT           The text for the watermark
  --font-size FONT_SIZE
                        Font size for the watermark text. Defaults to 5% of
                        video height.
  --font-color FONT_COLOR
                        Font color in RGBA format (e.g., '255,255,255,128').
  --position {top-left,top-right,bottom-left,bottom-right,center}
                        Position of the watermark.
  --margin MARGIN       Margin from the edges of the video in pixels.
```

<!--help-watermark !-->

## Contributing

Contributions are welcome! Please see the [Contributing](CONTRIBUTING) file for details on how to set up your development environment and submit pull requests.

## License

This project is licensed under the GNU Affero General Public License v3.0 or later. See the [License](LICENSE) file for details.
