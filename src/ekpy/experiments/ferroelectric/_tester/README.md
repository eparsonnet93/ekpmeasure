# Usage

Take Ferroelectric loops using a DAQ (part: USB-1208HS) and preamp (part: SRS560 preamp). Currently, the app does not control the preamp, and settings must be set manually. Recommended base settings (optimization may be required) are >1e3 amplification and and band-pass filter from [\~30Hz,300kHz]

To configure the circuit, follow the diagram below:

![Circuit Diagram](imgs/circuit.png)

Further usage details can be found in the notebook. 

# Installation

1. You will need to install the driver software for the USB-1208HS daq, which can be found [here](https://www.mccdaq.com/Software-Downloads.aspx)

2. Navigate to the directory where you wish install the experimental control notebook and run

```bash
python -m ekpmeasure.experiments.ferroelectric._tester --name <notebook_name>
```

This will create a notebook with name `<notebook_name>` which can be used to run the ferroelectric switching experiments.