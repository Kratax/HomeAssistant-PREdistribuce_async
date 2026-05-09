# PRE Distribuce - Home Assistant Sensor

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

This sensor is scraping data from https://www.predistribuce.cz/cs/potrebuji-zaridit/zakaznici/stav-hdo/. Put id of receiver command (see contract with PRE CZ or your energy meter) in configuration.yaml

Adjusted based on https://github.com/slesinger/homeassistant-predistribuce
Created with Gemini to comply with the new async approach in HA and several other changes

This sensor always show
- current state of HDO
- sensor to be used in apex charts
- time to reach low tariff or time needed to wait for low tarrif

optionally also
-  if a an applience (e.g. washing machine) can be run now to finish under low tariff


### Installation

Copy this folder to `<config_dir>/custom_components/predistribuce_async/`.

Add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry for showing current HDO state and HTML for rendering a time schedule
binary_sensor:
  platform: predistribuce_async
  name: nocni proud
  receiver_command_id: 605
```

```yaml
# entry as above + extra binary sensors that show if a an applience (e.g. washing machine) can be run now to finish under low tariff
binary_sensor:
  - platform: predistribuce_async
    receiver_command_id: 605
    periods:
      - name: HDO Pračka
        minutes: 30
      - name: HDO Myčka
        minutes: 150
```

```yaml

sensor:
  - platform: predistribuce_async
    receiver_command_id: 605



```
For creation of apex chart use:
```yaml
type: custom:apexcharts-card
header:
  show: true
  title: HDO Rozvrh (Dnes)
  show_states: false
  colorize_states: true
graph_span: 24h
span:
  start: day
apex_config:
  chart:
    height: 140px
    type: area
    toolbar:
      show: false
  yaxis:
    min: 0
    max: 1
    tickAmount: 1
    labels:
      show: true
      style:
        fontSize: 10px
  xaxis:
    type: datetime
    labels:
      show: true
      format: HH
      rotate: 0
      style:
        fontSize: 10px
    tickAmount: 8
  grid:
    show: true
    strokeDashArray: 3
  dataLabels:
    enabled: false
  stroke:
    width: 2
series:
  - entity: sensor.hdo_cas_do_zmeny_tarifu
    name: Tarif
    curve: stepline
    type: area
    color: "#4caf50"
    data_generator: |
      return entity.attributes.schedule.map((entry) => {
        const now = new Date();
        const [hours, minutes] = entry.start.split(':');
        const timestamp = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hours, minutes).getTime();
        return [timestamp, entry.tariff === 'N' ? 1 : 0];
      });

```


