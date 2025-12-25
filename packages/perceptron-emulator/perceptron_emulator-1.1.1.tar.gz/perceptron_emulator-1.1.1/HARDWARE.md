# Building a Physical Perceptron Circuit

This document provides instructions for building a physical hardware version of the perceptron emulator.

## Overview

The physical perceptron uses analog electronics to implement the weighted sum calculation: **output = Σ(input × weight) + bias**

## Components Required

### Main Components
- **16× Toggle Switches** (SPST) - Binary inputs
- **16× LEDs** (Red, 5mm) - Input indicators
- **16× Resistors** (220Ω) - LED current limiting
- **17× Potentiometers** (10kΩ, linear taper) - 16 weights + 1 bias
- **1× Analog Panel Meter** (0-100µA or similar) - Output display
- **16× Operational Amplifiers** (e.g., LM324 quad op-amp × 4)
- **1× Summing Amplifier** (op-amp for final sum)
- **Power Supply** (±12V dual rail)
- **Breadboard or PCB**
- **Wire** (22-24 AWG)
- **Knobs** for potentiometers

### Optional Components
- **Enclosure** (project box)
- **Panel mount components** for professional look
- **Voltage regulator** (7812/7912) if using higher voltage supply

## Circuit Description

### Input Stage (per input)
Each of the 16 inputs consists of:
1. **Toggle Switch**: Provides binary input (0V or +5V)
2. **LED Indicator**: Shows switch state
3. **Weight Potentiometer**: Variable resistor (0-10kΩ)
4. **Scaling Resistor**: Converts voltage to current

### Weight Multiplication
Each input is multiplied by its weight using a voltage divider:
- When switch is ON (+5V), current flows through the potentiometer
- Potentiometer position determines the weight (-30 to +30 range)
- Center position = 0 (no contribution)

### Summing Stage
All weighted inputs feed into a summing amplifier:
- Uses an operational amplifier in inverting configuration
- Sums all input currents
- Output voltage proportional to weighted sum

### Bias Stage
- Additional potentiometer adds/subtracts a constant offset
- Allows shifting the output range

### Output Stage
- Analog meter displays the final sum
- Can be calibrated to show -100 to +100 range

## Schematic

```
Input 1:
[Switch]---[LED+R]---[Pot (Weight)]---+
                                      |
Input 2:                              |
[Switch]---[LED+R]---[Pot (Weight)]---+---> [Summing Amp] ---> [Meter]
                                      |              ^
...                                   |              |
                                      |         [Bias Pot]
Input 16:                             |
[Switch]---[LED+R]---[Pot (Weight)]---+
```

## Detailed Wiring

### Per Input Channel (repeat 16 times)

1. **Switch and LED**:
   ```
   +5V ----[Switch]----+----[LED]----[220Ω]---- GND
                       |
                       +---- To Weight Circuit
   ```

2. **Weight Circuit**:
   ```
   Input ----[10kΩ Pot]----[10kΩ Resistor]---- Summing Junction
   ```

### Summing Amplifier

```
All Inputs ----[Resistors]----+---- [-] Op-Amp
                              |         |
                              |      [Feedback R]
                              |         |
                         [Bias Pot]  Output ---> Meter
                              |
                             GND
```

## Assembly Instructions

### Step 1: Power Supply
1. Build or obtain ±12V dual rail power supply
2. Add decoupling capacitors (0.1µF) near each IC
3. Test voltage levels before connecting components

### Step 2: Input Switches and LEDs
1. Mount 16 toggle switches in 4×4 grid
2. Wire each switch to +5V supply
3. Connect LED in series with 220Ω resistor to ground
4. Test each switch/LED pair

### Step 3: Weight Potentiometers
1. Mount 16 potentiometers in 4×4 grid (matching switches)
2. Connect each pot wiper to a scaling resistor
3. Connect pot ends to ±5V for bipolar range
4. Add knobs with position markers

### Step 4: Summing Circuit
1. Build summing amplifier on breadboard/PCB
2. Connect all 16 weight outputs to summing junction
3. Add bias potentiometer input
4. Test with multimeter

### Step 5: Output Meter
1. Connect analog meter to summing amp output
2. Add series resistor to limit current if needed
3. Calibrate meter scale (mark -100, 0, +100)

### Step 6: Enclosure
1. Mount all components in project box
2. Label inputs, weights, and output
3. Add power switch and indicator LED

## Calibration

1. **Zero Calibration**:
   - Set all switches OFF
   - Adjust bias to center meter at zero

2. **Weight Calibration**:
   - Turn one switch ON, set weight pot to max
   - Adjust scaling to get desired deflection
   - Repeat for all channels

3. **Range Calibration**:
   - Set all switches ON, all weights to max
   - Verify meter shows +100
   - Set all weights to min, verify -100

## Power Requirements

- **Voltage**: ±12V DC (dual rail)
- **Current**: ~500mA (depends on meter and number of LEDs)
- **Total Power**: ~12W

## Safety Notes

- Use appropriate fuses on power supply
- Ensure proper grounding
- Keep voltages within component ratings
- Use heat sinks on voltage regulators if needed

## Alternative Designs

### Digital Version
- Replace analog multipliers with DACs
- Use microcontroller for calculation
- Keep analog meter for retro aesthetic

### Simplified Version
- Reduce to 2×2 or 3×3 grid
- Use single supply (+5V only)
- Simpler summing circuit

## Resources

- Op-amp datasheets: [LM324](https://www.ti.com/product/LM324)
- Analog meter selection guide
- PCB layout software (KiCad, EasyEDA)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Meter doesn't move | Check summing amp output, verify power |
| LEDs don't light | Check resistor values, switch connections |
| Weights have no effect | Verify pot connections, check scaling resistors |
| Output always maxed | Reduce feedback resistor in summing amp |

## Photos and Diagrams

See the reference image provided - this shows a professional implementation with:
- 4×4 grid of input switches
- 4×4 grid of weight knobs
- Analog panel meter
- Clean panel layout
