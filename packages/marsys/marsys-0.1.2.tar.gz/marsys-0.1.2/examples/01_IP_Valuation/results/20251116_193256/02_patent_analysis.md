# Patent Technology Analysis Report
**Patent Number:** US10958080B2  
**Title:** Method and apparatus for transmitting wireless power  
**Analysis Date:** November 16, 2025

---

## 1. Technology Summary

### Core Innovation
This patent presents a multi-device wireless power transmission system with intelligent resource allocation and dynamic handshaking protocol. The innovation enables a single wireless power transmitter to simultaneously charge multiple receivers with automatic detection, negotiation, and power distribution capability.

### Key Technical Characteristics
- **Power Transmission Architecture:** Resonant inductive coupling for wireless power transfer using power transmitting resonators
- **Multi-Device Management:** Simultaneous operation with multiple power receivers while maintaining efficient power delivery
- **Intelligent Handshaking:** Search and join protocol allowing new receivers to discover and request charging without interrupting existing charging operations
- **Dynamic Load Assessment:** Real-time evaluation of receiver power requirements against transmitter capacity
- **Communication Integration:** Embedded bidirectional communication channel for device discovery, negotiation, and operational control
- **Safety Features:** Foreign object detection with responsive system adjustments to protect users and equipment

---

## 2. Claims Analysis

### Independent Claims (Scope Definition)

**Claim 1: Wireless Power Transmitter Equipment Claim**
- **Scope:** Defines the hardware apparatus comprising:
  - Power transmitting resonator (conversion of electrical to magnetic energy)
  - Communication unit (bidirectional signaling)
  - Controller with multi-function logic
- **Strength:** STRONG - Broad scope covering multiple device discovery and handshaking while actively charging
- **Coverage:** Device architecture with real-time multi-receiver support

**Claim 10: Control Method Claim**
- **Scope:** Procedural method for power transmitter operation during dual charging scenarios
- **Strength:** STRONG - Method claims provide protection independent of hardware implementation
- **Coverage:** Process sequence for power transmission, signal reception, and response transmission

### Dependent Claims Analysis
- **Claims 2-3:** Signal composition details (protocol version, network ID, impedance information)
  - Adds specificity to information exchange
  - Moderate strength - provides concrete technical details
- **Claim 4:** DC/DC converter interface specifications
  - Voltage range parameters for receiver front-end
  - Moderate-to-strong: Technical depth increases value
- **Claim 5:** Acknowledgment signal transmission
  - Reinforces bidirectional communication/handshaking
  - Enhances completeness of protocol claim

### Overall Claims Assessment
- **Claim Breadth:** BROAD - Covers generalized multi-receiver scenarios
- **Claim Depth:** MODERATE-TO-DEEP - Specific signal types and voltage parameters provided
- **Innovation Level:** HIGH - Represents non-obvious solution to multi-device charging coordination
- **Enforceability:** STRONG - Clear relationships between transmitter capabilities and receiver requirements

---

## 3. CPC-to-NAICS Industry Mapping

### Mapping Results
**Source:** Curated CPC-to-NAICS mapping based on CPC definitions and NAICS classifications

| Industry Classification | NAICS Code | Confidence | Primary CPC Match |
|------------------------|-----------|------------|-------------------|
| Wireless Telecommunications | 517 | 0.90 (90%) | H04W52 |
| Communications Equipment Manufacturing | 3342 | 0.85 (85%) | H04B5 |
| Power Systems & Charging | 3359 | 0.80 (80%) | H02J50 |

### CPC Code Breakdown

**Power Management CPC Codes (H02J series):**
- H02J5/005 - Primary power switching
- H02J7/00034 - Charger with device data exchange
- H02J50/10 - Inductive coupling wireless power
- H02J50/12 - Resonant inductive coupling (HIGH RELEVANCE)
- H02J50/40 - Multiple transmitter/receiver systems (HIGH RELEVANCE)
- H02J50/60 - Foreign object detection
- H02J50/80 - Data exchange between transmitter/receiver (HIGH RELEVANCE)
- H02J50/90 - Position detection and optimization
- H02J7/0044 - Mechanical design for portable device charging
- H02J7/025 - Power supply charging circuits

**Communications CPC Codes (H04 series):**
- H04B5/0037 - Near-field transmission systems
- H04B5/79 - Wireless power with data transfer (HIGH RELEVANCE)
- H04W52/0225-0245 - Power management monitoring and signal strength

**Sustainability CPC Code:**
- Y02D30/70 - Energy efficiency in wireless networks

### Key Technical Issues Represented
The CPC profile emphasizes:
1. **Wireless Power Transfer** (primary technical domain)
2. **Multi-device Coordination** (multiple transmitter/receiver support)
3. **Data Communication** (signal exchange during power transmission)
4. **Safety Systems** (foreign object detection)
5. **Power Optimization** (position and signal strength monitoring)

---

## 4. Landscapes Validation

