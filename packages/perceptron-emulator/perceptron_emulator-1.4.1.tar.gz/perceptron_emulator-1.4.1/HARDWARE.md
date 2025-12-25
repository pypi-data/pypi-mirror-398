# Building a Physical Perceptron Circuit

This document provides comprehensive instructions for building a physical hardware version of the perceptron emulator using analog electronics.

## Overview

The physical perceptron implements the weighted sum calculation using operational amplifiers and analog components:

```
output = Σ(input_i × weight_i) + bias
```

**Difficulty**: Intermediate to Advanced  
**Estimated Build Time**: 20-40 hours  
**Estimated Cost**: $150-$300 USD

---

## Bill of Materials (BOM)

### Input Stage (per channel, ×16)
| Component | Specification | Quantity | Unit Price | Supplier |
|-----------|--------------|----------|------------|----------|
| Toggle Switch | SPDT, Panel Mount, 6A 125VAC | 16 | $1.50 | Mouser, Digikey |
| LED | 5mm Red, 20mA, 2V forward | 16 | $0.15 | Mouser, Digikey |
| Current Limiting Resistor | 220Ω, 1/4W, 5% | 16 | $0.05 | Mouser, Digikey |
| Scaling Resistor | 10kΩ, 1/4W, 1% (metal film) | 16 | $0.10 | Mouser, Digikey |

### Weight/Bias Controls
| Component | Specification | Quantity | Unit Price | Supplier |
|-----------|--------------|----------|------------|----------|
| Weight Potentiometers | 10kΩ, Linear Taper, Panel Mount | 16 | $2.50 | Bourns 3590S series |
| Bias Potentiometer | 10kΩ, Linear Taper, Panel Mount | 1 | $2.50 | Bourns 3590S series |
| Knobs | 1" diameter, pointer style | 17 | $1.20 | Davies 1510 series |

### Operational Amplifiers
| Component | Specification | Quantity | Unit Price | Supplier |
|-----------|--------------|----------|------------|----------|
| Quad Op-Amp IC | LM324N (DIP-14) or TL074 | 5 | $0.60 | Texas Instruments |
| IC Sockets | 14-pin DIP | 5 | $0.25 | Standard |
| Decoupling Capacitors | 0.1µF ceramic, 50V | 10 | $0.10 | Standard |

### Summing Amplifier Components
| Component | Specification | Quantity | Unit Price | Supplier |
|-----------|--------------|----------|------------|----------|
| Summing Resistors | 10kΩ, 1/4W, 1% (metal film) | 17 | $0.10 | Vishay Dale |
| Feedback Resistor | 100kΩ, 1/4W, 1% (metal film) | 1 | $0.10 | Vishay Dale |
| Offset Trim Pot | 10kΩ multi-turn trimmer | 1 | $1.50 | Bourns 3296 series |

### Output Stage
| Component | Specification | Quantity | Unit Price | Supplier |
|-----------|--------------|----------|------------|----------|
| Analog Panel Meter | 100µA, 2.5" square, -100 to +100 scale | 1 | $25-$45 | Simpson, Hoyt |
| Meter Shunt Resistor | Calculated based on meter | 1 | $0.50 | Metal film, 1% |

### Power Supply
| Component | Specification | Quantity | Unit Price | Supplier |
|-----------|--------------|----------|------------|----------|
| Dual Rail Power Supply | ±12V, 1A minimum | 1 | $20-$40 | Mean Well, Triad |
| Voltage Regulators | 7812 (+12V) and 7912 (-12V) | 2 | $0.75 | Standard |
| Filter Capacitors | 1000µF, 25V electrolytic | 4 | $0.50 | Standard |
| Ceramic Capacitors | 0.1µF, 50V | 4 | $0.10 | Standard |
| Power Switch | SPST, Panel Mount, 3A | 1 | $2.00 | Standard |
| Power LED | 5mm Green, with holder | 1 | $0.50 | Standard |
| Fuse Holder | Panel mount, 5×20mm | 1 | $1.50 | Littelfuse |
| Fuses | 1A slow-blow, 5×20mm | 2 | $0.50 | Littelfuse |

### Enclosure and Hardware
| Component | Specification | Quantity | Unit Price | Supplier |
|-----------|--------------|----------|------------|----------|
| Enclosure | 16"×12"×4" aluminum or steel | 1 | $40-$80 | Hammond, Bud |
| Front Panel | Aluminum, custom drilled | 1 | $20-$40 | SendCutSend, OSH Cut |
| Standoffs | M3×10mm, brass | 20 | $0.15 | Standard |
| Screws | M3×6mm, Phillips | 40 | $0.05 | Standard |
| Wire | 22 AWG stranded, multiple colors | 100ft | $15 | Standard |
| Heat Shrink Tubing | Assorted sizes | 1 set | $8 | Standard |

