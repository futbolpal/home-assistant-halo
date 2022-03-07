[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

# Home Assistant Custom Component for Halo

This custom component for Halo/Avi-on lights manages [HALO HOME HLB6 Series 6 in. 2700K-5000K Tunable CCT Smart Integrated LED White Recessed Downlight, Round Trim](https://www.homedepot.com/p/HLB6-Series-6-in-2700K-5000K-Tunable-CCT-Smart-Integrated-LED-White-Recessed-Downlight-Round-Trim-1-Qty-HLB6099BLE40AWH/314912175) lights.

Instead of communicating through Bluetooth, this integration relies on the [Halo Access Bridge](https://www.amazon.com/Bluetooth-Enabled-Internet-Access-Halo/dp/B079TBGYZ7).

## Avi-on API

[Postman](https://documenter.getpostman.com/view/6065583/RzfmEmUY#61a21dee-d09d-48e3-b5c1-f7772e2e62a2)

## Alternatives

[Home Assistant Core Component](https://github.com/home-assistant/core/tree/dev/homeassistant/components/avion)

This core component uses the [Avi-on python library](https://github.com/mjg59/python-avion) which is based on Bluetooth communication.

## Installing
1. Clone this repo.
2. Copy the contents of `custom_components/` to your custom components folder (e.g. `/config/custom_components/`).
3. Update your `configuration.yaml`:

```
halo:
  username: <your Halo app login email>
  password: <your Halo app login password>
```
4. Go to Configuration and restart HA