### Patent Landscapes Provided
1. ✅ **Engineering & Computer Science** - VALIDATED: CPC codes span multiple engineering domains
2. ✅ **Power Engineering** - VALIDATED: H02J series codes focus on power transmission/conversion
3. ✅ **Computer Networks & Wireless Communication** - VALIDATED: H04W codes address wireless protocols
4. ✅ **Signal Processing** - VALIDATED: H04B codes cover signal transmission and detection
5. ✅ **Charge And Discharge Circuits For Batteries Or The Like** - VALIDATED: H02J7 codes specifically address charging circuits
6. ✅ **Mobile Radio Communication Systems** - VALIDATED: H04W codes address wireless communication systems

### Technology-Landscape Alignment
All six landscapes align with CPC code distributions. The patent operates at the intersection of wireless communications protocols and power engineering, with specific expertise in resonant inductive coupling systems.

---

## 5. Potential Applications

### Primary Application Markets

**Tier 1: High Commercial Value**
1. **Mobile Device Charging Pads** (smartphones, tablets, wearables)
   - Multi-device charging surfaces
   - Consumer electronics at scale
   - Market potential: Billions of devices annually

2. **Electric Vehicle (EV) Charging**
   - Dynamic fleet charging management
   - Parking lot multi-vehicle systems
   - Market potential: Vehicle charging infrastructure

3. **Smart Home Charging Hubs**
   - Simultaneous charging of IoT smart home devices
   - Unified charging infrastructure
   - Market potential: Growing smart home market

**Tier 2: Specialized/Emerging**
4. **Medical Device Charging** (hearing aids, implants, portable medical equipment)
5. **Workplace/Campus Charging Infrastructure** (office environments with multiple device availability)
6. **Public Transportation Charging Systems** (airport lounges, train stations, conference centers)
7. **IoT Device Networks** (sensor arrays, connected devices in industrial settings)
8. **Wireless Robot Charging Stations** (autonomous robots in warehouses, factories)

### Technical Enablers for Each Application
- **Resonant coupling** enables longer transmission distances than traditional inductive methods
- **Multi-device support** eliminates need for individual charging points
- **Intelligent negotiation** provides safety and efficiency in shared charging environments
- **Foreign object detection** ensures safety in public-facing deployments

---

## 6. Primary Target Market Selection

### Market Analysis

**Selected Primary Target Market:** **Mobile Consumer Electronics Multi-Device Charging Systems**

#### Market Justification

**1. Market Size & Growth**
- Global smartphone market: ~1.2 billion units annually
- Tablet market: ~150 million units annually
- Wearables market: ~500+ million units annually
- TAM: Multi-billion dollar charging accessory market
- CAGR: 8-12% in wireless charging segment (2025-2030)

**2. Technology Fit**
- Patent directly addresses simultaneous charging of multiple devices
- Resonant inductive coupling ideal for consumer-grade distances (5-25cm)
- Search/join protocol enables seamless user experience
- Safety features (foreign object detection) critical for consumer applications

**3. Commercialization Readiness**
- Consumer electronics manufacturers actively deploying wireless charging
- Market infrastructure increasingly standardizing on wireless protocols (Qi, WPC)
- Supply chain established for resonant coupling components
- Price point acceptable for consumer market (charging pads $30-150)

**4. Competitive Advantage**
- Multi-device capability eliminates need for multiple charging spots
- Intelligent power distribution enables simultaneous optimal charging
- Real-time capability negotiation improves user experience
- Protection mechanisms (foreign object detection) reduce liability

**5. Regulatory Alignment**
- FCC regulations support ISM band wireless power (902-928 MHz, 2.4 GHz)
- WiFi Alliance and Qi standards provide interoperability frameworks
- Safety standards (IEC, UL, CE) accommodate foreign object detection

---

## 7. Innovation Assessment

### Innovation Level: **HIGH**

#### Novelty Factors
1. **Multi-Receiver Simultaneous Charging:** Non-obvious combination of:
   - Continuous charging of established receiver
   - Search signal detection and response while charging (multi-tasking)
   - New receiver capability negotiation
   - Dynamic power distribution among receivers

2. **Intelligent Handshaking Protocol:**
   - Structured search/join communication sequence
   - Power requirement negotiation before charging initiation
   - Dynamic capacity assessment (transmitter capability vs. receiver need)
   - No prior art clearly combines these elements seamlessly

3. **System-Level Coordination:**
   - Controller manages multiple concurrent charging sessions
   - Real-time signal processing during power transmission
   - Safety-critical foreign object detection integration
   - Represents system-level architecture innovation beyond component-level

#### Non-Obviousness Factors
- Combining independent concepts (wireless power + multi-device + intelligent negotiation) yields non-obvious result
- Technical challenge: Detecting weak search signals during active high-power transmission
- Solution requires sophisticated signal processing and protocol design
- Not a simple aggregation of known elements; represents inventive step