### PCB (Optional but Recommended)
| Component | Specification | Quantity | Unit Price | Supplier |
|-----------|--------------|----------|------------|----------|
| Custom PCB | 200mm × 150mm, 2-layer | 1 | $20-$50 | JLCPCB, PCBWay |

**Total Estimated Cost**: $200-$350 depending on component quality and sourcing

---

## Detailed Circuit Design

### Input Channel Architecture

Each of the 16 input channels consists of:

```
+5V ──┬──[Toggle Switch]──┬──[LED]──[220Ω]──GND
      │                   │
      │                   └──[10kΩ Pot]──[10kΩ R]──→ Summing Junction
      │
     GND
```

**Operation**:
- Switch ON: +5V applied to potentiometer
- Switch OFF: 0V applied
- Potentiometer wiper position determines weight (-30 to +30)
- Scaling resistor converts voltage to current

### Weight Multiplication Circuit

Using voltage-to-current conversion:

```
V_in (0 or +5V) → [Pot: 0-10kΩ] → [R_scale: 10kΩ] → I_out
```

**Current calculation**:
- I_out = V_in × (Pot_position / (Pot_value + R_scale))
- Range: 0 to ~250µA per channel

### Summing Amplifier Design

Classic inverting summing configuration:

```
Input 1 ──[10kΩ]──┐
Input 2 ──[10kΩ]──┤
    ...           ├──[─] Op-Amp ──[100kΩ Feedback]──→ Output
Input 16──[10kΩ]──┤      │
Bias ────[10kΩ]───┘      │
                        [+]
                         │
                        GND
```

**Gain calculation**:
- V_out = -(R_feedback / R_input) × Σ(V_inputs)
- Gain = -10 (inverts and amplifies)
- Output range: ±10V (scaled for meter)

### Output Meter Interface

```
Summing Amp Output ──[R_series]──[Meter: 100µA]──GND
                                      │
                                  [R_shunt]
```

**Meter calibration**:
- Full scale deflection: 100µA
- Internal resistance: ~1kΩ (typical)
- Series resistor: Calculated to limit current
- Shunt resistor: For range adjustment

---

## Step-by-Step Assembly

### Phase 1: Power Supply (2-4 hours)

1. **Voltage Regulator Circuit**:
   ```
   AC Input → [Transformer] → [Bridge Rectifier] → [Filter Caps] → [7812/7912] → ±12V
   ```

2. **Assembly**:
   - Mount voltage regulators on heat sinks
   - Add 1000µF filter capacitors (observe polarity!)
   - Add 0.1µF ceramic bypass capacitors
   - Test output voltages with multimeter
   - Install fuse holder and fuses

3. **Safety**:
   - Use insulated wire for AC connections
   - Ensure proper grounding
   - Test with load before connecting to circuit

### Phase 2: PCB Preparation (4-6 hours)

**Option A: Custom PCB** (Recommended)
1. Design PCB in KiCad or EasyEDA
2. Order from JLCPCB/PCBWay (5-10 day lead time)
3. Inspect for defects upon arrival
4. Apply solder mask if needed

**Option B: Perfboard/Stripboard**
1. Plan component layout on paper
2. Mark drilling points
3. Drill holes for components
4. Plan wire routing

### Phase 3: Input Stage Assembly (6-8 hours)

