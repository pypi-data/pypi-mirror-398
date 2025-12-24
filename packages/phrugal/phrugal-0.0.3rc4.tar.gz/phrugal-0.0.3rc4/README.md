# phrugal

save money when printing photos

## Use case

You like to take pictures, but the prints that you get at the drug store are kind of big?
Would you like to print several images per print? Phrugal can do this for you in a
hopefully aesthetically pleasing way. Plus, phrugal adds a border with meta information
according to user configuration.

This is how an example output might look like:
![example-out.jpg](doc%2Fimg%2Fexample-out.jpg)

## Usage

🚧 These features are not yet implemented.

In order to use phrugal, first install it:

```bash
pip install phrugal
```

Then, refer to the CLI help for usage notes:

```bash
phrugal --help
```

🚧 TODO: This section needs expansion

## Configuration

🚧 TODO: describe after implementation.

## Limitations and Scope

When creating a "composition" of several images, the user needs to tell phrugal
a desired aspect ratio. Phrugal currently does not attempt to optimize which images
to combine on one page. Instead, it adds padding to all images until they
have the desired aspect ratio.

As another limitation, phrugal does offer all possible EXIF fields as metadata.
It does not support [XMP tags](https://exiftool.org/TagNames/XMP.html) currently.


### Not in scope

Phrugal will probably never:

* attempt to modify the actual look of the input image, e.g. do a black and white 
  conversion or apply some filter. I believe there are better tools for that.

## References and acknowledgements

Phrugal makes heavy use of:

- [Pillow](https://pillow.readthedocs.io/en/stable/)
- [exifread](https://github.com/ianare/exif-py)
- [geopy](https://github.com/geopy/geopy) (as an interface with Nominatim to translate GPS
  coordinates into location names)
