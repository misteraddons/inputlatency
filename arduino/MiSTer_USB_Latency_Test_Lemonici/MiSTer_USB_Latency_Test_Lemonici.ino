/* This code is a slightly modified version of the code by @jorge_
 * Original can be found here: https://pastebin.com/ktqn7izx
 * Primary change is to output formatting to preserve more information
 * Also makes some minor changes to timings so serial correlation is slightly less likely
 */
 
long unsigned startMicros;
volatile long unsigned duration;
volatile long unsigned ISRCounter = 0;
 
int pinButton = 5; // Pulls button LOW
int pinMister = 2; // Registers press (needs to be an interrupt pin)
 
int delayPress = 16; // Time between HIGH and LOW toggles
 
void setup() {
  // I wanted decent random seed generation. This isn't perfect but it does the job much better than just reading a blank pin.
  // If you can do it better, please reach out.
  float base = ((float) analogRead(7) * analogRead(7)) / analogRead(7) * ((float) analogRead(7) * analogRead(7)) / analogRead(7);
  int seed = floor(abs(base * 10000));
  randomSeed(seed);

  pinMode(pinButton,INPUT);
  
  pinMode(pinMister,INPUT);
 
  // External interrupt 
  attachInterrupt(digitalPinToInterrupt(pinMister), timeArrival, FALLING);
 
  // Waits for serial monitor before starting
  while (!Serial);
  Serial.begin(115200);
  Serial.println("read, delay");
}
 
 
void loop() {
 
  // Random button presses
  delayMicroseconds(random(0, 1000));
 
  // Start timer
  startMicros = micros();
  
  // Controller button to ground
  pinMode(pinButton,OUTPUT);
  
  // Pause before and after button press
  delay(delayPress);
 
  // Reset pinButton to floating
  pinMode(pinButton,INPUT);
 
  delay(delayPress);
 
}
 
 
// Interrupt function, just timestamps and prints :)
void timeArrival(){

  // Calculate delay
  duration = micros() - startMicros;
  // Increment counter
  ISRCounter += 1;
  // Print count and delay, comma makes conversion to .csv easy
  Serial.print(ISRCounter);
  Serial.print(", ");
  Serial.println(duration / float(1000));
  
}