1. **Switch and LED Installation**:
   - Drill 16 holes in front panel (4×4 grid, 2" spacing)
   - Mount toggle switches
   - Install LED holders
   - Wire switches to +5V bus
   - Wire LEDs with 220Ω resistors to ground
   - Test each switch/LED pair

2. **Weight Potentiometer Installation**:
   - Drill 16 holes for potentiometers (aligned with switches)
   - Mount potentiometers
   - Install knobs with pointer indicators
   - Add scale markings (-30, 0, +30) around each knob

### Phase 4: Analog Processing (8-12 hours)

1. **Op-Amp Socket Installation**:
   - Install 5× 14-pin DIP sockets on PCB
   - Add decoupling capacitors (0.1µF) near each socket
   - Connect power rails (±12V)
   - Test power distribution

2. **Summing Resistor Network**:
   - Install 17× 10kΩ summing resistors
   - Install 100kΩ feedback resistor
   - Wire all inputs to summing junction
   - Add offset trim potentiometer

3. **Op-Amp Installation**:
   - Insert LM324 ICs into sockets (observe pin 1 orientation!)
   - Test each IC with multimeter
   - Verify ±12V on power pins

### Phase 5: Output Stage (2-3 hours)

1. **Meter Installation**:
   - Drill hole for meter in front panel
   - Mount meter securely
   - Calculate series resistor value:
     ```
     R_series = (V_max - V_meter) / I_meter
     ```
   - Install series and shunt resistors
   - Connect to summing amp output

2. **Calibration**:
   - Set all switches OFF, all pots to center
   - Adjust offset trim for zero reading
   - Turn one switch ON, pot to max
   - Verify positive deflection
   - Turn pot to min, verify negative deflection

### Phase 6: Final Assembly (4-6 hours)

1. **Enclosure Preparation**:
   - Drill holes for power switch, power LED, fuse holder
   - Mount all panel components
   - Install PCB on standoffs inside enclosure

2. **Wiring**:
   - Use color-coded wire (red: +V, black: GND, blue: signal)
   - Keep wires neat with cable ties
   - Use heat shrink on all connections
   - Double-check all connections before power-on

3. **Labeling**:
   - Print labels for inputs (1-16)
   - Label weight knobs
   - Add bias label
   - Create output scale (-100 to +100)

---

## Calibration Procedure

### 1. Zero Calibration
```
1. Power ON
2. All switches OFF
3. All weight pots to center (0)
4. Bias pot to center
5. Adjust offset trim for meter zero
```

### 2. Gain Calibration
```
1. Switch 1 ON, all others OFF
2. Weight 1 pot to maximum
3. Measure output voltage
4. Adjust feedback resistor if needed (target: ~10V)
5. Repeat for all 16 channels
```

### 3. Range Calibration
```
1. All switches ON
2. All weight pots to maximum
3. Meter should read +100 (or close)
4. Adjust meter shunt resistor if needed
5. Set all pots to minimum
6. Meter should read -100
```

### 4. Linearity Test
```
1. One switch ON
2. Sweep weight pot from min to max
3. Verify smooth, linear meter response
4. Repeat for all channels
```

---

## Troubleshooting Guide

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| No power LED | Fuse blown, power switch issue | Check fuse, test switch continuity |
| Meter pegged at max | Summing amp saturated | Reduce feedback resistor value |
| Meter doesn't move | No signal, broken connection | Check summing amp output with scope |
| Erratic readings | Noise, poor grounding | Add more bypass caps, improve ground |
| One channel dead | Bad switch, broken wire | Test switch, check continuity |
| Non-linear response | Wrong resistor values | Verify all resistors with multimeter |
| Oscillation | Unstable op-amp | Add compensation cap, check power |
| Offset drift | Temperature, poor components | Use 1% resistors, add trim pot |

---

## Advanced Modifications

### Digital Hybrid Version
- Replace potentiometers with digital potentiometers (MCP4131)
- Add Arduino/ESP32 for computer control
- Keep analog meter for aesthetic
- Add USB interface for software integration

### Precision Version
- Use precision op-amps (OPA2134, AD8620)
- 0.1% metal film resistors throughout
- Temperature-compensated design
- Shielded enclosure for noise reduction

### Portable Version
- Battery powered (9V or Li-ion)
- Smaller 2×2 or 3×3 grid
- LCD display instead of analog meter
- Compact enclosure

---

## Safety and Best Practices

### Electrical Safety
- ⚠️ **Always disconnect power before working on circuit**
- Use insulated tools
- Wear safety glasses when soldering
- Ensure proper ventilation
- Keep liquids away from electronics

### Component Handling
- Op-amps are static-sensitive - use ESD precautions
- Observe polarity on electrolytic capacitors
- Don't exceed component voltage/current ratings
- Use heat sinks on voltage regulators

### Testing
- Test each subsection before integration
- Use multimeter to verify voltages
- Oscilloscope helpful for debugging
- Document all modifications

---

## Resources and References

### Datasheets
- [LM324 Quad Op-Amp](https://www.ti.com/lit/ds/symlink/lm324.pdf)
- [7812/7912 Voltage Regulators](https://www.ti.com/lit/ds/symlink/lm7812.pdf)
- [Bourns 3590S Potentiometer](https://www.bourns.com/docs/Product-Datasheets/3590.pdf)

### Design Tools
- **KiCad**: Free PCB design software
- **LTspice**: Free circuit simulation
- **Fritzing**: Breadboard layout tool

### Suppliers
- **Mouser Electronics**: mouser.com
- **Digikey**: digikey.com
- **JLCPCB**: jlcpcb.com (PCB fabrication)
- **Hammond Manufacturing**: hammfg.com (enclosures)

### Learning Resources
- "The Art of Electronics" by Horowitz & Hill
- "Op Amps for Everyone" (Texas Instruments)
- YouTube: EEVblog, GreatScott!, ElectroBOOM

---

## Conclusion

Building a physical perceptron is a rewarding project that combines analog electronics, mechanical assembly, and machine learning concepts. The result is a unique, functional demonstration of how neural networks can be implemented in hardware.

**Estimated Total Time**: 30-50 hours  
**Skill Level Required**: Intermediate electronics  
**Satisfaction Level**: Very High! 🎉

Good luck with your build! Share your results on GitHub or electronics forums.
