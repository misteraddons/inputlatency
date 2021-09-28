# Input latency testing for MiSTer FPGA
The purpose of this setup is to measure the latency of a USB controller using an arduino, DE10-nano, and IO board to form a closed-loop feedback system. The arduino is soldered to a button on the controller under test, and is also connected to the IO board's user port. When executed, the code commands a virtual button press on the controller and measures the response from the input latency core. The button under test must be mapped explicitly in the NES core. Results are monitored using putty or similar to connect to the COM port of the Arduino.

* Test PCB
  * I made a hat for the DE10-nano. It replaces the IO board and has a spot for the arduino pro-micro, 2 pins for the controller, and connects to all the necessary DE10-nano pins for signals and power.

* Troubleshooting
  * If no response is registered, ensure the button is mapped in the core
    * If this does not fix it, try flipping the + and - leads from the arduino to the button. Some only trigger when wired backwards from normal.
