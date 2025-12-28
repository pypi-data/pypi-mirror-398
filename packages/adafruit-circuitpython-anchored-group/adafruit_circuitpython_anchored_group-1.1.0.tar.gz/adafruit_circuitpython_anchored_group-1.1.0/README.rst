Introduction
============


.. image:: https://readthedocs.org/projects/adafruit-circuitpython-anchored-group/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/anchored_group/en/latest/
    :alt: Documentation Status


.. image:: https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_Bundle/main/badges/adafruit_discord.svg
    :target: https://adafru.it/discord
    :alt: Discord


.. image:: https://github.com/adafruit/Adafruit_CircuitPython_Anchored_Group/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_Anchored_Group/actions
    :alt: Build Status


.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Code Style: Ruff

A displayio Group that supports placement by anchor_point and anchored_position properties


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_
or individual libraries can be installed using
`circup <https://github.com/adafruit/circup>`_.



Installing from PyPI
=====================

On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-anchored-group/>`_.
To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-anchored-group

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-anchored-group

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .venv
    source .env/bin/activate
    pip3 install adafruit-circuitpython-anchored-group

Installing to a Connected CircuitPython Device with Circup
==========================================================

Make sure that you have ``circup`` installed in your Python environment.
Install it with the following command if necessary:

.. code-block:: shell

    pip3 install circup

With ``circup`` installed and your CircuitPython device connected use the
following command to install:

.. code-block:: shell

    circup install adafruit_anchored_group

Or the following command to update an existing version:

.. code-block:: shell

    circup update

Usage Example
=============

.. code-block:: python

    from adafruit_anchored_group import AnchoredGroup
    from displayio import Group, Bitmap, TileGrid, Palette
    from adafruit_display_text.bitmap_label import Label
    import supervisor
    import terminalio

    display = supervisor.runtime.display

    main_group = Group()

    display.root_group = main_group

    anchored_group = AnchoredGroup()

    icon_bmp = Bitmap(30,30, 1)
    icon_palette = Palette(1)
    icon_palette[0] = 0xff00ff
    icon_tg = TileGrid(bitmap=icon_bmp, pixel_shader=icon_palette)

    lbl = Label(terminalio.FONT, text="Something")
    lbl.anchor_point = (0, 0.5)
    lbl.anchored_position = (icon_tg.x + (icon_tg.width * icon_tg.tile_width) + 6,
                             (icon_tg.y + (icon_tg.height * icon_tg.tile_height)) //2)


    anchored_group.append(icon_tg)
    anchored_group.append(lbl)
    print(f"group size: {anchored_group.size}")

    anchored_group.anchor_point = (1.0, 0)
    anchored_group.anchored_position = (display.width-4, 0)

    main_group.append(anchored_group)

    while True:
        pass


Documentation
=============
API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/anchored_group/en/latest/>`_.

For information on building library documentation, please check out
`this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_Anchored_Group/blob/HEAD/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
