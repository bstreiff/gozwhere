# gozwhere

A script to build a connection diagram between A/V devices.

By identifying [what _gozinta_ and what _gozouta_](https://www.prosoundweb.com/channels/recording/in_the_studio_glossary_of_common_cable_connections/),
we can graph what _gozwhere_.

Loosely inspired by other connection diagrams I've seen around Twitch, such as [pidgezero_one](http://pidgezero.one/)'s [console graph](http://pidgezero.one/setup.html).

## Requirements

Requires graphviz.

## Syntax

```yaml
tv:
    name: My Awesome Television
    # image is optional
    image: tv.png
    # bgcolor is optional; if not given, 'name' is hashed to determine color
    bgcolor: #aabbcc
    # gozintas define your inputs. It's recommended to denote these with
    # anchors, so they can be targets of gozoutas (defined later)
    gozintas:
        - &tv_hdmi1 { name: 'HDMI1' }
        - &tv_hdmi2 { name: 'HDMI2' }

receiver:
    name: My Limited Receiver
    image: receiver.png
    gozintas:
        - &rec_av1 { name: 'A/V 1 In' }
        - &rec_av2 { name: 'A/V 2 In' }
        - &rec_hdmi { name: 'HDMI In' }
    # gozoutas define outputs. The 'gozta' parameter indicates what this is
    # connected to; it can be a single alias, or a list of aliases (for
    # example, if you have a splitter with multiple outputs).
    gozoutas:
        - { name: 'HDMI Out', gozta: *tv_hdmi }
```
