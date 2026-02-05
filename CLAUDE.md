# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a USB controller input latency testing system for MiSTer FPGA. It uses a closed-loop feedback system with an Arduino Pro Micro, DE10-nano, and IO board to measure controller latency in milliseconds.

## Architecture

**Hardware Components:**
- Arduino Pro Micro - triggers button presses and measures response time via interrupt
- DE10-nano with MiSTer FPGA running `NES_Lag_Tester.rbf` core
- Test PCB hat that replaces the IO board (connects Arduino, controller pins, and DE10-nano)

**Data Flow:**
1. Arduino triggers virtual button press on controller under test
2. MiSTer's latency test core detects the input
3. Arduino measures time delta via interrupt on pin 2
4. Results output via serial (CSV format: `read, delay`)

**Key Files:**
- `arduino/MiSTer_USB_Latency_Test_Lemonici/` - Arduino firmware for latency measurement
- `test_core/NES_Lag_Tester.rbf` - MiSTer FPGA core for detecting inputs
- `captures/` - Raw CSV capture files from individual controller tests
- `rpubs/input.Rmd` - R Markdown report that pulls from Google Sheets and generates visualizations
- `pcb/InputLatencyTester.zip` - PCB design files for the test hat

## Working with the R Report

The report in `rpubs/input.Rmd` uses these R packages:
- tidyverse, ggplot2 - data manipulation and visualization
- gsheet - pulls data from Google Sheets
- DT, crosstalk - interactive data tables with filters

Data source: https://docs.google.com/spreadsheets/d/1KlRObr3Be4zLch7Zyqg6qCJzGuhyGmXaOIUrpfncXIM/

## Arduino Configuration

Key timing parameters in the .ino file:
- `delayPress = 16` - ms between button state toggles
- `maxExtraDelayPress = 200` - timeout for slow controllers
- Pin 5: button trigger (pulls LOW)
- Pin 2: MiSTer response (interrupt, FALLING edge)

Serial output is 115200 baud, CSV format for easy import.
