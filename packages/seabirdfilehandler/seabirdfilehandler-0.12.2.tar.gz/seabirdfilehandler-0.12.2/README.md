# Intro

This is a library for handling the different SeaBird file types. Each file is
meant to be represented by one object that stores all of its information in a
structured way. Through the grouping of different data types, more complex
calculations, visualisations and output forms are possible inside of those
objects.

By being able to parse edited data and metadata back to the original file
format, this package can be used to process data using custom ideas, while
staying compatible to the original SeaBird software packages. This way, one can
create new workflows that interchangeably use old and new processing modules.
One implementation of this idea is the [ctd-processing python package](https://ctd-software.pages.iow.de/processing/), also developed at the IOW.

The structured metadata does provide the possibility to leverage the vast
amounts of information stored inside the extensive metadata header. Sensor data
and processing information are readily available in intuitive dictionaries.

## Development roadmap

### misc improvements

- refactor processing module handling
- extend individual parameter information
- handle duplicate input columns

### visualisation

- write an intuitive visualisation module
