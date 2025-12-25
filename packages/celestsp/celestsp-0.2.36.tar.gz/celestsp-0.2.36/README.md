# Celestial TSP

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.13%2B-blue)

## Overview

Celestial TSP calculates optimal observation order for celestial bodies.
The script uses the Traveling Salesman Problem (TSP) algorithm to find the shortest path between celestial bodies and generates a spherical image showing the optimal order.

## Table of Contents

- [Overview](#overview)
- [Table of Contents](#table-of-contents)
- [Installation](#installation)
- [Usage](#usage)
- [Results](#results)
- [License](#license)
- [Contact](#contact)

## Installation

```bash
brew tap rioriost/celestsp
brew install celestsp
```

## Usage

```bash
celestsp --help
usage: celestsp [-h] [--lat LAT] [--lon LON] [--height HEIGHT] [--date DATE] [--time TIME] [--tz TZ] [--output OUTPUT] [--first_body FIRST_BODY] input_file_path

Celestial TSP Planner

positional arguments:
  input_file_path       Input file path with celestial coordinates.

options:
  -h, --help            show this help message and exit
  --lat LAT             Latitude of observation location.
  --lon LON             Longitude of observation location.
  --height HEIGHT       Height of observation location (in meters).
  --date DATE           Observation date (YYYY-MM-DD).
  --time TIME           Observation time (HH:MM:SS).
  --tz TZ               Time zone offset (e.g., +9 for JST).
  --output OUTPUT       Filename for the output image.
  --first_body FIRST_BODY
                        Name of the celestial body to start the TSP from.
```

Provide the input file containing celestial coordinates and specify the observation location and time.

```bash
celestsp --lat 34.863 --lon 138.843 --height 1000 --date 2025-03-22 --time 18:30:00 --tz +9 sources/m_0322_1830.txt
```

```bash
cat sources/m_0322_1830.txt
M74
M33
M32
M31
M110
M76
M103
......
```

## Results
```
Location: Lat: 34.863, Lon: 138.843, 1000.0m
Observation Date/Time: 2025-03-22 18:30:00 +9

Optimal Order of Celestial Bodies:
Name: M39,     RA: 322.89, Dec:48.25, Altitude:1.12,   Azimuth:333.80, Times to set:0.22   Observable: True
Name: M52,     RA: 351.19, Dec:61.59, Altitude:21.74,  Azimuth:331.37, Times to set:inf    Observable: True
Name: M103,    RA: 23.34,  Dec:60.66, Altitude:35.73,  Azimuth:324.02, Times to set:inf    Observable: True
Name: M76,     RA: 25.58,  Dec:51.58, Altitude:35.16,  Azimuth:312.79, Times to set:5.09   Observable: True
Name: M110,    RA: 10.09,  Dec:41.69, Altitude:21.71,  Azimuth:306.68, Times to set:2.50   Observable: True
Name: M31,     RA: 10.68,  Dec:41.27, Altitude:21.91,  Azimuth:306.06, Times to set:2.50   Observable: True
Name: M32,     RA: 10.67,  Dec:40.87, Altitude:21.71,  Azimuth:305.68, Times to set:2.45   Observable: True
Name: M33,     RA: 23.46,  Dec:30.66, Altitude:26.30,  Azimuth:290.58, Times to set:2.45   Observable: True
Name: M74,     RA: 24.17,  Dec:15.78, Altitude:19.54,  Azimuth:276.16, Times to set:1.63   Observable: True
Name: M77,     RA: 40.67,  Dec:-0.01, Altitude:23.89,  Azimuth:252.15, Times to set:1.97   Observable: True
Name: M45,     RA: 56.60,  Dec:24.11, Altitude:50.17,  Azimuth:266.82, Times to set:4.25   Observable: True
Name: M36,     RA: 84.08,  Dec:34.13, Altitude:76.00,  Azimuth:271.95, Times to set:6.75   Observable: True
Name: M38,     RA: 82.17,  Dec:35.82, Altitude:74.58,  Azimuth:279.12, Times to set:6.75   Observable: True
Name: M37,     RA: 88.07,  Dec:32.55, Altitude:78.95,  Azimuth:261.61, Times to set:6.89   Observable: True
Name: M1,      RA: 83.63,  Dec:22.02, Altitude:70.04,  Azimuth:234.63, Times to set:5.93   Observable: True
Name: M35,     RA: 92.27,  Dec:24.34, Altitude:76.98,  Azimuth:218.37, Times to set:6.63   Observable: True
Name: M78,     RA: 86.69,  Dec:0.08,  Altitude:52.69,  Azimuth:204.35, Times to set:5.05   Observable: True
Name: M43,     RA: 83.88,  Dec:-5.27, Altitude:46.70,  Azimuth:205.57, Times to set:4.61   Observable: True
Name: M42,     RA: 83.82,  Dec:-5.39, Altitude:46.57,  Azimuth:205.59, Times to set:4.59   Observable: True
Name: M79,     RA: 81.04,  Dec:-24.52,Altitude:27.63,  Azimuth:200.75, Times to set:3.41   Observable: True
Name: M41,     RA: 101.50, Dec:-20.72,Altitude:34.39,  Azimuth:179.68, Times to set:5.00   Observable: True
Name: M50,     RA: 105.68, Dec:-8.37, Altitude:46.52,  Azimuth:173.52, Times to set:5.91   Observable: True
Name: M47,     RA: 114.15, Dec:-14.49,Altitude:39.08,  Azimuth:163.77, Times to set:6.17   Observable: True
Name: M46,     RA: 115.44, Dec:-14.84,Altitude:38.42,  Azimuth:162.32, Times to set:6.22   Observable: True
Name: M93,     RA: 116.14, Dec:-23.85,Altitude:29.54,  Azimuth:164.30, Times to set:5.79   Observable: True
Name: M48,     RA: 123.41, Dec:-5.73, Altitude:44.25,  Azimuth:148.28, Times to set:7.21   Observable: True
Name: M67,     RA: 132.85, Dec:11.81, Altitude:53.09,  Azimuth:121.02, Times to set:8.65   Observable: True
Name: M44,     RA: 130.05, Dec:19.62, Altitude:60.21,  Azimuth:113.38, Times to set:8.86   Observable: True
Name: M95,     RA: 160.99, Dec:11.70, Altitude:31.23,  Azimuth:97.85,  Times to set:10.52  Observable: True
Name: M96,     RA: 161.69, Dec:11.82, Altitude:30.72,  Azimuth:97.29,  Times to set:10.57  Observable: True
Name: M105,    RA: 161.96, Dec:12.58, Altitude:30.93,  Azimuth:96.38,  Times to set:10.62  Observable: True
Name: M65,     RA: 169.73, Dec:13.09, Altitude:24.84,  Azimuth:91.23,  Times to set:11.17  Observable: True
Name: M66,     RA: 170.06, Dec:12.99, Altitude:24.52,  Azimuth:91.13,  Times to set:11.20  Observable: True
Name: M98,     RA: 183.45, Dec:14.90, Altitude:14.60,  Azimuth:81.99,  Times to set:12.18  Observable: True
Name: M99,     RA: 184.71, Dec:14.42, Altitude:13.31,  Azimuth:81.72,  Times to set:12.23  Observable: True
Name: M100,    RA: 185.73, Dec:15.82, Altitude:13.25,  Azimuth:79.96,  Times to set:12.37  Observable: True
Name: M85,     RA: 186.35, Dec:18.19, Altitude:14.04,  Azimuth:77.58,  Times to set:12.54  Observable: True
Name: M88,     RA: 188.00, Dec:14.42, Altitude:10.65,  Azimuth:79.93,  Times to set:12.44  Observable: True
Name: M91,     RA: 188.86, Dec:14.50, Altitude:10.00,  Azimuth:79.40,  Times to set:12.52  Observable: True
Name: M90,     RA: 189.21, Dec:13.16, Altitude:8.98,   Azimuth:80.33,  Times to set:12.47  Observable: True
Name: M89,     RA: 188.92, Dec:12.56, Altitude:8.87,   Azimuth:81.00,  Times to set:12.42  Observable: True
Name: M58,     RA: 189.43, Dec:11.82, Altitude:8.04,   Azimuth:81.33,  Times to set:12.42  Observable: True
Name: M59,     RA: 190.51, Dec:11.65, Altitude:7.07,   Azimuth:80.88,  Times to set:12.47  Observable: True
Name: M60,     RA: 190.92, Dec:11.55, Altitude:6.69,   Azimuth:80.73,  Times to set:12.49  Observable: True
Name: M87,     RA: 187.71, Dec:12.39, Altitude:9.76,   Azimuth:81.81,  Times to set:12.32  Observable: True
Name: M86,     RA: 186.55, Dec:12.95, Altitude:11.01,  Azimuth:81.97,  Times to set:12.28  Observable: True
Name: M84,     RA: 186.27, Dec:12.89, Altitude:11.21,  Azimuth:82.18,  Times to set:12.25  Observable: True
Name: M49,     RA: 187.44, Dec:8.00,  Altitude:7.52,   Azimuth:85.63,  Times to set:12.11  Observable: True
Name: M61,     RA: 185.48, Dec:4.47,  Altitude:7.13,   Azimuth:89.68,  Times to set:11.80  Observable: True
Name: M53,     RA: 198.23, Dec:18.17, Altitude:4.65,   Azimuth:71.23,  Times to set:13.31  Observable: True
Name: M64,     RA: 194.18, Dec:21.68, Altitude:9.77,   Azimuth:70.48,  Times to set:13.24  Observable: True
Name: M3,      RA: 205.55, Dec:28.38, Altitude:5.24,   Azimuth:58.98,  Times to set:14.39  Observable: True
Name: M63,     RA: 198.96, Dec:42.03, Altitude:17.41,  Azimuth:50.62,  Times to set:15.06  Observable: True
Name: M94,     RA: 192.72, Dec:41.12, Altitude:20.99,  Azimuth:53.93,  Times to set:14.56  Observable: True
Name: M106,    RA: 184.74, Dec:47.30, Altitude:28.79,  Azimuth:50.44,  Times to set:14.80  Observable: True
Name: M109,    RA: 179.40, Dec:53.37, Altitude:33.91,  Azimuth:44.92,  Times to set:15.78  Observable: True
Name: M97,     RA: 168.70, Dec:55.02, Altitude:40.35,  Azimuth:44.26,  Times to set:15.95  Observable: True
Name: M108,    RA: 167.88, Dec:55.67, Altitude:40.87,  Azimuth:43.45,  Times to set:inf    Observable: True
Name: M40,     RA: 185.55, Dec:58.08, Altitude:31.81,  Azimuth:38.43,  Times to set:inf    Observable: True
Name: M101,    RA: 210.80, Dec:54.35, Altitude:17.65,  Azimuth:35.32,  Times to set:18.28  Observable: True
Name: M51,     RA: 202.47, Dec:47.20, Altitude:18.02,  Azimuth:44.63,  Times to set:15.95  Observable: True
Name: M102,    RA: 226.62, Dec:55.76, Altitude:11.79,  Azimuth:28.05,  Times to set:inf    Observable: True
Name: M82,     RA: 148.97, Dec:69.68, Altitude:46.66,  Azimuth:22.22,  Times to set:inf    Observable: True
Name: M81,     RA: 148.89, Dec:69.07, Altitude:46.97,  Azimuth:23.00,  Times to set:inf    Observable: True
Name: M34,     RA: 40.53,  Dec:42.72, Altitude:43.19,  Azimuth:298.84, Times to set:4.64   Observable: True
Plot saved as results_20250216_223009.png
```

![results_20250216_223009.png](https://raw.githubusercontent.com/rioriost/homebrew-celestsp/main/images/results_20250216_223009.png)

## Release Notes

### 0.2.36 Release
- Dependency update

### 0.2.35 Release
- Dependency update

### 0.2.34 Release
- Security update

### 0.2.33 Release
- Security update

### 0.2.32 Release
- Dependency update

### 0.2.31 Release
- Dependency update

### 0.2.30 Release
- Dependency update

### 0.2.29 Release
- Dependency update

### 0.2.28 Release
- Dependency update

### 0.2.27 Release
- Dependency update

### 0.2.26 Release
- Dependency update

### 0.2.25 Release
- Dependency update

### 0.2.24 Release
- Dependency update

### 0.2.23 Release
- Dependency update

### 0.2.22 Release
- Dependency update

### 0.2.21 Release
- Dependency update

### 0.2.20 Release
- Dependency update

### 0.2.19 Release
- Dependency update

### 0.2.18 Release
- Dependency update

### 0.2.17 Release
- Dependency update

### 0.2.16 Release
- Dependency update

### 0.2.15 Release
- Dependency update

### 0.2.14 Release
- Dependency update

### 0.2.13 Release
- Dependency update

### 0.2.12 Release
- Dependency update

### 0.2.11 Release
- Dependency update

### 0.2.10 Release
- Dependency update

### 0.2.9 Release
- Dependency update

### 0.2.8 Release
- Dependency update

### 0.2.7 Release
- Dependency update

### 0.2.6 Release
- Dependency update

### 0.2.5 Release
- Dependency update

### 0.2.4 Release
* Updated for the dependencies.

### 0.2.3 Release
* Updated for the dependencies.

### 0.2.2 Release
* Updated for the dependencies.

### 0.2.1 Release
* Updated for the dependencies.

### 0.1.0 Release
* Initial release.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

If you have any questions or suggestions, feel free to contact me.

- Name: Rio Fujita
- Email: rifujita@microsoft.com
- GitHub: [github-profile](https://github.com/rioriost)
