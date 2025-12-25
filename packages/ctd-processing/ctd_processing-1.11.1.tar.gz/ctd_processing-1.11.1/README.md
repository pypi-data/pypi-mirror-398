# Intro

This is a custom software suite to process Sea-Bird CTD data. It fully supports running Sea-Birds original processing modules, but also custom ones, written in python or independent executables, that adhere to the command line interface of the original Sea-Bird modules. They can interchangeably be used as part of 'processing procedures', workflows of multiple processing steps in sequence on one or more data file. These procedures are defined by .toml configuration files.

# Current development goals

- Developing new custom processing modules

  - Improving AlignCTD

  - A module to retrieve start and end of a cast (cast_borders)

  - A new bottle handling module, that creates btl files after all processing steps

- Writing an entry point to the different functionalities

- The replacement of Sea-Birds executables by their python packages