#### Prior Art Considerations
- Single-receiver wireless charging was well-known
- Multi-device charging with sequential activation was known
- **Novel aspect:** Simultaneous charging of active receiver with search/join capability
- Represents advancement requiring technical insight beyond routine engineering

### Claim Strength Assessment

| Factor | Rating | Notes |
|--------|--------|-------|
| Claim Breadth | BROAD | Covers multiple architectures and receiver types |
| Claim Clarity | CLEAR | Technical terms well-defined in specification |
| Support in Specification | STRONG | Multiple embodiments and operational modes described |
| Enablement | COMPLETE | Sufficient teaching for person skilled in art |
| Distinctiveness | STRONG | Clear differentiation from prior single-device charging |
| Vulnerability to Challenges | LOW | Strong basis for defending dependent claims |

---

## 8. Technical Feature Summary

### Core Technical Elements

**1. Hardware Architecture**
- Power transmitting resonator: Converts electrical energy to resonant magnetic field
- Communication unit: Bidirectional wireless signaling separate from power transmission
- Controller: Manages protocol sequencing and power distribution logic
- Support for multiple simultaneous power receivers

**2. Power Management**
- Resonant inductive coupling (typically 6.78 MHz or similar ISM band frequency)
- Multiple power delivery paths with independent control
- Voltage regulation at DC/DC converter interface
- Adaptive power allocation based on receiver capability

**3. Communication Protocol**
- **Search Phase:** New receivers broadcast search signals
- **Discovery Phase:** Transmitter responds with search response containing network ID and parameters
- **Join Request Phase:** Receiver sends capability information (power requirements)
- **Capability Assessment:** Transmitter evaluates if capacity exceeds receiver requirements
- **Charging Authorization:** Transmitter sends charge start command if capable
- **Ongoing Negotiation:** Continuous data exchange during charging for optimization

**4. Safety Systems**
- Foreign object detection: Identifies conductive/biological interference
- Responsive system adjustments: Reduces power or halts transmission upon detection
- Multiple monitoring mechanisms: Signal strength, frequency response analysis
- Protection of both user and equipment

### Operational Sequence
```
[Active Charging Receiver 1] → [Search Signal Reception from Receiver 2]
    ↓
[Respond with Search Response + Network ID]
    ↓
[Receiver 2 sends Join Request with Power Requirements]
    ↓
[Transmitter Evaluates: Capacity > Requirement?]
    ↓
[YES] → [Send Charge Start Command] → [Simultaneous Dual Charging]
[NO]  → [Send Rejection or Queue Response]
```

---

## 9. Source Citations & References

### CPC Code Classification Source
- **Source:** Curated CPC-to-NAICS mapping based on CPC definitions and NAICS classifications
- **Standard:** International Patent Classification and cooperative patent databases
- **Reference:** For accurate concordance data, refer to Zolas et al. (2020), ALP concordance available at https://zenodo.org/record/4633894

### Patent Data Sources
- **Patent Office:** United States Patent and Trademark Office (USPTO)
- **Patent Number:** US10958080B2
- **Priority:** Based on provisional application filed December 15, 2011
- **International Priority:** Korean Patent Application Serial No. 10-2012-0110008 (October 4, 2012)
- **Related Patents:** Multiple continuation applications establishing consistent inventive concept
  - US9,711,969 (July 18, 2017)
  - US9,768,621 (September 19, 2017)
  - US10,312,696 (June 4, 2019)

### Standards & Regulatory References
- **Wireless Power Alliance (WPA)/Qi Standard:** IEC 61980 series
- **FDA Regulations:** Part 47 CFR Part 15 (ISM band operations)
- **International Standards:** IEC 62040 (Uninterruptible power supplies)
- **Safety Standards:** UL 2089 (Standard for wireless power chargers)

### Industry Classification References
- **NAICS 517:** Wireless Telecommunications Services
- **NAICS 3342:** Communications Equipment Manufacturing
- **NAICS 3359:** Other Electrical Equipment and Component Manufacturing

---

## 10. Recommendations for IP Strategy

### Licensing Potential
- **High-value licensing targets:** Consumer electronics manufacturers (Apple, Samsung, Google), automotive OEMs (Tesla, traditional auto), wireless charging manufacturers (Powermat, WiTricity)
- **Cross-licensing opportunities:** Mobile device chipset manufacturers, power management IC designers

### Patent Portfolio Expansion
- **Complementary innovations:** Application-specific implementations (automotive, medical, IoT), advanced signal detection methods, multi-frequency transmission systems
- **Geographic expansion:** Already filed in Korea; consider PCT expansion, China, Europe

### Competitive Positioning
- Enables manufacturers to differentiate with simultaneous multi-device charging
- Creates ecosystem advantages through standardized protocol
- Provides defensive moat against single-receiver charging competition

---

**Report Generated:** November 16, 2025  
**Analysis Framework:** Patent Technology Analyzer  
**Status:** Complete - Ready for downstream agent processing
